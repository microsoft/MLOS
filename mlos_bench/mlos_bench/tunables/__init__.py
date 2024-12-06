#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tunables classes for Environments in mlos_bench.

.. contents:: Table of Contents
   :depth: 3

Overview
^^^^^^^^

mlos_bench uses the concept of "tunables" to define the configuration space for an
:py:class:`~mlos_bench.environments.base_environment.Environment`.

An :py:class:`~mlos_bench.optimizers.base_optimizer.Optimizer` can then use these
tunables to explore the configuration space in order to improve some target
objective metrics (e.g., reduce tail latency, reduce cost, improve throughput,
etc.).

They are similar to the concept of "hyperparameters" in machine learning, but are
used to configure the system being tested.

Classes
^^^^^^^

Tunable
+++++++

The :py:class:`~mlos_bench.tunables.tunable.Tunable` class is used to define a
single tunable parameter.
A ``Tunable`` can be a ``categorical`` or numeric (``int`` or ``float``) and always has
at least a domain (``range`` or set of ``values``) and default.
Each type can also have a number of additional properties that can optionally be set
to help control the sampling of the tunable.

For instance:

- Numeric tunables can have a ``distribution`` property to specify the sampling
  distribution.  ``log`` sampling can also be enabled for numeric tunables.
- Categorical tunables can have a ``values_weights`` property to specify biased
  sampling of the values
- ``special`` values can be marked to indicate that they need more explicit testing
  This can be useful for values that indicate "automatic" or "disabled" behavior.

The full set of supported properties can be found in the `JSON schema for tunable
parameters
<https://github.com/microsoft/MLOS/blob/main/mlos_bench/mlos_bench/config/schemas/tunables/tunable-params-schema.json>`_
and seen in some of the `test examples in the source tree
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/tests/config/schemas/tunable-params/test-cases/good/>`_.

CovariantGroup
++++++++++++++

The :py:class:`~mlos_bench.tunables.covariant_group.CovariantTunableGroup` class is
used to define a group of related tunable parameters that are all configured
together with the same ``cost`` (e.g., is a more expensive operation required to
reconfigure the system like redeployed vs. restarted vs. reloaded).
Optimizers can use this information to explore the configuration space more efficiently.

TunableGroups
+++++++++++++

The :py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups` class is used to
define an entire set of tunable parameters (e.g., combined set of covariant groups).

Usage
^^^^^

Most user interactions with tunables will be through JSON configuration files.

Since tunables are associated with an Environment, their configs are typically
colocated with the environment configs (e.g., ``env-name-tunables.jsonc``) and
loaded with the Environment using the ``include_tunables`` property in the
Environment config.

Then individual covariant groups can be enabled via the ``tunable_params`` and
``tunable_params_map`` properties, possibly via ``globals`` variable expansion.

See the :py:mod:`mlos_bench.config` and :py:mod:`mlos_bench.environments` module
documentation for more information.

In benchmarking-only mode (e.g., without an ``Optimizer`` specified), ``mlos_bench``
can still run with a particular set of ``--tunable-values`` (e.g., a simple
key-value file declaring a set of values to assign to the set of configured tunable
parameters) in order to manually explore a configuration space.

See the :py:mod:`mlos_bench.run` module documentation for more information.

During an Environment's ``setup`` and ``run`` phases the tunables can be exported to
a JSON file using the ``dump_params_file`` property of the Environment config for
the user scripts to use when configuring the target system.
The ``meta`` property of the tunable config can be used to add additional
information for this step (e.g., a unit suffix to append to the value).

See the :py:mod:`mlos_bench.environments` module documentation for more information.

Examples
--------
Here's a short (incomplete) example of some of the TunableGroups JSON configuration
options, expressed in Python (for testing purposes).
However, most of the time you will be loading these from a JSON config file stored
along with the associated Environment config.

For more tunable parameters examples refer to the `JSON schema
<https://github.com/microsoft/MLOS/blob/main/mlos_bench/mlos_bench/config/schemas/tunables/tunable-params-schema.json>`_
or some of the `test examples in the source tree
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/tests/config/schemas/tunable-params/test-cases/good/>`_.

There are also examples of `tunable values in the source tree
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/tests/config/schemas/tunable-values/test-cases/good/>`_.

>>> # Load tunables from JSON string.
>>> import json5
>>> from mlos_bench.services.config_persistence import ConfigPersistenceService
>>> service = ConfigPersistenceService()
>>> json_config = '''
... {
...   "group_1": {
...     "cost": 1,
...     "params": {
...       "colors": {
...         "type": "categorical",
...         // Values for the categorical tunable.
...         "values": ["red", "blue", "green"],
...         // Weights for each value in the categorical distribution.
...         "values_weights": [0.1, 0.2, 0.7],
...         // Default value.
...         "default": "green",
...       },
...       "int_param": {
...         "type": "int",
...         "range": [-1, 10],
...         "default": 5,
...         // Mark some values as "special", that need more explicit testing.
...         // e.g., maybe these indicate "automatic" or "disabled" behavior for
...         // the system being tested instead of an explicit size
...         "special": [-1, 0],
...         // Optionally specify a sampling distribution.
...         "distribution": {
...             "type": "uniform" // alternatively, "beta" or "normal"
...         },
...         // Free form key-value pairs that can be used with the
...         // tunable upon sampling for composing configs.
...         "meta": {
...           "suffix": "MB"
...         }
...       },
...       "float_param": {
...         "type": "float",
...         "range": [1, 10000],
...         "default": 1,
...         // Quantize the range into 100 bins
...         "quantization_bins": 100,
...         // enable log sampling of the bins
...         "log": true
...       }
...     }
...   }
... }
... '''
>>> tunables = service.load_tunables(jsons=[json_config])
>>> # Retrieve the current value for the tunable groups.
>>> tunables.get_param_values()
{'colors': 'green', 'int_param': 5, 'float_param': 1.0}
>>> # Or an individual parameter:
>>> tunables["colors"]
'green'
>>> # Assign new values to the tunable groups.
>>> tunable_values = json5.loads('''
... {
...   // can be partially specified
...   "colors": "red"
... }
... ''')
>>> _ = tunables.assign(tunable_values)
>>> tunables.get_param_values()
{'colors': 'red', 'int_param': 5, 'float_param': 1.0}
>>> # Check if the tunables have been updated.
>>> # mlos_bench uses this to reinvoke the setup() phase of the
>>> # associated Environment to reconfigure the system.
>>> tunables.is_updated()
True
>>> # Reset the tunables to their default values.
>>> # As a special case, an empty json object will reset all tunables to the defaults.
>>> tunable_values = json5.loads('''
... {}
... ''')
>>> _ = tunables.assign(tunable_values)
>>> tunables.is_defaults()
True
>>> tunables.get_param_values()
{'colors': 'green', 'int_param': 5, 'float_param': 1.0}

Notes
-----
Internally, :py:class:`.TunableGroups` are converted to
:external:py:class:`ConfigSpace.ConfigurationSpace` objects for use with
:py:mod:`mlos_core`.
See the "Spaces" section in the :py:mod:`mlos_core` module documentation for more
information.

See Also
--------
:py:mod:`mlos_bench.config` : Overview of the configuration system.
:py:mod:`mlos_bench.environments` : Overview of Environments and their configurations.
:py:mod:`mlos_core.optimizers` : Overview of mlos_core optimizers.
:py:mod:`mlos_core.spaces` : Overview of the mlos_core configuration space system.
:py:meth:`.TunableGroups.assign` : Notes on special cases for assigning tunable values.
"""

from mlos_bench.tunables.tunable import Tunable, TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

__all__ = [
    "Tunable",
    "TunableValue",
    "TunableGroups",
]
