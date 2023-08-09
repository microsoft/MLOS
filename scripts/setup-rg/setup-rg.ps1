
param(
    # ARM template params
    [Parameter(Mandatory=$True)]
    [string] $armParameters,
    # Other params
    [Parameter(Mandatory=$True)]
    [string] $servicePrincipalName,
    [Parameter(Mandatory=$True)]
    [string] $resourceGroupName,
    [Parameter(Mandatory=$True)]
    [string] $certName
)

$currentUserAlias = az account show --query user.name --output tsv

$servicePrincipalId = az ad sp list `
    --display-name $servicePrincipalName `
    --query '[].id' `
    --output tsv

# Assign 'Contributor' access to Service Principal
az role assignment create `
    --assignee $servicePrincipalId `
    --role "Contributor" `
    --resource-group $resourceGroupName

# Provision resources into the resource group with ARM template
$deploymentResults = az deployment group create `
    --resource-group $resourceGroupName `
    --template-file .\rg-template.json `
    --parameters $armParameters
    | ConvertFrom-JSON

if (!$?) {
    Write-Error "Error in provisioning resources!"
    return
}

# Assign 'Key Vault Administrator' access to current user
$kvName = $deploymentResults.properties.outputs.kvName.value
$kvId = az keyvault show --name $kvName --query "id" --output tsv
az role assignment create `
    --assignee $currentUserAlias `
    --role "Key Vault Administrator" `
    --scope $kvId

# Generate certificate if doesnt exist
$certThumprint = az keyvault certificate show `
    --name $certName `
    --vault-name $kvName `
    --query "x509ThumbprintHex" --output tsv
if (!$?) {
    Write-Output "Generating certificate in the key vault..."
    az keyvault certificate get-default-policy | Out-File -Encoding utf8 defaultCertPolicy.json
    az keyvault certificate create `
        --vault-name $kvName `
        --name $certName `
        --policy `@defaultCertPolicy.json
    $certThumprint = az keyvault certificate show `
        --name $certName `
        --vault-name $kvName `
        --query "x509ThumbprintHex" --output tsv
} else {
    Write-Output "Certificate exists in the key vault already."
}

# Upload certificate to service principal if doesnt exist
$spCertThumbprints = az ad sp credential list `
    --id $servicePrincipalId `
    --cert `
    --query "[].customKeyIdentifier" --output tsv
if (!$spCertThumbprints.Contains($certThumprint)) {
    # Download the public portion of the certificate from key vault
    Write-Output "Downloading certificate from key vault..."
    az keyvault certificate download `
        --vault-name $kvName `
        --name $certName `
        --file "$certName.pem"

    # Upload the certificate to the service principal
    Write-Output "Uploading certificate to service principal..."
    az ad sp credential reset `
        --id $servicePrincipalId `
        --cert "$certName.pem" `
        --append
} else {
    Write-Output "Certificate uploaded to the Service Principal already."
}
