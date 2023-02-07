# MlosCore

This repository contains a stripped down implementation of essentially just the core optimizer and config space description APIs from the original [MLOS](https://github.com/microsoft/MLOS) as well as the `mlos-bench` module intended to help automate and manage running experiments for autotuning systems with `mlos-core`.

It is intended to provide a simplified, easier to consume (e.g. via `pip`), with lower dependencies abstraction to

- describe a space of context, parameters, their ranges, constraints, etc. and result objectives
- an "optimizer" service abstraction (e.g. `register()` and `suggest()`) so we can easily swap out different implementations methods of searching (e.g. random, BO, etc.)
- provide some helpers for automating optimization experiment runner loops and data collection

For these design requirements we intend to reuse as much from existing OSS libraries as possible and layer policies and optimizations specifically geared towards autotuning over top.

## Getting Started

The development environment for MlosCore uses `conda` to ease dependency management.

### Devcontainer

For a quick start, you can use the provided [VSCode devcontainer](https://code.visualstudio.com/docs/remote/containers) configuration.

Simply open the project in VSCode and follow the prompts to build and open the devcontainer and the conda environment and additional tools will be installed automatically inside the container.

### Manually

> See Also: [`conda` install instructions](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
>
> Note: to support Windows we rely on some pre-compiled packages from `conda-forge` channels, which increases the `conda` solver time during environment create/update.
>
> To work around this the (currently) experimental `libmamba` solver can be used.
>
> See <https://github.com/conda-incubator/conda-libmamba-solver#getting-started> for more details.

0. Create the `mlos_core` Conda environment.

     ```sh
    conda env create -f conda-envs/mlos_core.yml
    ```

   or

    ```sh
    # This will also ensure the environment is update to date using "conda env update -f conda-envs/mlos_core.yml"
    make conda-env
    ```

    > Note: the latter expects a *nix environment.

1. Initialize the shell environment.

    ```sh
    conda activate mlos_core
    ```

2. Run the [`BayesianOptimization.ipynb`](./Notebooks/BayesianOptimization.ipynb) notebook.

## Distributing

1. Build the *wheel* file(s)

    ```sh
    make dist
    ```

2. Install it (e.g. after copying it somewhere else).

    ```sh
    # this will install just the optimizer component with emukit support:
    pip install dist/mlos_core-0.0.4-py3-none-any.whl[emukit]

    # this will install just the optimizer component with skopt support:
    pip install dist/mlos_core-0.0.4-py3-none-any.whl[skopt]
    ```

    ```sh
    # this will install both the optimizer and the experiment runner:
    pip install dist/mlos_bench-0.0.4-py3-none-any.whl
    ```

## See Also

- API and Examples Documentation: <https://aka.ms/mlos-core/docs>
- Source Code Repository: <https://aka.ms/mlos-core/src>
- Initial Design Discussion Doc: [MlosCoreApiDesign.docx](https://microsoft.sharepoint.com/:w:/t/CISLGSL/ESAS3G9q4P5Hoult9uqTfB4B3xh2v6yUfp3YNgIvoyR_IA?e=B6klWZ)
