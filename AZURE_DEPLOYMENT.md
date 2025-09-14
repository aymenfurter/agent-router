# Azure Deployment Guide for Agent Router

This document provides step-by-step instructions for deploying the Agent Router application to Azure using Infrastructure as Code (Bicep templates).

## Overview

The Agent Router is deployed to Azure App Service with the following supporting resources:
- **Azure App Service**: Hosts the Python Flask application with React UI
- **Azure App Service Plan**: Standard S1 tier for auto-scaling and staging slots
- **Azure Key Vault**: Secure storage for secrets and API keys
- **Application Insights**: Application monitoring and telemetry
- **Log Analytics Workspace**: Centralized logging
- **Managed Identity**: Secure authentication between Azure services

## Prerequisites

Before deploying, ensure you have:

1. **Azure CLI** installed and updated to version 2.77.0 or higher
   ```bash
   az --version
   az upgrade
   ```

2. **Azure subscription** with appropriate permissions:
   - Contributor role on the subscription or resource group
   - User Access Administrator role for RBAC assignments

3. **Azure login** configured:
   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```

4. **Required Azure services** provisioned (see Configuration section):
   - Azure AI Agent Service endpoint
   - Microsoft Purview instance
   - Bing Search API connection
   - (Optional) Azure OpenAI service
   - (Optional) Microsoft Fabric connection
   - (Optional) Databricks instance with Genie space

## Deployment Options

### Option 1: Manual Deployment with Azure CLI

#### Step 1: Validate Deployment

Run the validation script to check prerequisites and perform a dry-run:

```bash
# Set environment variables
export AZURE_ENV_NAME="agent-router-dev"
export AZURE_LOCATION="eastus" 
export AZURE_PRINCIPAL_ID="$(az ad signed-in-user show --query id -o tsv)"

# Run validation
./validate-deployment.sh
```

#### Step 2: Deploy Infrastructure

If validation passes, deploy the infrastructure:

```bash
az deployment group create \
  --resource-group "rg-$AZURE_ENV_NAME" \
  --template-file "infra/main.bicep" \
  --parameters "environmentName=$AZURE_ENV_NAME" "location=$AZURE_LOCATION" "principalId=$AZURE_PRINCIPAL_ID"
```

#### Step 3: Deploy Application Code

After infrastructure is created, deploy the application:

```bash
# Build the application
./build.sh

# Create deployment package
zip -r app.zip . -x "*.git*" "node_modules/*" "ui/node_modules/*" ".env*"

# Deploy to App Service
az webapp deployment source config-zip \
  --resource-group "rg-$AZURE_ENV_NAME" \
  --name "azapp$(az deployment group show --name main --resource-group "rg-$AZURE_ENV_NAME" --query properties.outputs.resourceToken.value -o tsv)" \
  --src app.zip
```

### Option 2: Azure Developer CLI (Recommended)

If Azure Developer CLI (azd) is available:

```bash
# Initialize the project
azd init

# Set environment variables
azd env set AZURE_ENV_NAME "agent-router-dev"
azd env set AZURE_LOCATION "eastus"

# Deploy infrastructure and application
azd up
```

## Configuration

After deployment, you need to configure the application settings with your Azure service endpoints:

### Required Configuration

Set the following environment variables in the Azure App Service:

```bash
# Get the web app name from deployment output
WEB_APP_NAME=$(az deployment group show --name main --resource-group "rg-$AZURE_ENV_NAME" --query properties.outputs.WEB_APP_NAME.value -o tsv)

# Configure required settings
az webapp config appsettings set --resource-group "rg-$AZURE_ENV_NAME" --name "$WEB_APP_NAME" --settings \
  AZURE_AI_AGENT_ENDPOINT="https://your-ai-agent-endpoint.services.ai.azure.com/api/projects/agents" \
  MODEL_DEPLOYMENT_NAME="your-model-deployment-name" \
  PURVIEW_ENDPOINT="https://your-purview-instance.purview.azure.com" \
  BING_CONNECTION_ID="/subscriptions/your-subscription-id/resourceGroups/your-rg/providers/Microsoft.CognitiveServices/accounts/your-account/projects/agents/connections/bingservice"
```

### Optional Configuration

For enhanced functionality, configure these optional settings:

```bash
# Microsoft Fabric integration
az webapp config appsettings set --resource-group "rg-$AZURE_ENV_NAME" --name "$WEB_APP_NAME" --settings \
  ENABLE_FABRIC_AGENT="true" \
  FABRIC_CONNECTION_ID="/subscriptions/your-subscription-id/resourceGroups/your-rg/providers/Microsoft.CognitiveServices/accounts/your-account/projects/agents/connections/fabric"

# Databricks Genie integration  
az webapp config appsettings set --resource-group "rg-$AZURE_ENV_NAME" --name "$WEB_APP_NAME" --settings \
  DATABRICKS_INSTANCE="your-databricks-instance.azuredatabricks.net" \
  GENIE_SPACE_ID="your-genie-space-id" \
  DATABRICKS_AUTH_TOKEN="your-databricks-auth-token"
```

## Post-Deployment Verification

### 1. Check Application Status

```bash
# Get application URL
APP_URL=$(az deployment group show --name main --resource-group "rg-$AZURE_ENV_NAME" --query properties.outputs.WEB_APP_URL.value -o tsv)
echo "Application URL: $APP_URL"

# Check health endpoint
curl "$APP_URL/health"
```

### 2. Monitor Application Logs

```bash
# Stream logs
az webapp log tail --resource-group "rg-$AZURE_ENV_NAME" --name "$WEB_APP_NAME"

# Download logs
az webapp log download --resource-group "rg-$AZURE_ENV_NAME" --name "$WEB_APP_NAME"
```

### 3. Verify Resources

```bash
# List all resources in the resource group
az resource list --resource-group "rg-$AZURE_ENV_NAME" --output table
```

## Security Considerations

The deployment includes several security best practices:

- **HTTPS Only**: All traffic is encrypted in transit
- **Managed Identity**: Service-to-service authentication without credentials
- **Key Vault**: Secure storage for secrets and API keys
- **RBAC**: Least-privilege access controls
- **Network Security**: Public network access controlled for Key Vault

## Troubleshooting

### Common Issues

1. **Deployment Fails with Permission Errors**
   - Ensure you have Contributor and User Access Administrator roles
   - Check if resource providers are registered: `az provider register --namespace Microsoft.Web`

2. **Application Fails to Start**
   - Check application logs: `az webapp log tail --resource-group "rg-$AZURE_ENV_NAME" --name "$WEB_APP_NAME"`
   - Verify all required environment variables are set
   - Ensure dependencies are installed: check `requirements.txt`

3. **Key Vault Access Denied**
   - Verify managed identity has Key Vault Secrets User role
   - Check Key Vault access policies or RBAC settings

### Support Resources

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)

## Cleanup

To remove all resources created by this deployment:

```bash
# Delete the resource group and all contained resources
az group delete --name "rg-$AZURE_ENV_NAME" --yes --no-wait
```

## Cost Optimization

The deployed configuration uses the following pricing tiers:
- **App Service Plan**: S1 Standard (~$73/month)
- **Application Insights**: Pay-per-use (first 5GB free)
- **Key Vault**: Standard (~$0.03 per 10,000 operations)
- **Log Analytics**: Pay-per-GB (first 5GB free)

For development environments, consider:
- Using B1 Basic App Service Plan (~$13/month)
- Setting retention policies for logs
- Using Azure Dev/Test pricing if eligible

## Next Steps

After successful deployment:

1. Configure monitoring alerts in Application Insights
2. Set up staging slots for blue-green deployments
3. Configure custom domains and SSL certificates
4. Set up CI/CD pipelines for automated deployments
5. Configure backup and disaster recovery procedures