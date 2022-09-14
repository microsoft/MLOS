#!/bin/bash
az account get-access-token |
    jq ".storageAccountKey = `
        az storage account keys list \
            --resource-group os-autotune \
            --account-name osatsharedstorage \
            --query '[0].value'`"
