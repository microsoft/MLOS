#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""A simple single-threaded synchronous optimization loop implementation."""
import logging
from typing import Any, Dict, List
from mlos_bench.environments.base_environment import Environment
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.schedulers.sync_scheduler import SyncScheduler
from mlos_bench.storage.base_storage import Storage
from mlos_bench.util import merge_parameters

_LOG = logging.getLogger(__name__)


class CyclicScheduler(SyncScheduler):
    """
    A simple single-threaded synchronous benchmarking loop implementation
    that cycles through a list of provided configuration IDs.

    This scheduler does not use any optimizer and is mainly used for benchmarking
    specific configurations against each other only.

    `cycle_config_ids` is the  list of existing configuration IDs to cycle through.
    It can be provided via the scheduler's config, or overwritten through the global config.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        config: Dict[str, Any],
        global_config: Dict[str, Any],
        environment: Environment,
        optimizer: Optimizer,
        storage: Storage,
        root_env_config: str,
    ):
        """
        Create a new instance of the scheduler. The constructor of this and the derived
        classes is called by the persistence service after reading the class JSON
        configuration. Other objects like the Environment and Optimizer are provided by
        the Launcher.
        Parameters
        ----------
        config : dict
            The configuration for the scheduler.
        global_config : dict
            The global configuration for the experiment.
        environment : Environment
            The environment to benchmark/optimize.
        optimizer : Optimizer
            The optimizer to use.
        storage : Storage
            The storage to use.
        root_env_config : str
            Path to the root environment configuration.
        """
        super().__init__(
            config=config,
            global_config=global_config,
            environment=environment,
            optimizer=optimizer,
            storage=storage,
            root_env_config=root_env_config,
        )
        config = merge_parameters(
            dest=config.copy(),
            source=global_config,
            required_keys=["cycle_config_ids"],
        )
        self._cycle_config_ids: List[int] = config.get("cycle_config_ids", [0])

    def _schedule_new_optimizer_suggestions(self) -> bool:
        not_done = self.not_done()
        if not_done:
            config_id = self._cycle_config_ids[self._trial_count % len(self._cycle_config_ids)]
            tunables = self.load_config(config_id)
            self.schedule_trial(tunables)
        return not_done
