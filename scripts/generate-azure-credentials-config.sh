#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

set -eu
set -x

AZURE_DEFAULTS_GROUP=${AZURE_DEFAULTS_GROUP:-$(az config get --local defaults.group --query value -o tsv)}
AZURE_STORAGE_ACCOUNT_RG=${AZURE_STORAGE_ACCOUNT_RG:-$AZURE_DEFAULTS_GROUP}
AZURE_STORAGE_ACCOUNT_NAME=${AZURE_STORAGE_ACCOUNT_NAME:-$(az config get --local storage.account --query value -o tsv)}

az account get-access-token --query "{tenant:tenant,subscription:subscription}"
