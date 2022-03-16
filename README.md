# MlosCore

This repository contains a stripped down implementation of essentially just the core optimizer and config space description APIs from the original [MLOS](https://github.com/microsoft/MLOS).

It is intended to provide a simplified, easier to consume (e.g. via `pip`), with lower dependencies abstraction to

- describe a space of context, parameters, their ranges, constraints, etc. and result objectives
- an "optimizer" service abstraction (e.g. `register()` and `suggest()`) so we can easily swap out different implementations methods of searching (e.g. random, BO, etc.)

For both design requires intend to reuse as much OSS libraries as possible.

## Getting Started

0. Create the `mlos_core` Conda environment.

    ```sh
    conda env create -f conda-envs/mlos_core.yml
    ```

    or

    ```sh
    # This will also ensure the environment is update to date using "conda env update -f conda-envs/mlos_core.yml"
    make conda-env
    ```

1. Initialize the shell environment.

    ```sh
    conda activate mlos_core
    ```

2. Run the [`BayesianOptimization.ipynb`](./Notebooks/BayesianOptimization.ipynb) notebook.

## Distributing

1. Build the *wheel* file.

    ```sh
    make dist
    ```

2. Install it (e.g. after copying it somewhere else).

    ```sh
    # this will install it with emukit support:
    pip install dist/mlos_core-0.0.2-py3-none-any.whl[emukit]

    # this will install it with skopt support:
    pip install dist/mlos_core-0.0.2-py3-none-any.whl[skopt]
    ```

## See Also

[MlosCoreApiDesign.docx](https://microsoft.sharepoint.com/:w:/t/CISLGSL/ESAS3G9q4P5Hoult9uqTfB4B3xh2v6yUfp3YNgIvoyR_IA?e=B6klWZ)
