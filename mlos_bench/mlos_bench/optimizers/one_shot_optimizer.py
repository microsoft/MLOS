#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
No-op optimizer for mlos_bench that proposes a single configuration.
"""

import logging
from typing import Dict, Optional, Any

from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.optimizers.mock_optimizer import MockOptimizer

_LOG = logging.getLogger(__name__)


class OneShotOptimizer(MockOptimizer):
    """
    Mock optimizer that proposes a single configuration and returns.
    Explicit configs (partial or full) are possible using configuration files.
    """

    # TODO: Add support for multiple explicit configs (i.e., FewShot or Manual Optimizer).

    def __init__(self, tunables: TunableGroups,
                 service: Optional[Service], config: Dict[str, Any]):
        super().__init__(tunables, service, config)
        if self._service is None:
            _LOG.warning("Config loading service not available")
        else:
            # Generate initial random or default suggestion based on optimizer config.
            self._tunables = super().suggest()
            # Now assign the values we were given in the config.
            for data_file in config.get("include_tunable_values", []):
                tunable_values = self._service.config_loader_service.load_config(data_file)
                assert isinstance(tunable_values, Dict)
                self._tunables.assign(tunable_values)
        self._tunables.assign(config.get("tunable_values", {}))

        _LOG.info("Run a single iteration for: %s", self._tunables)
        self._max_iter = 1  # Always run for just one iteration.

    def suggest(self) -> TunableGroups:
        _LOG.info("Suggest: %s", self._tunables)
        return self._tunables.copy()
