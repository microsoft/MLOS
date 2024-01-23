# mlos-bench Storage APIs

The [`mlos_bench.storage`](./) module provides APIs for both storing and retrieving experiment results.

## Write Access APIs for Experimentation

The `mlos_bench.storage` modules include the `Storage`, `Experiment`, and `Trial` classes.

The `Storage` class is the top-level class that implements a storage backend (e.g., SQL RDBMS).

Storage config files are typically needed to configure these (e.g., hostname and authentication info), but a default of `storage/sqlite.jsonc` is provided for local only storage.

The `Experiment` and `Trial` classes are used to store experiment and trial results, respectively.

See Also: <https://microsoft.github.io/MLOS> for full API details.

## Read Access APIs for Analysis

Read access to experiment results is provided via the `ExperimentData` and `TrialData` classes.

The former can be accessed thru `Storage.experiments[experiment_id]` and the latter thru `ExperimentData.trials[trial_id]`.

These are expected to be used in a more interactive environment such as a Jupyter notebook.

For example:

```python
from mlos_bench.storage import from_config
# Specify the experiment_id used for your experiment.
experiment_id = "YourExperimentId"
trial_id = 1
# Specify the path to your storage config file.
storage = from_config(config_file="storage/sqlite.jsonc")
# Access one of the experiments' data:
experiment_data = storage.experiments[experiment_id]
# Full experiment results are accessible in a data frame:
results_data_frame = experiment_data.results
# Individual trial results are accessible via the trials dictionary:
trial_data = experiment_data.trials[trial_id]
# Tunables used for the trial are accessible via the config property:
trial_config = trial_data.config
```

See the [`sqlite-autotuning`](https://github.com/Microsoft-CISL/sqlite-autotuning) repository for a full example.
