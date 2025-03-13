#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tunable Environments for mlos_bench.

.. contents:: Table of Contents
   :depth: 3

Overview
++++++++

Environments are classes that represent an execution setting (i.e., environment) for
running a benchmark or tuning process.

For instance, a :py:class:`~.LocalEnv` represents a local execution environment, a
:py:class:`~.RemoteEnv` represents a remote execution environment, a
:py:class:`~mlos_bench.environments.remote.vm_env.VMEnv` represents a virtual
machine, etc.

An Environment goes through a series of *phases* (e.g.,
:py:meth:`~.Environment.setup`, :py:meth:`~.Environment.run`,
:py:meth:`~.Environment.teardown`, etc.) that can be used to prepare a VM, workload,
etc.; run a benchmark, script, etc.; and clean up afterwards.
Often, what these phases do (e.g., what commands to execute) will depend on the
specific Environment and the configs that Environment was loaded with.
This lets Environments be very flexible in what they can accomplish.

Environments can be stacked together with the :py:class:`.CompositeEnv` class to
represent complex setups (e.g., an application running on a remote VM with a
benchmark running from a local machine).

See below for the set of Environments currently available in this package.

Note that additional ones can also be created by extending the base
:py:class:`~.Environment` class and referencing them in the :py:mod:`json configs
<mlos_bench.config>` using the ``class`` key.

Environment Parameterization
++++++++++++++++++++++++++++

Each :py:class:`~.Environment` can have a set of parameters that define the
environment's configuration. These parameters can be _constant_ (i.e., immutable from one trial
run to the next) or _tunable_ (i.e., suggested by the optimizer or provided by the user). The
following clauses in the environment configuration are used to declare these parameters:

- ``tunable_params``:
  A list of tunable parameters' _groups_. At each trial, the environment will obtain the new
  values of these parameters from the outside (e.g., from the optimizer).

- ``const_args``:
  A dictionary of _constant_ parameters along with their values.

- ``required_args``:
  A list of _constant_ parameters supplied to the environment externally
  (i.e., from a parent environment, global config file, or command line).

Again, tunable parameters change on every trial, while constant parameters stay fixed for the
entire experiment.

During the setup and run phases, MLOS will combine the constant and tunable parameters and their
values into a single dictionary and pass it to the corresponding method.

Values of constant parameters defined in the environment config can be overridden with the values
from the command line and/or external config files. That allows MLOS users to have reusable
immutable environment configurations and move all experiment-specific or sensitive data outside of
the version-controlled files. We discuss the parameter propagation mechanism in the section below.

Environment Tunables
++++++++++++++++++++

Each environment can use
:py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups` to specify the set of
configuration parameters that can be optimized or searched.
At each iteration of the optimization process, the optimizer will generate a set of
values for the :py:class:`Tunables <mlos_bench.tunables.tunable.Tunable>` that the
environment can use to configure itself.

At a python level, this happens by passing a
:py:meth:`~mlos_bench.tunables.tunable_groups.TunableGroups` object to the
``tunable_groups`` parameter of the :py:class:`~.Environment` constructor, but that
is typically handled by the
:py:meth:`~mlos_bench.services.config_persistence.ConfigPersistenceService.load_environment`
method of the
:py:meth:`~mlos_bench.services.config_persistence.ConfigPersistenceService` invoked
by the ``mlos_bench`` command line tool's :py:class:`mlos_bench.launcher.Launcher`
class.

In the typical json user level configs, this is specified in the
``include_tunables`` section of the Environment config to include the
:py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups` definitions from other
json files when the :py:class:`~mlos_bench.launcher.Launcher` processes the initial
set of config files.

The ``tunable_params`` setting in the ``config`` section of the Environment config
can also be used to limit *which* of the ``TunableGroups`` should be used for the
Environment.

Since :py:mod:`json configs <mlos_bench.config>` also support ``$variable``
substitution in the values using the `globals` mechanism, this setting can used to
dynamically change the set of active TunableGroups for a given Experiment using only
`globals`, allowing for configs to be more modular and composable.

Variable Propagation
++++++++++++++++++++

Parameters declared in the ``const_args`` or ``required_args`` sections of the
Environment config can be overridden with values of the corresponding parameters
of the parent Environment or specified in the external config files or the
command line.

In fact, ``const_args`` or ``required_args`` sections can be viewed as
placeholders for the parameters that are being pushed to the environment from
the outside.

The same parameter can be present in both ``const_args`` and ``required_args`` sections.
``required_args`` is just a way to emphasize the importance of the parameter and create a
placeholder for it when no default value can be specified the ``const_args`` section.

Variable replacement happens in the bottom-up manner. That is, if a certain
parameter is present in the parent (:py:class:`~.CompositeEnv`) Environment, it
will replace the corresponding parameter in the child, and so on.

Note that the parameter _must_ appear in the child Environment ``const_args`` or
``required_args`` section; if a parameter is not present in one of these
placeholders of the child Environment config, it will not be propagated. This
hierarchy allows MLOS users to have small immutable Environment configurations
at the lower levels and combine and parameterize them at the higher levels.

Taking it to the next level outside of the Environment configs, the parameters
can be defined in the external key-value JSON config files (usually referred to
as `global config files
<../config/index.html#globals-and-variable-substitution>`_ in MLOS lingo).
See :py:mod:`mlos_bench.config` for more details.

We can summarize the parameter propagation rules as follows:

1. Child environment will only get the parameters defined in its ``const_args`` or
   ``required_args`` sections.
2. Value of the parameter defined in the ``const_args`` section of the parent Environment will
   override the value of the corresponding parameter in the child environments.
3. Values of the parameters defined in the global config files will override the values of the
   corresponding parameters in all environments.
4. Values of the command line parameters take precedence over values defined in the global or
   environment configs.

Environment Services
++++++++++++++++++++

Environments can also reference :py:mod:`~mlos_bench.services` that provide the
necessary support to perform the actions that environment needs for each of its
phases depending upon where its being deployed (e.g., local machine, remote machine,
cloud provider VM, etc.)

Although this can be done in the Environment config directly with the
``include_services`` key, it is often more useful to do it in the global or
:py:mod:`cli config <mlos_bench.config>` to allow for the same Environment to be
used in different settings (e.g., local machine, SSH accessible machine, Azure VM,
etc.) without having to change the Environment config.

Variable propagation rules described in the previous section for the environment
configs also apply to the :py:mod:`Service <mlos_bench.services>`
configurations.

That is, every parameter defined in the Service config can be overridden by a
corresponding parameter from the global config or the command line.

All global configs, command line parameters, Environment ``const_args`` and
``required_args`` sections, and Service config parameters thus form one flat
name space of parameters.  This imposes a certain risk of name clashes, but also
simplifies the configuration process and allows users to keep all
experiment-specific data in a few human-readable files.

We will discuss the examples of such global and local configuration parameters in the
documentation of the concrete :py:mod:`~mlos_bench.services` and
:py:mod:`~mlos_bench.environments`.

Examples
--------
While this documentation is generated from the source code and is intended to be a
useful reference on the internal details, most users will be more interested in
generating json configs to be used with the ``mlos_bench`` command line tool.

For a simple working user oriented example please see the `test_local_env_bench.jsonc
<https://github.com/microsoft/MLOS/blob/main/mlos_bench/mlos_bench/tests/config/environments/local/test_local_env.jsonc>`_
file or other examples in the source tree linked below.

For more developer oriented examples please see the `mlos_bench/tests/environments
<https://github.com/microsoft/MLOS/blob/main/mlos_bench/mlos_bench/tests/>`_
directory in the source tree.

Notes
-----
- See `mlos_bench/environments/README.md
  <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/environments/>`_
  for additional documentation in the source tree.
- See `mlos_bench/config/environments/README.md
  <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/environments/>`_
  for additional config examples in the source tree.

See Also
--------
:py:mod:`mlos_bench.config` :
    Overview of the configuration system.
:py:mod:`mlos_bench.services` :
    Overview of the Services available to the Environments and their configurations.
:py:mod:`mlos_bench.tunables` :
    Overview of the Tunables available to the Environments and their configurations.
"""

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.composite_env import CompositeEnv
from mlos_bench.environments.local.local_env import LocalEnv
from mlos_bench.environments.local.local_fileshare_env import LocalFileShareEnv
from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.environments.remote.remote_env import RemoteEnv
from mlos_bench.environments.status import Status

__all__ = [
    "Status",
    "Environment",
    "MockEnv",
    "RemoteEnv",
    "LocalEnv",
    "LocalFileShareEnv",
    "CompositeEnv",
]
