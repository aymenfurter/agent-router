#!/bin/bash

# Azure deployment dry-run validation script for agent-router
set -e

echo "🔍 Azure Deployment Validation for Agent Router"
echo "================================================="

# Check if required tools are installed
echo "Checking required tools..."
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install Azure CLI."
    exit 1
fi

echo "✅ Azure CLI found: $(az version --query '"azure-cli"' -o tsv)"

# Check Azure login
echo "Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
ACCOUNT_NAME=$(az account show --query user.name -o tsv)
echo "✅ Logged into Azure as: $ACCOUNT_NAME"
echo "   Subscription: $SUBSCRIPTION_ID"

# Set deployment parameters
RESOURCE_GROUP_NAME="${AZURE_ENV_NAME:-agent-router-dev}"
LOCATION="${AZURE_LOCATION:-eastus}"
PRINCIPAL_ID="${AZURE_PRINCIPAL_ID:-$(az ad signed-in-user show --query id -o tsv)}"

echo ""
echo "Deployment Parameters:"
echo "  Resource Group: $RESOURCE_GROUP_NAME"
echo "  Location: $LOCATION"
echo "  Principal ID: $PRINCIPAL_ID"

# Validate Bicep template syntax
echo ""
echo "🔧 Validating Bicep template syntax..."
if az bicep build --file infra/main.bicep --stdout > /dev/null; then
    echo "✅ Bicep template syntax is valid"
else
    echo "❌ Bicep template has syntax errors"
    exit 1
fi

# Create resource group if it doesn't exist
echo ""
echo "📁 Checking/creating resource group..."
if az group show --name "$RESOURCE_GROUP_NAME" &> /dev/null; then
    echo "✅ Resource group '$RESOURCE_GROUP_NAME' already exists"
else
    echo "🆕 Creating resource group '$RESOURCE_GROUP_NAME'..."
    az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION" --tags "azd-env-name=$RESOURCE_GROUP_NAME"
    echo "✅ Resource group created"
fi

# Run deployment validation (what-if)
echo ""
echo "🎯 Running deployment validation (what-if analysis)..."
az deployment group what-if \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --template-file "infra/main.bicep" \
    --parameters "environmentName=$RESOURCE_GROUP_NAME" "location=$LOCATION" "principalId=$PRINCIPAL_ID"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment validation successful!"
    echo "   The Bicep template would deploy the following resources:"
    echo "   - User Assigned Managed Identity"
    echo "   - Log Analytics Workspace"
    echo "   - Application Insights"
    echo "   - Key Vault"
    echo "   - App Service Plan (S1 Standard)"
    echo "   - App Service (Python 3.12)"
    echo "   - RBAC Role Assignments"
    echo ""
    echo "🚀 Ready for deployment! Run the following to deploy:"
    echo "   az deployment group create \\"
    echo "     --resource-group '$RESOURCE_GROUP_NAME' \\"
    echo "     --template-file 'infra/main.bicep' \\"
    echo "     --parameters 'environmentName=$RESOURCE_GROUP_NAME' 'location=$LOCATION' 'principalId=$PRINCIPAL_ID'"
else
    echo "❌ Deployment validation failed!"
    exit 1
fi