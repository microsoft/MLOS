#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Mock optimizer for mlos_bench.
"""

import random
import logging
from typing import Tuple, List, Union

from mlos_bench.environment.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups

from mlos_bench.optimizer.base_optimizer import Optimizer

_LOG = logging.getLogger(__name__)


class MockOptimizer(Optimizer):
    """
    Mock optimizer to test the Environment API.
    """

    def __init__(self, tunables: TunableGroups, config: dict):
        super().__init__(tunables, config)
        rnd = random.Random(config.get("seed", 42))
        self._random = {
            "categorical": lambda tunable: rnd.choice(tunable.categorical_values),
            "float": lambda tunable: rnd.uniform(*tunable.range),
            "int": lambda tunable: rnd.randint(*tunable.range),
        }
        self._best_config = None
        self._best_score = None

    def bulk_register(self, configs: List[dict], scores: List[float]):
        for (params, score) in zip(configs, scores):
            tunables = self._tunables.copy().assign(params)
            self.register(tunables, Status.SUCCEEDED, score)

    def suggest(self) -> TunableGroups:
        """
        Generate the next (random) suggestion.
        """
        tunables = self._tunables.copy()
        for (tunable, _group) in tunables:
            tunable.value = self._random[tunable.type](tunable)
        _LOG.info("Iteration %d :: Suggest: %s", self._iter, tunables)
        return tunables

    def register(self, tunables: TunableGroups, status: Status,
                 score: Union[float, dict] = None) -> float:
        score = super().register(tunables, status, score)
        if status.is_succeeded and (self._best_score is None or score < self._best_score):
            self._best_score = score
            self._best_config = tunables.copy()
        self._iter += 1
        return score

    def get_best_observation(self) -> Tuple[float, TunableGroups]:
        return (self._best_score * self._opt_sign, self._best_config)
