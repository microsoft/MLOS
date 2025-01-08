#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Simple class to run an individual Trial on a given Environment."""

import logging
from datetime import datetime
from types import TracebackType
from typing import Any, Literal

from pytz import UTC

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.status import Status
from mlos_bench.event_loop_context import EventLoopContext
from mlos_bench.services.base_service import Service
from mlos_bench.services.config_persistence import ConfigPersistenceService
from mlos_bench.services.local.local_exec import LocalExecService
from mlos_bench.services.types import SupportsConfigLoading
from mlos_bench.storage.base_storage import Storage
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class TrialRunner:
    """
    Simple class to help run an individual Trial on an environment.

    TrialRunner manages the lifecycle of a single trial, including setup, run, teardown,
    and async status polling via EventLoopContext background threads.

    Multiple TrialRunners can be used in a multi-processing pool to run multiple trials
    in parallel, for instance.
    """

    @classmethod
    def create_from_json(
        cls,
        *,
        config_loader: Service,
        env_json: str,
        svcs_json: str | list[str] | None = None,
        num_trial_runners: int = 1,
        tunable_groups: TunableGroups | None = None,
        global_config: dict[str, Any] | None = None,
    ) -> list["TrialRunner"]:  # pylint: disable=too-many-arguments
        """
        Create a list of TrialRunner instances, and their associated Environments
        and Services, from JSON configurations.

        Since each TrialRunner instance is independent, they can be run in parallel,
        and hence must each get their own copy of the Environment and Services to
        operate on.

        The global_config is shared across all TrialRunners, but each copy gets its
        own unique trial_runner_id.

        Parameters
        ----------
        config_loader : Service
            A service instance capable of loading configuration (i.e., SupportsConfigLoading).
        env_json : str
            JSON file or string representing the environment configuration.
        svcs_json : str | list[str] | None
            JSON file(s) or string(s) representing the Services configuration.
        num_trial_runners : int
            Number of TrialRunner instances to create. Default is 1.
        tunable_groups : TunableGroups | None
            TunableGroups instance to use as the parent Tunables for the
            environment. Default is None.
        global_config : dict[str, Any] | None
            Global configuration parameters. Default is None.

        Returns
        -------
        list[TrialRunner]
            A list of TrialRunner instances created from the provided configuration.
        """
        assert isinstance(config_loader, SupportsConfigLoading)
        svcs_json = svcs_json or []
        tunable_groups = tunable_groups or TunableGroups()
        global_config = global_config or {}
        trial_runners: list[TrialRunner] = []
        for trial_runner_id in range(1, num_trial_runners + 1):  # use 1-based indexing
            # Make a fresh Environment and Services copy for each TrialRunner.
            # Give each global_config copy its own unique trial_runner_id.
            # This is important in case multiple TrialRunners are running in parallel.
            global_config_copy = global_config.copy()
            global_config_copy["trial_runner_id"] = trial_runner_id
            # Each Environment's parent service starts with at least a
            # LocalExecService in addition to the ConfigLoader.
            parent_service: Service = ConfigPersistenceService(
                config={"config_path": config_loader.config_paths},
                global_config=global_config_copy,
            )
            parent_service = LocalExecService(parent=parent_service)
            parent_service = config_loader.load_services(
                svcs_json,
                global_config_copy,
                parent_service,
            )
            env = config_loader.load_environment(
                env_json,
                tunable_groups.copy(),
                global_config_copy,
                service=parent_service,
            )
            trial_runners.append(TrialRunner(trial_runner_id, env))
        return trial_runners

    def __init__(self, trial_runner_id: int, env: Environment) -> None:
        self._trial_runner_id = trial_runner_id
        self._env = env
        assert self._env.parameters["trial_runner_id"] == self._trial_runner_id
        self._in_context = False
        self._is_running = False
        self._event_loop_context = EventLoopContext()

    def __repr__(self) -> str:
        return (
            f"TrialRunner({self.trial_runner_id}, {self.environment}"
            f"""[trial_runner_id={self.environment.parameters.get("trial_runner_id")}])"""
        )

    @property
    def trial_runner_id(self) -> int:
        """Get the TrialRunner's id."""
        return self._trial_runner_id

    @property
    def environment(self) -> Environment:
        """Get the Environment."""
        return self._env

    def __enter__(self) -> "TrialRunner":
        assert not self._in_context
        _LOG.debug("TrialRunner START :: %s", self)
        # TODO: self._event_loop_context.enter()
        self._env.__enter__()
        self._in_context = True
        return self

    def __exit__(
        self,
        ex_type: type[BaseException] | None,
        ex_val: BaseException | None,
        ex_tb: TracebackType | None,
    ) -> Literal[False]:
        assert self._in_context
        _LOG.debug("TrialRunner END :: %s", self)
        self._env.__exit__(ex_type, ex_val, ex_tb)
        # TODO: self._event_loop_context.exit()
        self._in_context = False
        return False  # Do not suppress exceptions

    @property
    def is_running(self) -> bool:
        """Get the running state of the current TrialRunner."""
        return self._is_running

    def run_trial(
        self,
        trial: Storage.Trial,
        global_config: dict[str, Any] | None = None,
    ) -> None:
        """
        Run a single trial on this TrialRunner's Environment and stores the results in
        the backend Trial Storage.

        Parameters
        ----------
        trial : Storage.Trial
            A Storage class based Trial used to persist the experiment trial data.
        global_config : dict
            Global configuration parameters.

        Returns
        -------
        (trial_status, trial_score) : (Status, dict[str, float] | None)
            Status and results of the trial.
        """
        assert self._in_context

        assert not self._is_running
        self._is_running = True

        assert trial.trial_runner_id == self.trial_runner_id, (
            f"TrialRunner {self} should not run trial {trial} "
            f"with different trial_runner_id {trial.trial_runner_id}."
        )

        if not self.environment.setup(trial.tunables, trial.config(global_config)):
            _LOG.warning("Setup failed: %s :: %s", self.environment, trial.tunables)
            # FIXME: Use the actual timestamp from the environment.
            _LOG.info("TrialRunner: Update trial results: %s :: %s", trial, Status.FAILED)
            trial.update(Status.FAILED, datetime.now(UTC))
            return

        # TODO: start background status polling of the environments in the event loop.

        # Block and wait for the final result.
        (status, timestamp, results) = self.environment.run()
        _LOG.info("TrialRunner Results: %s :: %s\n%s", trial.tunables, status, results)

        # In async mode (TODO), poll the environment for status and telemetry
        # and update the storage with the intermediate results.
        (_status, _timestamp, telemetry) = self.environment.status()

        # Use the status and timestamp from `.run()` as it is the final status of the experiment.
        # TODO: Use the `.status()` output in async mode.
        trial.update_telemetry(status, timestamp, telemetry)

        trial.update(status, timestamp, results)
        _LOG.info("TrialRunner: Update trial results: %s :: %s %s", trial, status, results)

        self._is_running = False

    def teardown(self) -> None:
        """
        Tear down the Environment.

        Call it after the completion of one (or more) `.run()` in the TrialRunner
        context.
        """
        assert self._in_context
        self._env.teardown()
