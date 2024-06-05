This is a directory that contains wrappers for different optimizers to integrate into MLOS.
This is implemented though child classes for the `BaseOptimizer` class defined in `optimizer.py`.

The main goal of these optimizers is to take a suggest configurations based on prior samples to find an optimum based on some objective. This process is interacted with through and ask and tell interface.

The following defintions are useful for understanding the implementation
- `configuration`: a vector representation of a configuration of a system to be evaluated.
- `score`: the objective(s) associated with a configuration
- `metadata`: additional information about the evaluation, such as the runtime budget used during evaluation.
- `context`: additional information about the evaluation used to extend the internal model used for suggesting samples. This is not yet implemented.

The interface for these classes can be described as follows:

- `register`: this is a function that takes a configuration, a score, and, optionally, metadata about the evaluation to update the model for future evaluations.
- `suggest`: this function returns a new confiugration for evaluation. Some optimizers will return additional metadata for evaluation, that should be used durin the register phase. This function can also optionally take context (not yet implemented), and an argument to force the function to return the default configuration.
- `register_pending`: registers a configuration and metadata pair as pending to the optimizer.
- `get_observations`: returns all observations reproted to the optimizer as a triplet of DataFrames (config, score, metadata).
- `get_best_observations`: returns the best observation as A triplet of best (config, score, metadata) DataFrames.