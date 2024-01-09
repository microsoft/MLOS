# mlos-bench

This [directory](./) contains the code for the `mlos-bench` experiment runner package.

It makes use of the [`mlos-core`](../mlos_core/) package for its optimizer.

It's available for `pip install` via the pypi repository at [mlos-bench](https://pypi.org/project/mlos-bench/).

## Table of Contents

<!-- markdownlint-disable MD007 -->

<!-- TOC -->

- [mlos-bench](#mlos-bench)
    - [Table of Contents](#table-of-contents)
    - [Description](#description)
    - [Features](#features)
    - [Quickstart](#quickstart)
        - [Install and activate the conda environment](#install-and-activate-the-conda-environment)
        - [Make sure that you have Azure CLI tool installed and working](#make-sure-that-you-have-azure-cli-tool-installed-and-working)
        - [Generate access tokens to interact with Azure resources](#generate-access-tokens-to-interact-with-azure-resources)
        - [Create a JSON config with DB credentials Optional](#create-a-json-config-with-db-credentials-optional)
        - [Create a top-level configuration file for your MLOS setup](#create-a-top-level-configuration-file-for-your-mlos-setup)
        - [Create another config file for the parameters specific to your experiment](#create-another-config-file-for-the-parameters-specific-to-your-experiment)
            - [Importance of the Experiment ID config](#importance-of-the-experiment-id-config)
        - [Run the benchmark](#run-the-benchmark)
    - [Optimization](#optimization)
        - [Resuming interrupted experiments](#resuming-interrupted-experiments)

<!-- /TOC -->

<!-- markdownlint-enable MD007 -->

## Description

`mlos-bench` is an end-to-end benchmarking service that can be independently launched for experimentation but is also integrated with `mlos-core` as its optimizer for OS tuning.
 Given a user-provided VM configuration, `mlos-bench` provisions a configured environment and remotely executes benchmarks on the cloud.
 Experiment results (benchmark results & telemetry) are stored as input to the `mlos-core` optimization engine loop to evaluate proposed configuration parameters and produce new results.

## Features

With a [JSON5](https://spec.json5.org) [config file](./mlos_bench/config/) and command line parameters as input, `mlos-bench` streamlines workload performance measurement by automating the following benchmarking steps:

1. Set up & clean up benchmark and application configuration
    - **Ease of use:** Mlos-bench abstracts away controls for managing VMs in Azure, e.g., setup, teardown, stop, deprovision, and reboot. Get visibility into VM status through Azure Portal, ensuring that a VM is provisioned & running before issuing commands to it.
    - **Versatility:** Mlos-bench provides a common interface to control a collection of environments (application, OS, VM), regardless of where or which cloud they come from. This allows changes to easily propagate to all environment layers when a new set of kernel parameters are applied.
    - **Efficiency:** In adapting an environment to new parameters, mlos-bench optimizes for low re-configuration costs during optimization. For example, considering that not all OS kernel parameter adjustments require a full reboot, as some can be changed during run-time.
2. Run benchmarks in the provisioned environment & standardize results for the optimizer
    - Through Azure File Share, access docker scripts to run benchmarks & store results as input for optimization. For example, execute Redis benchmark uploaded to the file share, running a benchmark docker container with specified parameters. The file share is mounted to VMs via remote execution, instead of ARM templates.
    - **Configurable:** Specify a python script in the initial config to post-process & standardize benchmark results. An example post-processing script for Redis benchmarks is included.
    - **Local & remote benchmark execution:** Benchmarks can be run both locally in Hyper-V and remotely on Azure. Local execution allows better accuracy, while Azure runs are required to estimate the benchmark noise and understand the VM behavior when using cloud storage.
    - **Cloud agnostic:** Mlos-bench can remotely execute benchmarks on other clouds, outside of Azure - e.g., controls for EC2 instances and ability to provision environments on AWS with Terraform.
    - **Persistence:** Storage integration is available to persist experiment parameters and track results for re-use, either for analysis during & after trials, or warm-starting future experiments.

## Quickstart

To get started, we can adapt an example configuration to test out running `mlos-bench`.
For these instructions, we will be using Azure for our resources.

### 1. Install and activate the conda environment

From here onwards we assume we are in the project root directory.
Ensure you have a conda environment (`mlos`) set up for executing `mlos_bench`.
Create and activate the environment with:

```sh
conda env create -f conda-envs/mlos.yml
conda activate mlos
```

> Note: if you are running inside the devcontainer, this should be done automatically.

### 2. Make sure that you have Azure CLI tool installed and working

> Installation instructions for `az` (Azure CLI) [can be found here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
>
> Note: `az` comes preinstalled inside the devcontainer.

If necessary, login to Azure and set your default subscription:

```shell
# If using az cli for the first time, a login will be required:
az login
# Make sure to set your default subscription, RG, and Storage Account for these experiments.
# For instance:
az account set --subscription "My Subscription Name"
az config set defaults.group=MyRG --local
az config set storage.account=MyStorageAccount --local
az account set --subscription "..."
```

### 3. Generate access tokens to interact with Azure resources

A script at `./scripts/generate-azure-credentials-config` produces a JSON config snippet with necessary Azure credentials.

```shell
./scripts/generate-azure-credentials-config > ./global_config_azure.jsonc
```

This data produced in the `global_config_azure.jsonc` file is in the format that can be used by our framework.

```jsonc
{
  "subscription": "some-guid",
  "tenant": "some-other-guid",
  "storageAccountKey": "some-base-64-encoded-key",
}
```

> Note: On Linux, this script also requires `jq` to also be installed (comes preinstalled in the devcontainer).

### 4. Create a JSON config with DB credentials (Optional)

If you plan to store the information about experiments and benchmarks in a (remote) database like PostgreSQL or MySQL, create a JSON/JSONC file with the DB hostname and password.
See [`mysql.jsonc`](./mlos_bench/config/storage/mysql.jsonc) or [`postgresql.jsonc`](./mlos_bench/config/storage/postgresql.jsonc) configuration files for examples with a more complete list of DB parameters supported by underlying the [SqlAlchemy](https://www.sqlalchemy.org/library.html#reference) library.
Save your config in `./global_config_storage.jsonc` file.
It should look like this:

```jsonc
{
    "host": "mysql-db.mysql.database.azure.com",
    "password": "database_password"
}
```

Any parameter that is not specified in `./global_config_storage.json` will be taken from the corresponding DB's config file, e.g., [`postgresql.jsonc`](./mlos_bench/config/storage/postgresql.jsonc).

For database like SQLite or DuckDB, there is no need for an additional config file.
The data will be stored locally in a file, e.g., `./mlos_bench.duckdb`.
See [`sqlite.jsonc`](./mlos_bench/config/storage/sqlite.jsonc) or [`duckdb.jsonc`](./mlos_bench/config/storage/duckdb.jsonc) for more details.

> Note: if no storage is specified, a basic sqlite config will be used by default.

### 5. Create a top-level configuration file for your MLOS setup

We provide a few examples of such files in [`./mlos_bench/config/cli/`](./mlos_bench/config/cli).
For example, [`azure-redis-opt.jsonc`](./mlos_bench/config/cli/azure-redis-opt.jsonc) is a configuration for optimizing Redis VM on Azure and saving the results in a local SQLite database.
Likewise, [`azure-redis-bench.jsonc`](./mlos_bench/config/cli/azure-redis-bench.jsonc) is a setup to run a single Redis benchmark (and, again, save the results in SQLite).

CLI configs like those are meant to connect several MLOS components together, namely:

- Benchmarking environment (configured in [`environments/root/root-azure-redis.jsonc`](./mlos_bench/config/environments/root/root-azure-redis.jsonc));
- Optimization engine ([`optimizers/mlos_core_flaml.jsonc`](./mlos_bench/config/optimizers/mlos_core_flaml.jsonc));
- Storage for experimental data ([`storage/sqlite.jsonc`](./mlos_bench/config/storage/sqlite.jsonc));

They also refer to other configs, e.g.

- Reusable config snippets in `"config_path"` section, and
- Additional config files containing sensitive data like DB passwords and Azure credentials.

> Make sure that the files `./global_config_azure.jsonc` and `./global_config_storage.json` you created in the previous steps are included in the `"globals"` section of your CLI config.

For the purpose of this tutorial, we will assume that we reuse the existing [`azure-redis-bench.jsonc`](./mlos_bench/config/cli/azure-redis-bench.jsonc) and [`azure-redis-opt.jsonc`](./mlos_bench/config/cli/azure-redis-opt.jsonc) configurations without any changes.
In a more realistic scenario, however, you might need to change and/or create new config files for some parts of your benchmarking environment.
We'll give more details on that below.

### 5. Create another config file for the parameters specific to your experiment

Copy one of our examples, e.g., [`experiment_RedisBench.jsonc`](./mlos_bench/config/experiments/experiment_RedisBench.jsonc) and name it after your experiment, e.g. `experiment_MyBenchmark.jsonc`.

In that file, you can specify any parameters that occur in your other configs, namely in `"const_args"` section of the Environment configs, or in `"config"` sections of your Service, Storage, or Optimizer configurations.

> A general rule is that the parameters from the global configs like `./global_config_azure.jsonc` or `experiment_MyAppBench.jsonc` override the corresponding parameters in other configurations.
> That allows us to propagate the values of the parameters that are specific to the experiment into other components of the framework and keep the majority of the config files in our library immutable and reusable.

#### Importance of the Experiment ID config

An important part of this file is the value of `experiment_id` which controls the storage and retrieval of trial data.
Should the experiment be interrupted, the `experiment_id` will be used to resume the experiment from the last completed trial, reloading the optimizer with data from the previously completed trial data.

As such this value should be unique for each experiment.
Be sure to change it whenever *"incompatible"* changes are made to the experiment configuration or scripts.
Unfortunately, determining what constitutes and *"incompatible"* change for any given system is not always possible, so `mlos_bench` largely leaves this up to the user.

### 6. Run the benchmark

Now we can run our configuration with `mlos_bench`:

```shell
mlos_bench --config "./mlos_bench/mlos_bench/config/cli/azure-redis-bench.jsonc" --globals "experiment_MyBenchmark.jsonc"
```

This should run a single trial with the given tunable values (loaded from one or more files in the `"tunable_values"`), write the results to the log and keep the environment running (as directed by the `"teardown": false` configuration parameter in the CLI config).

Note that using the `--globals` command line option is the same as adding `experiment_MyBenchmark.jsonc` to the `"globals"` section of the CLI config.
Same applies to all other CLI parameters - e.g., you can change the log level by adding `--log_level INFO` to the command line.

Also, note that you don't have to provide full path to the `experiment_MyBenchmark.jsonc` file - the application will look for it in the paths specified in the `"config_path"` section of the CLI config.

## Optimization

Searching for an optimal set of tunable parameters is very similar to running a single benchmark.
All we have to do is specifying the [`Optimizer`](./mlos_bench/optimizers/) in the top-level configuration, like in our [`azure-redis-opt.jsonc`](./mlos_bench/config/cli/azure-redis-opt.jsonc) example.

```sh
mlos_bench --config "./mlos_bench/mlos_bench/config/cli/azure-redis-opt.jsonc" --globals "experiment_MyBenchmark.jsonc" --max_iterations 10
```

Note that again we use the command line option `--max_iterations` to override the default value from [`mlos_core_flaml.jsonc`](./mlos_bench/config/optimizers/mlos_core_flaml.jsonc).

We don't have to specify the `"tunable_values"` for the optimization: the optimizer will suggest new values on each iteration and the framework will feed this data into the benchmarking environment.

### Resuming interrupted experiments

Experiments sometimes get interrupted, e.g., due to errors in automation scripts or other failures in the system.

<!-- TODO: Document retry logic once implemented: #523 -->

To resume an interrupted experiment, simply run the same command as before.

As mentioned above in the [importance of the `experiment_id` config](#importance-of-the-experiment-id-config) section, the `experiment_id` is used to resume interrupted experiments, reloading prior trial data for that `experiment_id`.
