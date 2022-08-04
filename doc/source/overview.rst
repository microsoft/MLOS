#############################
mlos-core API
#############################

This is a list of major functions and classes provided by `mlos_core`.

.. currentmodule:: mlos_core

Optimizers
==============
.. currentmodule:: mlos_core.optimizers
.. autosummary::
   :toctree: generated/
   :template: class.rst

   BaseOptimizer
   RandomOptimizer
   EmukitOptimizer
   SkoptOptimizer


Spaces
=========
.. currentmodule:: mlos_core.spaces
.. autosummary::
   :toctree: generated/
   :template: function.rst

   configspace_to_emukit_space
   configspace_to_skopt_space

#############################
mlos-bench API
#############################

This is a list of major functions and classes provided by `mlos_bench`.

.. currentmodule:: mlos_bench

Main
====
.. currentmodule:: mlos_bench.main
.. autosummary::
   :toctree: generated/
   :template: functions.rst

   optimize

Optimizer
=========
.. currentmodule:: mlos_bench.opt
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Optimizer

Environments
============
.. currentmodule:: mlos_bench.environment
.. autosummary::
   :toctree: generated/
   :template: class.rst

   Environment
   AppEnv
   CompositeEnv
   Service
   Status

Azure
-----

.. currentmodule:: mlos_bench.environment.azure
.. autosummary::
    :toctree: generated/
    :template: class.rst

    OSEnv
    VMEnv
    AzureVMService
