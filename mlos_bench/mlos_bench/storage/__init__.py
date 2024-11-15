#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Interfaces to the storage backends for mlos_bench.

Storage backends (for instance :py:mod:`~mlos_bench.storage.sql`) are used to store
and retrieve the results of experiments and implement a persistent queue for
:py:mod:`~mlos_bench.schedulers`.

The :py:class:`~mlos_bench.storage.base_storage.Storage` class is the main interface
and provides the ability to

- Create or reload a new :py:class:`~.Storage.Experiment` with one or more
  associated :py:class:`~.Storage.Trial` instances which are used by the
  :py:mod:`~mlos_bench.schedulers` during ``mlos_bench`` run time to execute
  `Trials`.

  In MLOS terms, an *Experiment* is a group of *Trials* that share the same scripts
  and target system.

  A *Trial* is a single run of the target system with a specific *Configuration*
  (e.g., set of tunable parameter values).
  (Note: other systems may call this a *sample*)

- Retrieve the :py:class:`~mlos_bench.storage.base_trial_data.TrialData` results
  with the :py:attr:`~mlos_bench.storage.base_experiment_data.ExperimentData.trials`
  property on a :py:class:`~mlos_bench.storage.base_experiment_data.ExperimentData`
  instance via the :py:class:`~.Storage` instance's
  :py:attr:`~mlos_bench.storage.base_storage.Storage.experiments` property.

  These can be especially useful with :py:mod:`mlos_viz` for interactive exploration
  in a Jupyter Notebook interface, for instance.

The :py:func:`.from_config` :py:mod:`.storage_factory` function can be used to get a
:py:class:`.Storage` instance from a
:py:attr:`~mlos_bench.config.schemas.config_schemas.ConfigSchema.STORAGE` type json
config.

Example
-------
TODO: Add example usage.

Notes
-----
- See `sqlite-autotuning notebooks
  <https://github.com/Microsoft-CISL/sqlite-autotuning/blob/main/mlos_demo_sqlite_teachers.ipynb>`_
  for additional examples.
"""

from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.storage_factory import from_config

__all__ = [
    "Storage",
    "from_config",
]
