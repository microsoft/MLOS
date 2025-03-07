#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Mock optimizer for mlos_bench.

Mostly intended for testing and validation. This optimizer produces random suggestions.
The range of the suggestions can be controlled by a config.

See the test cases or example json configs for more details.
"""

import logging
import random
from collections.abc import Callable, Sequence

from mlos_bench.environments.status import Status
from mlos_bench.optimizers.track_best_optimizer import TrackBestOptimizer
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable import Tunable
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tunables.tunable_types import TunableValue

_LOG = logging.getLogger(__name__)


class MockOptimizer(TrackBestOptimizer):
    """Mock optimizer to test the Environment API."""

    def __init__(
        self,
        tunables: TunableGroups,
        config: dict,
        global_config: dict | None = None,
        service: Service | None = None,
    ):
        super().__init__(tunables, config, global_config, service)
        rnd = random.Random(self.seed)
        self._random: dict[str, Callable[[Tunable], TunableValue]] = {
            "categorical": lambda tunable: rnd.choice(tunable.categories),
            "float": lambda tunable: rnd.uniform(*tunable.range),
            "int": lambda tunable: rnd.randint(*(int(x) for x in tunable.range)),
        }

    def bulk_register(
        self,
        configs: Sequence[dict],
        scores: Sequence[dict[str, TunableValue] | None],
        status: Sequence[Status] | None = None,
    ) -> bool:
        if not super().bulk_register(configs, scores, status):
            return False
        if status is None:
            status = [Status.SUCCEEDED] * len(configs)
        for params, score, trial_status in zip(configs, scores, status):
            tunables = self._tunables.copy().assign(params)
            self.register(tunables, trial_status, score)
        if _LOG.isEnabledFor(logging.DEBUG):
            (best_score, _) = self.get_best_observation()
            _LOG.debug("Bulk register END: %s = %s", self, best_score)
        return True

    def suggest(self) -> TunableGroups:
        """Generate the next (random) suggestion."""
        tunables = super().suggest()
        if self._start_with_defaults:
            _LOG.info("Use default tunable values")
            self._start_with_defaults = False
        else:
            for tunable, _group in tunables:
                tunable.value = self._random[tunable.type](tunable)
        _LOG.info("Iteration %d :: Suggest: %s", self._iter, tunables)
        return tunables
