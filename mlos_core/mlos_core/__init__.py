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
>>> space_adpaters_kwargs = {} # no additional args for this example
>>> opt = OptimizerFactory.create(
...     parameter_space=cs,
...     optimization_targets=["y"],
...     optimizer_type=OptimizerType.SMAC,
...     optimizer_kwargs=opt_args,
...     space_adapter_type=SpaceAdapterType.IDENTITY,   # or LLAMATUNE
...     space_adapter_kwargs=space_adpaters_kwargs,
... )
>>> # Get a new configuration suggestion.
>>> (config_df, _metadata_df) = opt.suggest()
>>> # Examine the suggested configuration.
>>> assert len(config_df) == 1
>>> config_df.iloc[0]
x    3
Name: 0, dtype: int64
>>> # Register the configuration and its corresponding target value
>>> score = 42 # a made up score
>>> scores_df = pandas.DataFrame({"y": [score]})
>>> opt.register(configs=config_df, scores=scores_df)
>>> # Get a new configuration suggestion.
>>> (config_df, _metadata_df) = opt.suggest()
>>> config_df.iloc[0]
x    10
Name: 0, dtype: int64
>>> score = 7 # a better made up score
>>> # Optimizers minimize by convention, so a lower score is better
>>> # You can use a negative score to maximize values instead
>>> #
>>> # Convert it to a DataFrame again
>>> scores_df = pandas.DataFrame({"y": [score]})
>>> opt.register(configs=config_df, scores=scores_df)
>>> # Get the best observations.
>>> (configs_df, scores_df, _contexts_df) = opt.get_best_observations()
>>> # The default is to only return one
>>> assert len(configs_df) == 1
>>> assert len(scores_df) == 1
>>> configs_df.iloc[0]
x    10
Name: 1, dtype: int64
>>> scores_df.iloc[0]
y    7
Name: 1, dtype: int64

See Also
--------
`mlos_core/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_core/>`_
for additional documentation and examples in the source tree.
"""
from mlos_core.version import VERSION

__version__ = VERSION


if __name__ == "__main__":
    import doctest

    doctest.testmod()
