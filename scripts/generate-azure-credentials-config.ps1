# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

az account get-access-token |
    ConvertFrom-Json |
    Add-Member "storageAccountKey" (
        az storage account keys list `
            --resource-group os-autotune `
            --account-name osatsharedstorage `
            --query "[0].value" `
            --output tsv `
        ) -PassThru |
    ConvertTo-Json
