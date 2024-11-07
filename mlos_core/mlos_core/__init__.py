#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Basic initializer module for the mlos_core package.

:mod:`~mlos_core` provides the main Optimizer portions of the MLOS project for use with
autotuning purposes.  Although it is generally intended to be used with
:mod:`~mlos_bench`, it can be used independently as well.

To do this it provides a small set of wrapper classes around other OSS tuning
libraries in order to provide a consistent interface so that the rest of the code
using it can easily exchange one optimizer for another (or even stack them).

Specifically:

- :class:`~mlos_core.optimizers.optimizer.BaseOptimizer` is the base class for all Optimizers

   Its core methods are:

   - :meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.suggest` which returns a
     new configuration to evaluate
   - :meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.register` which registers
     a "score" for an evaluated configuration with the Optimizer

- :meth:`~mlos_core.optimizers.OptimizerFactory.create` is a factory function
  that creates a new :type:`~mlos_core.optimizers.ConcreteOptimizer` instance

  To do this it uses the :class:`~mlos_core.optimizers.OptimizerType` enum to
  specify which underlying optimizer to use (e.g.,
  :class:`~mlos_core.optimizers.OptimizerType.FLAML` or
  :class:`~mlos_core.optimizers.OptimizerType.SMAC`).
"""
from mlos_core.version import VERSION

__version__ = VERSION
