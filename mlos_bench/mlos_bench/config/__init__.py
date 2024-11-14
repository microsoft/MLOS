#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A module for managing json config schemas and their validation for various components of
MLOS.

Overview
++++++++

MLOS is a framework for doing benchmarking and autotuning for systems written in
python. As such, all of the code classes documented here take python objects in
their construction.

However, most users of MLOS will interact with the system via the ``mlos_bench`` CLI
and its json config files. This module attempts to document some of those high level
interactions.

General JSON Config Structure
+++++++++++++++++++++++++++++

We use `json5 <https://pypi.org/project/json5/>`_ to parse the json files, since it
allows for inline C style comments (e.g., ``//``, ``/* */``).

By convention files use the ``*.mlos.json`` or ``*.mlos.jsonc`` extension to indicate
that they are an ``mlos_bench`` config file.

This allows tools that support `JSON Schema Store
<https://www.schemastore.org/json/>`_ (e.g., `VSCode
<https://code.visualstudio.com/>`_) to provide helpful autocomplete and validation
of the json configs while editing.

CLI Configs
^^^^^^^^^^^

Tunable Configs
^^^^^^^^^^^^^^^

Tunable

Class Configs
^^^^^^^^^^^^^

Class style configs include most anything else and roughly take this form:

.. code block:: json
   {
      // some mlos class name to load
      "class": "mlos_bench.type.ClassName",
      "config": {
        // class specific config
        "key": "value"
      }
   }

Globals and Variable Substitution
+++++++++++++++++++++++++++++++++
TODO: Document globals and variable substitution.

Well Known Variables
++++++++++++++++++++

Here is a list of well known variables that are used in the config files:

- ``$experiment_id``: A unique identifier for the experiment.
    Typically provided in globals.

Config Processing
+++++++++++++++++

Config files are processed by the :py:class:`~mlos_bench.launcher.Launcher` and
:py:class:`~mlos_bench.services.config_persistence.ConfigPersistenceService` classes
at startup time by the ``mlos_bench`` CLI.

The typical entrypoint is a CLI config which references other configs, especially
the base Environment config, Services, Optimizer, and Storage.

See `mlos_bench CLI usage </mlos_bench.run.usage.html>`_ for more details on
those arguments.

Schema Definitions
++++++++++++++++++

For further details on the schema definitions and validation, see the
:py:class:`~mlos_bench.config.schemas.config_schemas.ConfigSchema` class
documentation, which also contains links to the actual schema definitions in the
source tree (see below).

Notes
-----
See `mlos_bench/config/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/>`_ and
`mlos_bench/tests/config/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/tests/config/>`_
for additional documentation and examples in the source tree.
"""
