#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""No-op optimizer for mlos_bench that proposes a single configuration."""

import logging

from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


class OneShotOptimizer(MockOptimizer):
    """
    No-op optimizer that proposes a single configuration and returns.

    Explicit configs (partial or full) are possible using configuration files.
    """

    def __init__(
        self,
        tunables: TunableGroups,
        config: dict,
        global_config: dict | None = None,
        service: Service | None = None,
    ):
        super().__init__(tunables, config, global_config, service)
        _LOG.info("Run a single iteration for: %s", self._tunables)
        self._max_suggestions = 1  # Always run for just one iteration.

    def suggest(self) -> TunableGroups:
        """Always produce the same (initial) suggestion."""
        tunables = super().suggest()
        self._start_with_defaults = True
        return tunables

    @property
    def supports_preload(self) -> bool:
        return False
