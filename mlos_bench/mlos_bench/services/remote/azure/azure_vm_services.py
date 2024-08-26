#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A collection Service functions for managing VMs on Azure."""

import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import requests

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.remote.azure.azure_deployment_services import (
    AzureDeploymentService,
)
from mlos_bench.services.types.host_ops_type import SupportsHostOps
from mlos_bench.services.types.host_provisioner_type import SupportsHostProvisioning
from mlos_bench.services.types.os_ops_type import SupportsOSOps
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec
from mlos_bench.util import merge_parameters

_LOG = logging.getLogger(__name__)


class AzureVMService(
    AzureDeploymentService,
    SupportsHostProvisioning,
    SupportsHostOps,
    SupportsOSOps,
    SupportsRemoteExec,
):
    """Helper methods to manage VMs on Azure."""

    # pylint: disable=too-many-ancestors

    # Azure Compute REST API calls as described in
    # https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/start
    _URL_START = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Compute"
        "/virtualMachines/{vm_name}"
        "/start"
        "?api-version=2022-03-01"
    )

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/power-off
    _URL_STOP = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Compute"
        "/virtualMachines/{vm_name}"
        "/powerOff"
        "?api-version=2022-03-01"
    )

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/deallocate
    _URL_DEALLOCATE = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Compute"
        "/virtualMachines/{vm_name}"
        "/deallocate"
        "?api-version=2022-03-01"
    )

    # TODO: This is probably the more correct URL to use for the deprovision operation.
    # However, previous code used the deallocate URL above, so for now, we keep
    # that and handle that change later.
    # See Also: #498
    _URL_DEPROVISION = _URL_DEALLOCATE

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/delete
    # _URL_DEPROVISION = (
    #    "https://management.azure.com"
    #    "/subscriptions/{subscription}"
    #    "/resourceGroups/{resource_group}"
    #    "/providers/Microsoft.Compute"
    #    "/virtualMachines/{vm_name}"
    #    "/delete"
    #    "?api-version=2022-03-01"
    # )

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/restart
    _URL_REBOOT = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Compute"
        "/virtualMachines/{vm_name}"
        "/restart"
        "?api-version=2022-03-01"
    )

    # From:
    # https://learn.microsoft.com/en-us/rest/api/compute/virtual-machine-run-commands/create-or-update
    _URL_REXEC_RUN = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Compute"
        "/virtualMachines/{vm_name}"
        "/runcommands/{command_name}"
        "?api-version=2024-07-01"
    )
    _URL_REXEC_RESULT = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Compute"
        "/virtualMachines/{vm_name}"
        "/runcommands/{command_name}"
        "?$expand=instanceView&api-version=2024-07-01"
    )

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional[Service] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
        """
        Create a new instance of Azure VM services proxy.

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
            config,
            global_config,
            parent,
            self.merge_methods(
                methods,
                [
                    # SupportsHostProvisioning
                    self.provision_host,
                    self.deprovision_host,
                    self.deallocate_host,
                    self.wait_host_deployment,
                    # SupportsHostOps
                    self.start_host,
                    self.stop_host,
                    self.restart_host,
                    self.wait_host_operation,
                    # SupportsOSOps
                    self.shutdown,
                    self.reboot,
                    self.wait_os_operation,
                    # SupportsRemoteExec
                    self.remote_exec,
                    self.get_remote_exec_results,
                ],
            ),
        )

        # As a convenience, allow reading customData out of a file, rather than
        # embedding it in a json config file.
        # Note: ARM templates expect this data to be base64 encoded, but that
        # can be done using the `base64()` string function inside the ARM template.
        self._custom_data_file = self.config.get("customDataFile", None)
        if self._custom_data_file:
            if self._deploy_params.get("customData", None):
                raise ValueError("Both customDataFile and customData are specified.")
            self._custom_data_file = self.config_loader_service.resolve_path(
                self._custom_data_file
            )
            with open(self._custom_data_file, "r", encoding="utf-8") as custom_data_fh:
                self._deploy_params["customData"] = custom_data_fh.read()

    def _set_default_params(self, params: dict) -> dict:  # pylint: disable=no-self-use
        # Try and provide a semi sane default for the deploymentName if not provided
        # since this is a common way to set the deploymentName and can same some
        # config work for the caller.
        if "vmName" in params and "deploymentName" not in params:
            params["deploymentName"] = f"{params['vmName']}-deployment"
            _LOG.info(
                "deploymentName missing from params. Defaulting to '%s'.",
                params["deploymentName"],
            )
        return params

    def wait_host_deployment(self, params: dict, *, is_setup: bool) -> Tuple[Status, dict]:
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
        return self._wait_deployment(params, is_setup=is_setup)

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
        # Try and provide a semi sane default for the deploymentName
        params.setdefault(f"{params['vmName']}-deployment")
        return self._wait_while(self._check_operation_status, Status.RUNNING, params)

    def wait_remote_exec_operation(self, params: dict) -> Tuple["Status", dict]:
        """
        Waits for a pending remote execution on an Azure VM to resolve to SUCCEEDED or
        FAILED. Return TIMED_OUT when timing out.

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
        _LOG.info("Wait for run command % on VM %s", params["commandName"], params["vmName"])
        return self._wait_while(self._check_remote_exec_status, Status.RUNNING, params)

    def wait_os_operation(self, params: dict) -> Tuple["Status", dict]:
        return self.wait_host_operation(params)

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
        return self._provision_resource(params)

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
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "deploymentName",
                "vmName",
            ],
        )
        _LOG.info("Deprovision VM: %s", config["vmName"])
        _LOG.info("Deprovision deployment: %s", config["deploymentName"])
        # TODO: Properly deprovision *all* resources specified in the ARM template.
        return self._azure_rest_api_post_helper(
            config,
            self._URL_DEPROVISION.format(
                subscription=config["subscription"],
                resource_group=config["resourceGroup"],
                vm_name=config["vmName"],
            ),
        )

    def deallocate_host(self, params: dict) -> Tuple[Status, dict]:
        """
        Deallocates the VM on Azure by shutting it down then releasing the compute
        resources.

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
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ],
        )
        _LOG.info("Deallocate VM: %s", config["vmName"])
        return self._azure_rest_api_post_helper(
            config,
            self._URL_DEALLOCATE.format(
                subscription=config["subscription"],
                resource_group=config["resourceGroup"],
                vm_name=config["vmName"],
            ),
        )

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
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ],
        )
        _LOG.info("Start VM: %s :: %s", config["vmName"], params)
        return self._azure_rest_api_post_helper(
            config,
            self._URL_START.format(
                subscription=config["subscription"],
                resource_group=config["resourceGroup"],
                vm_name=config["vmName"],
            ),
        )

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
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ],
        )
        _LOG.info("Stop VM: %s", config["vmName"])
        return self._azure_rest_api_post_helper(
            config,
            self._URL_STOP.format(
                subscription=config["subscription"],
                resource_group=config["resourceGroup"],
                vm_name=config["vmName"],
            ),
        )

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
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
            ],
        )
        _LOG.info("Reboot VM: %s", config["vmName"])
        return self._azure_rest_api_post_helper(
            config,
            self._URL_REBOOT.format(
                subscription=config["subscription"],
                resource_group=config["resourceGroup"],
                vm_name=config["vmName"],
            ),
        )

    def reboot(self, params: dict, force: bool = False) -> Tuple["Status", dict]:
        return self.restart_host(params, force)

    def remote_exec(
        self,
        script: Iterable[str],
        config: dict,
        env_params: dict,
    ) -> Tuple[Status, dict]:
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
        config = self._set_default_params(config)
        config = merge_parameters(
            dest=self.config.copy(),
            source=config,
            required_keys=[
                "subscription",
                "resourceGroup",
                "vmName",
                "commandName",
                "location",
            ],
        )

        if _LOG.isEnabledFor(logging.INFO):
            _LOG.info("Run a script on VM: %s\n  %s", config["vmName"], "\n  ".join(script))

        json_req = {
            "location": config["location"],
            "properties": {
                "source": {"script": "; ".join(script)},
                "parameters": [{"name": key, "value": val} for (key, val) in env_params.items()],
                "timeoutInSeconds": int(self._poll_timeout),
                "asyncExecution": True,
                "treatFailureAsDeploymentFailure": True,
            },
        }

        url = self._URL_REXEC_RUN.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
            command_name=config["commandName"],
        )

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Request: PUT %s\n%s", url, json.dumps(json_req, indent=2))

        response = requests.put(
            url,
            json=json_req,
            headers=self._get_headers(),
            timeout=self._request_timeout,
        )

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(
                "Response: %s\n%s",
                response,
                json.dumps(response.json(), indent=2) if response.content else "",
            )
        else:
            _LOG.info("Response: %s", response)

        if response.status_code in {200, 201}:
            results_url = self._URL_REXEC_RESULT.format(
                subscription=config["subscription"],
                resource_group=config["resourceGroup"],
                vm_name=config["vmName"],
                command_name=config["commandName"],
            )
            return (
                Status.PENDING,
                {**config, "asyncResultsUrl": results_url},
            )
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            return (Status.FAILED, {})

    def _check_remote_exec_status(self, params: dict) -> Tuple[Status, dict]:
        """
        Checks the status of a pending remote execution on an Azure VM.

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
            Status is one of {PENDING, RUNNING, SUCCEEDED, FAILED}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        url = params.get("asyncResultsUrl")
        if url is None:
            return Status.PENDING, {}

        session = self._get_session(params)
        try:
            response = session.get(url, timeout=self._request_timeout)
        except requests.exceptions.ReadTimeout:
            _LOG.warning("Request timed out after %.2f s: %s", self._request_timeout, url)
            return Status.RUNNING, {}
        except requests.exceptions.RequestException as ex:
            _LOG.exception("Error in request checking operation status", exc_info=ex)
            return (Status.FAILED, {})

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(
                "Response: %s\n%s",
                response,
                json.dumps(response.json(), indent=2) if response.content else "",
            )

        if response.status_code == 200:
            output = response.json()
            execution_state = (
                output.get("properties", {}).get("instanceView", {}).get("executionState")
            )
            if execution_state == "Running":
                return Status.RUNNING, {}
            elif execution_state == "Succeeded":
                return Status.SUCCEEDED, output

        _LOG.error("Response: %s :: %s", response, response.text)
        return Status.FAILED, {}

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
            A dict can have an "stdout" key with the remote output
            and an "stderr" key for errors / warnings.
        """
        _LOG.info("Check the results on VM: %s", config.get("vmName"))
        (status, result) = self.wait_remote_exec_operation(config)
        _LOG.debug("Result: %s :: %s", status, result)
        if not status.is_succeeded():
            # TODO: Extract the telemetry and status from stdout, if available
            return (status, result)

        output = result.get("properties", {}).get("instanceView", {})
        exit_code = output.get("exitCode")
        execution_state = output.get("executionState")
        outputs = output.get("output", "").strip().split("\n")
        errors = output.get("error", "").strip().split("\n")

        if execution_state == "Succeeded" and exit_code == 0:
            status = Status.SUCCEEDED
        else:
            status = Status.FAILED

        return (
            status,
            {
                "stdout": outputs,
                "stderr": errors,
                "exitCode": exit_code,
                "startTimestamp": datetime.fromisoformat(output["startTime"]),
                "endTimestamp": datetime.fromisoformat(output["endTime"]),
            },
        )
