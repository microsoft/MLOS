# Environments

## Overview

This directory contains the code for the [`Environment`](./base_environment.py) classes used in the [`mlos_bench`](../../../mlos_bench/) benchmarking automation framework.
An [`Environment`](./base_environment.py) is a class that represents a system that can be benchmarked.
It is responsible for setting up a portion of the system, running the benchmark (or some other command), and tearing down that portion of the system.
A `CompositeEnvironment` can be used to stack these together to represent the entire system under evaluation (e.g., VM, OS, App, etc.)
Each `Environment` object also keeps track of the current state of the system, and can be used to query the system for metrics.

Environments can have [`Tunable`](../tunables/tunable.py) parameters and [`TunableGroups`](../tunables/tunable_groups.py) for controlling their configuration.
It is generally expected that all [`Tunable`](../tunables/tunable.py) parameters within an `Environment` will have the same cost to change.
> It may therefore make sense to split a portion of the system logically across `Environments` (e.g., boot-time vs. runtime settings).

Common and platform-specific functionality of the environments is implemented in [`Service`](../services/) classes.

## Lifecycle

Each Environment has several stages that it goes through:

- `setup`
- `run`
- `teardown`

One can also query the current state of the system via the `.status()` method.
Our current implementation of the `Environment` classes is synchronous; that means, a `.status()` method can only be used *after* `.run()` method has been called.

Once we implement an asynchronous mode of operation, the `.status()` method will be usable at any time during the `Environment` object lifecycle.

## Composite Environments

Environments can be stacked via the [`CompositeEnv`](./composite_env.py) class.
For instance, a VM, OS, and Application Environment can be stacked together to form a full benchmarking environment, each with their own tunables.
Thus one may represent a system by multiple `Environment` objects, e.g., [`VMEnv`](./remote/vm_env.py), [`RemoteEnv`](remote/remote_env.py), and so on.
