#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Mock optimizer for mlos_bench.
"""

import logging
from abc import ABCMeta
from typing import Optional, Tuple, Union

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups

from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.services.base_service import Service

_LOG = logging.getLogger(__name__)


class TrackBestOptimizer(Optimizer, metaclass=ABCMeta):
    """
    Base Optimizer class that keeps track of the best score and configuration.
    """

    def __init__(self,
                 tunables: TunableGroups,
                 config: dict,
                 global_config: Optional[dict] = None,
                 service: Optional[Service] = None):
        super().__init__(tunables, config, global_config, service)
        self._best_config: Optional[TunableGroups] = None
        self._best_score: Optional[float] = None

    def register(self, tunables: TunableGroups, status: Status,
                 score: Optional[Union[float, dict]] = None) -> Optional[float]:
        registered_score = super().register(tunables, status, score)
        if status.is_succeeded() and (
            self._best_score is None or (registered_score is not None and registered_score < self._best_score)
        ):
            self._best_score = registered_score
            self._best_config = tunables.copy()
        return registered_score

    def get_best_observation(self) -> Union[Tuple[float, TunableGroups], Tuple[None, None]]:
        if self._best_score is None:
            return (None, None)
        assert self._best_config is not None
        return (self._best_score * self._opt_sign, self._best_config)
