#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Interfaces and wrapper classes for optimizers to be used in :py:mod:`mlos_bench` for
autotuning or benchmarking.

Overview
++++++++

One of the main purposes of the mlos_bench :py:class:`.Optimizer` class is to
provide a wrapper for the :py:mod:`mlos_core.optimizers` via the
:py:class:`.MlosCoreOptimizer` in order to perform autotuning.

However, several other *config suggesters* that conform to the Optimizer APIs are
also available for use:

- :py:class:`.GridSearchOptimizer` :
    Useful for exhaustive search of a *small* parameter space.
- :py:class:`.OneShotOptimizer` :
    Useful for one-off config experimentation and benchmarking.
- :py:class:`.ManualOptimizer` :
    Useful for repeatedly testing a small set of known configs.

API
+++

Like the mlos_core :py:class:`~mlos_core.optimizers.optimizer.BaseOptimizer`, the
core APIs here are :py:meth:`.Optimizer.suggest` and :py:meth:`.Optimizer.register`.

The :py:meth:`.Optimizer.bulk_register` method is also available to pre-warm a new
Optimizer instance using observations from a prior set of
:py:class:`~mlos_bench.storage.base_storage.Storage.Trial` runs (e.g., from the
:py:mod:`mlos_bench.storage`).

.. note::
    We also refer to this as "merging" this only makes sense if the past Trials
    were run from a set of Experiments *compatible* with this one (e.g., same
    software, workload, VM size, overlapping parameter spaces, etc.).
    Automatically determining whether that makes sense to do is challenging and
    is left to the user to ensure for now.

Stopping Conditions
^^^^^^^^^^^^^^^^^^^
Currently the :py:meth:`.Optimizer.not_converged` method only checks that the number
of suggestions is less than the ``max_suggestions`` property of the Optimizer
config.

However, in the future we intend to implement more sophisticated stopping conditions
(e.g., total time, convergence, cost budget, etc.).

Spaces
++++++

Unlike mlos_core, the :py:mod:`mlos_bench.optimizers` operate on
:py:mod:`~mlos_bench.tunables` instead of :py:class:`ConfigSpace.ConfigurationSpace`
instances, so mlos_bench handles conversions internally (see
:py:mod:`mlos_bench.optimizers.convert_configspace`).

Config
++++++

Typically these tunables are combined from the individual Environments they are
associated with and loaded via JSON config files.

In the Examples used within this module's documentation we will simply represent
them as JSON strings for explanatory purposes.

Notes
-----
The full set of supported properties is specified in the `JSON schemas for optimizers
<https://github.com/microsoft/MLOS/blob/main/mlos_bench/mlos_bench/config/schemas/optimizers/>`_.
and can be seen in some of the `test examples in the source tree
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/tests/config/schemas/optimizers/test-cases/good/>`_.

See Also
--------
:py:mod:`mlos_bench.config` :
    For more information about the mlos_bench configuration system.

Examples
--------
Note: All of the examples in this module are expressed in Python for testing
purposes.

>>> # Load tunables from a JSON string.
>>> # Note: normally these would be automatically loaded from the Environment(s)'s
>>> # `include_tunables` config parameter.
>>> #
>>> import json5 as json
>>> import mlos_core.optimizers
>>> from mlos_bench.environments.status import Status
>>> from mlos_bench.services.config_persistence import ConfigPersistenceService
>>> service = ConfigPersistenceService()
>>> json_config = '''
... {
...   "group_1": {
...     "cost": 1,
...     "params": {
...       "flags": {
...         "type": "categorical",
...         "values": ["on", "off", "auto"],
...         "default": "auto",
...       },
...       "int_param": {
...         "type": "int",
...         "range": [1, 100],
...         "default": 10,
...       },
...       "float_param": {
...         "type": "float",
...         "range": [0, 100],
...         "default": 50.0,
...       }
...     }
...   }
... }
... '''
>>> tunables = service.load_tunables(jsons=[json_config])
>>> # Here's the defaults:
>>> tunables.get_param_values()
{'flags': 'auto', 'int_param': 10, 'float_param': 50.0}

>>> # Load a JSON config string for an MlosCoreOptimizer.
>>> # You must specify an mlos_bench Optimizer class in the JSON config.
>>> # (e.g., "mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer")
>>> # All optimizers support the following config properties at a minimum:
>>> sorted(Optimizer.BASE_SUPPORTED_CONFIG_PROPS)
['max_suggestions', 'optimization_targets', 'seed', 'start_with_defaults']

>>> # When using the MlosCoreOptimizer, we can also specify some additional
>>> # properties, for instance the optimizer_type, which is one of the mlos_core
>>> # OptimizerType enum values:
>>> print([member.name for member in mlos_core.optimizers.OptimizerType])
['RANDOM', 'FLAML', 'SMAC']

>>> # Here's an example JSON config for an MlosCoreOptimizer.
>>> optimizer_json_config = '''
... {
...   "class": "mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer",
...   "description": "MlosCoreOptimizer",
...     "config": {
...         "max_suggestions": 1000,
...         "optimization_targets": {
...             "throughput": "max",
...             "cost": "min",
...         },
...         "start_with_defaults": true,
...         "seed": 42,
...         // Override the default optimizer type
...         // Must be one of the mlos_core OptimizerType enum values.
...         "optimizer_type": "SMAC",
...         // Optionally provide some additional configuration options for the optimizer.
...         // Note: these are optimizer-specific and may not be supported by all optimizers.
...         "n_random_init": 25,
...         "n_random_probability": 0.01,
...         // Optionally override the default space adapter type
...         // Must be one of the mlos_core SpaceAdapterType enum values.
...         // LlamaTune is a method for automatically doing space reduction
...         // from the original space.
...         /*
...         "space_adapter_type": "LLAMATUNE",
...         "space_adapter_config": {
...             // Note: these values are probably too low,
...             // but it's just for demonstration.
...             "num_low_dims": 2,
...             "max_unique_values_per_param": 10,
...          }
...         */
...     }
... }
... '''
>>> config = json.loads(optimizer_json_config)
>>> optimizer = service.build_optimizer(
...   tunables=tunables,
...   service=service,
...   config=config,
... )

>>> suggested_config_1 = optimizer.suggest()
>>> # Default should be suggested first, per json config.
>>> suggested_config_1.get_param_values()
{'flags': 'auto', 'int_param': 10, 'float_param': 50.0}
>>> # Get another suggestion.
>>> # Note that multiple suggestions can be pending prior to
>>> # registering their scores, supporting parallel trial execution.
>>> suggested_config_2 = optimizer.suggest()
>>> suggested_config_2.get_param_values()
{'flags': 'auto', 'int_param': 99, 'float_param': 5.8570134453475}
>>> # Register some scores.
>>> # Note: Maximization problems track negative scores to produce a minimization problem.
>>> optimizer.register(suggested_config_1, Status.SUCCEEDED, {"throughput": 42, "cost": 19})
{'throughput': -42.0, 'cost': 19.0}
>>> optimizer.register(suggested_config_2, Status.SUCCEEDED, {"throughput": 7, "cost": 17.2})
{'throughput': -7.0, 'cost': 17.2}
>>> (best_score, best_config) = optimizer.get_best_observation()
>>> best_score
{'throughput': 42.0, 'cost': 19.0}
>>> assert best_config == suggested_config_1
"""

from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.optimizers.grid_search_optimizer import GridSearchOptimizer
from mlos_bench.optimizers.manual_optimizer import ManualOptimizer
from mlos_bench.optimizers.mlos_core_optimizer import MlosCoreOptimizer
from mlos_bench.optimizers.mock_optimizer import MockOptimizer
from mlos_bench.optimizers.one_shot_optimizer import OneShotOptimizer

__all__ = [
    "GridSearchOptimizer",
    "ManualOptimizer",
    "MlosCoreOptimizer",
    "MockOptimizer",
    "OneShotOptimizer",
    "Optimizer",
]
