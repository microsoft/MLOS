# mlos-bench

This directory contains the code for the `mlos-bench` experiment runner package.

It makes use of the `mlos-core` package for its optimizer.

## Description

`mlos-bench` is an end-to-end benchmarking service that can be independently launched for experimentation but is also integrated with `mlos-core` as its optimizer for OS tuning.
 Given a user-provided VM configuration, `mlos-bench` provisions a configured environment and remotely executes benchmarks on the cloud.
 Experiment results (benchmark results & telemetry) are stored as input to the `mlos-core` optimization engine loop to evaluate proposed configuration parameters and produce new results.

## Features

With a JSON config file and command line parameters as input, `mlos-bench` streamlines workload performance measurement by automating the following benchmarking steps:

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

1. Make sure that you have Azure CLI tool installed and working.

    > Installation instructions for `az` (Azure CLI) [can be found here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).

    If necessary, login to Azure and set your default subscription:

    ```powershell
    # If using az cli for the first time, a login will be required:
    az login
    # Make sure that GSL subscription is your default:
    az account set --subscription "..."
    ```

2. Generate access tokens to interact with Azure resources.

    A script at `./scripts/generate-azure-credentials-config.ps1` produces a JSON with Azure credentials.
    This data is in the format that can be used by our framework.

    ```powershell
    # If using for the az cli first time, a login will be required
    ./scripts/generate-azure-credentials-config.ps1 > ./global_config.json
    ```

    On Linux, use `./scripts/generate-azure-credentials-config.sh` (requires `az` and `jq` to be installed).

3. Copy the sample config tree from `mlos_bench/config` to another folder of your choice, e.g.,

    ```sh
    cp -R mlos_bench/config ./my-config
    ```

4. Modify the service configuration files at `my-config/azure/service-*.jsonc` with your Azure setup data.
E.g., in `my-config/azure/service-provision-vm.jsonc`, put your target resource group information, as well as desired VM name, denoted in `{{ ... }}` below.

    > All resource names have to either:
    >
    > - Not conflict with existing resource names in the resource group for a new deployment, or
    > - Correspond to existing resources from a previous successful deployment.
    >
    > Re-using resources from a partial, unsuccessful deployment will likely fail. It is recommended to delete resources from those partial deployments.

    ```json
    [
        {
            "class": "mlos_bench.environment.azure.AzureVMService",

            "config": {
                "deployTemplatePath": "azure/arm-templates/azuredeploy-ubuntu-vm.jsonc",

                "subscription": "{{ ID of subscription to use }}",
                "resourceGroup": "{{ Name of resource group to use }}",
                "deploymentName": "{{ A deployment name to group all deployments under, e.g. redis-os-autotune-001 }}",
                "vmName": "{{ A VM name, e.g. redis-osat-vm }}",
            }
        }
    ]
    ```

5. Update your copy of `my-config/env-azure-ubuntu-redis.jsonc` and other config files with the details of your setup.
Please refer to inline comments in the corresponding `.jsonc` files for more information.

6. From here onwards we assume we are in the project root directory.
Ensure you have a conda environment (`mlos_core`) set up for executing `mlos_bench`.
Create and activate the environment with:

    ```sh
    conda env create -f conda-envs/mlos_core.yml
    conda activate mlos_core
    ```

7. Run our configuration through `mlos_bench`.

    We can also copy the output into log file `os-autotune.log` as follows:

    ```sh
    ./mlos_bench/mlos_bench/run_bench.py \
        --config-path ./my-config ./mlos_bench/examples . \  # Locations of config files and scripts
        --environment env-azure-ubuntu-redis.jsonc \         # Root config (location relative to --config-path)
        --tunables tunable-values-example.json \             # Key/value pairs of tunable parameters. Uses --config-path
        --globals global_config.json \                       # Config generated at step 2. Uses --config-path
        --log ./os-autotune.log \                            # Log file (also prints to stdout)
        --log-level 10 \                                     # Log level = DEBUG
        --no-teardown \                                      # Do not shutdown/deprovision a VM
        --experimentName RedisBench \                        # Experiment name (can be in global_config.json)
        --experimentId 001                                   # Unique experiment ID (can come from the persistent storage service)
    ```

8. Check `os-autotune.log` to verify we get output corresponding to the command we remotely executed in the VM.

## Optimization

Searching for an optimal set of tunable parameters is very similar to running a single benchmark.
Here's an example of how to run the optimization script:

```sh
./mlos_bench/mlos_bench/run_opt.py \
    --config-path ./my-config ./mlos_bench/examples . \  # Locations of config files and scripts
    --environment env-azure-ubuntu-redis.jsonc \         # Root config (location relative to --config-path)
    --optimizer ./optimizers/mlos_core_opt.jsonc \       # Optimizer config (relative to --config-path)
    --globals global_config.json \                       # Config generated at step 2. Uses --config-path
    --log ./os-autotune.log \                            # Log file (also prints to stdout)
    --log-level 10 \                                     # Log level = DEBUG
    --no-teardown \                                      # Do not shutdown/deprovision a VM
    --experimentName RedisBench \                        # Experiment name (can be in global_config.json)
    --experimentId 001                                   # Unique experiment ID (can come from the persistent storage service)
```

The only difference between `run_bench.py` and `run_opt.py` scripts is that the latter has the `--optimizer` parameter instead of using a fixed set of tunables via `--tunables` option.
