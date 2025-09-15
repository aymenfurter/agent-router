# Infrastructure Validation Pipeline

This GitHub Actions workflow automatically validates the Azure Bicep infrastructure templates whenever changes are made to the infrastructure code.

## When does it run?

The pipeline triggers on:
- **Push** to any branch when infrastructure files are modified
- **Pull requests** when infrastructure files are modified  
- **Manual trigger** via GitHub Actions UI

### Monitored files:
- `infra/**` - All Bicep templates and parameters
- `azure.yaml` - Azure Developer CLI configuration
- `validate-deployment.sh` - Deployment validation script
- `.github/workflows/infra-validation.yml` - This workflow file

## What does it validate?

### 1. Bicep Template Validation (`validate-bicep` job)
- **Syntax Check**: Compiles Bicep templates to ensure no syntax errors
- **Linting**: Runs Bicep linter to check for best practices and potential issues
- **Parameters Validation**: Verifies parameter files are valid JSON and contain expected fields
- **Azure.yaml Check**: Validates the Azure Developer CLI configuration file
- **Script Testing**: Tests the validation script for syntax errors

### 2. Security Scan (`security-scan` job)
- **Checkov**: Runs security and compliance scanning on Bicep templates
- **Security Best Practices**: Checks for:
  - HTTPS enforcement
  - Managed Identity usage
  - Key Vault integration
  - Application Insights monitoring

### 3. Integration Test (`integration-test` job)
- **Full Validation**: Runs complete deployment validation using Azure CLI what-if
- **Resource Cleanup**: Automatically cleans up any test resources created
- **Only runs on Pull Requests** with Azure credentials configured

## Configuration

### Required Repository Variables (for integration tests)
```
AZURE_CLIENT_ID - Service Principal Client ID
AZURE_TENANT_ID - Azure AD Tenant ID  
AZURE_SUBSCRIPTION_ID - Azure Subscription ID
```

### Optional Environment Variables
```
DRY_RUN=true - Skip Azure login and deployment validation (for local testing)
```

## How to use locally

You can run the validation script locally:

```bash
# Full validation (requires Azure login)
./validate-deployment.sh

# Dry-run mode (syntax and structure only)
export DRY_RUN=true
./validate-deployment.sh
```

## Pipeline Status

The workflow provides a comprehensive summary of all validation results in the GitHub Actions summary page, making it easy to see what passed or failed at a glance.

## Troubleshooting

### Common Issues:

1. **Bicep compilation fails**
   - Check template syntax in `infra/main.bicep`
   - Ensure all referenced resources and properties are valid

2. **Parameters file invalid**
   - Verify `infra/main.parameters.json` is valid JSON
   - Check that parameter names match those in the Bicep template

3. **Security scan failures**
   - Review Checkov output for security recommendations
   - Update templates to follow Azure security best practices

4. **Integration test fails**
   - Verify Azure credentials are correctly configured
   - Check that the subscription has necessary permissions
   - Review Azure quota limits for the target region

For more detailed troubleshooting, see the main [AZURE_DEPLOYMENT.md](../AZURE_DEPLOYMENT.md) documentation.