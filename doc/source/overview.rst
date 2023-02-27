#############################
mlos-core API
#############################

This is a list of major functions and classes provided by `mlos_core`.

.. currentmodule:: mlos_core

Optimizers
==========
.. currentmodule:: mlos_core.optimizers
.. autosummary::
   :toctree: generated/

   :template: class.rst

   OptimizerType
   OptimizerFactory

   :template: function.rst

   OptimizerFactory.create

.. currentmodule:: mlos_core.optimizers.optimizer
.. autosummary::
   :toctree: generated/
   :template: class.rst

   BaseOptimizer

.. currentmodule:: mlos_core.optimizers.random_optimizer
.. autosummary::
   :toctree: generated/
   :template: class.rst

   RandomOptimizer

.. currentmodule:: mlos_core.optimizers.bayesian_optimizers
.. autosummary::
   :toctree: generated/
   :template: class.rst

   BaseBayesianOptimizer
   EmukitOptimizer
   SkoptOptimizer

Spaces
======
.. currentmodule:: mlos_core.spaces
.. autosummary::
   :toctree: generated/
   :template: function.rst

   configspace_to_emukit_space
   configspace_to_skopt_space

Space Adapters
--------------
.. currentmodule:: mlos_core.spaces.adapters
.. autosummary::
   :toctree: generated/

   :template: class.rst

   SpaceAdapterType
   SpaceAdapterFactory

   :template: function.rst

   SpaceAdapterFactory.create

.. currentmodule:: mlos_core.spaces.adapters.adapter
.. autosummary::
   :toctree: generated/
   :template: class.rst

   BaseSpaceAdapter

.. currentmodule:: mlos_core.spaces.adapters.llamatune
.. autosummary::
   :toctree: generated/
   :template: class.rst

   LlamaTuneAdapter

#############################
mlos-bench API
#############################

This is a list of major functions and classes provided by `mlos_bench`.

.. currentmodule:: mlos_bench

Main
====

:doc:`run_opt.py </api/mlos_bench/mlos_bench.run_opt>`

    The main optimization loop script.

:doc:`run_bench.py </api/mlos_bench/mlos_bench.run_bench>`

    A helper script for testing a single application/workload run.

Benchmark Environments
======================
.. currentmodule:: mlos_bench.environment
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Environment
   MockEnv
   LocalEnv
   LocalFileShareEnv
   RemoteEnv
   CompositeEnv
   Status

Tunable Parameters
------------------
.. currentmodule:: mlos_bench.environment
.. autosummary::
    :toctree: generated/
    :template: class.rst

    Tunable
    TunableGroups

Service Mix-ins
---------------
.. currentmodule:: mlos_bench.environment
.. autosummary::
    :toctree: generated/
    :template: class.rst

   Service
   LocalExecService
   FileShareService
   ConfigPersistenceService

Azure Environments
------------------

.. currentmodule:: mlos_bench.environment.azure
.. autosummary::
    :toctree: generated/
    :template: class.rst

    OSEnv
    VMEnv

Azure Services
--------------

.. currentmodule:: mlos_bench.environment.azure
.. autosummary::
    :toctree: generated/
    :template: class.rst

    AzureVMService
    AzureFileShareService

Optimizer Adapters
==================
.. currentmodule:: mlos_bench.optimizer
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Optimizer
   MockOptimizer
   MlosCoreOptimizer
