"""
Application-specific benchmark environment.
"""

import json
import logging
from typing import Optional

from mlos_bench.environment.status import Status
from mlos_bench.environment.base_environment import Environment
from mlos_bench.environment.base_service import Service
from mlos_bench.environment.tunable import TunableGroups

_LOG = logging.getLogger(__name__)


class AppEnv(Environment):
    """
    Application-level benchmark environment.
    """

    _POLL_DELAY = 5  # Default polling interval in seconds.

    def __init__(self,
        name: str,
        config: dict,
        global_config: Optional[dict] = None,
        tunables: Optional[TunableGroups] = None,
        service: Optional[Service] = None,
    ):
        # pylint: disable=too-many-arguments
        """
        Create a new application environment with a given config.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections.
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
        self._script = self.config["script"]
        self._poll_delay = self.config.get("pollDelay", AppEnv._POLL_DELAY)

    def setup(self):
        """
        Check if the environment is ready and set up the application
        and benchmarks, if necessary.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Set up")
        return True

    def teardown(self):
        # Teardown app
        _LOG.info("App tear down")

        # Cleanup for the app
        status, cmd_output = self._service.remote_exec(["/mnt/osat-fs/cleanup-app.sh"], {})
        # Wait for cleanup script to complete
        if status == Status.PENDING:
            try:
                status, _cleanup_output = self._service.get_remote_exec_results(cmd_output)
            except TimeoutError:
                _LOG.error("Cleanup app timed out: %s", cmd_output)
                return False

        _LOG.info("Final status of app tear down: %s", status)

        return status == Status.READY

    def run(self, tunables: TunableGroups):
        """
        Submit a new experiment to the application environment.
        (Re)configure an application and launch the benchmark.

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
        _LOG.info("Run: %s", tunables)

        # Setup app
        status, cmd_output = self._service.remote_exec(["/mnt/osat-fs/setup-app.sh"], {})
        # Wait for setup script to complete
        if status == Status.PENDING:
            try:
                status, _setup_output = self._service.get_remote_exec_results(cmd_output)
                _LOG.debug("Setup app: %s", _setup_output)
            except TimeoutError:
                _LOG.error("Setup app timed out: %s", cmd_output)
                return False

        params = self._combine_tunables(tunables)
        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Benchmark:\n%s", json.dumps(params, indent=2))

        # TODO: Configure the application and start the benchmark
        (status, output) = self._service.remote_exec(self._script, params)
        self._result = (status, None)

        if status not in {Status.PENDING, Status.READY}:
            return False

        self.config.update(output)
        return True

    def _check_results(self):
        """
        Check if the results of the benchmark are available.

        Returns
        -------
        (benchmark_status, benchmark_result) : (enum, float)
            A pair of (benchmark status, benchmark result) values.
        """
        _LOG.debug("Check results: %s", self)
        (status, output) = self._service.get_remote_exec_results(self.config)
        # TODO: extract the results from `output`.
        _LOG.debug("Benchmark status: %s :: %s", status, output)
        return (status, None)

    def status(self):
        """
        Get the status of the environment.

        Returns
        -------
        status : mlos_bench.environment.Status
            Current status of the benchmark environment.
        """
        self._result = self._check_results()
        return self._result[0]

    def result(self):
        """
        Get the results of the benchmark. This is a blocking call that waits
        for the completion of the benchmark. It can have PENDING status only if
        the environment object has been read from the storage and not updated
        with the actual status yet.

        Returns
        -------
        (benchmark_status, benchmark_result) : (enum, float)
            A pair of (benchmark status, benchmark result) values.
            benchmark_status is of type mlos_bench.environment.Status.
            benchmark_result is a floating point time of the benchmark in
            seconds or None if the status is not COMPLETED.
        """
        try:
            status, output = self._service.get_remote_exec_results(self.config)
        except TimeoutError:
            _LOG.error("App result timed out: %s", self.config)
            return self._result

        _LOG.info("Benchmark result:\n%s", output["value"][0]["message"])
        self._result = (status, 123.456)  # FIXME: use the actual data
        return self._result
