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

:doc:`run.py </api/mlos_bench/mlos_bench.run>`

    The script to run the benchmarks or the optimization loop.

    Also available as `mlos_bench` command line tool.

Benchmark Environments
======================
.. currentmodule:: mlos_bench.environments
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Status
   Environment
   CompositeEnv
   MockEnv

Local Environments
-------------------

.. currentmodule:: mlos_bench.environments.local
.. autosummary::
   :toctree: generated/
   :template: class.rst

   LocalEnv
   LocalFileShareEnv

Remote Environments
-------------------

.. currentmodule:: mlos_bench.environments.remote
.. autosummary::
   :toctree: generated/
   :template: class.rst

   RemoteEnv
   OSEnv
   VMEnv

Tunable Parameters
==================
.. currentmodule:: mlos_bench.tunables
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Tunable
   TunableGroups

Service Mix-ins
===============
.. currentmodule:: mlos_bench.services
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Service
   FileShareService

.. currentmodule:: mlos_bench.services.config_persistence
.. autosummary::
   :toctree: generated/
   :template: class.rst

   ConfigPersistenceService

Local Services
---------------
.. currentmodule:: mlos_bench.services.local
.. autosummary::
   :toctree: generated/
   :template: class.rst

   LocalExecService

Remote Azure Services
---------------------

.. currentmodule:: mlos_bench.services.remote.azure
.. autosummary::
   :toctree: generated/
   :template: class.rst

   AzureVMService
   AzureFileShareService

Optimizer Adapters
==================
.. currentmodule:: mlos_bench.optimizers
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Optimizer
   MockOptimizer
   MlosCoreOptimizer

Storage
=======
.. currentmodule:: mlos_bench.storage
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Storage

SQL DB Storage
--------------
.. currentmodule:: mlos_bench.storage.sql.storage
.. autosummary::
   :toctree: generated/
   :template: class.rst

   SqlStorage
