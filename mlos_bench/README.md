# mlos-bench

This directory contains the code for the `mlos-bench` experiment runner package.

It makes use of the `mlos-core` package for its optimizer.

## Quickstart

To get started, we can adapt an example configuration to test out running `mlos-bench`.
For these instructions, we will be using Azure for our resources.

1. Ensure you have a SSH public key to authenticate with. If not available, you can generate one with `ssh-keygen`.

    ```sh
    # Generate SSH key if not available yet
    ssh-keygen -t rsa

    # Obtain your public key, starting with 'ssh-rsa ...'
    cat ~/.ssh/id_rsa.pub
    ```

2. Check that you can generate access tokens to interact with Azure resources.
Installation instructions for `az` (Azure CLI) [can be found here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).

    ```sh
    # If using for the az cli first time, a login will be required
    az login

    # The access token is under the `accessToken` key
    az account get-access-token
    ```

3. Make a copy of `services-example.json` so that we can adapt it with our own details.
For example,

    ```sh
    cp config/azure/services-example.json config/azure/services-mine.json
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
                "deploy_template_path": "./mlos_bench/config/azure/azuredeploy-ubuntu-vm.json",

                "subscription": "{{ ID of subscription to use }}",
                "resource_group": "{{ Name of resource group to use }}",
                "deployment_name": "{{ A deployment name to group all deployments under, e.g. redis-os-autotune-001 }}",
                "vmName": "{{ A VM name, e.g. redis-osat-vm }}",
            }
        }
    ]
    ```

5. Make a copy of `config-example.json` so that we can adapt it with our own details.
For example,

    ```sh
    cp config/config-example.json config/config-mine.json
    ```

6. Modify our new configuration file with desired resource names, denoted in `{{ ... }}` below.

    ```json
    {
        "name": "Azure VM Ubuntu Redis",
        "class": "mlos_bench.environment.CompositeEnv",

        "include_tunables": [
            "./mlos_bench/config/tunables.json"
        ],

        "include_services": [
            "{{ Path to your new service config, e.g. ./mlos_bench/config/azure/services-mine.json }}"
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
We can do so and pipe the output into log file `osat.log` as follows:

    ```sh
    python mlos_bench/mlos_bench/main.py --config mlos_bench/config/config-mine.json --accessToken "$(az account get-access-token --query accessToken --output tsv)" 2>&1 > ./osat.log
    ```

9. Check `osat.log` to verify we get output corresponding to the `ls -l /` command we remotely executed in the VM.
