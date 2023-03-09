"""
Application-specific benchmark environment.
"""

import logging
from typing import Optional

from mlos_bench.environment.status import Status
from mlos_bench.environment.base_environment import Environment
from mlos_bench.environment.base_service import Service
from mlos_bench.environment.tunable import TunableGroups

_LOG = logging.getLogger(__name__)


class RemoteEnv(Environment):
    """
    Environment to run benchmarks on a remote host.
    """

    def __init__(self,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
        # pylint: disable=too-many-arguments
        """
        Create a new environment for remote execution.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections.
            `RemoteEnv` must also have at least some of the following parameters:
            {setup, run, teardown, wait_boot}
        global_config : dict
            Free-format dictionary of global parameters (e.g., security credentials)
            to be mixed in into the "const_args" section of the local config.
        tunables : TunableGroups
            A collection of tunable parameters for *all* environments.
        service: Service
            An optional service object (e.g., providing methods to
            deploy or reboot a VM, etc.).
        """
        super().__init__(name, config, global_config, tunables, service)

        self._wait_boot = self.config.get("wait_boot", False)
        self._script_setup = self.config.get("setup")
        self._script_run = self.config.get("run")
        self._script_teardown = self.config.get("teardown")

        if self._script_setup is None and \
           self._script_run is None and \
           self._script_teardown is None and \
           not self._wait_boot:
            raise ValueError("At least one of {setup, run, teardown}" +
                             " must be present or wait_boot set to True.")

    def setup(self, tunables: TunableGroups) -> bool:
        """
        Check if the environment is ready and set up the application
        and benchmarks on a remote host.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of tunable OS and application parameters along with their
            values. Setting these parameters should not require an OS reboot.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        if not super().setup(tunables):
            return False

        if self._wait_boot:
            _LOG.info("Wait for the remote environment to start: %s", self)
            (status, params) = self._service.vm_start(self._params)
            if status.is_pending:
                (status, _) = self._service.wait_vm_operation(params)
            if not status.is_succeeded:
                return False

        if self._script_setup:
            _LOG.info("Set up the remote environment: %s", self)
            (status, _) = self._remote_exec(self._script_setup)
            _LOG.info("Remote set up complete: %s :: %s", self, status)
            self._is_ready = status.is_succeeded
        else:
            self._is_ready = True

        return self._is_ready

    def benchmark(self):
        """
        Submit a new experiment to the remote application environment.
        (Re)configure an application and launch the benchmark.

        Returns
        -------
        (benchmark_status, benchmark_result) : (enum, float)
            A pair of (benchmark status, benchmark result) values.
            benchmark_status is of type mlos_bench.environment.Status.
            benchmark_result is a floating point time of the benchmark in
            seconds or None if the status is not COMPLETED.
        """
        _LOG.info("Run benchmark remotely on: %s", self)
        (status, _) = result = super().benchmark()
        if not (status.is_ready and self._script_run):
            return result

        result = self._remote_exec(self._script_run)
        _LOG.info("Remote run complete: %s :: %s", self, result)
        return result

    def teardown(self):
        """
        Clean up and shut down the remote environment.
        """
        if self._script_teardown:
            _LOG.info("Remote teardown: %s", self)
            (status, _) = self._remote_exec(self._script_teardown)
            _LOG.info("Remote teardown complete: %s :: %s", self, status)
        super().teardown()

    def _remote_exec(self, script):
        """
        Run a script on the remote host.

        Parameters
        ----------
        script : [str]
            List of commands to be executed on the remote host.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
        """
        _LOG.debug("Submit script: %s", self)
        (status, output) = self._service.remote_exec(script, self._params)
        _LOG.debug("Script submitted: %s %s :: %s", self, status, output)
        if status in {Status.PENDING, Status.SUCCEEDED}:
            (status, output) = self._service.get_remote_exec_results(output)
            # TODO: extract the results from `output`.
        _LOG.debug("Status: %s :: %s", status, output)
        return (status, output)
