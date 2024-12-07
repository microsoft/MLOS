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

Here's a very basic example of the Storage APIs.

>>> # Create a new storage object from a JSON config.
>>> # Normally, we'd load these from a file, but for this example we'll use a string.
>>> global_config = '''
... {
...     // Additional global configuration parameters can be added here.
...     /* For instance:
...     "storage_host": "some-remote-host",
...     "storage_user": "mlos_bench",
...     "storage_pass": "SuperSecretPassword",
...     */
... }
... '''
>>> storage_config = '''
... {
...     "class": "mlos_bench.storage.sql.storage.SqlStorage",
...     "config": {
...         // Don't create the schema until we actually need it.
...         // (helps speed up initial launch and tests)
...         "lazy_schema_create": true,
...         // Parameters below must match kwargs of `sqlalchemy.URL.create()`:
...         // Normally, we'd specify a real database, but for testing examples
...         // we'll use an in-memory one.
...         "drivername": "sqlite",
...         "database": ":memory:"
...         // Otherwise we might use something like the following
...         // to pull the values from the globals:
...         /*
...         "host": "$storage_host",
...         "username": "$storage_user",
...         "password": "$storage_pass",
...         */
...     }
... }
... '''
>>> from mlos_bench.storage import from_config
>>> storage = from_config(storage_config, global_configs=[global_config])
>>> storage
sqlite::memory:
>>> #
>>> # Internally, mlos_bench will use this config and storage backend to track
>>> # Experiments and Trials it creates.
>>> # Most users won't need to do that, but it works something like the following:
>>> # Create a new experiment with a single trial.
>>> # (Normally, we'd use a real environment config, but for this example we'll use a string.)
>>> #
>>> # Create a dummy tunable group.
>>> from mlos_bench.services.config_persistence import ConfigPersistenceService
>>> config_persistence_service = ConfigPersistenceService()
>>> tunables_config = '''
... {
...   "param_group": {
...     "cost": 1,
...     "params": {
...       "param1": {
...         "type": "int",
...         "range": [0, 100],
...         "default": 50
...       }
...     }
...   }
... }
... '''
>>> tunables = config_persistence_service.load_tunables([tunables_config])
>>> from mlos_bench.environments.status import Status
>>> from datetime import datetime
>>> with storage.experiment(
...   experiment_id="my_experiment_id",
...   trial_id=1,
...   root_env_config="root_env_config_info",
...   description="some description",
...   tunables=tunables,
...   opt_targets={"objective_metric": "min"},
... ) as experiment:
...     # Create a dummy trial.
...     trial = experiment.new_trial(tunables=tunables)
...     # Pretend something ran with that trial and we have the results now.
...     _ = trial.update(Status.SUCCEEDED, datetime.now(), {"objective_metric": 42})
>>> #
>>> # Now, once there's data to look at, in a Jupyter notebook or similar,
>>> # we can also use the storage object to view the results.
>>> #
>>> storage.experiments
{'my_experiment_id': Experiment :: my_experiment_id: 'some description'}
>>> # Access ExperimentData by experiment id.
>>> experiment_data = storage.experiments["my_experiment_id"]
>>> experiment_data.trials
{1: Trial :: my_experiment_id:1 cid:1 SUCCEEDED}
>>> # Access TrialData for an Experiment by trial id.
>>> trial_data = experiment_data.trials[1]
>>> assert trial_data.status == Status.SUCCEEDED
>>> # Retrieve the tunable configuration from the TrialData as a dictionary.
>>> trial_config_data = trial_data.tunable_config
>>> trial_config_data.config_dict
{'param1': 50}
>>> # Retrieve the results from the TrialData as a dictionary.
>>> trial_data.results_dict
{'objective_metric': 42}
>>> # Retrieve the results of all Trials in the Experiment as a DataFrame.
>>> experiment_data.results_df.columns.tolist()
['trial_id', 'ts_start', 'ts_end', 'tunable_config_id', 'tunable_config_trial_group_id', 'status', 'config.param1', 'result.objective_metric']
>>> # Drop the timestamp columns to make it a repeatable test.
>>> experiment_data.results_df.drop(columns=["ts_start", "ts_end"])
   trial_id  tunable_config_id  tunable_config_trial_group_id     status  config.param1  result.objective_metric
0         1                  1                              1  SUCCEEDED             50                       42

[1 rows x 6 columns]

See Also
--------
mlos_bench.storage.base_storage : Base interface for backends.
mlos_bench.storage.base_experiment_data : Base interface for ExperimentData.
mlos_bench.storage.base_trial_data : Base interface for TrialData.

Notes
-----
- See `sqlite-autotuning notebooks
  <https://github.com/Microsoft-CISL/sqlite-autotuning/blob/main/mlos_demo_sqlite_teachers.ipynb>`_
  for additional examples.
"""  # pylint: disable=line-too-long # noqa: E501

from mlos_bench.storage.base_storage import Storage
from mlos_bench.storage.storage_factory import from_config

__all__ = [
    "Storage",
    "from_config",
]
