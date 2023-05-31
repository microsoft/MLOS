#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for managing VMs on Azure.
"""

import json
import time
import logging

from typing import Callable, Iterable, Tuple

import requests

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec
from mlos_bench.services.types.vm_provisioner_type import SupportsVMOps
from mlos_bench.util import check_required_params, merge_parameters

_LOG = logging.getLogger(__name__)


class AzureVMService(Service, SupportsVMOps, SupportsRemoteExec):
    """
    Helper methods to manage VMs on Azure.
    """

    _POLL_INTERVAL = 4     # seconds
    _POLL_TIMEOUT = 300    # seconds
    _REQUEST_TIMEOUT = 5   # seconds

    # Azure Resources Deployment REST API as described in
    # https://docs.microsoft.com/en-us/rest/api/resources/deployments

    _URL_DEPLOY = (
        "https://management.azure.com" +
        "/subscriptions/{subscription}" +
        "/resourceGroups/{resource_group}" +
        "/providers/Microsoft.Resources" +
        "/deployments/{deployment_name}" +
        "?api-version=2022-05-01"
    )

    # Azure Compute REST API calls as described in
    # https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/start
    _URL_START = (
        "https://management.azure.com" +
        "/subscriptions/{subscription}" +
        "/resourceGroups/{resource_group}" +
        "/providers/Microsoft.Compute" +
        "/virtualMachines/{vm_name}" +
        "/start" +
        "?api-version=2022-03-01"
    )

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/power-off
    _URL_STOP = (
        "https://management.azure.com" +
        "/subscriptions/{subscription}" +
        "/resourceGroups/{resource_group}" +
        "/providers/Microsoft.Compute" +
        "/virtualMachines/{vm_name}" +
        "/powerOff" +
        "?api-version=2022-03-01"
    )

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/deallocate
    _URL_DEPROVISION = (
        "https://management.azure.com" +
        "/subscriptions/{subscription}" +
        "/resourceGroups/{resource_group}" +
        "/providers/Microsoft.Compute" +
        "/virtualMachines/{vm_name}" +
        "/deallocate" +
        "?api-version=2022-03-01"
    )

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/restart
    _URL_REBOOT = (
        "https://management.azure.com" +
        "/subscriptions/{subscription}" +
        "/resourceGroups/{resource_group}" +
        "/providers/Microsoft.Compute" +
        "/virtualMachines/{vm_name}" +
        "/restart" +
        "?api-version=2022-03-01"
    )

    # From: https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines/run-command
    _URL_REXEC_RUN = (
        "https://management.azure.com" +
        "/subscriptions/{subscription}" +
        "/resourceGroups/{resource_group}" +
        "/providers/Microsoft.Compute" +
        "/virtualMachines/{vm_name}" +
        "/runCommand" +
        "?api-version=2022-03-01"
    )

    def __init__(self, config: dict, parent: Service):
        """
        Create a new instance of Azure services proxy.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(config, parent)

        check_required_params(
            config, {
                "subscription",
                "accessToken",
                "resourceGroup",
                "deploymentName",
                "deploymentTemplatePath",
                "deploymentTemplateParameters",
            }
        )

        # Register methods that we want to expose to the Environment objects.
        self.register([
            self.wait_vm_deployment,
            self.wait_vm_operation,
            self.vm_provision,
            self.vm_start,
            self.vm_stop,
            self.vm_deprovision,
            self.vm_restart,
            self.remote_exec,
            self.get_remote_exec_results,
        ])

        # These parameters can come from command line as strings, so conversion is needed.
        self._poll_interval = float(config.get("pollInterval", self._POLL_INTERVAL))
        self._poll_timeout = float(config.get("pollTimeout", self._POLL_TIMEOUT))
        self._request_timeout = float(config.get("requestTimeout", self._REQUEST_TIMEOUT))

        # TODO: Provide external schema validation?
        template = self.config_loader_service.load_config(
            config['deploymentTemplatePath'], schema_type=None)
        assert template is not None and isinstance(template, dict)
        self._deploy_template = template

        self._deploy_params = merge_parameters(
            dest=config['deploymentTemplateParameters'].copy(), source=self.config)

        self._headers = {
            # Access token from `az account get-access-token`:
            "Authorization": "Bearer " + config["accessToken"]
        }

    @staticmethod
    def _extract_arm_parameters(json_data: dict) -> dict:
        """
        Extract parameters from the ARM Template REST response JSON.

        Returns
        -------
        parameters : dict
            Flat dictionary of parameters and their values.
        """
        return {
            key: val.get("value")
            for (key, val) in json_data.get("properties", {}).get("parameters", {}).items()
            if val.get("value") is not None
        }

    def _azure_vm_post_helper(self, params: dict, url: str) -> Tuple[Status, dict]:
        """
        General pattern for performing an action on an Azure VM via its REST API.

        Parameters
        ----------
        params: dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        url: str
            REST API url for the target to perform on the Azure VM.
            Should be a url that we intend to POST to.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED}
            Result will have a value for 'asyncResultsUrl' if status is PENDING,
            and 'pollInterval' if suggested by the API.
        """
        _LOG.debug("Request: POST %s", url)

        response = requests.post(url, headers=self._headers, timeout=self._request_timeout)
        _LOG.debug("Response: %s", response)

        # Logical flow for async operations based on:
        # https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/async-operations
        if response.status_code == 200:
            return (Status.SUCCEEDED, params.copy())
        elif response.status_code == 202:
            result = params.copy()
            if "Azure-AsyncOperation" in response.headers:
                result["asyncResultsUrl"] = response.headers.get("Azure-AsyncOperation")
            elif "Location" in response.headers:
                result["asyncResultsUrl"] = response.headers.get("Location")
            if "Retry-After" in response.headers:
                result["pollInterval"] = float(response.headers["Retry-After"])

            return (Status.PENDING, result)
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            # _LOG.error("Bad Request:\n%s", response.request.body)
            return (Status.FAILED, {})

    def _check_vm_operation_status(self, params: dict) -> Tuple[Status, dict]:
        """
        Checks the status of a pending operation on an Azure VM.

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

        response = requests.get(url, headers=self._headers, timeout=self._request_timeout)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Response: %s\n%s", response,
                       json.dumps(response.json(), indent=2)
                       if response.content else "")

        if response.status_code == 200:
            output = response.json()
            status = output.get("status")
            if status == "InProgress":
                return Status.RUNNING, {}
            elif status == "Succeeded":
                return Status.SUCCEEDED, output

        _LOG.error("Response: %s :: %s", response, response.text)
        return Status.FAILED, {}

    def wait_vm_deployment(self, is_setup: bool, params: dict) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an Azure VM to resolve to SUCCEEDED or FAILED.
        Return TIMED_OUT when timing out.

        Parameters
        ----------
        is_setup : bool
            If True, wait for VM being deployed; otherwise, wait for successful deprovisioning.
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        _LOG.info("Wait for %s to %s", params["deploymentName"],
                  "provision" if is_setup else "deprovision")
        return self._wait_while(self._check_deployment, Status.PENDING, params)

    def wait_vm_operation(self, params: dict) -> Tuple[Status, dict]:
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

        response = requests.head(url, headers=self._headers, timeout=self._request_timeout)
        _LOG.debug("Response: %s", response)

        if response.status_code == 204:
            return (Status.SUCCEEDED, {})
        elif response.status_code == 404:
            return (Status.PENDING, {})

        _LOG.error("Response: %s :: %s", response, response.text)
        return (Status.FAILED, {})

    def vm_provision(self, params: dict) -> Tuple[Status, dict]:
        """
        Check if Azure VM is ready. Deploy a new VM, if necessary.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            VMEnv tunables are variable parameters that, together with the
            VMEnv configuration, are sufficient to provision a VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is the input `params` plus the
            parameters extracted from the response JSON, or {} if the status is FAILED.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        config = merge_parameters(dest=self.config.copy(), source=params)
        params = merge_parameters(dest=self._deploy_params.copy(), source=params)
        _LOG.info("Deploy: %s :: %s", config["deploymentName"], params)

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
                                headers=self._headers, timeout=self._request_timeout)

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

    def vm_start(self, params: dict) -> Tuple[Status, dict]:
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

    def vm_stop(self, params: dict) -> Tuple[Status, dict]:
        """
        Stops the VM on Azure by initiating a graceful shutdown.

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
        _LOG.info("Stop VM: %s", config["vmName"])
        return self._azure_vm_post_helper(config, self._URL_STOP.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        ))

    def vm_deprovision(self, params: dict) -> Tuple[Status, dict]:
        """
        Deallocates the VM on Azure by shutting it down then releasing the compute resources.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always the same as input `params`.
            Status is one of {PENDING, SUCCEEDED, FAILED}
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
        _LOG.info("Deprovision: %s", config["deploymentName"])
        # TODO: Properly deprovision all resources specified in the ARM template.
        if "vmName" in config:
            return self.vm_stop(params)
        return (Status.SUCCEEDED, config)

    def vm_restart(self, params: dict) -> Tuple[Status, dict]:
        """
        Reboot the VM on Azure by initiating a graceful shutdown.

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
        _LOG.info("Reboot VM: %s", config["vmName"])
        return self._azure_vm_post_helper(config, self._URL_REBOOT.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        ))

    def remote_exec(self, script: Iterable[str], params: dict) -> Tuple[Status, dict]:
        """
        Run a command on Azure VM.

        Parameters
        ----------
        script : Iterable[str]
            A list of lines to execute as a script on a remote VM.
        params : dict
            Flat dictionary of (key, value) pairs of parameters.
            They usually come from `const_args` and `tunable_params`
            properties of the Environment.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
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

        if _LOG.isEnabledFor(logging.INFO):
            _LOG.info("Run a script on VM: %s\n  %s", config["vmName"], "\n  ".join(script))

        json_req = {
            "commandId": "RunShellScript",
            "script": list(script),
            "parameters": [{"name": key, "value": val} for (key, val) in params.items()]
        }

        url = self._URL_REXEC_RUN.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"],
        )

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Request: POST %s\n%s", url, json.dumps(json_req, indent=2))

        response = requests.post(
            url, json=json_req, headers=self._headers, timeout=self._request_timeout)

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

    def get_remote_exec_results(self, params: dict) -> Tuple[Status, dict]:
        """
        Get the results of the asynchronously running command.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncResultsUrl" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
        """
        config = merge_parameters(
            dest=self.config.copy(), source=params, required_keys=["vmName"])

        _LOG.info("Check the results on VM: %s", config["vmName"])

        status, result = self.wait_vm_operation(params)

        if status.is_succeeded:
            return status, result.get("properties", {}).get("output", {})
        else:
            return status, result
