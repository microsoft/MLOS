#Requires -Version 7
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

param(
    # Main control plane ARM template params
    [Parameter(Mandatory=$True)]
    [string] $controlPlaneArmParamsFile,
    # Results DB ARM template params
    [Parameter(Mandatory=$False)]
    [string] $resultsDbArmParamsFile,
    [Parameter(Mandatory=$True)]
    [string] $resourceGroupName,
    # Managed Identity params
    [Parameter(Mandatory=$True, ParameterSetName="ByMI")]
    [string] $managedIdentityName,
    # Service Principal params
    [Parameter(Mandatory=$True, ParameterSetName="BySP")]
    [string] $servicePrincipalName,
    [Parameter(Mandatory=$True, ParameterSetName="BySP")]
    [string] $certName,
    [Parameter(Mandatory=$False, ParameterSetName="BySP")]
    [int] $certExpirationYears = 1
)

# Provision resources into the resource group with ARM template
Write-Output "Provisioning control plane resources..."
$deploymentResults = az deployment group create `
    --resource-group $resourceGroupName `
    --template-file .\rg-template.json `
    --parameters $controlPlaneArmParamsFile `
    --output json `
    | ConvertFrom-JSON

if (!$?) {
    Write-Error "Error in provisioning control plane resources!"
    return
}

$vmName = $deploymentResults.properties.outputs.vmName.value
$storageAccountNames = $deploymentResults.properties.outputs.storageAccountNames.value

# Conditional provisioning of results DB
if ($resultsDbArmParamsFile) {
    Write-Output "Provisioning results DB..."
    $dbDeploymentResults = az deployment group create `
        --resource-group $resourceGroupName `
        --template-file ./results-db/mysql-template.json `
        --parameters $resultsDbArmParamsFile `
        --output json `
        | ConvertFrom-JSON

    if (!$?) {
        Write-Error "Error in provisioning results DB!"
    }
    else {
        $dbName = $dbDeploymentResults.properties.outputs.dbName.value
        $vmIpAddress = $deploymentResults.properties.outputs.vmIpAddress.value

        # VM IP access for results DB
        az mysql flexible-server firewall-rule create `
            --resource-group $resourceGroupName `
            --name $dbName `
            --rule-name "AllowVM-$vmName" `
            --start-ip-address $vmIpAddress `
            --end-ip-address $vmIpAddress
    }
}

$currentUserAlias = az account show --query "user.name" --output tsv
$resourceGroupId = az group show --name $resourceGroupName --query "id" --output tsv

# Assign 'Key Vault Administrator' access to current user
$kvName = $deploymentResults.properties.outputs.kvName.value
$kvId = az keyvault show --name $kvName --resource-group $resourceGroupName --query "id" --output tsv
az role assignment create `
    --assignee $currentUserAlias `
    --role "Key Vault Administrator" `
    --scope $kvId

# Check if cert of same name exists in keyvault already
$certThumbprint = az keyvault certificate show `
    --name $certName `
    --vault-name $kvName `
    --query "x509ThumbprintHex" --output tsv `
    2>$null `
    || "NOCERT"

switch ($PSCmdlet.ParameterSetName) {
    "BySP" {
        if ($certThumbprint -eq "NOCERT") {
            # The cert does not exist yet.
            # Create the service principal if doesn't exist, storing the cert in the keyvault
            # If it does exist, this also patches the current service principal with the role
            az ad sp create-for-rbac `
                --name $servicePrincipalName `
                --role "Contributor" `
                --scopes $resourceGroupId `
                --create-cert `
                --cert $certName `
                --keyvault $kvName `
                --years $certExpirationYears
        } else {
            # The cert already exists in the keyvault.

            # Ensure the SP exists with correct roles, without creating a cert.
            az ad sp create-for-rbac `
                --name $servicePrincipalName `
                --role "Contributor" `
                --scopes $resourceGroupId `

            # SP's certs, which are stored in the registered application instead
            $servicePrincipalAppId = az ad sp list `
                --display-name $servicePrincipalName `
                --query "[?servicePrincipalType == 'Application'].appId" `
                --output tsv
            $spCertThumbprints = az ad app credential list `
                --id $servicePrincipalAppId `
                --cert `
                --query "[].customKeyIdentifier" `
                --output tsv

            if ($spCertThumbprints.Contains($certThumbprint)) {
                Write-Output "Keyvault contains the certificate '$certName' that is linked to the service principal '$servicePrincipalName' already."
            } else {
                Write-Warning "Keyvault already contains a certificate called '$certName', but is not linked with the service principal '$servicePrincipalName'! Skipping cert handling"
            }
        }
        break
    }
    "ByMI" {
        # Ensure the user managed identity is created
        $miId = az identity create `
            --name $managedIdentityName `
            --resource-group $resourceGroupName `
            --query "principalId" --output tsv

        Write-Output "Using managed identity $managedIdentityName with principalId $miId"

        # Assign the identity to the VM
        Write-Output "Assigning the identity to the VM..."
        az vm identity assign --name $vmName --resource-group $resourceGroupName --identities $managedIdentityName

        # Assign the identity access to the storage accounts
        foreach ($storageAccountName in $storageAccountNames) {
            Write-Output "Assigning the identity the role for $storageAccountName..."
            $storageAccountResourceId = az storage account show --name $storageAccountName --resource-group $resourceGroupName --query "id" --output tsv
            az role assignment create `
                --assignee $miId `
                --role "Storage File Data Privileged Contributor" `
                --scope $storageAccountResourceId
        }
        break
    }
}

