#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Scheduler-side Environment to run scripts locally
and upload/download data to the shared storage.
"""

import logging

from string import Template
from typing import Optional, Dict, List, Tuple, Any

from mlos_bench.service.base_service import Service
from mlos_bench.service.local.local_exec_type import SupportsLocalExec
from mlos_bench.environment.status import Status
from mlos_bench.environment.local.local_env import LocalEnv
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class LocalFileShareEnv(LocalEnv):
    """
    Scheduler-side Environment that runs scripts locally
    and uploads/downloads data to the shared file storage.
    """

    def __init__(self,
                 name: str,
                 config: dict,
                 global_config: Optional[dict] = None,
                 tunables: Optional[TunableGroups] = None,
                 service: Optional[Service] = None):
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
            `LocalFileShareEnv` must also have at least some of the following
            parameters: {setup, upload, run, download, teardown,
            dump_params_file, read_results_file}
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

        assert self._service is not None and isinstance(self._service, SupportsLocalExec), \
            "LocalEnv requires a service that supports local execution"
        self._local_exec_service: SupportsLocalExec = self._service

        self._upload = self._template_from_to("upload")
        self._download = self._template_from_to("download")

    def _template_from_to(self, config_key: str) -> List[Tuple[Template, Template]]:
        """
        Convert a list of {"from": "...", "to": "..."} to a list of pairs
        of string.Template objects so that we can plug in self._params into it later.
        """
        return [
            (Template(d['from']), Template(d['to']))
            for d in self.config.get(config_key, [])
        ]

    @staticmethod
    def _expand(from_to: List[Tuple[Template, Template]], params: Dict[str, Any]):
        """
        Substitute $var parameters in from/to path templates.
        Return a generator of (str, str) pairs of paths.
        """
        return (
            (path_from.safe_substitute(params), path_to.safe_substitute(params))
            for (path_from, path_to) in from_to
        )

    def setup(self, tunables: TunableGroups, global_config: Optional[dict] = None) -> bool:
        """
        Run setup scripts locally and upload the scripts and data to the shared storage.

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
        prev_temp_dir = self._temp_dir
        with self._local_exec_service.temp_dir_context(self._temp_dir) as self._temp_dir:
            # Override _temp_dir so that setup and upload both use the same path.
            self._is_ready = super().setup(tunables, global_config)
            if self._is_ready:
                params = self._params.copy()
                params["PWD"] = self._temp_dir
                for (path_from, path_to) in self._expand(self._upload, params):
                    self._service.upload(self._config_loader_service.resolve_path(
                        path_from, extra_paths=[self._temp_dir]), path_to)
            self._temp_dir = prev_temp_dir
            return self._is_ready

    def run(self) -> Tuple[Status, Optional[dict]]:
        """
        Download benchmark results from the shared storage
        and run post-processing scripts locally.

        Returns
        -------
        (status, output) : (Status, dict)
            A pair of (Status, output) values, where `output` is a dict
            with the results or None if the status is not COMPLETED.
            If run script is a benchmark, then the score is usually expected to
            be in the `score` field.
        """
        prev_temp_dir = self._temp_dir
        with self._local_exec_service.temp_dir_context(self._temp_dir) as self._temp_dir:
            # Override _temp_dir so that download and run both use the same path.
            params = self._params.copy()
            params["PWD"] = self._temp_dir
            for (path_from, path_to) in self._expand(self._download, params):
                self._service.download(
                    path_from, self._config_loader_service.resolve_path(
                        path_to, extra_paths=[self._temp_dir]))
            result = super().run()
            self._temp_dir = prev_temp_dir
            return result
