"Application-specific benchmark environment."

import json
import logging

from mlos_bench.environment import Environment, Status

_LOG = logging.getLogger(__name__)


class AppEnv(Environment):
    "Application-level benchmark environment."

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

    def run(self, tunables):
        """
        Submit a new experiment to the application environment.
        (Re)configure an application and launch the benchmark.

        Parameters
        ----------
        tunables : dict
            Flat dictionary of (key, value) of the OS and application
            parameters. Setting these parameters should not require an
            OS reboot.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        _LOG.info("Run: %s", tunables)

        # FIXME: Plug in the tunables into the script for remote execution
        # params = self._combine_tunables(tunables)
        params = self._const_args

        if _LOG.isEnabledFor(logging.DEBUG):
            _LOG.debug("Benchmark:\n%s", json.dumps(params, indent=2))

        # TODO: Configure the application and start the benchmark
        (status, _output) = self._service.remote_exec(params)
        return status in {Status.PENDING, Status.READY}

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
        self._result = (Status.COMPLETED, 123.456)
        _LOG.info("Benchmark result: %s", self._result)
        return self._result
