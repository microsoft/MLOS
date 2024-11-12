#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""mlos_core is a wrapper around other OSS tuning libraries to provide a consistent
interface for autotuning experimentation.

:py:mod:`mlos_core` can be installed from `pypi <https://pypi.org/project/mlos-core>`_
with ``pip install mlos-core`` from and provides the main
:py:mod:`Optimizer <mlos_core.optimizers>` portions of the MLOS project for use with
autotuning purposes.
Although it is generally intended to be used with :py:mod:`mlos_bench` to help
automate the generation of ``(config, score)`` pairs to register with the Optimizer,
it can be used independently as well.

To do this it provides a small set of wrapper classes around other OSS tuning
libraries in order to provide a consistent interface so that the rest of the code
using it can easily exchange one optimizer for another (or even stack them).

Specifically:

- :py:class:`~mlos_core.optimizers.optimizer.BaseOptimizer` is the base class for all Optimizers

   Its core methods are:

   - :py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.suggest` which returns a
     new configuration to evaluate
   - :py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.register` which registers
     a "score" for an evaluated configuration with the Optimizer

- :py:meth:`mlos_core.optimizers.OptimizerFactory.create` is a factory function
  that creates a new :py:type:`~mlos_core.optimizers.ConcreteOptimizer` instance

  To do this it uses the :py:class:`~mlos_core.optimizers.OptimizerType` enum to
  specify which underlying optimizer to use (e.g.,
  :py:class:`~mlos_core.optimizers.OptimizerType.FLAML` or
  :py:class:`~mlos_core.optimizers.OptimizerType.SMAC`).

Examples
--------
TODO: Add example usage here.

See Also
--------
`mlos_core/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_core/>`_
for additional documentation in the source tree.
"""
from mlos_core.version import VERSION

__version__ = VERSION
