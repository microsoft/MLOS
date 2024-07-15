#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
No-op optimizer for mlos_bench that proposes a single configuration.
"""

import logging
from typing import Optional

from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.mock_optimizer import MockOptimizer

_LOG = logging.getLogger(__name__)


class OneShotOptimizer(MockOptimizer):
    """
    No-op optimizer that proposes a single configuration and returns.
    Explicit configs (partial or full) are possible using configuration files.
    """

    # TODO: Add support for multiple explicit configs (i.e., FewShot or Manual Optimizer) - #344

    def __init__(self,
                 tunables: TunableGroups,
                 config: dict,
                 global_config: Optional[dict] = None,
                 service: Optional[Service] = None):
        super().__init__(tunables, config, global_config, service)
        _LOG.info("Run a single iteration for: %s", self._tunables)
        self._max_iter = 1  # Always run for just one iteration.

    def suggest(self) -> TunableGroups:
        """
        Always produce the same (initial) suggestion.
        """
        tunables = super().suggest()
        self._start_with_defaults = True
        return tunables

    @property
    def supports_preload(self) -> bool:
        return False
