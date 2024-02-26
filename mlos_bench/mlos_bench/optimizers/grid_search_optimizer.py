#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Mock optimizer for mlos_bench.
"""

import logging

from typing import Dict, Optional, Sequence, Tuple, Union

import numpy as np
import ConfigSpace as CS

from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable import Tunable, TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.services.base_service import Service

_LOG = logging.getLogger(__name__)


class GridSearchOptimizer(Optimizer):
    """
    Grid search optimizer.
    """

    def __init__(self,
                 tunables: TunableGroups,
                 config: dict,
                 global_config: Optional[dict] = None,
                 service: Optional[Service] = None):
        super().__init__(tunables, config, global_config, service)
        self._sanity_check()

        # TODO: Add tests for this
        self._configs = CS.util.generate_grid(self.config_space, {
            tunable.name: tunable.cardinality
            for (tunable, _group) in self._tunables
            if tunable.quantization
        })

        self._best_config: Optional[TunableGroups] = None
        self._best_score: Optional[float] = None

    def _sanity_check(self) -> None:
        size = 1
        for (tunable, _group) in self._tunables:
            cardinality = tunable.cardinality
            if cardinality == np.inf:
                raise ValueError(f"Unquantized tunables are not supported for grid search: {self.tunable_params}")
            size *= cardinality
        if cardinality > 10000:
            _LOG.warning("Large number of config points requested for grid search: %s", self.tunable_params)

    def bulk_register(self, configs: Sequence[dict], scores: Sequence[Optional[float]],
                      status: Optional[Sequence[Status]] = None) -> bool:
        if not super().bulk_register(configs, scores, status):
            return False
        if status is None:
            status = [Status.SUCCEEDED] * len(configs)
        for (params, score, trial_status) in zip(configs, scores, status):
            tunables = self._tunables.copy().assign(params)
            self.register(tunables, trial_status, None if score is None else float(score))
            self._iter -= 1  # Do not advance the iteration counter during warm-up.
        if _LOG.isEnabledFor(logging.DEBUG):
            (score, _) = self.get_best_observation()
            _LOG.debug("Warm-up end: %s = %s", self.target, score)
        return True

    def suggest(self) -> TunableGroups:
        """
        Generate the next (random) suggestion.
        """
        tunables = self._tunables.copy()
        if self._start_with_defaults:
            _LOG.info("Use default values for the first trial")
            self._start_with_defaults = False
        else:
            for (tunable, _group) in tunables:
                tunable.value = self._random[tunable.type](tunable)
        _LOG.info("Iteration %d :: Suggest: %s", self._iter, tunables)
        return tunables

    def register(self, tunables: TunableGroups, status: Status,
                 score: Optional[Union[float, dict]] = None) -> Optional[float]:
        registered_score = super().register(tunables, status, score)
        if status.is_succeeded() and (
            self._best_score is None or (registered_score is not None and registered_score < self._best_score)
        ):
            self._best_score = registered_score
            self._best_config = tunables.copy()
        self._iter += 1
        return registered_score

    def get_best_observation(self) -> Union[Tuple[float, TunableGroups], Tuple[None, None]]:
        if self._best_score is None:
            return (None, None)
        assert self._best_config is not None
        return (self._best_score * self._opt_sign, self._best_config)
