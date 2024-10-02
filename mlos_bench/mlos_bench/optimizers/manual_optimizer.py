#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Optimizer for mlos_bench that proposes an explicit sequence of configuration."""

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
        self._cycle_tunable_values: List[Dict[str, TunableValue]] = config.get(
            "cycle_tunable_values", []
        )
        if len(self._cycle_tunable_values) == 0:
            _LOG.warning("No cycle_tunable_values provided, using default values.")
            self._cycle_tunable_values = [tunables.get_param_values()]

    def suggest(self) -> TunableGroups:
        """Always produce the same sequence of explicit suggestions, in a cycle."""
        tunables = super().suggest()
        cycle_index = (self._iter - 1) % len(self._cycle_tunable_values)
        tunables.assign(self._cycle_tunable_values[cycle_index])
        _LOG.info("Iteration %d :: Suggest: %s", self._iter, tunables)
        return tunables

    @property
    def supports_preload(self) -> bool:
        return False
