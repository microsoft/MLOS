# Tunables

This directory contains the code for the *Tunables* used in the [`mlos_bench`](../../../mlos_bench/) benchmarking optimization framework.

A `TunableGroup` is a collection of `Tunables` that are related to each other in some way.
For example, they may all be part of the same [`Environment`](../environments/) and hence have the same cost to change together.
A good example are "boot time" kernel parameters vs. "runtime" kernel parameters vs. "application" parameters.

## TODOs

- Evaluate replacing these entirely with [`ConfigSpace`](https://automl.github.io/ConfigSpace/main/), since that is currently what we use to configure the ([`mlos_core`](../../../mlos_core/)) [`Optimizer`](../optimizers/).
