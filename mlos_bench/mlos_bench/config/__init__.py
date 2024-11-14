#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A module for and documentation about the structure and mangement of json configs,
their schemas and validation for various components of MLOS.

.. contents:: Table of Contents
   :depth: 3

Overview
++++++++

MLOS is a framework for doing benchmarking and autotuning for systems.
The bulk of the code to do that is written in python. As such, all of the code
classes documented here take python objects in their construction.

However, most users of MLOS will interact with the system via the ``mlos_bench`` CLI
and its json config files and their own scripts for MLOS to invoke. This module
attempts to document some of those high level interactions.

General JSON Config Structure
+++++++++++++++++++++++++++++

We use `json5 <https://pypi.org/project/json5/>`_ to parse the json files, since it
allows for inline C style comments (e.g., ``//``, ``/* */``), trailing commas, etc.,
so it is slightly more user friendly than strict json.

By convention files use the ``*.mlos.json`` or ``*.mlos.jsonc`` extension to
indicate that they are an ``mlos_bench`` config file.

This allows tools that support `JSON Schema Store
<https://www.schemastore.org/json/>`_ (e.g., `VSCode
<https://code.visualstudio.com/>`_) to provide helpful autocomplete and validation
of the json configs while editing.

CLI Configs
^^^^^^^^^^^

:py:attr:`~.mlos_bench.config.schemas.config_schemas.ConfigSchema.CLI` style configs
are typically used to start the ``mlos_bench`` CLI using the ``--config`` argument
and a restricted key-value dict form where each key corresponds to a CLI argument.

For instance:

.. code-block:: json

   // cli-config.mlos.json
   {
     "experiment": "path/to/base/experiment-config.mlos.json",
     "services": [
       "path/to/some/service-config.mlos.json",
     ],
     "globals": "path/to/basic-globals-config.mlos.json",
   }

   // basic-globals-config.mlos.json
   {
     "location": "westus",
     "vm_size": "Standard_D2s_v5",
   }

Typically CLI configs will reference some other configs, especially the base
Environment and Services configs, but some ``globals`` may be left to be specified
on the command line.

For instance:

.. code-block:: shell

   mlos_bench --config path/to/cli-config.mlos.json --globals experiment-config.mlos.json

where ``experiment-config.mlos.json`` might look something like this:

.. code-block:: json
   {
     "experiment_id": "my_experiment",
     "some_var": "some_value",
   }

This allows some of the ``globals`` to be specified on the CLI to alter the behavior
of a set of Experiments without having to adjust many of the other config files
themselves.

See below for examples.

Notes
-----
- See `mlos_bench CLI usage </mlos_bench.run.usage.html>`_ for more details on the
  CLI arguments.
- See `mlos_bench/config/cli
  <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/cli>`_
  and `mlos_bench/tests/config/cli
  <https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/tests/config/cli>`_
  for some examples of CLI configs.

Globals and Variable Substitution
+++++++++++++++++++++++++++++++++

:py:attr:`Globals <mlos_bench.config.schemas.config_schemas.ConfigSchema.GLOBALS>`
are basically just key-value variables that can be used in other configs using
``$variable`` substituion via the
:py:meth:`~mlos_bench.dict_templater.DictTemplater.expand_vars` method.

For instance:

.. code-block:: json

   // globals-config.mlos.json
   {
     "experiment_id": "my_experiment",
     "some_var": "some_value",
     // environment variable expansion also works here
     "current_dir": "$PWD",
     "some_expanded_var": "$some_var: $experiment_id",
     "location": "eastus",
   }

There are additional details about variable propogation in the
:py:mod:`mlos_bench.environments` module.

Well Known Variables
^^^^^^^^^^^^^^^^^^^^

Here is a list of some well known variables that are provided or required by the
system and may be used in the config files:

- ``$experiment_id``: A unique identifier for the experiment.
    Typically provided in globals.
- ``$trial_id``: A unique identifier for the trial currently being executed.
    This can be useful in the configs for :py:mod:`mlos_bench.environments` for
    instance (e.g., when writing scripts).
- TODO: Document more variables here.

Tunable Configs
^^^^^^^^^^^^^^^

There are two forms of tunable configs:

- "TunableParams"  style configs

    Which are used to define the set of
    :py:mod:`~mlos_bench.tunables.tunable_groups.TunableGroups` (i.e., tunable
    parameters).

    .. code-block:: json

       // env-tunables.json
       {
         // a group of tunables that are tuned together
         "covariant_group_name": [
           {
             "name": "tunable_name",
             "type": "int",
             "range": [0, 100],
             "default": 50,
           },
           // more tunables
         ],
         // another group of tunables
         // both can be enabled at the same time
         "another_group_name": [
           {
             "name": "another_tunable_name",
             "type": "categorical",
             "values": ["red", "yellow", "green"],
             "default": "green"
           },
           // more tunables
         ],
       }

       Since TunableParams are associated with Environments, they are typically kept
       in the same directory as that environment and named something like
       ``env-tunables.json``.

- "TunableValues" style configs which are used to specify the values for an
  instantiation of a set of tunables params.

  These are essentially just a dict of the tunable names and their values.
  For instance:

    .. code-block:: json

       {
          "tunable_name": 25,
          "another_tunable_name": "red",
       }

  These can be used with the
  :py:class:`~mlos_bench.optimizers.one_shot_optimizer.OneShotOptimizer`
  :py:class:`~mlos_bench.optimizers.manual_optimizer.ManualOptimizer` to run a
  benchmark with a particular config or set of configs.

Class Configs
^^^^^^^^^^^^^

Class style configs include most anything else and roughly take this form:

.. code-block:: json

   // class configs (environments, services, etc.)
   {
      // some mlos class name to load
      "class": "mlos_bench.type.ClassName",
      "config": {
        // class specific config
        "key": "value",
        "key2": "$some_var",    // variable substitution is allowed here too
      }
   }

Where ``type`` is one of the core classes in the system:

- :py:mod:`~mlos_bench.environments`
- :py:mod:`~mlos_bench.optimizers`
- :py:mod:`~mlos_bench.services`
- :py:mod:`~mlos_bench.schedulers`
- :py:mod:`~mlos_bench.storage`

Each of which have their own submodules and classes that dictate the allowed and
expected structure of the ``config`` section.

In certain cases (e.g., script command execution) the variable substitution rules
take on slightly different behavior
See various documentation in :py:mod:`mlos_bench.environments` for more details.

Config Processing
+++++++++++++++++

Config files are processed by the :py:class:`~mlos_bench.launcher.Launcher` and
:py:class:`~mlos_bench.services.config_persistence.ConfigPersistenceService` classes
at startup time by the ``mlos_bench`` CLI.

The typical entrypoint is a CLI config which references other configs, especially
the base Environment config, Services, Optimizer, and Storage.

See `mlos_bench CLI usage </mlos_bench.run.usage.html>`_ for more details on those
arguments.

Schema Definitions
++++++++++++++++++

For further details on the schema definitions and validation, see the
:py:class:`~mlos_bench.config.schemas.config_schemas.ConfigSchema` class
documentation, which also contains links to the actual schema definitions in the
source tree (see below).

Notes
+++++
See `mlos_bench/config/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/>`_ and
`mlos_bench/tests/config/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/tests/config/>`_
for additional documentation and examples in the source tree.
"""
