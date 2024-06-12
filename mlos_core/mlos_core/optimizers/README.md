# Optimizers

This is a directory that contains wrappers for different optimizers to integrate into MLOS.
This is implemented though child classes for the `BaseOptimizer` class defined in `optimizer.py`.

The main goal of these optimizers is to `suggest` configurations, possibly based on prior trial data to find an optimum based on some objective(s).
This process is interacted with through `register` and `suggest` interfaces.

The following defintions are useful for understanding the implementation
- `configuration`: a vector representation of a configuration of a system to be evaluated.
- `score`: the objective(s) associated with a configuration
- `metadata`: additional information about the evaluation, such as the runtime budget used during evaluation.
- `context`: additional (static) information about the evaluation used to extend the internal model used for suggesting samples.
   For instance, a descriptor of the VM size (vCore count and # of GB of RAM), and some descriptor of the workload.
   The intent being to allow either sharing or indexing of trial info between "similar" experiments in order to help make the optimization process more efficient for new scenarios.
   > Note: This is not yet implemented.

The interface for these classes can be described as follows:

- `register`: this is a function that takes a configuration, a score, and, optionally, metadata about the evaluation to update the model for future evaluations.
- `suggest`: this function returns a new configuration for evaluation.

   Some optimizers will return additional metadata for evaluation, that should be used during the register phase.
   This function can also optionally take context (not yet implemented), and an argument to force the function to return the default configuration.
- `register_pending`: registers a configuration and metadata pair as pending to the optimizer.
- `get_observations`: returns all observations reproted to the optimizer as a triplet of DataFrames (config, score, context, metadata).
- `get_best_observations`: returns the best observation as a triplet of best (config, score, context, metadata) DataFrames.