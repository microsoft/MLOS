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

The ``tunable_params`` setting in the ``config`` section of the Environment config can then be
used to limit *which* of the ``TunableGroups`` should be used for the Environment.

Tunable Parameters Map
^^^^^^^^^^^^^^^^^^^^^^

Although the full set of tunable parameters (and groups) of each Environment is always known in
advance, in practice we often want to limit it to a smaller subset for a given experiment. This
can be done by adding an extra level of indirection and specifying the ``tunable_params_map`` in
the global config. ``tunable_params_map`` associates a variable name with a list of
:py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups` names, e.g.,

    .. code-block:: json

        // experiment-globals.mlos.jsonc
        {
          "tunable_params_map": {
            "tunables_ref1": ["tunable_group1", "tunable_group2"],
            "tunables_ref2": []  // Useful to disable all tunables.
          }
        }

Later, in the Environment config, we can use these variable names to refer to the
tunable groups we want to use for that Environment:

    .. code-block:: json

        // environment.mlos.jsonc
        {
          // ...
          "config": {
            "tunable_params": [
              "$tunables_ref1",  // Will be replaced with "tunable_group1", "tunable_group2"
              "$tunables_ref2",  // A no-op
              "tunable_group3"   // Can still refer to a group directly.
            ],
        // ... etc.

Note: this references the `dummy-tunables.jsonc
<https://github.com/microsoft/MLOS/blob/main/mlos_bench/mlos_bench/config/tunables/dummy-tunables.jsonc>`_
file for simplicity.

Using such ``"$tunables_ref"`` variables in the Environment config allows us to dynamically
change the set of active ``TunableGroups`` for a given Environment using the global config
without modifying the Environment configuration files for each experiment, thus making them
more modular and composable.

Variable Propagation
++++++++++++++++++++

Parameters declared in the ``const_args`` or ``required_args`` sections of the Environment
config can be overridden with values specified in the external config files or the command
line. In fact, ``const_args`` or ``required_args`` sections can be viewed as placeholders
for the parameters that are being pushed to the environment from the outside.

The same parameter can be present in both ``const_args`` and ``required_args`` sections.
``required_args`` is just a way to emphasize the importance of the parameter and create a
placeholder for it when no default value can be specified the ``const_args`` section.
If a ``required_args`` parameter is not present in the ``const_args`` section,
and can't be resolved from the ``globals`` this allows MLOS to fail fast and
return an error to the user indicating an incomplete config.

Note that the parameter **must** appear in the child Environment ``const_args`` or
``required_args`` section; if a parameter is not present in one of these
placeholders of the Environment config, it will not be propagated. This allows MLOS
users to have small immutable Environment configurations and combine and parameterize
them with external (global) configs.

Taking it to the next level outside of the Environment configs, the parameters
can be defined in the external key-value JSON config files (usually referred to
as `global config files
<../config/index.html#globals-and-variable-substitution>`_ in MLOS lingo).
See :py:mod:`mlos_bench.config` for more details.

We can summarize the parameter propagation rules as follows:

1. An environment will only get the parameters defined in its ``const_args`` or
   ``required_args`` sections.
2. Values of the parameters defined in the global config files will override the values of the
   corresponding parameters in all environments.
3. Values of the command line parameters take precedence over values defined in the global or
   environment configs.

Examples
--------
Here's a simple working example of a local environment config (written in Python
instead of JSON for testing) to show how variable propagation works:

Note: this references the `dummy-tunables.jsonc
<https://github.com/microsoft/MLOS/blob/main/mlos_bench/mlos_bench/config/tunables/dummy-tunables.jsonc>`_
file for simplicity.

>>> # globals.jsonc
>>> globals_json = '''
... {
...     "experiment_id": "test_experiment",
...
...     "const_arg_from_globals_1": "Substituted from globals - 1",
...     "const_arg_from_globals_2": "Substituted from globals - 2",
...
...     "const_arg_from_cli_1": "Will be overridden from CLI",
...
...     // Define reference names to represent tunable groups in the Environment configs.
...     "tunable_params_map": {
...         "tunables_ref1": ["dummy_params_group1", "dummy_params_group2"],
...         "tunables_ref2": [],  // Useful to disable all tunables for the Environment.
...     }
... }
... '''

>>> # environment.jsonc
>>> environment_json = '''
... {
...     "class": "mlos_bench.environments.local.local_env.LocalEnv",
...     "name": "test_env1",
...     "include_tunables": [
...         "tunables/dummy-tunables.jsonc"  // For simplicity, include all tunables available.
...     ],
...     "config": {
...         "tunable_params": [
...             "$tunables_ref1",       // Includes "dummy_params_group1", "dummy_params_group2"
...             "$tunables_ref2",       // A no-op
...             "dummy_params_group3"   // Can still refer to a group directly.
...         ],
...         "const_args": {
...             // Environment-specific non-tunable constant parameters:
...             "const_arg_1": "Default value of const_arg_1",
...             "const_arg_from_globals_1": "To be replaced from global config",
...             "const_arg_from_cli_1": "To be replaced from CLI"
...         },
...         "required_args": [
...             // These parameters always come from elsewhere:
...             "const_arg_from_globals_2",
...             "const_arg_from_cli_2",
...             // We already define these parameters in "const_args" section above;
...             // mentioning them here is optional, but can be used for clarity:
...             "const_arg_from_globals_1",
...             "const_arg_from_cli_1"
...         ],
...         "run": [
...             "echo Hello world"
...         ]
...     }
... }
... '''

Now that we have our environment and global configurations, we can instantiate the
:py:class:`~.Environment` and inspect it. In this example we will simulate the command line execution to demonstrate how CLI parameters propagate to the environment.

>>> # Load the globals and environment configs defined above via the Launcher as
>>> # if we were calling `mlos_bench` directly on the CLI.
>>> from mlos_bench.launcher import Launcher
>>> argv = [
...     "--environment", environment_json,
...     "--globals", globals_json,
...     # Override some values via CLI directly:
...     "--const_arg_from_cli_1", "Substituted from CLI - 1",
...     "--const_arg_from_cli_2", "Substituted from CLI - 2",
... ]
>>> launcher = Launcher("sample_launcher", argv=argv)
>>> env = launcher.root_environment
>>> env.name
'test_env1'

``env`` is an instance of :py:class:`~.Environment` class that we can use to setup, run, and tear
down the environment. It also has a set of properties and methods that we can use to access the
object's parameters. This way we can check the actual runtime configuration of the environment.

First, let's check the tunable parameters:

>>> assert env.tunable_params.get_param_values() == {
...    "dummy_param": "dummy",
...    "dummy_param_int": 0,
...    "dummy_param_float": 0.5,
...    "dummy_param3": 0.0
... }

We can see the tunables from ``dummy_params_group1`` and ``dummy_params_group2`` groups specified
via ``$tunables_ref1``, as well as the tunables from ``dummy_params_group3`` that we specified
directly in the Environment config. All tunables are initialized to their default values.

Now let's see how the variable propagation works.

>>> env.const_args["const_arg_1"]
'Default value of const_arg_1'

``const_arg_1`` has the value we have assigned in the ``"const_args"`` section of the
Environment config. No surprises here.

>>> env.const_args["const_arg_from_globals_1"]
'Substituted from globals - 1'
>>> env.const_args["const_arg_from_globals_2"]
'Substituted from globals - 2'

``const_arg_from_globals_1`` and ``const_arg_from_globals_2`` were declared in the Environment's
``const_args`` and ``required_args`` sections, respectively. Their values were overridden by the
values from the global config.

>>> env.const_args["const_arg_from_cli_1"]
'Substituted from CLI - 1'
>>> env.const_args["const_arg_from_cli_2"]
'Substituted from CLI - 2'

Likewise, ``const_arg_from_cli_1`` and ``const_arg_from_cli_2`` got their values from the
command line. Note that for ``const_arg_from_cli_1`` the value from the command line takes
precedence over the values specified in the Environment's ``const_args`` section **and** the one
in the global config.

Now let's set up the environment and see how the constant and tunable parameters get combined.
We'll also assign some non-default values to the tunables, as the optimizer would do on each
trial.

>>> env.tunable_params["dummy_param_int"] = 99
>>> env.tunable_params["dummy_param3"] = 0.999
>>> with env:
...     assert env.setup(env.tunable_params)
...     assert env.parameters == {
...         "const_arg_1": "Default value of const_arg_1",
...         "const_arg_from_globals_1": "Substituted from globals - 1",
...         "const_arg_from_globals_2": "Substituted from globals - 2",
...         "const_arg_from_cli_1": "Substituted from CLI - 1",
...         "const_arg_from_cli_2": "Substituted from CLI - 2",
...         "trial_id": 1,
...         "trial_runner_id": 1,
...         "experiment_id": "test_experiment",
...         "dummy_param": "dummy",
...         "dummy_param_int": 99,
...         "dummy_param_float": 0.5,
...         "dummy_param3": 0.999
...     }

These are the values visible to the implementations of the :py:meth:`~.Environment.setup`,
:py:meth:`~.Environment.run`, and :py:meth:`~.Environment.teardown` methods. We can see both
the constant and tunable parameters combined into a single dictionary
:py:attr:`~.Environment.parameters` with proper values assigned to each of them on each iteration.
When implementing a new :py:class:`~.Environment`-derived class, developers can rely on the
:py:attr:`~.Environment.parameters` data in their versions of :py:meth:`~.Environment.setup` and
other methods. For example, :py:class:`~mlos_bench.environments.remote.vm_env.VMEnv` would then
pass the :py:attr:`~.Environment.parameters` into an ARM template when provisioning a new VM,
and :py:class:`~mlos_bench.environments.local.local_env.LocalEnv` can dump them into a JSON file
specified in the ``dump_params_file`` config property, or/and cherry-pick some of these values
and make them shell variables with the ``shell_env_params``.

A few `Well Known Parameters <../config/index.html#well-known-variables>`_
parameters like ``trial_id`` and ``trial_runner_id`` are added by the
:py:mod:`Scheduler <mlos_bench.schedulers>` and used for trials parallelization
and storage of the results. It is sometimes useful to add them, for example, to
the paths used by the Environment, as in, e.g.,
``"/storage/$experiment_id/$trial_id/data/"``, to prevent conflicts when running
multiple Experiments and Trials in parallel.

We will discuss passing the parameters to external scripts and using them in referencing files
and directories in local and shared storage in the documentation of the concrete
:py:class:`~.Environment` implementations, especially
:py:class:`~mlos_bench.environments.script_env.ScriptEnv` and
:py:class:`~mlos_bench.environments.local.local_env.LocalEnv`.

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
