# AI-Powered Anomaly Detection in GitHub Actions CI/CD Pipelines

A complete DevOps solution featuring a Flask web application with automated CI/CD pipelines using GitHub Actions, Terraform for infrastructure as code, and Azure cloud services.

## 🏗️ Architecture

### Infrastructure Components (Managed by Terraform)
- **Azure Resource Group**: Container for all resources
- **Azure Container Registry (ACR)**: Private Docker registry for container images
- **Azure App Service Plan**: Linux-based, Basic tier (B1)
- **Azure App Service**: Container-based web app hosting
- **Azure Storage Account**: Terraform remote state storage

### CI/CD Pipelines
1. **Terraform Infrastructure Deployment** (`.github/workflows/terraform-deploy.yml`)
   - Provisions and manages Azure infrastructure
   - Runs on changes to `terraform/**` files
   - Outputs infrastructure details for app deployment

2. **Flask Application CI/CD** (`.github/workflows/ci-cd.yml`)
   - Builds and tests the Flask application
   - Builds Docker images and pushes to ACR
   - Deploys to Azure App Service
   - Depends on Terraform workflow completion

## 🚀 Features

- **Infrastructure as Code**: Complete Azure infrastructure defined in Terraform
- **OIDC Authentication**: Secure, keyless authentication to Azure (no client secrets!)
- **Automated Testing**: Pytest with coverage reporting
- **Docker Containerization**: Consistent deployment across environments
- **Health Checks**: Built-in health monitoring endpoints
- **Managed Identity**: App Service uses managed identity to pull from ACR
- **Workflow Dependencies**: App deployment waits for infrastructure provisioning

## 📋 Prerequisites

1. **Azure Account** with an active subscription
2. **Azure CLI** installed locally (for initial setup)
3. **Terraform** >= 1.0 installed locally (optional, for local testing)
4. **GitHub Repository** with Actions enabled

## 🔧 Setup Instructions

### Step 1: Create Azure App Registration for OIDC

```bash
# Login to Azure
az login

# Create App Registration
az ad app create --display-name "github-actions-flask-app"

# Get the Application (client) ID
APP_ID=$(az ad app list --display-name "github-actions-flask-app" --query "[0].appId" -o tsv)
echo "Application ID: $APP_ID"

# Create Service Principal
az ad sp create --id $APP_ID

# Get Tenant and Subscription IDs
TENANT_ID=$(az account show --query tenantId -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo "Tenant ID: $TENANT_ID"
echo "Subscription ID: $SUBSCRIPTION_ID"
```

### Step 2: Configure Federated Credentials

In Azure Portal:
1. Go to **Azure Active Directory** → **App registrations**
2. Find your app registration
3. Go to **Certificates & secrets** → **Federated credentials**
4. Click **Add credential**
5. Select **GitHub Actions deploying Azure resources**
6. Fill in:
   - **Organization**: Your GitHub username/organization
   - **Repository**: `AI-Powered-Anomaly-Detection-in-GitHub-Actions-CI-CD-Pipelines`
   - **Entity type**: `Branch`
   - **Based on selection**: `main`
   - **Name**: `github-actions-main`
7. Click **Add**

### Step 3: Assign Azure Permissions

```bash
# Assign Contributor role to the service principal
az role assignment create \
  --assignee $APP_ID \
  --role "Contributor" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

# Optional: If you want to use Managed Identity for ACR pull (instead of admin credentials)
# Assign User Access Administrator role (required for role assignments in Terraform)
az role assignment create \
  --assignee $APP_ID \
  --role "User Access Administrator" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"
```

**Note**: The Contributor role is sufficient for basic deployment. User Access Administrator is only needed if you want to enable the managed identity role assignment in `resources.tf`.

### Step 4: Create Terraform State Storage

```bash
# Create resource group for Terraform state
az group create --name terraform-state-rg --location westeurope

# Create storage account (name must be globally unique, lowercase, alphanumeric)
az storage account create \
  --name tfstatedevopsdelk \
  --resource-group terraform-state-rg \
  --location westeurope \
  --sku Standard_LRS \
  --encryption-services blob

# Get storage account key
ACCOUNT_KEY=$(az storage account keys list \
  --resource-group terraform-state-rg \
  --account-name tfstatedevopsdelk \
  --query '[0].value' -o tsv)

# Create blob container
az storage container create \
  --name tfstate \
  --account-name tfstatedevopsdelk \
  --account-key $ACCOUNT_KEY
```

### Step 5: Configure GitHub Secrets

In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions** and add:

- `AZURE_CLIENT_ID`: The Application (client) ID from Step 1
- `AZURE_TENANT_ID`: The Tenant ID from Step 1
- `AZURE_SUBSCRIPTION_ID`: The Subscription ID from Step 1

### Step 6: Update Terraform Variables

Edit `terraform/terraform.tfvars` to use globally unique names:

```hcl
# IMPORTANT: Change these to globally unique values
acr_name         = "yourcompanyacr123"      # Lowercase alphanumeric only, globally unique
app_service_name = "yourcompany-flask-001"  # Globally unique across all Azure

# Other settings
resource_group_name    = "flask-app-rg"
location              = "westeurope"
app_service_plan_name = "flask-app-plan"
```

**Note**: 
- Authentication (subscription_id, client_id, tenant_id) is handled via OIDC environment variables in GitHub Actions. No client secret is needed!
- ACR names must be 5-50 characters, lowercase letters and numbers only
- App Service names must be globally unique and can contain letters, numbers, and hyphens

## 📁 Project Structure

```
.
├── .github/
│   └── workflows/
│       ├── terraform-deploy.yml    # Infrastructure deployment
│       └── ci-cd.yml               # Application CI/CD
├── terraform/
│   ├── main.tf                     # Provider and backend config
│   ├── resources.tf                # Infrastructure resources
│   ├── variables.tf                # Input variables
│   ├── outputs.tf                  # Output values
│   └── terraform.tfvars.example    # Example variables
├── app.py                          # Flask application
├── requirements.txt                # Python dependencies
├── test_app.py                     # Pytest tests
├── Dockerfile                      # Container image definition
└── README.md                       # This file
```

## 🔄 Workflow Execution Order

1. **Push to `main` with Terraform changes:**
   ```
   Terraform Workflow → Provisions Infrastructure → Outputs ACR & App Service details
                                                    ↓
   CI/CD Workflow → Build & Test → Push to ACR → Deploy to App Service
   ```

2. **Push to `main` with only app code changes:**
   ```
   CI/CD Workflow → Build & Test → Push to ACR → Deploy to existing App Service
   ```

## 🧪 Local Development

### Run Flask App Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Access at http://localhost:8000
```

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage
pytest --cov=. --cov-report=term
```

### Build Docker Image Locally

```bash
docker build -t flask-app:latest .
docker run -p 8000:8000 flask-app:latest
```

### Test Terraform Locally

```bash
cd terraform

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Plan changes
terraform plan

# Apply (with confirmation)
terraform apply
```

## 📊 Monitoring & Health Checks

The application includes a health check endpoint:

```bash
curl https://your-app-service.azurewebsites.net/health
```

Response:
```json
{
  "status": "healthy"
}
```

## 🔒 Security Best Practices

✅ **OIDC Authentication**: No long-lived secrets in GitHub
✅ **Managed Identity**: App Service uses managed identity to pull from ACR
✅ **HTTPS Only**: All App Service traffic is HTTPS
✅ **Private ACR**: Container registry is private with RBAC
✅ **Terraform State**: Remote state in encrypted Azure Storage
✅ **Sensitive Outputs**: Sensitive Terraform outputs are marked as such

## 🛠️ Troubleshooting

### OIDC Authentication Fails

- Verify federated credentials are configured correctly in Azure
- Check that the subject identifier matches: `repo:ORG/REPO:ref:refs/heads/main`
- Ensure the service principal has Contributor role

### ACR Login Fails

- Verify ACR was created successfully by Terraform
- Check that admin access is enabled on ACR
- Ensure the App Service managed identity has AcrPull role

### Role Assignment Permission Error

If you see: `does not have authorization to perform action 'Microsoft.Authorization/roleAssignments/write'`

**Solution 1** (Recommended for quick start):
- The role assignment is already commented out in `resources.tf`
- App Service uses admin credentials instead (already configured)
- This works fine for development and testing

**Solution 2** (For production with managed identity):
```bash
# Grant User Access Administrator role
az role assignment create \
  --assignee $APP_ID \
  --role "User Access Administrator" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

# Then uncomment the azurerm_role_assignment block in resources.tf
```

### Terraform State Issues

- Verify storage account `tfstatedevopsdelk` exists
- Check that the `tfstate` container exists
- Ensure service principal has access to the storage account

## 📝 License

This project is provided as-is for educational and demonstration purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
