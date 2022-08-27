"""
A collection Service functions for managing VMs on Azure.
"""

import json
import logging
import requests

from mlos_bench.environment import Service, Status, _check_required_params

_LOG = logging.getLogger(__name__)


class AzureVMService(Service):
    """
    Helper methods to manage VMs on Azure.
    """

    # Azure Resources Deployment REST API as described in
    # https://docs.microsoft.com/en-us/rest/api/resources/deployments

    _URL_DEPLOY = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Resources"
        "/deployments/{deployment_name}"
        "?api-version=2022-05-01"
    )

    # Azure Compute REST API calls as described in
    # https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines

    _URL_START = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Compute"
        "/virtualMachines/{vm_name}"
        "/start"
        "?api-version=2022-03-01"
    )

    _URL_REXEC_RUN = (
        "https://management.azure.com"
        "/subscriptions/{subscription}"
        "/resourceGroups/{resource_group}"
        "/providers/Microsoft.Compute"
        "/virtualMachines/{vm_name}"
        "/runCommand"
        "?api-version=2022-03-01"
    )

    def __init__(self, config):
        """
        Create a new instance of Azure services proxy.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        """
        super().__init__(config)

        _check_required_params(
            config, {
                "deployTemplatePath",
                "subscription",
                "accessToken",
                "resourceGroup",
                "deploymentName",
                "vmName"
            }
        )

        # Register methods that we want to expose to the Environment objects.
        self.register([
            self.vm_provision,
            self.vm_start,
            self.remote_exec,
            self.get_remote_exec_results
        ])

        with open(config['deployTemplatePath']) as fh_json:
            self._deploy_template = json.load(fh_json)

        self._url_deploy = AzureVMService._URL_DEPLOY.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            deployment_name=config["deploymentName"]
        )

        self._url_start = AzureVMService._URL_START.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"]
        )

        self._url_rexec_run = AzureVMService._URL_REXEC_RUN.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            vm_name=config["vmName"]
        )

        self._headers = {
            # Access token from `az account get-access-token`:
            "Authorization": "Bearer " + config["accessToken"]
        }

    @staticmethod
    def _build_arm_parameters(params):
        """
        Merge input with config parameters and convert the results
        into the ARM Template format.
        """
        return {key: {"value": val} for (key, val) in params.items()}

    @staticmethod
    def _extract_arm_parameters(json_data):
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

    def vm_provision(self, params):
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
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, READY, FAILED}
        """
        _LOG.info("Deploy VM: %s :: %s", self.config["vmName"], params)

        json_req = {
            "properties": {
                "mode": "Incremental",
                "template": self._deploy_template,
                "parameters": AzureVMService._build_arm_parameters(params)
            }
        }

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Request: PUT %s\n%s",
                       self._url_deploy, json.dumps(json_req, indent=2))

        response = requests.put(
            self._url_deploy, headers=self._headers, json=json_req)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Response: %s\n%s", response,
                       json.dumps(response.json(), indent=2)
                       if response.content else "")
        else:
            _LOG.info("Response: %s", response)

        if response.status_code == 200:
            output = AzureVMService._extract_arm_parameters(response.json())
            if _LOG.isEnabledFor(logging.DEBUG):
                _LOG.debug("Extracted parameters:\n%s",
                           json.dumps(output, indent=2))
            # self.config.update(params)
            return (Status.READY, output)
        elif response.status_code == 201:
            return (Status.PENDING, {})
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            # _LOG.error("Bad Request:\n%s", response.request.body)
            return (Status.FAILED, {})

    def vm_start(self, params):
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
            Status is one of {PENDING, READY, FAILED}
        """
        _LOG.info("Start VM: %s :: %s", self.config["vmName"], params)
        _LOG.debug("Request: POST %s", self._url_start)

        response = requests.post(self._url_start, headers=self._headers)
        _LOG.info("Response: %s", response)

        if response.status_code == 200:
            return (Status.PENDING, {})
        elif response.status_code == 202:
            return (Status.READY, {})
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            # _LOG.error("Bad Request:\n%s", response.request.body)
            return (Status.FAILED, {})

    def remote_exec(self, params):
        """
        Run a command on Azure VM.

        Parameters
        ----------
        tunables : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have "commandId", "script", and "parameters" keys.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, READY, FAILED}
        """
        _LOG.info("Run a command on VM: %s :: %s",
                  self.config["vmName"], params["commandId"])

        json_req = {
            "commandId": params["commandId"],
            "script": params["script"],
            "parameters": params.get("parameters", [])
        }

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Request: POST %s\n%s",
                       self._url_rexec_run, json.dumps(json_req, indent=2))

        response = requests.post(
            self._url_rexec_run, headers=self._headers, json=json_req)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Response: %s\n%s", response,
                       json.dumps(response.json(), indent=2)
                       if response.content else "")
        else:
            _LOG.info("Response: %s", response)

        if response.status_code == 200:
            # TODO: extract the results from JSON response
            return (Status.READY, {})
        elif response.status_code == 202:
            return (Status.PENDING, {
                "asyncResultsUrl": response.headers.get("Azure-AsyncOperation")
            })
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            # _LOG.error("Bad Request:\n%s", response.request.body)
            return (Status.FAILED, {})

    def get_remote_exec_results(self, params):
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
            Status is one of {PENDING, RUNNING, READY, FAILED}
        """
        _LOG.info("Check the results on VM: %s :: %s",
                  self.config["vmName"], params.get("commandId", ""))

        url = params.get("asyncResultsUrl")
        if url is None:
            return (Status.PENDING, {})

        response = requests.get(url, headers=self._headers)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Response: %s\n%s", response,
                       json.dumps(response.json(), indent=2)
                       if response.content else "")
        else:
            _LOG.info("Response: %s", response)

        if response.status_code == 200:
            # TODO: extract the results from JSON response
            output = response.json()
            status = output.get("status")
            if status == "InProgress":
                return (Status.RUNNING, {})
            elif status == "Succeeded":
                return (Status.READY, output.get("properties", {}).get("output", {}))

        _LOG.error("Response: %s :: %s", response, response.text)
        # _LOG.error("Bad Request:\n%s", response.request.body)
        return (Status.FAILED, {})
