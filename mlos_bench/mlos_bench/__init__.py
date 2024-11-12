#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_bench is a framework to help automate benchmarking and OS/application parameter
autotuning and the data management of the results.

It can be installed from `pypi <https://pypi.org/project/mlos-bench>`_ via
``pip install mlos-bench`` and executed using the ``mlos_bench``
`command <../../mlos_bench.run.usage.html>`_ using a collection of `json`
`configs <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/>`_.

It is intended to be used with :py:mod:`mlos_core` via
:py:class:`~mlos_bench.optimizers.mlos_core_optimizer.MlosCoreOptimizer` to help
navigate complex parameter spaces more effeciently, though other
:py:mod:`~mlos_bench.optimizers` are also available to
help customize the search process easily by simply swapping out the
:py:class:`~mlos_bench.optimizers.base_optimizer.Optimizer` class in the associated
json configs.
For instance,
:py:class:`~mlos_bench.optimizers.grid_search_optimizer.GridSearchOptimizer` can be
used to perform a grid search over the parameter space instead.

The other core classes in this package are:

- :py:mod:`~mlos_bench.environments` which provide abstractions for representing an
  execution environment.

  These are generally the target of the optimization process and are used to
  evaluate the performance of a given configuration, though can also be used to
  simply run a single benchmark.
  They can be used, for instance, to :py:mod:`provision VMs
  <mlos_bench.environments.remote.vm_env>`, run benchmarks or execute any other
  arbitrary code on a :py:mod:`remote machine <mlos_bench.environments.remote.remote_env>`,
  and many other things.

- :py:mod:`~mlos_bench.environments` are often associated with
  :py:mod:`~mlos_bench.tunables` which provide a language for specifying the set of
  configuration parameters that can be optimized or searched over with the
  :py:mod:`~mlos_bench.optimizers`.

- :py:mod:`~mlos_bench.services` provide the necessary abstractions to run interact
  with the :py:mod:`~mlos_bench.environments` in different settings.

  For instance, the
  :py:class:`~mlos_bench.services.remote.azure.azure_vm_services.AzureVMService`
  can be used to run commands on Azure VMs for a remote
  :py:mod:`~mlos_bench.environments.remote.vm_env.VMEnv`.

  Alternatively, one could swap out that service for
  :py:class:`~mlos_bench.services.remote.ssh.ssh_host_service.SshHostService` in
  order to target a different VM without having to change the
  :py:class:`~mlos_bench.environments.base_environment.Environment` configuration at
  all since they both implement the same
  :py:class:`~mlos_bench.services.types.remote_exec_type.SupportsRemoteExec`
  :py:mod:`Services type<mlos_bench.services.types>` interfaces.

  This is particularly useful when running the same benchmark on different
  ecosystems and makes the configs more modular and composable.

- :py:mod:`~mlos_bench.storage` which provides abstractions for storing and
  retrieving data from the experiments.

  For instance, nearly any :py:mod:`SQL <mlos_bench.storage.sql>` backend that
  `sqlalchemy <https://www.sqlalchemy.org>`_ supports can be used.

See below for more information on the classes in this package.

Notes
-----
Note that while the docstrings in this package are generated from the source code
and hence sometimes more focused on the implementation details, most user
interactions with the package will be through the
`json configs <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/>`_.
Even so it may be useful to look at the source code to understand how those are
interpretted.

Examples
--------
TODO: Add examples

See Also
--------
`mlos_bench/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/>`_
for additional documentation and examples in the source tree.
"""
from mlos_bench.version import VERSION

__version__ = VERSION
