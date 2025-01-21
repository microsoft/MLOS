#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Manual config suggester (Optimizer) for mlos_bench that proposes an explicit sequence of
configurations.

This is useful for testing and validation, as it allows you to run a sequence of
configurations in a cyclic fashion.

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

>>> # Now create a ManualOptimizer from a JSON config string.
>>> optimizer_json_config = '''
... {
...   "class": "mlos_bench.optimizers.manual_optimizer.ManualOptimizer",
...   "description": "ManualOptimizer",
...     "config": {
...         "max_cycles": 3,
...         "tunable_values_cycle": [
...             {"colors": "red", "int_param": 1, "float_param": 0.0},
...             {"colors": "blue", "int_param": 3, "float_param": 1.0},
...             // special case: {} - represents the defaults, without
...             // having to copy them from the tunables JSON
...             // (which is presumably specified elsewhere)
...             {},
...         ],
...     }
... }
... '''
>>> config = json.loads(optimizer_json_config)
>>> optimizer = service.build_optimizer(
...   tunables=tunables,
...   service=service,
...   config=config,
... )
>>> # Run the optimizer.
>>> # Note that the cycle will repeat 3 times, as specified in the config.
>>> while optimizer.not_converged():
...     suggestion = optimizer.suggest()
...     print(suggestion.get_param_values())
{'colors': 'red', 'int_param': 1, 'float_param': 0.0}
{'colors': 'blue', 'int_param': 3, 'float_param': 1.0}
{'colors': 'green', 'int_param': 2, 'float_param': 0.5}
{'colors': 'red', 'int_param': 1, 'float_param': 0.0}
{'colors': 'blue', 'int_param': 3, 'float_param': 1.0}
{'colors': 'green', 'int_param': 2, 'float_param': 0.5}
{'colors': 'red', 'int_param': 1, 'float_param': 0.0}
{'colors': 'blue', 'int_param': 3, 'float_param': 1.0}
{'colors': 'green', 'int_param': 2, 'float_param': 0.5}
"""

import logging

from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.services.base_service import Service
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.tunables.tunable_types import TunableValue

_LOG = logging.getLogger(__name__)


class ManualOptimizer(MockOptimizer):
    """Optimizer that proposes an explicit sequence of tunable values."""

    def __init__(
        self,
        tunables: TunableGroups,
        config: dict,
        global_config: dict | None = None,
        service: Service | None = None,
    ):
        super().__init__(tunables, config, global_config, service)
        self._tunable_values_cycle: list[dict[str, TunableValue]] = config.get(
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
