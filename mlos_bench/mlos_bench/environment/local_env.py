"""
Scheduler-side benchmark environment to run scripts locally.
"""

import os
import json
import logging

from typing import Optional

import pandas

from mlos_bench.environment.status import Status
from mlos_bench.environment.base_environment import Environment
from mlos_bench.environment.base_service import Service
from mlos_bench.environment.tunable import TunableGroups

_LOG = logging.getLogger(__name__)


class LocalEnv(Environment):
    """
    Scheduler-side benchmark environment that runs scripts locally.
    """

    def __init__(self,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
        # pylint: disable=too-many-arguments
        """
        Create a new environment for local execution.

        Parameters
        ----------
        name: str
            Human-readable name of the environment.
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration. Each config must have at least the "tunable_params"
            and the "const_args" sections.
            `LocalEnv` must also have at least some of the following parameters:
            {setup, run, teardown, dump_params_file, read_results_file}
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

        self._temp_dir = self.config.get("temp_dir")
        self._script_setup = self.config.get("setup")
        self._script_run = self.config.get("run")
        self._script_teardown = self.config.get("teardown")

        self._dump_params_file = self.config.get("dump_params_file")
        self._read_results_file = self.config.get("read_results_file")

        if self._script_setup is None and \
           self._script_run is None and \
           self._script_teardown is None:
            raise ValueError("At least one of {setup, run, teardown} must be present")

        if self._script_setup is None and self._dump_params_file is not None:
            raise ValueError("'setup' must be present if 'dump_params_file' is specified")

        if self._script_run is None and self._read_results_file is not None:
            raise ValueError("'run' must be present if 'read_results_file' is specified")

    def setup(self, tunables: TunableGroups) -> bool:
        """
        Check if the environment is ready and set up the application
        and benchmarks, if necessary.

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

        if not self._script_setup:
            self._is_ready = True
            return True

        with self._service.temp_dir_context(self._temp_dir) as temp_dir:

            _LOG.info("Set up the environment locally: %s at %s", self, temp_dir)

            if self._dump_params_file:
                with open(os.path.join(temp_dir, self._dump_params_file),
                          "wt", encoding="utf-8") as fh_tunables:
                    # json.dump(self._params, fh_tunables)  # Tunables *and* const_args
                    json.dump(tunables.get_param_values(self._tunable_params.get_names()),
                              fh_tunables)

            (return_code, _stdout, stderr) = self._service.local_exec(
                self._script_setup, env=self._params, cwd=temp_dir)

            if return_code == 0:
                _LOG.info("Local set up complete: %s", self)
            else:
                _LOG.warning("ERROR: Local setup returns with code %d stderr:\n%s",
                             return_code, stderr)

            self._is_ready = (return_code == 0)

        return self._is_ready

    def benchmark(self):
        """
        Run an experiment in the local application environment.
        (Re)configure an application and launch the benchmark.

        Returns
        -------
        (benchmark_status, benchmark_result) : (enum, DataFrame)
            A pair of (benchmark status, benchmark result) values.
            benchmark_status is of type mlos_bench.environment.Status.
            benchmark_result is a pandas DataFrame of the benchmark data
            or None if the status is not COMPLETED.
        """
        (status, _) = result = super().benchmark()
        if not (status.is_ready and self._script_run):
            return result

        with self._service.temp_dir_context(self._temp_dir) as temp_dir:

            _LOG.info("Run benchmark locally on: %s at %s", self, temp_dir)
            (return_code, _stdout, stderr) = self._service.local_exec(
                self._script_run, env=self._params, cwd=temp_dir)

            if return_code != 0:
                _LOG.warning("ERROR: Local run returns with code %d stderr:\n%s",
                             return_code, stderr)
                return (Status.FAILED, None)

            data = pandas.read_csv(self._service.resolve_path(
                self._read_results_file, extra_paths=[temp_dir]))

            _LOG.info("Local run complete: %s ::\n%s", self, data)
            return (Status.SUCCEEDED, data)

    def teardown(self):
        """
        Clean up the local environment.
        """
        if self._script_teardown:
            _LOG.info("Local teardown: %s", self)
            (status, _) = self._service.local_exec(self._script_teardown, env=self._params)
            _LOG.info("Local teardown complete: %s :: %s", self, status)
        super().teardown()
