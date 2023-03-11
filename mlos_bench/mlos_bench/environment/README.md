# Environments

This directory contains the code for the `Environments` used in the [`mlos_bench`](../../../mlos_bench/) benchmarking automation framework.

Each Environment has several stages that it goes through:

- `setup`
- `run`
- `teardown`

Which are implemented using [`Services`](../service/).

Environments also have [`Tunables`](../tunables/) and [`TunableGroups`](../tunables/) for controlling their configuration.

Environments can also be stackable via the [`CompositeEnvironment`](./composite.py) class.

For instance, a VM, OS, and Application Environment can be stacked together to form a full benchmarking environment, each with their own tunables.

It is generally expected that all `Tunables` within an `Environment` will have the same cost to change.
Thus one may represent a system by multiple `Environments` (e.g. `BootTimeEnvironment`, `RuntimeEnvironment`, etc.)
