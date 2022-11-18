# mlos-bench

This directory contains the code for the `mlos-bench` experiment runner package.

It makes use of the `mlos-core` package for its optimizer.

# Description


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

3. Make a copy of `services.json` so that we can adapt it with our own details.

    For example,

    ```sh
    cp config/azure/services.json ./services-mine.json
    ```

4. Modify our new service configuration file with our target resource group information, as well as desired VM name, denoted in `{{ ... }}` below.

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
                "deployTemplatePath": "azure/azuredeploy-ubuntu-vm.json",

                "subscription": "{{ ID of subscription to use }}",
                "resourceGroup": "{{ Name of resource group to use }}",
                "deploymentName": "{{ A deployment name to group all deployments under, e.g. redis-os-autotune-001 }}",
                "vmName": "{{ A VM name, e.g. redis-osat-vm }}",
            }
        }
    ]
    ```

5. Make a copy of `env-azure-ubuntu-redis.json` so that we can adapt it with our own details.
For example,

    ```sh
    cp config/env-azure-ubuntu-redis.json ./config-mine.json
    ```

6. Modify our new configuration file with desired resource names, denoted in `{{ ... }}` below.

    ```json
    {
        "name": "Azure VM Ubuntu Redis",
        "class": "mlos_bench.environment.CompositeEnv",

        "include_tunables": [
            "tunables.json"
        ],

        "include_services": [
            "{{ Path to your new service config, e.g. ./services-mine.json }}"
        ],

        "config": {

            "children": [
                {
                    "name": "Deploy Ubuntu VM on Azure",
                    "class": "mlos_bench.environment.azure.VMEnv",

                    "config": {
                        ...,
                        "const_args": {
                            "vmName": "{{ The same VM name as above, e.g. redis-osat-vm }}",
                            "adminUsername": "{{ An admin username for the VM, e.g. osat-admin }}",
                            "authenticationType": "sshPublicKey",
                            "adminPasswordOrKey": "{{ The SSH public key from step 1. }}",

                            "virtualNetworkName": "{{ A vnet name, e.g. redis-osat-vnet }}",
                            "subnetName": "{{ A subnet name, e.g. redis-osat-subnet }}",
                            "networkSecurityGroupName": "{{ An NSG name, e.g. redis-osat-sg }}",

                            "ubuntuOSVersion": "18.04-LTS"
                        }
                    }
                },
                ...
            ]
        }
    }
    ```

7. From here onwards we assume we are in the project root directory.
Ensure you have a conda environment (`mlos_core`) set up for executing `mlos_bench`.
Create and activate the environment with:

    ```sh
    conda env create -f conda-envs/mlos_core.yml
    conda activate mlos_core
    ```

8. Run our configuration through `mlos_bench`.

    We can also copy the output into log file `os-autotune.log` as follows:

    ```sh
    ./mlos_bench/mlos_bench/run_opt.py --config ./config-mine.json --global ./global_config.json --log ./os-autotune.log
    ```

9. Check `os-autotune.log` to verify we get output corresponding to the command we remotely executed in the VM.
