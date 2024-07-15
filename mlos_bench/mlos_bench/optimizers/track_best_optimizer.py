#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Mock optimizer for mlos_bench."""

import logging
from abc import ABCMeta
from typing import Dict, Optional, Tuple, Union

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class TrackBestOptimizer(Optimizer, metaclass=ABCMeta):
    """Base Optimizer class that keeps track of the best score and configuration."""

    def __init__(
        self,
        tunables: TunableGroups,
        config: dict,
        global_config: Optional[dict] = None,
        service: Optional[Service] = None,
    ):
        super().__init__(tunables, config, global_config, service)
        self._best_config: Optional[TunableGroups] = None
        self._best_score: Optional[Dict[str, float]] = None

    def register(
        self,
        tunables: TunableGroups,
        status: Status,
        score: Optional[Dict[str, TunableValue]] = None,
    ) -> Optional[Dict[str, float]]:
        registered_score = super().register(tunables, status, score)
        if status.is_succeeded() and self._is_better(registered_score):
            self._best_score = registered_score
            self._best_config = tunables.copy()
        return registered_score

    def _is_better(self, registered_score: Optional[Dict[str, float]]) -> bool:
        """Compare the optimization scores to the best ones so far lexicographically."""
        if self._best_score is None:
            return True
        assert registered_score is not None
        for opt_target, best_score in self._best_score.items():
            score = registered_score[opt_target]
            if score < best_score:
                return True
            elif score > best_score:
                return False
        return False

    def get_best_observation(
        self,
    ) -> Union[Tuple[Dict[str, float], TunableGroups], Tuple[None, None]]:
        if self._best_score is None:
            return (None, None)
        score = self._get_scores(Status.SUCCEEDED, self._best_score)
        assert score is not None
        assert self._best_config is not None
        return (score, self._best_config)
