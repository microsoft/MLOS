# MLOS

[![MLOS DevContainer](https://github.com/microsoft/MLOS/actions/workflows/devcontainer.yml/badge.svg)](https://github.com/microsoft/MLOS/actions/workflows/devcontainer.yml)
[![MLOS Linux](https://github.com/microsoft/MLOS/actions/workflows/linux.yml/badge.svg)](https://github.com/microsoft/MLOS/actions/workflows/linux.yml)
[![MLOS Windows](https://github.com/microsoft/MLOS/actions/workflows/windows.yml/badge.svg)](https://github.com/microsoft/MLOS/actions/workflows/windows.yml)
[![Code Coverage Status](https://microsoft.github.io/MLOS/_images/coverage.svg)](https://microsoft.github.io/MLOS/htmlcov/index.html)

This repository contains a stripped down implementation of essentially just the core optimizer and config space description APIs from the original [MLOS](https://github.com/microsoft/MLOS)<!-- /tree/deprecated --> as well as the [`mlos-bench`](./mlos_bench/) module intended to help automate and manage running experiments for autotuning systems with [`mlos-core`](./mlos_core/).

It is intended to provide a simplified, easier to consume (e.g. via `pip`), with lower dependencies abstraction to

- describe a space of context, parameters, their ranges, constraints, etc. and result objectives
- an "optimizer" service [abstraction](https://microsoft.github.io/MLOS/overview.html#mlos-core-api) (e.g. [`register()`](https://microsoft.github.io/MLOS/generated/mlos_core.optimizers.optimizer.BaseOptimizer.html#mlos_core.optimizers.optimizer.BaseOptimizer.register) and [`suggest()`](https://microsoft.github.io/MLOS/generated/mlos_core.optimizers.optimizer.BaseOptimizer.html#mlos_core.optimizers.optimizer.BaseOptimizer.suggest)) so we can easily swap out different implementations methods of searching (e.g. random, BO, etc.)
- provide some helpers for [automating optimization experiment](https://microsoft.github.io/MLOS/overview.html#mlos-bench-api) runner loops and data collection

For these design requirements we intend to reuse as much from existing OSS libraries as possible and layer policies and optimizations specifically geared towards autotuning over top.

## Getting Started

The development environment for MLOS uses `conda` to ease dependency management.

### Devcontainer

For a quick start, you can use the provided [VSCode devcontainer](https://code.visualstudio.com/docs/remote/containers) configuration.

Simply open the project in VSCode and follow the prompts to build and open the devcontainer and the conda environment and additional tools will be installed automatically inside the container.

### Manually

> See Also: [`conda` install instructions](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
>
> Note: to support Windows we currently rely on some pre-compiled packages from `conda-forge` channels, which increases the `conda` solver time during environment create/update.
>
> To work around this the (currently) experimental `libmamba` solver can be used.
>
> See <https://github.com/conda-incubator/conda-libmamba-solver#getting-started> for more details.

0. Create the `mlos` Conda environment.

     ```sh
    conda env create -f conda-envs/mlos.yml
    ```

    > See the [`conda-envs/`](./conda-envs/) directory for additional conda environment files, including those used for Windows (e.g. [`mlos-windows.yml`](./conda-envs/mlos-windows.yml)).

   or

    ```sh
    # This will also ensure the environment is update to date using "conda env update -f conda-envs/mlos.yml"
    make conda-env
    ```

    > Note: the latter expects a *nix environment.

1. Initialize the shell environment.

    ```sh
    conda activate mlos
    ```

2. For an example of using the `mlos_core` optimizer APIs run the [`BayesianOptimization.ipynb`](./mlos_core/notebooks/BayesianOptimization.ipynb) notebook.

3. For an example of using the `mlos_bench` tool to run an experiment, see the [`mlos_bench` Quickstart README](./mlos_bench/README.md#quickstart).

    Here's a quick summary:

    ```shell
    ./scripts/generate-azure-credentials-config > global_config_azure.json

    # run a simple experiment
    mlos_bench --config ./mlos_bench/mlos_bench/config/cli/azure-redis-1shot.jsonc
    ```

    > See Also:
    >
    > - [mlos_bench/README.md](./mlos_bench/README.md) for a complete example.
    > - [mlos_bench/config](./mlos_bench/mlos_bench/config/) for additional configuration details

## Distributing

1. Build the *wheel* file(s)

    ```sh
    make dist
    ```

2. Install it (e.g. after copying it somewhere else).

    ```sh
    # this will install just the optimizer component with SMAC support:
    pip install dist/mlos_core-0.1.0-py3-none-any.whl[smac]

    # this will install just the optimizer component with flaml support:
    pip install dist/mlos_core-0.1.0-py3-none-any.whl[flaml]

    # this will install just the optimizer component with smac and flaml support:
    pip install dist/mlos_core-0.1.0-py3-none-any.whl[smac,flaml]
    ```

    ```sh
    # this will install both the optimizer and the experiment runner:
    pip install dist/mlos_bench-0.1.0-py3-none-any.whl
    ```

    > Note: exact versions may differ due to automatic versioning.

## See Also

- API and Examples Documentation: <https://aka.ms/mlos-core/docs>
- Source Code Repository: <https://aka.ms/mlos-core/src>
