# Resource Group Setup

These scripts are helpers for setting up a new resource group (RG) as the control plane for MLOS.

## Quickstart

1. Starting in this current directory, ensure that we are logged in to Azure CLI.

    ```sh
    az login
    ```

2. Make a copy of the ARM parameters file.

    ```sh
    cp rg-template.example.parameters.json rg-template.<your name>.parameters.json
    ```

3. Modify the ARM parameters in the newly created file as needed, especially the `PLACEHOLDER` values.

4. Execute the main script and follow prompts:

    ```sh
    ./setup-rg.ps1
    Supply values for the following parameters:
    armParameters: rg-template.<your name>.parameters.json
    servicePrincipalName: <name of service principal for generating tokens with>
    resourceGroupName: <target resource group for this control plane setup>
    certName: <desired key vault name of certificate for the service principal e.g. mlos-autotune-sp-cert>
    ```

## Manual

Parameters for script can also passed in manually (without prompt) as follows:

```sh
./setup-rg.ps1 `
    -armParameters $armParams `
    -servicePrincipalName $servicePrincipalName `
    -resourceGroupName $resourceGroupName `
    -certName $certName
```

where `$armParams` follows the same usage as `--parameters` in [az deployment group create](https://learn.microsoft.com/en-us/cli/azure/deployment/group?view=azure-cli-latest#az-deployment-group-create-examples).

## Workflow

The high-level flow for what this script automates is as follows:

1. Assign `Contributor` access to the Service Principal (SP) for write access over resources.
    For now we assume the experiment's resources are provisioned in the same RG as the control plane, so the access is granted to the same RG.

2. Provision control plane resources into the RG.
    This includes:
    - Networking (public IP, security group, vnet, subnet, network interface)
    - Key Vault
    - Storage (storage account, file share, MySQL Flex server)
    - VM

3. Assign `Key Vault Administrator` access to the current user.
    This allows the current user to retrieve secrets / certificates from the VM once it is set up.
    Ensure to log in as the same user in the VM.

4. If not existing yet, generate a certificate with `certName` in the key vault.

5. If not associated yet, upload the certificate from before to the SP.
