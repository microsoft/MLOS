#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Optimizer for mlos_bench that proposes an explicit sequence of configurations."""

import logging
from typing import Dict, List, Optional

from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable import TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class ManualOptimizer(MockOptimizer):
    """Optimizer that proposes an explicit sequence of tunable values."""

    def __init__(
        self,
        tunables: TunableGroups,
        config: dict,
        global_config: Optional[dict] = None,
        service: Optional[Service] = None,
    ):
        super().__init__(tunables, config, global_config, service)
        self._tunable_values_cycle: List[Dict[str, TunableValue]] = config.get(
            "tunable_values_cycle", []
        )
        assert len(self._tunable_values_cycle) > 0, "No tunable values provided."
        max_cycles = int(config.get("max_cycles", 1))
        self._max_suggestions = min(
            self._max_suggestions,
            max_cycles * len(self._tunable_values_cycle),
        )

    def suggest(self) -> TunableGroups:
        """Always produce the same sequence of explicit suggestions, in a cycle."""
        tunables = super().suggest()
        cycle_index = (self._iter - 1) % len(self._tunable_values_cycle)
        tunables.assign(self._tunable_values_cycle[cycle_index])
        _LOG.info("Iteration %d :: Suggest: %s", self._iter, tunables)
        return tunables

    @property
    def supports_preload(self) -> bool:
        return False
