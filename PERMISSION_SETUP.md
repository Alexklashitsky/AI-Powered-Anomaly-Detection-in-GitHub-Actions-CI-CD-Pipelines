# 🔐 Permission Issues & Post-Deployment Setup

## Overview
This guide addresses authorization errors during Terraform deployment and provides manual steps for role assignments.

---

## 🚨 Issues Encountered

### 1. Role Assignment Authorization Errors

**Errors:**
```
Error: The client does not have authorization to perform action 
'Microsoft.Authorization/roleAssignments/write'
```

**Root Cause:**
The service principal running Terraform needs the **User Access Administrator** or **Owner** role to create role assignments. The **Contributor** role is insufficient for managing permissions.

### 2. Key Vault Access Policy Already Exists

**Error:**
```
Error: A resource with the ID already exists - to be managed via Terraform 
this resource needs to be imported into the State.
```

**Root Cause:**
Azure ML Workspace automatically creates Key Vault access policies during creation, causing conflicts with Terraform-managed policies.

---

## ✅ Solutions Implemented

### Terraform Changes
All role assignments and access policies have been **commented out** in Terraform to allow successful deployment without elevated permissions.

**Files Modified:**
- `terraform/function_resources.tf` - Commented out Function App role assignments
- `terraform/ml_resources.tf` - Commented out ML Workspace role assignments and Key Vault access policy

---

## 🔧 Post-Deployment Manual Setup

After Terraform successfully creates the infrastructure, follow these steps to configure permissions:

### Step 1: Deploy Infrastructure
```powershell
cd terraform
terraform init
terraform plan
terraform apply
```

### Step 2: Configure Function App Permissions

```powershell
# Get Function App principal ID
$FUNCTION_PRINCIPAL_ID = (az functionapp identity show `
  --name <your-function-app-name> `
  --resource-group flask-app-rg `
  --query principalId -o tsv)

# Get ML Workspace ID
$ML_WORKSPACE_ID = (az ml workspace show `
  --name ml-workspace-anomaly-detection `
  --resource-group flask-app-rg `
  --query id -o tsv)

# Grant Reader access to ML Workspace
az role assignment create `
  --assignee $FUNCTION_PRINCIPAL_ID `
  --role "Reader" `
  --scope $ML_WORKSPACE_ID

# Grant Monitoring Reader access
az role assignment create `
  --assignee $FUNCTION_PRINCIPAL_ID `
  --role "Monitoring Reader" `
  --resource-group flask-app-rg
```

### Step 3: Configure ML Workspace Permissions

```powershell
# Get ML Workspace principal ID
$ML_PRINCIPAL_ID = (az ml workspace show `
  --name ml-workspace-anomaly-detection `
  --resource-group flask-app-rg `
  --query identity.principalId -o tsv)

# Get Storage Account ID
$STORAGE_ID = (az storage account show `
  --name mlstorageanomalydet `
  --resource-group flask-app-rg `
  --query id -o tsv)

# Get ACR ID
$ACR_ID = (az acr show `
  --name <your-acr-name> `
  --resource-group flask-app-rg `
  --query id -o tsv)

# Grant Storage Blob Data Contributor
az role assignment create `
  --assignee $ML_PRINCIPAL_ID `
  --role "Storage Blob Data Contributor" `
  --scope $STORAGE_ID

# Grant ACR Pull access
az role assignment create `
  --assignee $ML_PRINCIPAL_ID `
  --role "AcrPull" `
  --scope $ACR_ID
```

### Step 4: Verify Permissions

```powershell
# Check Function App role assignments
az role assignment list --assignee $FUNCTION_PRINCIPAL_ID --output table

# Check ML Workspace role assignments
az role assignment list --assignee $ML_PRINCIPAL_ID --output table

# Check Key Vault access policies
az keyvault show --name mlkv-anomaly-det --resource-group flask-app-rg --query properties.accessPolicies
```

---

## 🎯 Alternative: Grant Service Principal Elevated Permissions

If you want Terraform to manage all permissions automatically, grant your service principal additional roles:

### Option 1: User Access Administrator (Recommended)

```powershell
# Get your service principal ID
$SP_ID = "<your-service-principal-object-id>"
$SUBSCRIPTION_ID = (az account show --query id -o tsv)

# Grant User Access Administrator role
az role assignment create `
  --assignee $SP_ID `
  --role "User Access Administrator" `
  --scope "/subscriptions/$SUBSCRIPTION_ID"
```

Then **uncomment** the role assignment blocks in:
- `terraform/function_resources.tf`
- `terraform/ml_resources.tf`

And run:
```powershell
terraform apply
```

### Option 2: Owner Role (Full Control)

```powershell
# Grant Owner role (be cautious with this!)
az role assignment create `
  --assignee $SP_ID `
  --role "Owner" `
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/flask-app-rg"
```

---

## 📋 Complete Post-Deployment Script

Save this as `post-deployment-setup.ps1`:

```powershell
#!/usr/bin/env pwsh
# Post-Deployment Permission Setup Script

Write-Host "🚀 Starting post-deployment setup..." -ForegroundColor Cyan

# Configuration
$RESOURCE_GROUP = "flask-app-rg"
$FUNCTION_APP_NAME = Read-Host "Enter Function App name"
$ML_WORKSPACE_NAME = "ml-workspace-anomaly-detection"
$STORAGE_ACCOUNT_NAME = "mlstorageanomalydet"
$ACR_NAME = Read-Host "Enter ACR name"

# Get principal IDs
Write-Host "`n📝 Getting managed identity principal IDs..." -ForegroundColor Yellow

$FUNCTION_PRINCIPAL_ID = (az functionapp identity show `
  --name $FUNCTION_APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --query principalId -o tsv)

$ML_PRINCIPAL_ID = (az ml workspace show `
  --name $ML_WORKSPACE_NAME `
  --resource-group $RESOURCE_GROUP `
  --query identity.principalId -o tsv)

Write-Host "Function App Principal ID: $FUNCTION_PRINCIPAL_ID" -ForegroundColor Green
Write-Host "ML Workspace Principal ID: $ML_PRINCIPAL_ID" -ForegroundColor Green

# Get resource IDs
Write-Host "`n📝 Getting resource IDs..." -ForegroundColor Yellow

$ML_WORKSPACE_ID = (az ml workspace show `
  --name $ML_WORKSPACE_NAME `
  --resource-group $RESOURCE_GROUP `
  --query id -o tsv)

$STORAGE_ID = (az storage account show `
  --name $STORAGE_ACCOUNT_NAME `
  --resource-group $RESOURCE_GROUP `
  --query id -o tsv)

$ACR_ID = (az acr show `
  --name $ACR_NAME `
  --resource-group $RESOURCE_GROUP `
  --query id -o tsv)

# Assign Function App permissions
Write-Host "`n🔐 Assigning Function App permissions..." -ForegroundColor Yellow

az role assignment create `
  --assignee $FUNCTION_PRINCIPAL_ID `
  --role "Reader" `
  --scope $ML_WORKSPACE_ID

az role assignment create `
  --assignee $FUNCTION_PRINCIPAL_ID `
  --role "Monitoring Reader" `
  --resource-group $RESOURCE_GROUP

# Assign ML Workspace permissions
Write-Host "`n🔐 Assigning ML Workspace permissions..." -ForegroundColor Yellow

az role assignment create `
  --assignee $ML_PRINCIPAL_ID `
  --role "Storage Blob Data Contributor" `
  --scope $STORAGE_ID

az role assignment create `
  --assignee $ML_PRINCIPAL_ID `
  --role "AcrPull" `
  --scope $ACR_ID

# Verify
Write-Host "`n✅ Verifying role assignments..." -ForegroundColor Yellow

Write-Host "`nFunction App Roles:" -ForegroundColor Cyan
az role assignment list --assignee $FUNCTION_PRINCIPAL_ID --output table

Write-Host "`nML Workspace Roles:" -ForegroundColor Cyan
az role assignment list --assignee $ML_PRINCIPAL_ID --output table

Write-Host "`n✨ Post-deployment setup complete!" -ForegroundColor Green
Write-Host "You can now proceed with application deployment." -ForegroundColor Green
```

**Run the script:**
```powershell
.\post-deployment-setup.ps1
```

---

## 🔍 Verification Checklist

After running post-deployment setup:

- [ ] Function App has "Reader" role on ML Workspace
- [ ] Function App has "Monitoring Reader" role on Resource Group
- [ ] ML Workspace has "Storage Blob Data Contributor" on Storage Account
- [ ] ML Workspace has "AcrPull" on Container Registry
- [ ] Key Vault access policies are configured (auto-created by ML Workspace)
- [ ] No authorization errors in Azure Portal

---

## 🆘 Troubleshooting

### Issue: "Principal not found" Error

**Solution:**
Wait 60-90 seconds after resource creation before assigning roles. Managed identities need time to propagate.

```powershell
Write-Host "Waiting for managed identity propagation..."
Start-Sleep -Seconds 90
# Then run role assignments
```

### Issue: Role Assignment Already Exists

**Solution:**
This is normal if roles were auto-created. Verify with:
```powershell
az role assignment list --assignee $PRINCIPAL_ID --output table
```

### Issue: Still Getting Permission Errors

**Solution:**
1. Verify you're logged in with correct account:
   ```powershell
   az account show
   ```

2. Check if you have permission to create role assignments:
   ```powershell
   az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --output table
   ```

3. If not, ask your Azure administrator to run the post-deployment script

---

## 📊 Permission Matrix

| Resource | Principal | Role | Required For |
|----------|-----------|------|--------------|
| ML Workspace | Function App | Reader | Access ML models |
| Resource Group | Function App | Monitoring Reader | Query metrics |
| Storage Account | ML Workspace | Storage Blob Data Contributor | Store models/data |
| Container Registry | ML Workspace | AcrPull | Pull container images |
| Key Vault | ML Workspace | Get/List/Set/Delete | Store secrets (auto-created) |

---

## 🎯 Success Criteria

After completing post-deployment setup:

✅ Terraform apply completes without errors  
✅ All role assignments are in place  
✅ Function App can query ML Workspace  
✅ ML Workspace can access storage and ACR  
✅ Key Vault policies configured  
✅ Ready for application deployment  

---

## 📚 Related Documentation

- **[TERRAFORM_FIXES.md](./TERRAFORM_FIXES.md)** - Infrastructure fixes
- **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** - Deployment guide
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Common commands

---

**Status**: ✅ Solution Implemented  
**Last Updated**: December 2025
