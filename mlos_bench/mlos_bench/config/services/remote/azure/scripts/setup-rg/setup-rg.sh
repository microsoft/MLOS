#!/bin/bash
##
## Copyright (c) Microsoft Corporation.
## Licensed under the MIT License.
##

set -eu

function usage() {
    local msg="${1:-}"
    if [ -n "$msg" ]; then
        echo "ERROR: $msg"
    fi
    script_name=$(basename "$0")
    cat <<USAGE
$script_name
    --resourceGroupName someRgName
    --controlPlaneArmParamsFile someControlPlaneArmParamsFile.json
    --resultsDbArmParamsFile someResultsDbArmParamsFile.json
    --servicePrincipalName someServicePrincipalName
    --certName someCertName
USAGE
    exit 1
}

# Argument parsing
while [[ "$#" -gt 0 ]]; do
case $1 in
    # Main control plane ARM template params
    --controlPlaneArmParamsFile)
        controlPlaneArmParamsFile="$2"
        shift 2
        ;;
    # Results DB ARM template params
    --resultsDbArmParamsFile)
        resultsDbArmParamsFile="$2"
        shift 2
        ;;
    # Other params
    --servicePrincipalName)
        servicePrincipalName="$2"
        shift 2
        ;;
    --resourceGroupName)
        resourceGroupName="$2"
        shift 2
        ;;
    --certName)
        certName="$2"
        shift 2
        ;;
    --certExpirationYears)
        certExpirationYears="$2"
        shift 2
        ;;
    *)
        usage "Unknown parameter passed $1"
        shift 1
        ;;
esac
done

if [ -z "${resourceGroupName:-}" ]; then
    usage "missing required resourceGroupName"
elif [ -z "${controlPlaneArmParamsFile:-}" ]; then
    usage "missing required controlPlaneArmParamsFile"
elif [ -z "${servicePrincipalName:-}" ]; then
    usage "missing required servicePrincipalName"
elif [ -z "${certName:-}" ]; then
    usage "missing required certName"
fi

for dependency in az jq; do
    if ! type $dependency 2>/dev/null; then
        echo "ERROR: missing dependency: $dependency" >&2
        exit 1
    fi
done

# Default values
resultsDbArmParamsFile=${resultsDbArmParamsFile:-""}
certExpirationYears=${certExpirationYears:-1}

# Resolve some file names.
controlPlaneArmParamsFile=$(readlink -f "$controlPlaneArmParamsFile")
if [ -n "$resultsDbArmParamsFile" ]; then
    resultsDbArmParamsFile=$(readlink -f "$resultsDbArmParamsFile")
fi
scriptdir=$(dirname "$(readlink -f "$0")")

# Provision resources into the resource group with ARM template
echo "Provisioning control plane resources..."
deploymentResults=$(az deployment group create \
    --resource-group "$resourceGroupName" \
    --template-file "$scriptdir/rg-template.json" \
    --parameters "$controlPlaneArmParamsFile" \
    --output json \
    )

if [[ $? -ne 0 ]]; then
    echo "Error in provisioning control plane resources!"
    exit 1
fi

# Conditional provisioning of results DB
if [[ "$resultsDbArmParamsFile" ]]; then
    echo "Provisioning results DB..."
    dbDeploymentResults=$(az deployment group create \
        --resource-group "$resourceGroupName" \
        --template-file "$scriptdir/results-db/mysql-template.json" \
        --parameters "$resultsDbArmParamsFile" \
        --output json \
        )

    if [[ $? -ne 0 ]]; then
        echo "Error in provisioning results DB!"
    else
        dbName=$(echo "$dbDeploymentResults" | jq -r ".properties.outputs.dbName.value")
        vmName=$(echo "$deploymentResults" | jq -r ".properties.outputs.vmName.value")
        vmIpAddress=$(echo "$deploymentResults" | jq -r ".properties.outputs.vmIpAddress.value")

        # VM IP access for results DB
        az mysql flexible-server firewall-rule create \
            --resource-group "$resourceGroupName" \
            --name "$dbName" \
            --rule-name "AllowVM-$vmName" \
            --start-ip-address "$vmIpAddress" \
            --end-ip-address "$vmIpAddress"
    fi
fi

currentUserAlias=$(az account show --query "user.name" --output tsv)
resourceGroupId=$(az group show --name "$resourceGroupName" --query "id" --output tsv)

# Assign 'Key Vault Administrator' access to current user
kvName=$(echo "$deploymentResults" | jq -r ".properties.outputs.kvName.value")
kvId=$(az keyvault show --name "$kvName" --resource-group "$resourceGroupName" --query "id" --output tsv)
az role assignment create \
    --assignee "$currentUserAlias" \
    --role "Key Vault Administrator" \
    --scope "$kvId"

# Check if cert of same name exists in keyvault already
certThumbprint=$(az keyvault certificate show \
    --name "$certName" \
    --vault-name "$kvName" \
    --query "x509ThumbprintHex" --output tsv \
    2> /dev/null \
    || echo "NOCERT" \
    )

if [[ $certThumbprint == "NOCERT" ]]; then
    # The cert does not exist yet.
    # Create the service principal if doesn't exist, storing the cert in the keyvault
    # If it does exist, this also patches the current service principal with the role
    az ad sp create-for-rbac \
        --name "$servicePrincipalName" \
        --role "Contributor" \
        --scopes "$resourceGroupId" \
        --create-cert \
        --cert "$certName" \
        --keyvault "$kvName" \
        --years "$certExpirationYears"
else
    # The cert already exists in the keyvault.

    # Ensure the SP exists with correct roles, without creating a cert.
    az ad sp create-for-rbac \
        --name "$servicePrincipalName" \
        --role "Contributor" \
        --scopes "$resourceGroupId"

    # SP's certs, which are stored in the registered application instead
    servicePrincipalAppId=$(az ad sp list \
        --display-name "$servicePrincipalName" \
        --query "[?servicePrincipalType == 'Application'].appId" \
        --output tsv \
        )
    spCertThumbprints=$(az ad app credential list \
        --id "$servicePrincipalAppId" \
        --cert \
        --query "[].customKeyIdentifier" \
        --output tsv \
        )
    if [[ $spCertThumbprints == *$certThumbprint* ]]; then
        echo "Keyvault contains the certificate '$certName' that is linked to the service principal '$servicePrincipalName' already."
    else
        echo "Keyvault already contains a certificate called '$certName', but is not linked with the service principal '$servicePrincipalName'! Skipping cert handling"
    fi
fi
