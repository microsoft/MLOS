#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
No-op optimizer for mlos_bench that proposes a single configuration.

Explicit configs (partial or full) are possible using configuration files.

Examples
--------
>>> # Load tunables from a JSON string.
>>> # Note: normally these would be automatically loaded from the Environment(s)'s
>>> # `include_tunables` config parameter.
>>> #
>>> import json5 as json
>>> from mlos_bench.environments.status import Status
>>> from mlos_bench.services.config_persistence import ConfigPersistenceService
>>> service = ConfigPersistenceService()
>>> json_config = '''
... {
...   "group_1": {
...     "cost": 1,
...     "params": {
...       "colors": {
...         "type": "categorical",
...         "values": ["red", "blue", "green"],
...         "default": "green",
...       },
...       "int_param": {
...         "type": "int",
...         "range": [1, 3],
...         "default": 2,
...       },
...       "float_param": {
...         "type": "float",
...         "range": [0, 1],
...         "default": 0.5,
...         // Quantize the range into 3 bins
...         "quantization_bins": 3,
...       }
...     }
...   }
... }
... '''
>>> tunables = service.load_tunables(jsons=[json_config])
>>> # Check the defaults:
>>> tunables.get_param_values()
{'colors': 'green', 'int_param': 2, 'float_param': 0.5}

>>> # Load a JSON config of some tunable values to explicitly test.
>>> # Normally these would be provided by the
>>> # `mlos_bench --tunable-values`
>>> # CLI option.
>>> tunable_values_json = '''
... {
...   "colors": "red",
...   "int_param": 1,
...   "float_param": 0.0
... }
... '''
>>> tunable_values = json.loads(tunable_values_json)
>>> tunables.assign(tunable_values).get_param_values()
{'colors': 'red', 'int_param': 1, 'float_param': 0.0}
>>> assert not tunables.is_defaults()

>>> # Now create a OneShotOptimizer from a JSON config string.
>>> optimizer_json_config = '''
... {
...   "class": "mlos_bench.optimizers.one_shot_optimizer.OneShotOptimizer",
... }
... '''
>>> config = json.loads(optimizer_json_config)
>>> optimizer = service.build_optimizer(
...   tunables=tunables,
...   service=service,
...   config=config,
... )
>>> # Run the optimizer.
>>> # Note that it will only run for a single iteration and return the values we set.
>>> while optimizer.not_converged():
...     suggestion = optimizer.suggest()
...     print(suggestion.get_param_values())
{'colors': 'red', 'int_param': 1, 'float_param': 0.0}
"""

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
