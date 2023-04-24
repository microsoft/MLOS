#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
No-op implementation of the storage interface.
"""

import logging
from typing import Optional, List, Tuple, Dict, Iterator, Any

from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.storage.base_storage import Storage

_LOG = logging.getLogger(__name__)


class NullExperiment(Storage.Experiment):
    """
    No-op implementation of the storage for an experiment.
    """

    def merge(self, experiment_ids: List[str]) -> None:
        raise NotImplementedError()

    def load(self, opt_target: Optional[str] = None) -> Tuple[List[dict], List[float]]:
        return ([], [])

    def pending_trials(self) -> Iterator['Storage.Trial']:
        return iter([])

    def new_trial(self, tunables: TunableGroups,
                  config: Optional[Dict[str, Any]] = None) -> 'Storage.Trial':
        trial = Storage.Trial(
            tunables=tunables,
            experiment_id=self._experiment_id,
            trial_id=self._trial_id,
            config_id=self._trial_id,  # Always unique since there is no storage.
            opt_target=self._opt_target,
            config=config,
        )
        _LOG.info("New Trial: %s", trial)
        self._trial_id += 1
        return trial


class NullStorage(Storage):
    # pylint: disable=too-few-public-methods
    """
    No-op implementation of the storage interface.
    """

    def experiment(self, *,
                   experiment_id: str,
                   trial_id: int,
                   root_env_config: str,
                   description: str,
                   opt_target: str) -> 'Storage.Experiment':
        return NullExperiment(
            tunables=self._tunables,
            experiment_id=experiment_id,
            trial_id=trial_id,
            root_env_config=root_env_config,
            opt_target=opt_target,
        )
