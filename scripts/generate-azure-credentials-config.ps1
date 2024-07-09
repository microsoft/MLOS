# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

$AZURE_DEFAULTS_GROUP = $Env:AZURE_DEFAULTS_GROUP
if (-not $AZURE_DEFAULTS_GROUP) {
    $AZURE_DEFAULTS_GROUP = (az config get --local defaults.group --query value --output tsv)
}
if (-not $AZURE_DEFAULTS_GROUP) {
    Write-Error "Missing default az resource group config."
}

$AZURE_STORAGE_ACCOUNT_NAME = $Env:AZURE_STORAGE_ACCOUNT_NAME
if (-not $AZURE_STORAGE_ACCOUNT_NAME) {
    $AZURE_STORAGE_ACCOUNT_NAME = (az config get --local storage.account --query value --output tsv)
}
if (-not $AZURE_STORAGE_ACCOUNT_NAME) {
    Write-Error "Missing default az storage account name config."
}

az account get-access-token --query "{tenant:tenant,subscription:subscription}"
