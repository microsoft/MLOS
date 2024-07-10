#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Base class for certain Azure Services classes that do deployments."""

import abc
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests
from requests.adapters import HTTPAdapter, Retry

from mlos_bench.dict_templater import DictTemplater
from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.authenticator_type import SupportsAuth
from mlos_bench.util import check_required_params, merge_parameters

_LOG = logging.getLogger(__name__)


class AzureDeploymentService(Service, metaclass=abc.ABCMeta):
    """Helper methods to manage and deploy Azure resources via REST APIs."""

    _POLL_INTERVAL = 4  # seconds
    _POLL_TIMEOUT = 300  # seconds
    _REQUEST_TIMEOUT = 5  # seconds
    _REQUEST_TOTAL_RETRIES = 10  # Total number retries for each request
    # Delay (seconds) between retries: {backoff factor} * (2 ** ({number of previous retries}))
    _REQUEST_RETRY_BACKOFF_FACTOR = 0.3

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

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        global_config: Optional[Dict[str, Any]] = None,
        parent: Optional[Service] = None,
        methods: Union[Dict[str, Callable], List[Callable], None] = None,
    ):
        """
        Create a new instance of an Azure Services proxy.

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
        super().__init__(config, global_config, parent, methods)

        check_required_params(
            self.config,
            [
                "subscription",
                "resourceGroup",
            ],
        )

        # These parameters can come from command line as strings, so conversion is needed.
        self._poll_interval = float(self.config.get("pollInterval", self._POLL_INTERVAL))
        self._poll_timeout = float(self.config.get("pollTimeout", self._POLL_TIMEOUT))
        self._request_timeout = float(self.config.get("requestTimeout", self._REQUEST_TIMEOUT))
        self._total_retries = int(
            self.config.get("requestTotalRetries", self._REQUEST_TOTAL_RETRIES)
        )
        self._backoff_factor = float(
            self.config.get("requestBackoffFactor", self._REQUEST_RETRY_BACKOFF_FACTOR)
        )

        self._deploy_template = {}
        self._deploy_params = {}
        if self.config.get("deploymentTemplatePath") is not None:
            # TODO: Provide external schema validation?
            template = self.config_loader_service.load_config(
                self.config["deploymentTemplatePath"],
                schema_type=None,
            )
            assert template is not None and isinstance(template, dict)
            self._deploy_template = template

            # Allow for recursive variable expansion as we do with global params and const_args.
            deploy_params = DictTemplater(self.config["deploymentTemplateParameters"]).expand_vars(
                extra_source_dict=global_config
            )
            self._deploy_params = merge_parameters(dest=deploy_params, source=global_config)
        else:
            _LOG.info(
                "No deploymentTemplatePath provided. Deployment services will be unavailable.",
            )

    @property
    def deploy_params(self) -> dict:
        """Get the deployment parameters."""
        return self._deploy_params

    @abc.abstractmethod
    def _set_default_params(self, params: dict) -> dict:
        """
        Optionally set some default parameters for the request.

        Parameters
        ----------
        params : dict
            The parameters.

        Returns
        -------
        dict
            The updated parameters.
        """
        raise NotImplementedError("Should be overridden by subclass.")

    def _get_session(self, params: dict) -> requests.Session:
        """Get a session object that includes automatic retries and headers for REST API
        calls.
        """
        total_retries = params.get("requestTotalRetries", self._total_retries)
        backoff_factor = params.get("requestBackoffFactor", self._backoff_factor)
        session = requests.Session()
        session.mount(
            "https://",
            HTTPAdapter(max_retries=Retry(total=total_retries, backoff_factor=backoff_factor)),
        )
        session.headers.update(self._get_headers())
        return session

    def _get_headers(self) -> dict:
        """Get the headers for the REST API calls."""
        assert self._parent is not None and isinstance(
            self._parent, SupportsAuth
        ), "Authorization service not provided. Include service-auth.jsonc?"
        return self._parent.get_auth_headers()

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

    def _azure_rest_api_post_helper(self, params: dict, url: str) -> Tuple[Status, dict]:
        """
        General pattern for performing an action on an Azure resource via its REST API.

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

        response = requests.post(url, headers=self._get_headers(), timeout=self._request_timeout)
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

    def _check_operation_status(self, params: dict) -> Tuple[Status, dict]:
        """
        Checks the status of a pending operation on an Azure resource.

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
            status = output.get("status")
            if status == "InProgress":
                return Status.RUNNING, {}
            elif status == "Succeeded":
                return Status.SUCCEEDED, output

        _LOG.error("Response: %s :: %s", response, response.text)
        return Status.FAILED, {}

    def _wait_deployment(self, params: dict, *, is_setup: bool) -> Tuple[Status, dict]:
        """
        Waits for a pending operation on an Azure resource to resolve to SUCCEEDED or
        FAILED. Return TIMED_OUT when timing out.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
        is_setup : bool
            If True, wait for resource being deployed; otherwise, wait for
            successful deprovisioning.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
            Result is info on the operation runtime if SUCCEEDED, otherwise {}.
        """
        params = self._set_default_params(params)
        _LOG.info(
            "Wait for %s to %s",
            params.get("deploymentName"),
            "provision" if is_setup else "deprovision",
        )
        return self._wait_while(self._check_deployment, Status.PENDING, params)

    def _wait_while(
        self,
        func: Callable[[dict], Tuple[Status, dict]],
        loop_status: Status,
        params: dict,
    ) -> Tuple[Status, dict]:
        """
        Invoke `func` periodically while the status is equal to `loop_status`. Return
        TIMED_OUT when timing out.

        Parameters
        ----------
        func : a function
            A function that takes `params` and returns a pair of (Status, {})
        loop_status: Status
            Steady state status - keep polling `func` while it returns `loop_status`.
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Requires deploymentName.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
        """
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=["deploymentName"],
        )

        poll_period = params.get("pollInterval", self._poll_interval)

        _LOG.debug(
            "Wait for %s status %s :: poll %.2f timeout %d s",
            config["deploymentName"],
            loop_status,
            poll_period,
            self._poll_timeout,
        )

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
        # pylint: disable=too-many-return-statements
        """
        Check if Azure deployment exists. Return SUCCEEDED if true, PENDING otherwise.

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
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=[
                "subscription",
                "resourceGroup",
                "deploymentName",
            ],
        )

        _LOG.info("Check deployment: %s", config["deploymentName"])

        url = self._URL_DEPLOY.format(
            subscription=config["subscription"],
            resource_group=config["resourceGroup"],
            deployment_name=config["deploymentName"],
        )

        session = self._get_session(params)
        try:
            response = session.get(url, timeout=self._request_timeout)
        except requests.exceptions.ReadTimeout:
            _LOG.warning("Request timed out after %.2f s: %s", self._request_timeout, url)
            return Status.RUNNING, {}
        except requests.exceptions.RequestException as ex:
            _LOG.exception("Error in request checking deployment", exc_info=ex)
            return (Status.FAILED, {})

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

    def _provision_resource(self, params: dict) -> Tuple[Status, dict]:
        """
        Attempts to (re)deploy a resource.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Tunables are variable parameters that, together with the
            Environment configuration, are sufficient to provision the resource.

        Returns
        -------
        result : (Status, dict={})
            A pair of Status and result. The result is the input `params` plus the
            parameters extracted from the response JSON, or {} if the status is FAILED.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """
        if not self._deploy_template:
            raise ValueError(f"Missing deployment template: {self}")
        params = self._set_default_params(params)
        config = merge_parameters(
            dest=self.config.copy(),
            source=params,
            required_keys=["deploymentName"],
        )
        _LOG.info("Deploy: %s :: %s", config["deploymentName"], params)

        params = merge_parameters(dest=self._deploy_params.copy(), source=params)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug(
                "Deploy: %s merged params ::\n%s",
                config["deploymentName"],
                json.dumps(params, indent=2),
            )

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
                    key: {"value": val}
                    for (key, val) in params.items()
                    if key in self._deploy_template.get("parameters", {})
                },
            }
        }

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
