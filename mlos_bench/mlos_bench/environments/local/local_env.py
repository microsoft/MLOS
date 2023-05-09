#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Scheduler-side benchmark environment to run scripts locally.
"""

import os
import json
import logging

from typing import Optional, Tuple

import pandas

from mlos_bench.environments.status import Status
from mlos_bench.environments.base_environment import Environment
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.local_exec_type import SupportsLocalExec
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class LocalEnv(Environment):
    # pylint: disable=too-many-instance-attributes
    """
    Scheduler-side Environment that runs scripts locally.
    """

    def __init__(self,
                 *,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
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
        super().__init__(name=name, config=config, global_config=global_config, tunables=tunables, service=service)

        assert self._service is not None and isinstance(self._service, SupportsLocalExec), \
            "LocalEnv requires a service that supports local execution"
        self._local_exec_service: SupportsLocalExec = self._service

        self._temp_dir = self.config.get("temp_dir")
        self._script_setup = self.config.get("setup")
        self._script_run = self.config.get("run")
        self._script_teardown = self.config.get("teardown")

        self._dump_params_file: Optional[str] = self.config.get("dump_params_file")
        self._read_results_file: Optional[str] = self.config.get("read_results_file")

        if self._script_setup is None and \
           self._script_run is None and \
           self._script_teardown is None:
            raise ValueError("At least one of {setup, run, teardown} must be present")

        if self._script_setup is None and self._dump_params_file is not None:
            raise ValueError("'setup' must be present if 'dump_params_file' is specified")

        if self._script_run is None and self._read_results_file is not None:
            raise ValueError("'run' must be present if 'read_results_file' is specified")

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Check if the environment is ready and set up the application
        and benchmarks, if necessary.

        Parameters
        ----------
        tunables : TunableGroups
            A collection of tunable OS and application parameters along with their
            values. In a local environment these could be used to prepare a config
            file on the scheduler prior to transferring it to the remote environment,
            for instance.
        global_config : dict
            Free-format dictionary of global parameters of the environment
            that are not used in the optimization process.

        Returns
        -------
        is_success : bool
            True if operation is successful, false otherwise.
        """
        if not super().setup(tunables, global_config):
            return False

        if not self._script_setup:
            self._is_ready = True
            return True

        with self._local_exec_service.temp_dir_context(self._temp_dir) as temp_dir:

            _LOG.info("Set up the environment locally: %s at %s", self, temp_dir)

            if self._dump_params_file:
                with open(os.path.join(temp_dir, self._dump_params_file),
                          "wt", encoding="utf-8") as fh_tunables:
                    # json.dump(self._params, fh_tunables)  # Tunables *and* const_args
                    json.dump(tunables.get_param_values(self._tunable_params.get_covariant_group_names()),
                              fh_tunables)

            (return_code, _stdout, stderr) = self._local_exec_service.local_exec(
                self._script_setup, env=self._params, cwd=temp_dir)

            if return_code == 0:
                _LOG.info("Local set up complete: %s", self)
            else:
                _LOG.warning("ERROR: Local setup returns with code %d stderr:\n%s",
                             return_code, stderr)

            self._is_ready = bool(return_code == 0)

        return self._is_ready

    def run(self) -> Tuple[Status, Optional[dict]]:
        """
        Run a script in the local scheduler environment.

        Returns
        -------
        (status, output) : (Status, dict)
            A pair of (Status, output) values, where `output` is a dict
            with the results or None if the status is not COMPLETED.
            If run script is a benchmark, then the score is usually expected to
            be in the `score` field.
        """
        (status, _) = result = super().run()
        if not (status.is_ready and self._script_run):
            return result

        with self._local_exec_service.temp_dir_context(self._temp_dir) as temp_dir:

            _LOG.info("Run script locally on: %s at %s", self, temp_dir)
            (return_code, _stdout, stderr) = self._local_exec_service.local_exec(
                self._script_run, env=self._params, cwd=temp_dir)

            if return_code != 0:
                _LOG.warning("ERROR: Local run returns with code %d stderr:\n%s",
                             return_code, stderr)
                return (Status.FAILED, None)

            assert self._read_results_file is not None
            data = pandas.read_csv(self._config_loader_service.resolve_path(
                self._read_results_file, extra_paths=[temp_dir]))

            _LOG.debug("Read data:\n%s", data)
            if len(data) != 1:
                _LOG.warning("Local run has %d rows: assume long format of (metric, value)",
                             len(data))
                data = pandas.DataFrame([data.value.to_list()], columns=data.metric.to_list())

            data_dict = data.iloc[-1].to_dict()
            _LOG.info("Local run complete: %s ::\n%s", self, data_dict)
            return (Status.SUCCEEDED, data_dict)

    def teardown(self) -> None:
        """
        Clean up the local environment.
        """
        if self._script_teardown:
            _LOG.info("Local teardown: %s", self)
            (status, _, _) = self._local_exec_service.local_exec(self._script_teardown, env=self._params)
            _LOG.info("Local teardown complete: %s :: %s", self, status)
        super().teardown()
