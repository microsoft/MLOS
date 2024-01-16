# mlos_viz

The [`mlos_viz`](./) module is an aid to visualizing experiment benchmarking and optimization results generated and stored by [`mlos_bench`](../mlos_bench/).

Its core API is `mlos_viz.plot(experiment)`, initially implemented as a wrapper around [`dabl`](https://github.com/dabl/dabl) to provide a basic visual overview of the results, where `experiment` is an [`ExperimentData`](../mlos_bench/mlos_bench/storage/base_experiment_data.py) objected returned from the [`mlos_bench.storage`](../mlos_bench/mlos_bench/storage/) layer.

In the future, we plan to add more automatic visualizations, interactive visualizations, feedback to the `mlos_bench` experiment trial scheduler, etc.
