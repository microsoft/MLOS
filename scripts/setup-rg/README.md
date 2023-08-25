# Resource Group Setup

These scripts are helpers for setting up a new resource group (RG) in Azure as the *control plane* for MLOS.
The *control plane RG* is a container for the *persistent* resources of MLOS (results/metrics storage, scheduler VM, notebook interface, etc.).

## Quickstart

1. Starting in this current directory, ensure that we are logged in to Azure CLI.

    ```sh
    az login
    ```

2. Make a copy of the ARM parameters file.

    ```sh
    cp rg-template.example.parameters.json rg-template.parameters.json
    ```

3. Modify the ARM parameters in the newly created file as needed, especially the `PLACEHOLDER` values.

4. Execute the main script with CLI args as follows:

    ```shell
    ./setup-rg.ps1 `
        -armParameters $armParams `
        -servicePrincipalName $servicePrincipalName `
        -resourceGroupName $resourceGroupName `
        -certName $certName
    ```

    where `$armParams` can be `rg-template.parameters.json` from before. However, it also follows the same usage as `--parameters` in [az deployment group create](https://learn.microsoft.com/en-us/cli/azure/deployment/group?view=azure-cli-latest#az-deployment-group-create-examples).

## Workflow

The high-level flow for what this script automates is as follows:

1. Assign `Contributor` access to the Service Principal (SP) for write access over resources.
    Ideally, experiment resources are placed in their own RG.
    When that isn't possible, they can also be placed in the control plane RG, in which case the SP can optionally be given access to the control plane RG as well.

2. Provision control plane resources into the RG.
    This includes:
    - Networking (public IP, security group, vnet, subnet, network interface)
    - Key Vault for storing the SP credentials.
    - Storage (storage account, file share, DB)
    - VM for running the `mlos_bench` scheduler.

3. Assign `Key Vault Administrator` access to the current user.
    This allows the current user to retrieve secrets / certificates from the VM once it is set up.
    Ensure to log in as the same user in the VM.

4. If not existing yet, generate a certificate with `certName` in the key vault.

5. If not associated yet, upload the certificate from before to the SP.
