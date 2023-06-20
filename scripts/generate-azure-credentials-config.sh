#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

az account get-access-token \
    --query "{tenant:tenant,subscription:subscription}" |
    jq ".storageAccountKey = `
        az storage account keys list \
            --resource-group os-autotune \
            --account-name osatsharedstorage \
            --query '[0].value'`"
