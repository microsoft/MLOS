"OS-level benchmark environment on Azure."

import json
import logging
import requests

from mlos_bench.environment.status import Status
from mlos_bench.environment.base_svc import Service


_LOG = logging.getLogger(__name__)


class AzureVMService(Service):
    "Helper methods to manage VMs on Azure."

    # Azure REST API calls as described in
    # https://docs.microsoft.com/en-us/rest/api/compute/virtual-machines

    _URL_DEPLOY = "https://management.azure.com" \
                  "/subscriptions/%s" \
                  "/resourceGroups/%s" \
                  "/providers/Microsoft.Resources" \
                  "/deployments/%s" \
                  "?api-version=2022-05-01"

    _URL_START = "https://management.azure.com" \
                 "/subscriptions/%s" \
                 "/resourceGroups/%s" \
                 "/providers/Microsoft.Compute" \
                 "/virtualMachines/%s" \
                 "/start?api-version=2022-03-01"

    _URL_RUN = "https://management.azure.com/" \
               "/subscriptions/%s" \
               "/resourceGroups/%s" \
               "/providers/Microsoft.Compute" \
               "/virtualMachines/%s" \
               "/runCommand?api-version=2022-03-01"

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
        self.register([self.vm_deploy, self.vm_start, self.remote_exec])

        with open(config['template_path']) as fh_json:
            self._template = json.load(fh_json)

        self._url_deploy = AzureVMService._URL_DEPLOY % (
            config["subscription"],
            config["resource_group"],
            config["deployment_name"]
        )

        self._headers = {
            # Access token from `az account get-access-token`:
            "Authorization": "Bearer " + config["accessToken"]
        }

        self._url_start = AzureVMService._URL_START % (
            config["subscription"],
            config["resource_group"],
            config["vmName"]
        )

        self._url_run = AzureVMService._URL_RUN % (
            config["subscription"],
            config["resource_group"],
            config["vmName"]
        )

        self._headers = {
            # Access token from `az account get-access-token`:
            "Authorization": "Bearer " + config["accessToken"]
        }

    @staticmethod
    def _build_parameters(tunables):
        """
        Merge tunables with other parameters and convert into
        ARM Template format.
        """
        return {key: {"value": val} for (key, val) in tunables.items()}

    @staticmethod
    def _extract_parameters(json_data):
        """
        Extract parameters from the ARM Template REST response JSON.

        Returns
        -------
        parameters : dict
            Flat dictionary of parameters and their values.
        """
        return {
            key: val.get("value")
            for (key, val) in json_data.get(
                "properties", {}).get("parameters", {}).items()
        }

    def vm_deploy(self, tunables):
        """
        Check if Azure VM is ready. (Re)provision it, if necessary.

        Parameters
        ----------
        tunables : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            VMEnv tunables are variable parameters that, together with the
            VMEnv configuration, are sufficient to provision a VM.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, READY, FAILED}
        """
        _LOG.info("Deploy VM: %s :: %s", self.config["vmName"], tunables)

        json_req = {
            "properties": {
                "mode": "Incremental",
                "template": self._template,
                "parameters": AzureVMService._build_parameters(tunables)
            }
        }

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Request: PUT %s\n%s",
                       self._url_deploy, json.dumps(json_req, indent=2))

        response = requests.put(
            self._url_deploy, headers=self._headers, json=json_req)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Response: %s\n%s", response,
                       json.dumps(response.json(), indent=2))
        else:
            _LOG.info("Response: %s", response)

        if response.status_code == 200:
            params = AzureVMService._extract_parameters(response.json())
            _LOG.info("Extracted parameters: %s", params)
            return (Status.READY, params)
        elif response.status_code == 201:
            return (Status.PENDING, {})
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            # _LOG.error("Bad Request:\n%s", response.request.body)
            return (Status.FAILED, {})

    def vm_start(self, tunables):
        """
        Start the VM on Azure.

        Parameters
        ----------
        tunables : dict
            Flat dictionary of (key, value) pairs of tunable parameters.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is always {}.
            Status is one of {PENDING, READY, FAILED}
        """
        _LOG.info("Start VM: %s :: %s", self.config["vmName"], tunables)
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

    def remote_exec(self, tunables):
        """
        Run a command on Azure VM.

        Parameters
        ----------
        tunables : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have "commandId", "parameters", or "script" keys.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, READY, FAILED}
        """

        _LOG.info("Run a command on VM: %s :: %s %s %s",
                  self.config["vmName"], tunables["commandId"],
                  tunables.get("parameters", []),
                  tunables.get("script", []))

        json_req = tunables  # Pass to REST request as-is.
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Request: POST %s\n%s",
                       self._url_run, json.dumps(json_req, indent=2))

        response = requests.post(
            self._url_run, headers=self._headers, json=json_req)

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Response: %s\n%s", response,
                       json.dumps(response.json(), indent=2))
        else:
            _LOG.info("Response: %s", response)

        if response.status_code == 200:
            # TODO: extract the results from JSON response
            return (Status.READY, {})
        elif response.status_code == 202:
            return (Status.PENDING, {})
        else:
            _LOG.error("Response: %s :: %s", response, response.text)
            # _LOG.error("Bad Request:\n%s", response.request.body)
            return (Status.FAILED, {})
