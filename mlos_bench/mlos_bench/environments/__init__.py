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
environment's configuration. These parameters can be *constant* (i.e., immutable from one trial
run to the next) or *tunable* (i.e., suggested by the optimizer or provided by the user). The
following clauses in the environment configuration are used to declare these parameters:

- ``tunable_params``:
  A list of :py:mod:`tunable <mlos_bench.tunables>` parameters' (covariant) *groups*.
  At each trial, the Environment will obtain the new values of these parameters
  from the outside (e.g., from the :py:mod:`Optimizer <mlos_bench.optimizers>`).

  Typically, this is set using variable expansion via the special
  ``tunable_params_map`` key in the `globals config
  <../config/index.html#globals-and-variable-substitution>`_.

- ``const_args``:
  A dictionary of *constant* parameters along with their values.

- ``required_args``:
  A list of *constant* parameters supplied to the environment externally
  (i.e., from a parent environment, global config file, or command line).

Again, tunable parameters change on every trial, while constant parameters stay fixed for the
entire experiment.

During the ``setup`` and ``run`` phases, MLOS will combine the constant and
tunable parameters and their values into a single dictionary and pass it to the
corresponding method.

Values of constant parameters defined in the Environment config can be
overridden with the values from the command line and/or external config files.
That allows MLOS users to have reusable immutable environment configurations and
move all experiment-specific or sensitive data outside of the version-controlled
files. We discuss the `variable propagation <index.html#variable-propagation>`_ mechanism
in the section below.

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
If a ``required_args`` parameter is not present in the ``const_args`` section,
and can't be resolved from the ``globals`` this allows MLOS to fail fast and
return an error to the user indicating an incomplete config.

Variable replacement happens in the bottom-up manner. That is, if a certain
parameter is present in the parent (:py:class:`~.CompositeEnv`) Environment, it
will replace the corresponding parameter in the child, and so on.

Note that the parameter **must** appear in the child Environment ``const_args`` or
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
2. The value of the parameter defined in the ``const_args`` section of the
   parent Environment will override the value of the corresponding parameter in the
   child Environments.
3. Values of the parameters defined in the global config files will override the values of the
   corresponding parameters in all environments.
4. Values of the command line parameters take precedence over values defined in the global or
   environment configs.

Examples
^^^^^^^^

Here's a simple working example of a local environment config (written in Python
instead of JSON for testing) to show how variable propagation works:

Note: this references the `dummy-tunables.jsonc
<https://github.com/microsoft/MLOS/blob/main/mlos_bench/mlos_bench/config/tunables/dummy-tunables.jsonc>`_
file for simplicity.

>>> # globals.jsonc
>>> globals_json = '''
... {
...     "experiment_id": "VariablePropagationExample",
...
...     // Required arguments must have their value set from globals, cli args, or shell env.
...     "required_arg_from_globals": "required_arg_from_globals_val",
...     "required_arg_from_cli": "require_arg_from_globals_NOT_CLI", // will be replaced by cli invocation
...     "required_arg_from_shell_env": "$REQUIRED_ARG_FROM_SHELL_ENV",
...
...     // Const args have a default value if not set, but can be overridden by
...     // the globals, cli args, shell env, or parent env.
...
...     "const_arg_from_globals": "const_arg_from_globals_val",
...     "const_arg_from_shell_env": "$CONST_ARG_FROM_SHELL_ENV",
...     "const_arg_from_child2_env2": "FROM@GLOBALS!",
...     // special map of tunable_params_name to their set of enabled covariant tunable groups
...
...     "tunable_params_map": {
...         "my_env1_tunables": ["dummy_params"],
...         "my_env2_tunables": [/* none */],
...     },
... }
... '''

>>> # composite_env.jsonc
>>> composite_env_json = '''
... {
...     "class": "mlos_bench.environments.composite_env.CompositeEnv",
...     "name": "parent_env",
...     "config": {
...         // Must be populated by a global config or command line:
...         "required_args": [
...             "required_arg_from_globals",
...             "required_arg_from_cli",
...             //"required_arg_from_shell_env",    # TEST ME: does this need to be here to flow down?
...         ],
...         // Can be populate by variable expansion from a higher level, or else defaulted to here.
...         "const_args": {
...             "const_arg_from_globals": "const_arg_from_globals_parent_val",
...             "const_arg_from_shell_env": "const_arg_from_shell_parent_val",
...             "const_arg_from_cli": "const_arg_from_cli_parent_val",
...             "const_arg_from_parent_env": "const_arg_from_parent_env_val",
...             "const_arg_from_local_env": "const_arg_from_local_env_parent_val",
...             // const_arg defaults can also use variable expansion to refer
...             // to another variable previously defined (even another const_arg) in order to
...             // allow for variable renaming
...             "const_arg_from_required": "$required_arg_from_globals",
...         },
...         "children": [
...             {
...                 "class": "mlos_bench.environments.local.local_env.LocalEnv",
...                 "name": "child_env1",
...                 "include_tunables": [
...                     "tunables/dummy-tunables.jsonc"
...                 ],
...                 "config": {
...                    "tunable_params": ["$my_env1_tunables"],
...                     "required_args": [
...                         "required_arg_from_globals",
...                         "required_arg_from_cli",
...                         "required_arg_from_shell_env",
...                         // Here, we can simply declare a required_arg as
...                         // required, but let it inherit a value from a higher level environment.
...                         "const_arg_from_required",
...                         "const_arg_from_parent_env",
...                     ],
...                     "const_args": {
...                         // Here we provide defaults, though all of these should be overridden by higher levels.
...                         "const_arg_from_globals": "const_arg_from_globals_child1_val",
...                         "const_arg_from_shell_env": "const_arg_from_shell_child1_val",
...                         "const_arg_from_cli": "const_arg_from_cli_child1_val",
...                         "const_arg_from_local_env": "const_arg_from_local_env_child1_val",
...                     },
...                      "run": [
...                         "echo 'child1: required_arg_from_globals: ${required_arg_from_globals}'",
...                         "echo 'child1: required_arg_from_cli: $required_arg_from_cli'",
...                         "echo 'child1: required_arg_from_shell_env: $required_arg_from_shell_env'",
...                         "echo 'child1: const_arg_from_required: $const_arg_from_required'",
...                         "echo 'child1: const_arg_from_globals: $const_arg_from_globals'",
...                         "echo 'child1: const_arg_from_shell_env: $const_arg_from_shell_env'",
...                         "echo 'child1: const_arg_from_cli: $const_arg_from_cli'",
...                         "echo 'child1: const_arg_from_local_env: $const_arg_from_local_env'",
...                         "echo 'child1: const_arg_from_parent_env: $const_arg_from_parent_env'",
...                     ],
...                     "results_stdout_pattern": "(?:child[0-9]: )([a-zA-Z0-9_]+): (.+)",
...                 }
...             },
...             {
...                 "class": "mlos_bench.environments.local.local_env.LocalEnv",
...                 "name": "child_env2",
...                 "include_tunables": [
...                     "tunables/dummy-tunables.jsonc"
...                 ],
...                 "config": {
...                     "tunable_params": ["$my_env2_tunables"],
...                     "required_args": [
...                         "required_arg_from_globals",
...                         "required_arg_from_cli",
...                         "required_arg_from_shell_env",
...                         // Here, we can simply declare a required_arg as
...                         // required, but let it inherit a value from a higher level environment.
...                         "const_arg_from_required",
...                         "const_arg_from_parent_env",
...                     ],
...                     "const_args": {
...                         // Here we provide defaults, though all of these should be overridden by higher levels.
...                         "const_arg_from_globals": "const_arg_from_globals_child2_val",
...                         "const_arg_from_shell_env": "const_arg_from_shell_child2_val",
...                         "const_arg_from_cli": "const_arg_from_cli_child2_val",
...                         "const_arg_from_local_env": "const_arg_from_local_env_child2_val",
...                         "const_arg_from_child2_env1": "const_arg_from_child2_val",
...                         "const_arg_from_child2_env2": "const_arg_from_child2_val",
...                     },
...                     // Expose the args as shell env vars for the child env.
...                     "shell_env_params": [
...                         "required_arg_from_globals",
...                         "const_arg_from_globals",
...                     ],
...                     "run": [
...                         // Each of these commands undergoes variable replacement prior to being executed.
...                         "echo 'child2: required_arg_from_globals: $required_arg_from_globals'",
...                         "echo 'child2: required_arg_from_cli: $required_arg_from_cli'",
...                         "echo 'child2: required_arg_from_shell_env: $required_arg_from_shell_env'",
...                         "echo 'child2: const_arg_from_required: $const_arg_from_required'",
...                         "echo 'child2: const_arg_from_globals: $const_arg_from_globals'",
...                         "echo 'child2: const_arg_from_shell_env: $const_arg_from_shell_env'",
...                         "echo 'child2: const_arg_from_cli: $const_arg_from_cli'",
...                         "echo 'child2: const_arg_from_local_env: $const_arg_from_local_env'",
...                         "echo 'child2: const_arg_from_child2_env1: $const_arg_from_child2_env1'",
...                         "echo 'child2: const_arg_from_child2_env2: $const_arg_from_child2_env2'",
...                         "echo 'child2: const_arg_from_parent_env: $const_arg_from_parent_env'",
...                         // Only some of those parameters are actually exposed as shell env vars though.
...                         "printenv | grep _arg_from_ | sed -e 's/^/child2: /' -e 's/=/: /'",
...                     ],
...                     "results_stdout_pattern": "(?:child[0-9]: )([a-zA-Z0-9_]+): (.+)",
...                 }
...             }
...         ]
...     }
... }
... '''

>>> # Setup the shell env as if bash used an "export VAR='val'"
>>> import os
>>> os.environ["REQUIRED_ARG_FROM_SHELL_ENV"] = "required_arg_from_shell_env_val"
>>> os.environ["CONST_ARG_FROM_SHELL_ENV"] = "const_arg_from_shell_env_val"
>>> # Load the globals and environment configs defined above via the Launcher as
>>> # if we were calling `mlos_bench` directly on the CLI.
>>> from mlos_bench.launcher import Launcher
>>> argv = [
...     "--log-level=DEBUG", # WARNING
...     "--globals", globals_json,
...     "--environment", composite_env_json,
...     # Override some values via CLI directly:
...     "--required_arg_from_cli", "required_arg_from_cli_val",
...     "--const_arg_from_cli", "const_arg_from_cli_val",
... ]
>>> launcher = Launcher("sample_launcher", argv=argv)
>>> composite_env = launcher.root_environment
>>> child_env1 = composite_env.children[0]
>>> assert child_env1.name == "child_env1"
>>> child_env2 = composite_env.children[1]
>>> assert child_env2.name == "child_env2"

>>> # Demonstrate how tunable parameters are selected.
>>> child_env1.tunable_params.get_param_values()
{'dummy_param': 'dummy'}
>>> child_env2.tunable_params.get_param_values()
{}

>>> # Now see how the variable propagation works.
>>> child_env1.parameters["required_arg_from_globals"]
'required_arg_from_globals_val'
>>> child_env1.parameters["required_arg_from_cli"]
'required_arg_from_cli_val'
>>> child_env1.parameters["required_arg_from_shell_env"]
'required_arg_from_shell_env_val'
>>> # Note that the default value in the local child env is overridden:
>>> child_env1.parameters["const_arg_from_globals"]
'const_arg_from_globals_val'
>>> child_env1.parameters["const_arg_from_shell_env"]
'const_arg_from_shell_env_val'
>>> child_env1.parameters["const_arg_from_cli"]
'const_arg_from_cli_val'
>>> # This is treated as a required_arg and inherited from the parent.
>>> child_env1.parameters["const_arg_from_parent_env"]
'const_arg_from_parent_env_val'

>>> # TODO: child2

>>> # TODO: Simulate running the environment to see its output:
>>> from mlos_bench.environments.status import Status
>>> with child_env1:
...     assert child_env1.setup(child_env1.tunable_params)
...     (status, ts, result) = child_env1.run()
...     assert status == Status.SUCCEEDED
...     child_env1.teardown()
>>> # TODO: check output

>>> # TODO: child2

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
"""  # pylint: disable=line-too-long # noqa: E501

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
