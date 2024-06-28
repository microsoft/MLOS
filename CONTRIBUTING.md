# Contributing to MLOS

This project welcomes contributions and suggestions.
Most contributions require you to agree to a Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us the rights to use your contribution.
For details, visit https://cla.opensource.microsoft.com. <!-- markdownlint-disable-line MD034 -->

When you submit a pull request, a CLA bot will automatically determine whether you need to provide a CLA and decorate the PR appropriately (e.g., status check, comment).
Simply follow the instructions provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Environment

### Getting Started

The development environment for MLOS uses `conda` to ease dependency management.

#### Devcontainer (preferred)

For a quick start, you can use the provided [VSCode devcontainer](https://code.visualstudio.com/docs/remote/containers) configuration.

Simply open the project in VSCode and follow the prompts to build and open the devcontainer and the conda environment and additional tools will be installed automatically inside the container.

#### Manually

> See Also: [`conda` install instructions](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
>
> Note: to support Windows we currently rely on some pre-compiled packages from `conda-forge` channels, which increases the `conda` solver time during environment create/update.
>
> To work around this the (currently) experimental `libmamba` solver can be used.
>
> See <https://github.com/conda-incubator/conda-libmamba-solver#getting-started> for more details.

1. Create the `mlos` Conda environment.

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

### Details

[`main`](https://github.com/microsoft/MLOS/tree/main) is considered the primary development branch.

We expect development to follow a typical "forking" style workflow:

1. Fork a copy of the [MLOS repo in Github](https://github.com/microsoft/MLOS).
1. Create a development (a.k.a. topic) branch off of `main` to work on changes.

    For instance:

    ```shell
    git checkout -b YourDevName/some-topic-description main
    ```

1. Ensure all of the lint checks and tests pass.

    The easiest way to do this is to run the `make` commands that are also used in the CI pipeline:

    ```shell
    # All at once.
    make all

    # Or individually (for easier debugging)
    make check
    make test
    make dist-test
    make doc-test
    ```

1. Submit changes for inclusion as a [Pull Request on Github](https://github.com/microsoft/MLOS/pulls).

    > Please try to keep PRs small whenver possible and don't include unnecessaary formatting changes.

1. PRs are associated with [Github Issues](https://github.com/microsoft/MLOS/issues) and need [MLOS-committers](https://github.com/orgs/microsoft/teams/MLOS-committers) to sign-off (in addition to other CI pipeline checks like tests and lint checks to pass).
1. Once approved, the PR can be completed using a squash merge in order to keep a nice linear history.

## Distributing

You can also locally build and install from wheels like so:

1. Build the *wheel* file(s)

    ```sh
    make dist
    ```

2. Install it.

    ```sh
    # this will install just the optimizer component with SMAC support:
    pip install "dist/tmp/mlos_core-latest-py3-none-any.whl[smac]"
    ```

    ```sh
    # this will install both the optimizer and the experiment runner:
    pip install "dist/mlos_bench-latest-py3-none-any.whl[azure]"
    ```

    > Note: exact versions may differ due to automatic versioning so the `-latest-` part is a symlink.
    > If distributing elsewhere, adjust for the current version number in the module's `dist` directory.

### See Also

- <https://docs.github.com/en/get-started/quickstart/fork-a-repo>
- <https://www.atlassian.com/git/tutorials/comparing-workflows/forking-workflow>
