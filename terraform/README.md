# Terraform Azure Infrastructure

This directory contains Terraform configuration for provisioning Azure infrastructure for the Flask CI/CD pipeline.

## Prerequisites

1. **Azure CLI** installed and authenticated
2. **Terraform** (>= 1.0) installed
3. **Existing Azure Container Registry (ACR)** - The configuration assumes ACR already exists
4. **Azure Service Principal** with appropriate permissions

## Resources Provisioned

- **Resource Group** in West Europe
- **App Service Plan** (Linux, Basic B1 tier)
- **Linux Web App** (Container-based, pulling from ACR)
- **Role Assignment** (AcrPull role for App Service managed identity)

## Configuration

### 1. Set up Backend Storage (One-time setup)

Before using this Terraform configuration, create the backend storage account:

```bash
# Create resource group for Terraform state
az group create --name terraform-state-rg --location westeurope

# Create storage account (name must be globally unique)
az storage account create \
  --name tfstatedevops \
  --resource-group terraform-state-rg \
  --location westeurope \
  --sku Standard_LRS \
  --encryption-services blob

# Create blob container
az storage container create \
  --name tfstate \
  --account-name tfstatedevops
```

### 2. Configure Variables

Create a `terraform.tfvars` file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and fill in your values:

```hcl
acr_name           = "delekacr"
acr_resource_group = "your-acr-rg"
app_service_name   = "your-unique-app-name"
# ... other variables
```

### 3. Set Authentication via Environment Variables

**Option 1: Using PowerShell**

```powershell
$env:TF_VAR_subscription_id = "your-subscription-id"
$env:TF_VAR_client_id = "your-client-id"
$env:TF_VAR_client_secret = "your-client-secret"
$env:TF_VAR_tenant_id = "your-tenant-id"
```

**Option 2: Using Bash**

```bash
export TF_VAR_subscription_id="your-subscription-id"
export TF_VAR_client_id="your-client-id"
export TF_VAR_client_secret="your-client-secret"
export TF_VAR_tenant_id="your-tenant-id"
```

**Option 3: Using Azure CLI authentication**

```bash
az login
# Terraform will use your Azure CLI credentials
```

## Usage

### Initialize Terraform

```bash
cd terraform
terraform init
```

### Plan Infrastructure

```bash
terraform plan
```

### Apply Infrastructure

```bash
terraform apply
```

### Destroy Infrastructure

```bash
terraform destroy
```

## Outputs

After applying, Terraform will output:

- `app_service_name` - Name of the deployed App Service
- `app_service_url` - URL to access your Flask app
- `acr_login_server` - ACR login server URL
- `resource_group_name` - Resource group name
- And more...

## Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `subscription_id` | Azure Subscription ID | - | Yes (via env) |
| `client_id` | Service Principal Client ID | - | Yes (via env) |
| `client_secret` | Service Principal Secret | - | Yes (via env) |
| `tenant_id` | Azure Tenant ID | - | Yes (via env) |
| `acr_name` | Existing ACR name | `delekacr` | Yes |
| `acr_resource_group` | ACR resource group | - | Yes |
| `resource_group_name` | New resource group name | `flask-app-rg` | No |
| `location` | Azure region | `westeurope` | No |
| `app_service_name` | App Service name (globally unique) | `flask-app-service` | No |

## Integration with GitHub Actions

Update your GitHub Actions workflow to use the Terraform-provisioned resources:

```yaml
- name: Deploy to Azure App Service
  run: |
    APP_NAME="<output from terraform>"
    RESOURCE_GROUP="<output from terraform>"
    # ... deployment commands
```

## Security Notes

- ⚠️ **Never commit `terraform.tfvars`** - It contains sensitive information
- ✅ Use environment variables for sensitive data
- ✅ The `.gitignore` file is configured to exclude sensitive files
- ✅ App Service uses managed identity for ACR authentication
- ✅ Backend state is stored securely in Azure Storage

## Troubleshooting

### Backend initialization fails

If backend initialization fails, ensure:
1. Storage account and container exist
2. You have access to the storage account
3. Storage account name is correct in `main.tf`

### ACR data source not found

Ensure:
1. ACR name and resource group are correct
2. ACR exists and you have read permissions
3. ACR is in the same subscription

### App Service deployment fails

Check:
1. App Service name is globally unique
2. Container image exists in ACR
3. ACR admin access is enabled (or use managed identity)

## Next Steps

After provisioning infrastructure:

1. Update GitHub Actions workflow with actual resource names
2. Configure custom domain (optional)
3. Set up Application Insights for monitoring
4. Configure auto-scaling rules
