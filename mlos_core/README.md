# mlos-core

This [directory](./) contains the code for the `mlos-core` optimizer package.

## Description

`mlos-core` is an optimizer package, using Bayesian optimization to identify & sample tunable configuration parameters and propose optimal parameter values.
These are evaluated by `mlos-bench`, generating and tracking experiment results (proposed parameters, benchmark results & telemetry) to update the optimization loop.

## Features

Since the tunable OS kernel parameter search space is extremely large, `mlos-core` automates the following steps to efficiently generate optimal task-specific kernel configurations.

1. Reduce the search space by identifying a promising set of tunable parameters
    - Map out the configuration search space: Automatically track and manage the discovery of new Linux kernel parameters and their default values across versions. Filter out non-tunable parameters (e.g., not writable) and track which kernel parameters exist for a given kernel version.
    - Leverage parameter knowledge for optimization: Information on ranges, sampling intervals, parameter correlations, workload type sensitivities for tunable parameters are tracked and currently manually curated. In the future, this can be automatically maintained by scraping documentation pages on kernel parameters.
    - Tailored to application: Consider prior knowledge of the parameter's impact & an application's workload profile (e.g. network heavy, disk heavy, CPU bound, multi-threaded, latency sensitive, throughput oriented, etc.) to identify likely impactful candidates of tunable parameters, specific to a particular application.
2. Sampling to warm-start optimization in a high dimensional search space
3. Produce optimal configurations through Bayesian optimization
    - Support for various optimizer algorithms (default Bayesian optimizer, Flaml, SMAC, and random for baseline comparison), that handle multiple types of constraints. This includes cost-aware optimization, that considers experiment costs given current tunable parameters.
    - Integrated with `mlos-bench`, proposed configurations are logged and evaluated.
