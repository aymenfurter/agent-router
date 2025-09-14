targetScope = 'resourceGroup'

// Required parameters for azd
@minLength(1)
@maxLength(64)
@description('Name of the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

// Resource naming configuration  
var resourceToken = uniqueString(subscription().id, resourceGroup().id, location, environmentName)

// User-Assigned Managed Identity (required by azd rules)
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: 'azid${resourceToken}'
  location: location
  tags: {
    'azd-env-name': environmentName
  }
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2025-02-01' = {
  name: 'azlog${resourceToken}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'azai${resourceToken}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Key Vault for secrets management
resource keyVault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: 'azkv${resourceToken}'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enabledForTemplateDeployment: true
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
  }
}

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2024-11-01' = {
  name: 'azasp${resourceToken}'
  location: location
  sku: {
    name: 'S1'
    tier: 'Standard'
    capacity: 1
  }
  properties: {
    reserved: true // Linux
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2024-11-01' = {
  name: 'azapp${resourceToken}'
  location: location
  tags: {
    'azd-service-name': 'agent-router'
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    keyVaultReferenceIdentity: managedIdentity.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      pythonVersion: '3.12'
      appSettings: [
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.properties.ConnectionString
        }
        {
          name: 'AZURE_KEY_VAULT_ENDPOINT'
          value: keyVault.properties.vaultUri
        }
        {
          name: 'AZURE_CLIENT_ID'
          value: managedIdentity.properties.clientId
        }
        {
          name: 'FLASK_HOST'
          value: '0.0.0.0'
        }
        {
          name: 'FLASK_PORT'
          value: '8000'
        }
        {
          name: 'FLASK_DEBUG'
          value: 'false'
        }
        // Placeholder environment variables - these should be configured after deployment
        {
          name: 'AZURE_AI_AGENT_ENDPOINT'
          value: ''
        }
        {
          name: 'MODEL_DEPLOYMENT_NAME'
          value: ''
        }
        {
          name: 'PURVIEW_ENDPOINT'
          value: ''
        }
        {
          name: 'BING_CONNECTION_ID'
          value: ''
        }
        {
          name: 'FABRIC_CONNECTION_ID'
          value: ''
        }
        {
          name: 'ENABLE_FABRIC_AGENT'
          value: 'false'
        }
        {
          name: 'DATABRICKS_INSTANCE'
          value: ''
        }
        {
          name: 'GENIE_SPACE_ID'
          value: ''
        }
        {
          name: 'DATABRICKS_AUTH_TOKEN'
          value: ''
        }
      ]
    }
  }
}

// Site extension for App Service deployment (required by azd rules)
resource siteExtension 'Microsoft.Web/sites/siteextensions@2024-11-01' = {
  name: 'python311x64'
  parent: webApp
}

// RBAC role assignments
var keyVaultSecretsUserRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')

resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, managedIdentity.id, keyVaultSecretsUserRole)
  properties: {
    roleDefinitionId: keyVaultSecretsUserRole
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Optional: Grant the principal ID Key Vault Secrets User access if provided
resource principalKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: keyVault
  name: guid(keyVault.id, principalId, keyVaultSecretsUserRole)
  properties: {
    roleDefinitionId: keyVaultSecretsUserRole
    principalId: principalId
    principalType: 'User'
  }
}

// Outputs required by azd
output RESOURCE_GROUP_ID string = resourceGroup().id
output WEB_APP_NAME string = webApp.name
output WEB_APP_URL string = 'https://${webApp.properties.defaultHostName}'
output AZURE_KEY_VAULT_ENDPOINT string = keyVault.properties.vaultUri
output MANAGED_IDENTITY_CLIENT_ID string = managedIdentity.properties.clientId
output APPLICATION_INSIGHTS_CONNECTION_STRING string = applicationInsights.properties.ConnectionString