#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Mock optimizer for mlos_bench."""

import logging
from abc import ABCMeta

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
        global_config: dict | None = None,
        service: Service | None = None,
    ):
        super().__init__(tunables, config, global_config, service)
        self._best_config: TunableGroups | None = None
        self._best_score: dict[str, float] | None = None

    def register(
        self,
        tunables: TunableGroups,
        status: Status,
        score: dict[str, TunableValue] | None = None,
    ) -> dict[str, float] | None:
        registered_score = super().register(tunables, status, score)
        if status.is_succeeded() and self._is_better(registered_score):
            self._best_score = registered_score
            self._best_config = tunables.copy()
        return registered_score

    def _is_better(self, registered_score: dict[str, float] | None) -> bool:
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
    ) -> tuple[dict[str, float], TunableGroups] | tuple[None, None]:
        if self._best_score is None:
            return (None, None)
        score = self._get_scores(Status.SUCCEEDED, self._best_score)
        assert score is not None
        assert self._best_config is not None
        return (score, self._best_config)
