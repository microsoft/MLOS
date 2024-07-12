#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Scheduler-side Environment to run scripts locally and upload/download data to the
shared storage.
"""

import logging
from datetime import datetime
from string import Template
from typing import Any, Dict, Generator, Iterable, List, Mapping, Optional, Tuple

from mlos_bench.environments.local.local_env import LocalEnv
from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.fileshare_type import SupportsFileShareOps
from mlos_bench.services.types.local_exec_type import SupportsLocalExec
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class LocalFileShareEnv(LocalEnv):
    """Scheduler-side Environment that runs scripts locally and uploads/downloads data
    to the shared file storage.
    """

    def __init__(
        self,
        *,
        name: str,
        config: dict,
        global_config: Optional[dict] = None,
        tunables: Optional[TunableGroups] = None,
        service: Optional[Service] = None,
    ):
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
        super().__init__(
            name=name,
            config=config,
            global_config=global_config,
            tunables=tunables,
            service=service,
        )

        assert self._service is not None and isinstance(
            self._service, SupportsLocalExec
        ), "LocalEnv requires a service that supports local execution"
        self._local_exec_service: SupportsLocalExec = self._service

        assert self._service is not None and isinstance(
            self._service, SupportsFileShareOps
        ), "LocalEnv requires a service that supports file upload/download operations"
        self._file_share_service: SupportsFileShareOps = self._service

        self._upload = self._template_from_to("upload")
        self._download = self._template_from_to("download")

    def _template_from_to(self, config_key: str) -> List[Tuple[Template, Template]]:
        """Convert a list of {"from": "...", "to": "..."} to a list of pairs of
        string.Template objects so that we can plug in self._params into it later.
        """
        return [(Template(d["from"]), Template(d["to"])) for d in self.config.get(config_key, [])]

    @staticmethod
    def _expand(
        from_to: Iterable[Tuple[Template, Template]],
        params: Mapping[str, TunableValue],
    ) -> Generator[Tuple[str, str], None, None]:
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
        self._is_ready = super().setup(tunables, global_config)
        if self._is_ready:
            assert self._temp_dir is not None
            params = self._get_env_params(restrict=False)
            params["PWD"] = self._temp_dir
            for path_from, path_to in self._expand(self._upload, params):
                self._file_share_service.upload(
                    self._params,
                    self._config_loader_service.resolve_path(
                        path_from,
                        extra_paths=[self._temp_dir],
                    ),
                    path_to,
                )
        return self._is_ready

    def _download_files(self, ignore_missing: bool = False) -> None:
        """
        Download files from the shared storage.

        Parameters
        ----------
        ignore_missing : bool
            If True, raise an exception when some file cannot be downloaded.
            If False, proceed with downloading other files and log a warning.
        """
        assert self._temp_dir is not None
        params = self._get_env_params(restrict=False)
        params["PWD"] = self._temp_dir
        for path_from, path_to in self._expand(self._download, params):
            try:
                self._file_share_service.download(
                    self._params,
                    path_from,
                    self._config_loader_service.resolve_path(
                        path_to,
                        extra_paths=[self._temp_dir],
                    ),
                )
            except FileNotFoundError as ex:
                _LOG.warning("Cannot download: %s", path_from)
                if not ignore_missing:
                    raise ex
            except Exception as ex:
                _LOG.exception("Cannot download %s to %s", path_from, path_to)
                raise ex

    def run(self) -> Tuple[Status, datetime, Optional[Dict[str, TunableValue]]]:
        """
        Download benchmark results from the shared storage and run post-processing
        scripts locally.

        Returns
        -------
        (status, timestamp, output) : (Status, datetime, dict)
            3-tuple of (Status, timestamp, output) values, where `output` is a dict
            with the results or None if the status is not COMPLETED.
            If run script is a benchmark, then the score is usually expected to
            be in the `score` field.
        """
        self._download_files()
        return super().run()

    def status(self) -> Tuple[Status, datetime, List[Tuple[datetime, str, Any]]]:
        self._download_files(ignore_missing=True)
        return super().status()
