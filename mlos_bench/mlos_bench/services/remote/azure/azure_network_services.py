#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for managing virtual networks on Azure.
"""

import json
import time
import logging

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import requests

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.remote.azure.azure_services import AzureService
from mlos_bench.services.types.authenticator_type import SupportsAuth
from mlos_bench.services.types.network_provisioner_type import SupportsNetworkProvisioning
from mlos_bench.util import check_required_params, merge_parameters

_LOG = logging.getLogger(__name__)


class AzureNetworkService(AzureService, SupportsNetworkProvisioning):
    """
    Helper methods to manage Virtual Networks on Azure.
    """

    # TODO: FIXME: Convert to Network REST APIs

    # Azure Compute REST API calls as described in
    # https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/delete
    _URL_DEPROVISION = (
        "https://management.azure.com" +
        "/subscriptions/{subscription}" +
        "/resourceGroups/{resource_group}" +
        "/providers/Microsoft.Compute" +
        "/virtualNetwork/{vnet_name}" +
        "/delete" +
        "?api-version=2022-03-01"
    )

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 global_config: Optional[Dict[str, Any]] = None,
                 parent: Optional[Service] = None,
                 methods: Union[Dict[str, Callable], List[Callable], None] = None):
        """
        Create a new instance of Azure Network services proxy.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        global_config : dict
            Free-format dictionary of global parameters.
        parent : Service
            Parent service that can provide mixin functions.
        methods : Union[Dict[str, Callable], List[Callable], None]
            New methods to register with the service.
        """
        super().__init__(
            config, global_config, parent,
            self.merge_methods(methods, [
                # SupportsNetworkProvisioning
                self.provision_network,
                self.deprovision_network,
                self.wait_network_deployment,
            ])
        )

    def wait_network_deployment(self, params: dict, *, is_setup: bool) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an Azure VM to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        is_setup : bool
            If True, wait for VM being deployed; otherwise, wait for successful deprovisioning.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        return self.wait_deployment(params, is_setup)

    # TODO: Finish cleaning up methods between base class and subclasses.

    def wait_host_operation(self, params: dict) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an Azure VM to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        params: dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncResultsUrl" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        _LOG.info("Wait for operation on VM %s", params["vmName"])
        return self._wait_while(self._check_vm_operation_status, Status.RUNNING, params)

    def _wait_while(self, func: Callable[[dict], Tuple[Status, dict]],
                    loop_status: Status, params: dict) -> Tuple[Status, dict]:
        """
        Invoke `func` periodically while the status is equal to `loop_status`.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        func : a function
            A function that takes `params` and returns a pair of (Status, {})
        loop_status: Status
            Steady state status - keep polling `func` while it returns `loop_status`.
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
        """
        config = merge_parameters(
            dest=self.config.copy(), source=params, required_keys=["deploymentName"])

        poll_period = params.get("pollInterval", self._poll_interval)

        _LOG.debug("Wait for %s status %s :: poll %.2f timeout %d s",
                   config["deploymentName"], loop_status, poll_period, self._poll_timeout)

        ts_timeout = time.time() + self._poll_timeout
        poll_delay = poll_period
        while True:
            # Wait for the suggested time first then check status
            ts_start = time.time()
            if ts_start >= ts_timeout:
                break

            if poll_delay > 0:
                _LOG.debug("Sleep for: %.2f of %.2f s", poll_delay, poll_period)
                time.sleep(poll_delay)

            (status, output) = func(params)
            if status != loop_status:
                return status, output

            ts_end = time.time()
            poll_delay = poll_period - ts_end + ts_start

        _LOG.warning("Request timed out: %s", params)
        return (Status.TIMED_OUT, {})

    def _check_deployment(self, params: dict) -> Tuple[Status, dict]:
        """
        Check if Azure deployment exists.
        Return SUCCEEDED if true, PENDING otherwise.

        Parameters
        ----------
        _params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            This parameter is not used; we need it for compatibility with
            other polling functions used in `_wait_while()`.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {SUCCEEDED, PENDING, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "deploymentName",
            ]
        )

        _LOG.info("Check deployment: %s", config["deploymentName"])

        url = self._URL_DEPLOY.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            deployment_name=config["deploymentName"],
        )

        response = requests.get(url, headers=self._get_headers(), timeout=self._request_timeout)
        _LOG.debug("Response: %s", response)

        if response.status_code == 200:
            output = response.json()
            state = output.get("properties", {}).get("provisioningState", "")

            if state == "Succeeded":
                return (Status.SUCCEEDED, {})
            elif state in {"Accepted", "Creating", "Deleting", "Running", "Updating"}:
                return (Status.PENDING, {})
            else:
                _LOG.error("Response: %s :: %s", response, json.dumps(output, indent=2))
                return (Status.FAILED, {})
        elif response.status_code == 404:
            return (Status.PENDING, {})

        _LOG.error("Response: %s :: %s", response, response.text)
        return (Status.FAILED, {})

    def provision_host(self, params: dict) -> Tuple[Status, dict]:
        """
        Check if Azure VM is ready. Deploy a new VM, if necessary.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            HostEnv tunables are variable parameters that, together with the
            HostEnv configuration, are sufficient to provision a VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is the input `params` plus the
            parameters extracted from the response JSON, or {} if the status is FAILED.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(dest=self.config.copy(), source=params)
        _LOG.info("Deploy: %s :: %s", config["deploymentName"], params)

        params = merge_parameters(dest=self._deploy_params.copy(), source=params)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Deploy: %s merged params ::\n%s",
                       config["deploymentName"], json.dumps(params, indent=2))

        url = self._URL_DEPLOY.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            deployment_name=config["deploymentName"],
        )

        json_req = {
            "properties": {
                "mode": "Incremental",
                "template": self._deploy_template,
                "parameters": {
                    key: {"value": val} for (key, val) in params.items()
                    if key in self._deploy_template.get("parameters", {})
                }
            }
        }

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Request: PUT %s\n%s", url, json.dumps(json_req, indent=2))

        response = requests.put(url, json=json_req,
                                headers=self._get_headers(), timeout=self._request_timeout)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Response: %s\n%s", response,
                       json.dumps(response.json(), indent=2)
                       if response.content else "")
        else:
            _LOG.info("Response: %s", response)

        if response.status_code == 200:
            return (Status.PENDING, config)
        elif response.status_code == 201:
            output = self._extract_arm_parameters(response.json())
            if _LOG.isEnabledFor(logging.DEBUG):
                _LOG.debug("Extracted parameters:\n%s", json.dumps(output, indent=2))
            params.update(output)
            params.setdefault("asyncResultsUrl", url)
            params.setdefault("deploymentName", config["deploymentName"])
            return (Status.PENDING, params)
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            # _LOG.error("Bad Request:\n%s", response.request.body)
            return (Status.FAILED, {})

    def deprovision_host(self, params: dict) -> Tuple[Status, dict]:
        """
        Deprovisions the VM on Azure by deleting it.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "deploymentName",
                "vmName",
            ]
        )
        _LOG.info("Deprovision VM: %s", config["vmName"])
        _LOG.info("Deprovision deployment: %s", config["deploymentName"])
        # TODO: Properly deprovision *all* resources specified in the ARM template.
        return self._azure_vm_post_helper(config, self._URL_DEPROVISION.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        ))

    def deallocate_host(self, params: dict) -> Tuple[Status, dict]:
        """
        Deallocates the VM on Azure by shutting it down then releasing the compute resources.

        Note: This can cause the VM to arrive on a new host node when its
        restarted, which may have different performance characteristics.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ]
        )
        _LOG.info("Deallocate VM: %s", config["vmName"])
        return self._azure_vm_post_helper(config, self._URL_DEALLOCATE.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        ))

    def start_host(self, params: dict) -> Tuple[Status, dict]:
        """
        Start the VM on Azure.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ]
        )
        _LOG.info("Start VM: %s :: %s", config["vmName"], params)
        return self._azure_vm_post_helper(config, self._URL_START.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        ))

    def stop_host(self, params: dict, force: bool = False) -> Tuple[Status, dict]:
        """
        Stops the VM on Azure by initiating a graceful shutdown.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        force : bool
            If True, force stop the Host/VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ]
        )
        _LOG.info("Stop VM: %s", config["vmName"])
        return self._azure_vm_post_helper(config, self._URL_STOP.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        ))

    def shutdown(self, params: dict, force: bool = False) -> Tuple["Status", dict]:
        return self.stop_host(params, force)

    def restart_host(self, params: dict, force: bool = False) -> Tuple[Status, dict]:
        """
        Reboot the VM on Azure by initiating a graceful shutdown.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        force : bool
            If True, force restart the Host/VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ]
        )
        _LOG.info("Reboot VM: %s", config["vmName"])
        return self._azure_vm_post_helper(config, self._URL_REBOOT.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        ))

    def reboot(self, params: dict, force: bool = False) -> Tuple["Status", dict]:
        return self.restart_host(params, force)

    def remote_exec(self, script: Iterable[str], config: dict,
                    env_params: dict) -> Tuple[Status, dict]:
        """
        Run a command on Azure VM.

        Parameters
        ----------
        script : Iterable[str]
            A list of lines to execute as a script on a remote VM.
        config : dict
            Flat dictionary of (key, value) pairs of the Environment parameters.
            They usually come from `const_args` and `tunable_params`
            properties of the Environment.
        env_params : dict
            Parameters to pass as *shell* environment variables into the script.
            This is usually a subset of `config` with some possible conversions.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(
            dest=self.config.copy(),
            source=config,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ]
        )

        if _LOG.isEnabledFor(logging.INFO):
            _LOG.info("Run a script on VM: %s\n  %s", config["vmName"], "\n  ".join(script))

        json_req = {
            "commandId": "RunShellScript",
            "script": list(script),
            "parameters": [{"name": key, "value": val} for (key, val) in env_params.items()]
        }

        url = self._URL_REXEC_RUN.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        )

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Request: POST %s\n%s", url, json.dumps(json_req, indent=2))

        response = requests.post(
            url, json=json_req, headers=self._get_headers(), timeout=self._request_timeout)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Response: %s\n%s", response,
                       json.dumps(response.json(), indent=2)
                       if response.content else "")
        else:
            _LOG.info("Response: %s", response)

        if response.status_code == 200:
            # TODO: extract the results from JSON response
            return (Status.SUCCEEDED, config)
        elif response.status_code == 202:
            return (Status.PENDING, {
                **config,
                "asyncResultsUrl": response.headers.get("Azure-AsyncOperation")
            })
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            # _LOG.error("Bad Request:\n%s", response.request.body)
            return (Status.FAILED, {})

    def get_remote_exec_results(self, config: dict) -> Tuple[Status, dict]:
        """
        Get the results of the asynchronously running command.

        Parameters
        ----------
        config : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncResultsUrl" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            A dict can have an "stdout" key with the remote output.
        """
        _LOG.info("Check the results on VM: %s", config.get("vmName"))
        (status, result) = self.wait_host_operation(config)
        _LOG.debug("Result: %s :: %s", status, result)
        if not status.is_succeeded():
            # TODO: Extract the telemetry and status from stdout, if available
            return (status, result)
        val = result.get("properties", {}).get("output", {}).get("value", [])
        return (status, {"stdout": val[0].get("message", "")} if val else {})
