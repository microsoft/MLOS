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

Space Adapters
^^^^^^^^^^^^^^

When using the :py:class:`.MlosCoreOptimizer`, you can also specify a
``space_adapter_type`` to use for manipulating the configuration space into
something that may help the Optimizer find better configurations more quickly
(e.g., by automatically doing space reduction).

See the :py:mod:`mlos_core.spaces.adapters` module for more information.

Config
++++++

Typically these tunables are combined from the individual Environments they are
associated with and loaded via JSON config files.

In the Examples used within this module's documentation we will simply represent
them as JSON strings for explanatory purposes.

Several properties are common to all Optimizers, but some are specific to the
Optimizer being used.
The JSON schemas control what is considered a valid configuration for an Optimizer.
In the case of an :py:class:`.MlosCoreOptimizer`, the valid options can often be
inferred from the constructor arguments of the corresponding
:py:class:`mlos_core.optimizers` class.

Similarly for the SpaceAdapterType, the valid options can be inferred from the
individual :py:mod:`mlos_core.spaces.adapters` class constructors.

Generally speaking though the JSON config for an Optimizer will look something
like the following:

.. code-block:: json

    {
        // One of the mlos_bench Optimizer classes from this module.
        "class": "mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer",

        "description": "MlosCoreOptimizer",

        // Optional configuration properties for the selected Optimizer class.
        "config": {
            // Common properties for all Optimizers:
            "max_suggestions": 1000,
            "optimization_targets": {
                // Your optimization target(s) mapped to their respective
                // optimization goals.
                "throughput": "max",
                "cost": "min",
            },
            "start_with_defaults": true,
            "seed": 42,

            // Now starts a collection of key-value pairs that are specific to
            // the Optimizer class chosen.

            // Override the default optimizer type.
            // Must be one of the mlos_core OptimizerType enum values.
            "optimizer_type": "SMAC", // e.g., "RANDOM", "FLAML", "SMAC"

            // Optionally provide some additional configuration options for the optimizer.
            // Note: these are optimizer-specific and may not be supported by all optimizers.
            // For instance the following example is only supported by the SMAC optimizer.
            // In general, for MlosCoreOptimizers you can look at the arguments
            // to the corresponding OptimizerType in the mlos_core module.
            "n_random_init": 20,
            "n_random_probability": 0.25, // increased to prioritize exploration

            // In the case of an MlosCoreOptimizer, override the default space
            // adapter type.
            // Must be one of the mlos_core SpaceAdapterType enum values.
            // e.g., LlamaTune is a method for automatically doing space reduction
            // from the original space.
            "space_adapter_type": "LLAMATUNE",
            "space_adapter_config": {
                // Optional space adapter configuration.
                // The JSON schema controls the valid properties here.
                // In general check the constructor arguments of the specified
                // SpaceAdapterType.
                "num_low_dims": 10,
                "max_unique_values_per_param": 20,
            },
        }

However, it can also be as simple as the following and sane defaults will be
used for the rest.

.. code-block:: json

    {
        "class": "mlos_bench.optimizers.MlosCoreOptimizer"
    }

Or to only override the space adapter type:

.. code-block:: json

    {
        "class": "mlos_bench.optimizers.MlosCoreOptimizer",
        "config": {
            "space_adapter_type": "LLAMATUNE"
        }
    }

Or, to use a different class for suggesting configurations:

.. code-block:: json

    {
        "class": "mlos_bench.optimizers.GridSearchOptimizer"
    }

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

Load tunables from a JSON string.
Note: normally these would be automatically loaded from the
:py:mod:`~mlos_bench.environments.base_environment.Environment`'s
``include_tunables`` config parameter.

>>> import json5 as json
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

Next we'll load an Optimizer from a JSON string.

At a minimum, the JSON config must specify the Optimizer ``class`` to use (e.g.,
one of the classes from this module).

(e.g., ``"class": "mlos_bench.optimizers.MlosCoreOptimizer"``)

>>> # All optimizers support the following optional config properties at a
>>> # minimum:
>>> sorted(Optimizer.BASE_SUPPORTED_CONFIG_PROPS)
['max_suggestions', 'optimization_targets', 'seed', 'start_with_defaults']

When using the :py:class:`.MlosCoreOptimizer`, we can also specify some
additional properties, for instance the ``optimizer_type``, which is one of the
mlos_core :py:data:`~mlos_core.optimizers.OptimizerType` enum values:

>>> import mlos_core.optimizers
>>> print([member.name for member in mlos_core.optimizers.OptimizerType])
['RANDOM', 'FLAML', 'SMAC']

These may also include their own configuration options, which can be specified
as additional key-value pairs in the ``config`` section, where each key-value
corresponds to an argument to the respective OptimizerTypes's constructor.
See :py:meth:`mlos_core.optimizers.OptimizerFactory.create` for more details.

Other Optimizers may also have their own configuration options.
See each class' documentation for details.

When using :py:class:`.MlosCoreOptimizer`, we can also specify an optional an
``space_adapter_type``, which can sometimes help manipulate the configuration
space to something more manageable.  It should be one of the following
:py:data:`~mlos_core.spaces.adapters.SpaceAdapterType` enum values:

>>> import mlos_core.spaces.adapters
>>> print([member.name for member in mlos_core.spaces.adapters.SpaceAdapterType])
['IDENTITY', 'LLAMATUNE']

These may also include their own configuration options, which can be specified
as additional key-value pairs in the optional ``space_adapter_config`` section,
where each key-value corresponds to an argument to the respective
OptimizerTypes's constructor.  See
:py:meth:`mlos_core.spaces.adapters.SpaceAdapterFactory.create` for more details.

Here's an example JSON config for an :py:class:`.MlosCoreOptimizer`.

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
...         /* Not enabled for this example:
...         "space_adapter_type": "LLAMATUNE",
...         "space_adapter_config": {
...             // Note: these values are probably too low,
...             // but it's just for demonstration.
...             "num_low_dims": 2,
...             "max_unique_values_per_param": 10,
...          },
...         */
...     }
... }
... '''

That config will typically be loaded via the ``--optimizer`` command-line
argument to the :py:mod:`mlos_bench <mlos_bench.run>` CLI.
However, for demonstration purposes, we can load it directly here:

>>> config = json.loads(optimizer_json_config)
>>> optimizer = service.build_optimizer(
...   tunables=tunables,
...   service=service,
...   config=config,
... )

Now the :py:mod:`mlos_bench.schedulers` can use the selected
:py:class:`.Optimizer` to :py:meth:`.Optimizer.suggest` a new config to test in
a Trial and then :py:meth:`.Optimizer.register` the results.

A stripped down example of how this might look in practice is something like
this:

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
