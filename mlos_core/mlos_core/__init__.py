#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_core is a wrapper around other OSS tuning libraries to provide a consistent
interface for autotuning experimentation.

``mlos_core`` focuses on the optimization portion of the autotuning process.

.. contents:: Table of Contents
   :depth: 3

Overview
++++++++

:py:mod:`mlos_core` can be installed from `pypi <https://pypi.org/project/mlos-core>`_
with ``pip install mlos-core`` from and provides the main
:py:mod:`Optimizer <mlos_core.optimizers>` portions of the MLOS project for use with
autotuning purposes.
Although it is generally intended to be used with :py:mod:`mlos_bench` to help
automate the generation of ``(config, score)`` pairs (which we call
:py:class:`~mlos_core.data_classes.Observations`) to
:py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.register` with the
Optimizer, it can be used independently as well.
In that case, a :py:class:`~mlos_core.data_classes.Suggestion` is returned from a
:py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.suggest` call.
The caller is expected to score the associated config manually (or provide a
historical value) and :py:meth:`~mlos_core.data_classes.Suggestion.complete` it
convert it to an :py:class:`~mlos_core.data_classes.Observation` that can be
registered with the Optimizer before repeating.
In doing so, the Optimizer will attempt to find the best configuration to minimize
the score provided, ideally learning from the previous observations in order to
converge to the best possible configuration as quickly as possible.

To do this ``mlos_core`` provides a small set of wrapper classes around other OSS
tuning libraries (e.g.,
:py:mod:`~mlos_core.optimizers.bayesian_optimizers.smac_optimizer.SmacOptimizer`,
:py:mod:`~mlos_core.optimizers.flaml_optimizer.FlamlOptimizer`, etc.) in order to
provide a consistent interface so that the rest of the code
using it can easily exchange one optimizer for another (or even stack them).
This allows for easy experimentation with different optimizers, each of which have
their own strengths and weaknesses.

When used with :py:mod:`mlos_bench` doing this is as simple as a one line json
config change for the ``mlos_bench``
:py:class:`~mlos_bench.optimizers.base_optimizer.Optimizer` config.

Data Classes
++++++++++++

The :py:class:`~mlos_core.data_classes.Suggestion` and
:py:class:`~mlos_core.data_classes.Observation` :py:mod:`mlos_core.data_classes`
mentioned above internally use :external:py:mod:`pandas` as the acknowledged lingua
franca of data science tasks, as is the focus of the ``mlos_core`` package.

Spaces
++++++

In ``mlos_core`` parameter :py:mod:`~mlos_core.spaces` telling the optimizers which
configs to search over are specified using
:external:py:class:`ConfigSpace.ConfigurationSpace` s which provide features like

- log sampling
- quantization
- weighted distributions
- etc.

Refer to the `ConfigSpace documentation <https://automl.github.org/ConfigSpace/>`_
for additional details.

Internally, :py:mod:`~mlos_core.spaces.converters` are used to adapt those to
whatever the underlying Optimizer needs (in case it isn't using ConfigSpace).

*However*, note that in :py:mod:`mlos_bench`, a separate
:py:mod:`~mlos_bench.tunables.tunable_groups.TunableGroups` configuration language
is currently used instead (which is then internally converted into a
:py:class:`ConfigSpace.ConfigurationSpace`).

Space Adapters
^^^^^^^^^^^^^^

MLOS also provides :py:mod:`space adapters <mlos_core.spaces.adapters>` to help transform
one space to another.

This can be done for a variety for reasons.

One example is for automatic search space reduction (e.g., using
:py:mod:`~mlos_core.spaces.adapters.llamatune`) in order to try and improve search
efficiency (see the :py:mod:`~mlos_core.spaces.adapters.llamatune` and
:py:mod:`space adapters <mlos_core.spaces.adapters>` modules for additional
documentation.)

As with the Optimizers, the Space Adapters are designed to be easily swappable,
especially in the :py:mod:`mlos_bench`
:py:class:`~mlos_bench.optimizers.base_optimizer.Optimizer` config.

Classes Overview
++++++++++++++++

- :py:class:`~mlos_core.optimizers.optimizer.BaseOptimizer` is the base class for all Optimizers

   Its core methods are:

   - :py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.suggest` which returns a
     new configuration to evaluate
   - :py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.register` which registers
     a "score" for an evaluated configuration with the Optimizer

   Each operates on Pandas :py:class:`DataFrames <pandas.DataFrame>` as the lingua
   franca for data science.

- :py:meth:`mlos_core.optimizers.OptimizerFactory.create` is a factory function
  that creates a new :py:type:`~mlos_core.optimizers.ConcreteOptimizer` instance

  To do this it uses the :py:class:`~mlos_core.optimizers.OptimizerType` enum to
  specify which underlying optimizer to use (e.g.,
  :py:class:`~mlos_core.optimizers.OptimizerType.FLAML` or
  :py:class:`~mlos_core.optimizers.OptimizerType.SMAC`).

Examples
--------
>>> # Import the necessary classes.
>>> import pandas
>>> from ConfigSpace import ConfigurationSpace, UniformIntegerHyperparameter
>>> from mlos_core.optimizers import OptimizerFactory, OptimizerType
>>> from mlos_core.spaces.adapters import SpaceAdapterFactory, SpaceAdapterType
>>> # Create a simple ConfigurationSpace with a single integer hyperparameter.
>>> cs = ConfigurationSpace(seed=1234)
>>> _ = cs.add(UniformIntegerHyperparameter("x", lower=0, upper=10))
>>> # Create a new optimizer instance using the SMAC optimizer.
>>> opt_args = {"seed": 1234, "max_trials": 100}
>>> space_adapters_kwargs = {} # no additional args for this example
>>> opt = OptimizerFactory.create(
...     parameter_space=cs,
...     optimization_targets=["y"],
...     optimizer_type=OptimizerType.SMAC,  # or FLAML, etc.
...     optimizer_kwargs=opt_args,
...     space_adapter_type=SpaceAdapterType.IDENTITY,   # or LLAMATUNE
...     space_adapter_kwargs=space_adapters_kwargs,
... )
>>> # Get a new configuration suggestion.
>>> suggestion = opt.suggest()
>>> # Examine the suggested configuration.
>>> assert len(suggestion.config) == 1
>>> suggestion.config
x    3
dtype: object
>>> # Register the configuration and its corresponding target value
>>> score = 42 # a made up score
>>> scores_sr = pandas.Series({"y": score})
>>> opt.register(suggestion.complete(scores_sr))
>>> # Get a new configuration suggestion.
>>> suggestion = opt.suggest()
>>> suggestion.config
x    10
dtype: object
>>> score = 7 # a better made up score
>>> # Optimizers minimize by convention, so a lower score is better
>>> # You can use a negative score to maximize values instead
>>> #
>>> # Convert it to a Series again
>>> scores_sr = pandas.Series({"y": score})
>>> opt.register(suggestion.complete(scores_sr))
>>> # Get the best observations.
>>> observations = opt.get_best_observations()
>>> # The default is to only return one
>>> assert len(observations) == 1
>>> observations.configs
    x
0  10
>>> observations.scores
   y
0  7

Notes
-----
See `mlos_core/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_core/>`_
for additional documentation and examples in the source tree.
"""
from mlos_core.version import VERSION

__version__ = VERSION


if __name__ == "__main__":
    import doctest

    doctest.testmod()
