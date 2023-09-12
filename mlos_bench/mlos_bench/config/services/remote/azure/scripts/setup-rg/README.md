# Resource Group Setup

These scripts are helpers for setting up a new resource group (RG) in Azure as the *control plane* for MLOS.
The *control plane RG* is a container for the *persistent* resources of MLOS (results/metrics storage, scheduler VM, notebook interface, etc.).

## Quickstart

1. Starting in this current directory, ensure that we are logged in to Azure CLI.

    ```sh
    az login
    ```

2. Make a copy of the control plane ARM parameters file.

    ```sh
    cp rg-template.example.parameters.json rg-template.parameters.json
    ```

3. (Optional) Make a copy of the results DB parameters file, if planning to provision a results DB (suggested).

    ```sh
    cp results-db/mysql-template.parameters.example.json results-db/mysql-template.parameters.json
    ```

4. Modify the ARM parameters in the newly created files as needed, especially the `PLACEHOLDER` values.

5. Execute the main script with CLI args as follows:

    ```shell
    # With Powershell, recommended to use Powershell 7
    ./setup-rg.ps1 `
        -controlPlaneArmParamsFile $controlPlaneArmParamsFile `
        -resultsDbArmParamsFile $resultsDbArmParamsFile  # If provisioning results DB, otherwise omit `
        -servicePrincipalName $servicePrincipalName `
        -resourceGroupName $resourceGroupName `
        -certName $certName
    ```

    ```sh
    # With bash
    # If provisioning results DB include '--resultsDbArmsParamsFile', otherwise omit
    ./setup-rg.sh \
        --controlPlaneArmParamsFile $controlPlaneArmParamsFile \
        --resultsDbArmParamsFile $resultsDbArmParamsFile  \
        --servicePrincipalName $servicePrincipalName \
        --resourceGroupName $resourceGroupName \
        --certName $certName
    ```

    where `$*ArmParamsFile` can be the corresponding `*.parameters.json` and from before. However, it also follows the same usage as `--parameters` in [az deployment group create](https://learn.microsoft.com/en-us/cli/azure/deployment/group?view=azure-cli-latest#az-deployment-group-create-examples).

## Workflow

The high-level flow for what this script automates is as follows:

1. Assign `Contributor` access to the Service Principal (SP) for write access over resources.
    Ideally, experiment resources are placed in their own RG.
    When that isn't possible, they can also be placed in the control plane RG, in which case the SP can optionally be given access to the control plane RG as well.

2. Provision control plane resources into the RG.
    This includes:
    - Control VM for running the `mlos_bench` scheduler.
    - Control VM's networking (public IP, security group, vnet, subnet, network interface)
    - Key Vault for storing the SP credentials.
    - Storage (storage account, file share)

3. The results DB is then optionally provisioned, adding appropriate firewall rules.

4. Assign `Key Vault Administrator` access to the current user.
    This allows the current user to retrieve secrets / certificates from the VM once it is set up.
    Ensure to log in as the same user in the VM.

5. Check if the desired certificate name already exists in the key vault.

6. If certificate does not exist yet, create or update the Service Principal (SP) with `Contributor` access for write over resources.
    Ideally, experiment resources are placed in their own RG.
    When that isn't possible, they can also be placed in the control plane RG, in which case the SP can optionally be given access to the control plane RG as well.

7. Otherwise, create or update the SP just with similar access as before. Now also verify that the existing certificate in the key vault matches one linked to the SP already, via thumbprint.
