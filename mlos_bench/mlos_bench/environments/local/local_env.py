#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Scheduler-side benchmark environment to run scripts locally.
"""

import json
import logging
import sys

from datetime import datetime
from tempfile import TemporaryDirectory
from contextlib import nullcontext

from types import TracebackType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Type, Union
from typing_extensions import Literal

import pandas

from mlos_bench.environments.status import Status
from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.script_env import ScriptEnv
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.local_exec_type import SupportsLocalExec
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.util import path_join

_LOG = logging.getLogger(__name__)


class LocalEnv(ScriptEnv):
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
        super().__init__(name=name, config=config, global_config=global_config,
                         tunables=tunables, service=service)

        assert self._service is not None and isinstance(self._service, SupportsLocalExec), \
            "LocalEnv requires a service that supports local execution"
        self._local_exec_service: SupportsLocalExec = self._service

        self._temp_dir: Optional[str] = None
        self._temp_dir_context: Union[TemporaryDirectory, nullcontext, None] = None

        self._dump_params_file: Optional[str] = self.config.get("dump_params_file")
        self._dump_meta_file: Optional[str] = self.config.get("dump_meta_file")

        self._read_results_file: Optional[str] = self.config.get("read_results_file")
        self._read_telemetry_file: Optional[str] = self.config.get("read_telemetry_file")

    def __enter__(self) -> Environment:
        assert self._temp_dir is None and self._temp_dir_context is None
        self._temp_dir_context = self._local_exec_service.temp_dir_context(self.config.get("temp_dir"))
        self._temp_dir = self._temp_dir_context.__enter__()
        return super().__enter__()

    def __exit__(self, ex_type: Optional[Type[BaseException]],
                 ex_val: Optional[BaseException],
                 ex_tb: Optional[TracebackType]) -> Literal[False]:
        """
        Exit the context of the benchmarking environment.
        """
        assert not (self._temp_dir is None or self._temp_dir_context is None)
        self._temp_dir_context.__exit__(ex_type, ex_val, ex_tb)
        self._temp_dir = None
        self._temp_dir_context = None
        return super().__exit__(ex_type, ex_val, ex_tb)

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

        _LOG.info("Set up the environment locally: '%s' at %s", self, self._temp_dir)
        assert self._temp_dir is not None

        if self._dump_params_file:
            fname = path_join(self._temp_dir, self._dump_params_file)
            _LOG.debug("Dump tunables to file: %s", fname)
            with open(fname, "wt", encoding="utf-8") as fh_tunables:
                # json.dump(self._params, fh_tunables)  # Tunables *and* const_args
                json.dump(self._tunable_params.get_param_values(), fh_tunables)

        if self._dump_meta_file:
            fname = path_join(self._temp_dir, self._dump_meta_file)
            _LOG.debug("Dump tunables metadata to file: %s", fname)
            with open(fname, "wt", encoding="utf-8") as fh_meta:
                json.dump({
                    tunable.name: tunable.meta
                    for (tunable, _group) in self._tunable_params if tunable.meta
                }, fh_meta)

        if self._script_setup:
            (return_code, _output) = self._local_exec(self._script_setup, self._temp_dir)
            self._is_ready = bool(return_code == 0)
        else:
            self._is_ready = True

        return self._is_ready

    def run(self) -> Tuple[Status, Optional[Dict[str, TunableValue]]]:
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
        if not status.is_ready():
            return result

        assert self._temp_dir is not None

        stdout_data: Dict[str, TunableValue] = {}
        if self._script_run:
            (return_code, output) = self._local_exec(self._script_run, self._temp_dir)
            if return_code != 0:
                return (Status.FAILED, None)
            stdout_data = self._extract_stdout_results(output.get("stdout", ""))

        # FIXME: We should not be assuming that the only output file type is a CSV.
        if not self._read_results_file:
            _LOG.debug("Not reading the data at: %s", self)
            return (Status.SUCCEEDED, stdout_data)

        data = self._normalize_columns(pandas.read_csv(
            self._config_loader_service.resolve_path(
                self._read_results_file, extra_paths=[self._temp_dir]),
            index_col=False,
        ))

        _LOG.debug("Read data:\n%s", data)
        if list(data.columns) == ["metric", "value"]:
            _LOG.info("Local results have (metric,value) header and %d rows: assume long format", len(data))
            data = pandas.DataFrame([data.value.to_list()], columns=data.metric.to_list())
            # Try to convert string metrics to numbers.
            data = data.apply(pandas.to_numeric, errors="ignore")   # type: ignore[assignment]  # (false positive)
        elif len(data) == 1:
            _LOG.info("Local results have 1 row: assume wide format")
        else:
            raise ValueError(f"Invalid data format: {data}")

        stdout_data.update(data.iloc[-1].to_dict())
        _LOG.info("Local run complete: %s ::\n%s", self, stdout_data)
        return (Status.SUCCEEDED, stdout_data)

    @staticmethod
    def _normalize_columns(data: pandas.DataFrame) -> pandas.DataFrame:
        """
        Strip trailing spaces from column names (Windows only).
        """
        # Windows cmd interpretation of > redirect symbols can leave trailing spaces in
        # the final column, which leads to misnamed columns.
        # For now, we simply strip trailing spaces from column names to account for that.
        if sys.platform == 'win32':
            data.rename(str.rstrip, axis='columns', inplace=True)
        return data

    def status(self) -> Tuple[Status, List[Tuple[datetime, str, Any]]]:

        (status, _) = super().status()
        if not (self._is_ready and self._read_telemetry_file):
            return (status, [])

        assert self._temp_dir is not None
        try:
            fname = self._config_loader_service.resolve_path(
                self._read_telemetry_file, extra_paths=[self._temp_dir])

            # FIXME: We should not be assuming that the only output file type is a CSV.
            data = self._normalize_columns(
                pandas.read_csv(fname, index_col=False, parse_dates=[0]))

            expected_col_names = ["timestamp", "metric", "value"]
            if len(data.columns) != len(expected_col_names):
                raise ValueError(f'Telemetry data must have columns {expected_col_names}')

            if list(data.columns) != expected_col_names:
                # Assume no header - this is ok for telemetry data.
                data = pandas.read_csv(
                    fname, index_col=False, parse_dates=[0], names=expected_col_names)

        except FileNotFoundError as ex:
            _LOG.warning("Telemetry CSV file not found: %s :: %s", self._read_telemetry_file, ex)
            return (status, [])

        _LOG.debug("Read telemetry data:\n%s", data)
        col_dtypes: Mapping[int, Type] = {0: datetime}
        return (status, [
            (pandas.Timestamp(ts).to_pydatetime(), metric, value)
            for (ts, metric, value) in data.to_records(index=False, column_dtypes=col_dtypes)
        ])

    def teardown(self) -> None:
        """
        Clean up the local environment.
        """
        if self._script_teardown:
            _LOG.info("Local teardown: %s", self)
            (return_code, _output) = self._local_exec(self._script_teardown)
            _LOG.info("Local teardown complete: %s :: %s", self, return_code)
        super().teardown()

    def _local_exec(self, script: Iterable[str], cwd: Optional[str] = None) -> Tuple[int, dict]:
        """
        Execute a script locally in the scheduler environment.

        Parameters
        ----------
        script : Iterable[str]
            Lines of the script to run locally.
            Treat every line as a separate command to run.
        cwd : Optional[str]
            Work directory to run the script at.

        Returns
        -------
        (return_code, output) : (int, dict)
            Return code of the script and a dict with stdout/stderr. Return code = 0 if successful.
        """
        env_params = self._get_env_params()
        _LOG.info("Run script locally on: %s at %s with env %s", self, cwd, env_params)
        (return_code, stdout, stderr) = self._local_exec_service.local_exec(
            script, env=env_params, cwd=cwd)
        if return_code != 0:
            _LOG.warning("ERROR: Local script returns code %d stderr:\n%s", return_code, stderr)
        return (return_code, {"stdout": stdout, "stderr": stderr})
