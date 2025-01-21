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

See Also
--------
:py:mod:`mlos_bench.config` :
    For more information about the mlos_bench configuration system.

Examples
--------
TODO
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
