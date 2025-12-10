# Quick Reference Guide - AI Anomaly Detection System

## 🚀 Common Operations

### Initial Setup (One-time)

```powershell
# 1. Login to Azure
az login

# 2. Set variables
$APP_NAME = "github-actions-flask-app"
$SUBSCRIPTION_ID = (az account show --query id -o tsv)
$TENANT_ID = (az account show --query tenantId -o tsv)

# 3. Create App Registration
az ad app create --display-name $APP_NAME
$APP_ID = (az ad app list --display-name $APP_NAME --query "[0].appId" -o tsv)

# 4. Create Service Principal
az ad sp create --id $APP_ID

# 5. Assign Contributor role
az role assignment create `
  --assignee $APP_ID `
  --role "Contributor" `
  --scope "/subscriptions/$SUBSCRIPTION_ID"

# 6. Create Terraform state storage
az group create --name terraform-state-rg --location westeurope

az storage account create `
  --name tfstatedevopsdelk `
  --resource-group terraform-state-rg `
  --location westeurope `
  --sku Standard_LRS

$ACCOUNT_KEY = (az storage account keys list `
  --resource-group terraform-state-rg `
  --account-name tfstatedevopsdelk `
  --query '[0].value' -o tsv)

az storage container create `
  --name tfstate `
  --account-name tfstatedevopsdelk `
  --account-key $ACCOUNT_KEY

# 7. Configure GitHub Secrets (manually in GitHub UI)
# Add these secrets to your repository:
# - AZURE_CLIENT_ID: $APP_ID
# - AZURE_TENANT_ID: $TENANT_ID
# - AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID
```

### Deploy Infrastructure

```powershell
# Via GitHub Actions (Recommended)
git add terraform/
git commit -m "Update infrastructure"
git push origin main

# Or locally
cd terraform
terraform init `
  -backend-config="resource_group_name=terraform-state-rg" `
  -backend-config="storage_account_name=tfstatedevopsdelk" `
  -backend-config="container_name=tfstate" `
  -backend-config="key=flask-app.terraform.tfstate"

terraform plan
terraform apply
```

### Train ML Model

```powershell
# Via GitHub Actions (Recommended)
gh workflow run train-ml-model.yml

# Or locally with Azure authentication
$env:AZURE_CLIENT_ID = "your-client-id"
$env:AZURE_TENANT_ID = "your-tenant-id"
$env:AZURE_SUBSCRIPTION_ID = "your-subscription-id"

python train_anomaly_detection.py
```

### Deploy Azure Function

```powershell
# Via GitHub Actions (Recommended)
gh workflow run deploy-function.yml

# Or locally
cd .
func azure functionapp publish <function-app-name>
```

### Run Full CI/CD Pipeline

```powershell
# Simply push to main branch
git add .
git commit -m "Deploy application"
git push origin main

# This will automatically:
# 1. Build and test the app
# 2. Deploy to Azure App Service
# 3. Run anomaly detection monitoring
```

## 🔍 Monitoring & Debugging

### Check Pipeline Metrics

```powershell
# View latest GitHub Actions run
gh run list --workflow=ci-cd.yml --limit 1

# View run details
gh run view <run-id>

# Download anomaly detection artifacts
gh run download <run-id> --name anomaly-detection-report
```

### View Azure Function Logs

```powershell
# Stream logs in real-time
az webapp log tail --name <function-app-name> --resource-group flask-app-rg

# Download recent logs
az webapp log download --name <function-app-name> --resource-group flask-app-rg
```

### Query Application Insights

```powershell
# Open Application Insights in browser
az portal appinsights show --name <workspace-name>-insights

# Query with Azure CLI (requires app insights extension)
az monitor app-insights query `
  --app <app-insights-id> `
  --analytics-query "traces | where message contains 'anomaly' | take 10"
```

### Check Azure ML Workspace

```powershell
# List registered models
az ml model list --workspace-name <workspace-name> --resource-group flask-app-rg

# View model details
az ml model show --name pipeline-anomaly-detector --workspace-name <workspace-name> --resource-group flask-app-rg
```

## 🛠️ Troubleshooting

### Anomaly Detection Not Running

```powershell
# 1. Check if Azure Function is deployed
az functionapp list --resource-group flask-app-rg --query "[].name"

# 2. Verify function is running
az functionapp show --name <function-app-name> --resource-group flask-app-rg --query state

# 3. Check function app settings
az functionapp config appsettings list --name <function-app-name> --resource-group flask-app-rg

# 4. Test function manually
curl -X POST "https://<function-app-name>.azurewebsites.net/api/detect_anomalies" `
  -H "Content-Type: application/json" `
  -d '{"data":[{"build_id":"test","duration":300,"failure_rate":0.0}]}'
```

### GitHub Actions Workflow Failing

```powershell
# 1. Check OIDC authentication
# Verify federated credentials in Azure Portal:
# Azure AD → App registrations → Your app → Certificates & secrets → Federated credentials

# 2. Verify GitHub secrets are set
gh secret list

# 3. Check workflow logs
gh run view <run-id> --log

# 4. Validate Terraform state access
az storage blob list `
  --account-name tfstatedevopsdelk `
  --container-name tfstate `
  --auth-mode key
```

### ML Model Not Found

```powershell
# 1. Check if model is registered
az ml model list --workspace-name <workspace-name> --resource-group flask-app-rg

# 2. Retrain and register model
python train_anomaly_detection.py

# 3. Verify model in Azure ML Studio
# Browse to: https://ml.azure.com → Models
```

### Alerts Not Sending

```powershell
# 1. Check Azure Function environment variables
az functionapp config appsettings show `
  --name <function-app-name> `
  --resource-group flask-app-rg `
  --settings TEAMS_WEBHOOK_URL SENDGRID_API_KEY

# 2. Test Teams webhook
Invoke-WebRequest -Uri "YOUR_TEAMS_WEBHOOK_URL" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"text":"Test message"}'

# 3. Verify SendGrid API key
curl -X GET "https://api.sendgrid.com/v3/scopes" `
  -H "Authorization: Bearer YOUR_SENDGRID_KEY"
```

## 📊 Useful Queries

### GitHub Issues for Anomalies

```powershell
# List all anomaly issues
gh issue list --label anomaly

# View specific anomaly issue
gh issue view <issue-number>

# Close resolved anomaly
gh issue close <issue-number> --comment "Issue resolved"
```

### Terraform State Management

```powershell
# View current state
cd terraform
terraform show

# List all resources
terraform state list

# View specific resource
terraform state show azurerm_machine_learning_workspace.ml_workspace

# Refresh state from Azure
terraform refresh
```

### Azure Resource Management

```powershell
# List all resources in resource group
az resource list --resource-group flask-app-rg --output table

# Check App Service status
az webapp show --name <app-service-name> --resource-group flask-app-rg --query state

# View App Service URL
az webapp show --name <app-service-name> --resource-group flask-app-rg --query defaultHostName

# Restart services
az webapp restart --name <app-service-name> --resource-group flask-app-rg
az functionapp restart --name <function-app-name> --resource-group flask-app-rg
```

## 🎯 Testing

### Test Flask Application Locally

```powershell
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest --cov=. --cov-report=term

# Start application
python app.py

# Test health endpoint
curl http://localhost:8000/health
```

### Test Azure Function Locally

```powershell
# Install Azure Functions Core Tools
# Download from: https://docs.microsoft.com/azure/azure-functions/functions-run-local

# Install dependencies
pip install -r azure_function_requirements.txt

# Start function locally
func start

# Test HTTP trigger
Invoke-WebRequest -Uri "http://localhost:7071/api/detect_anomalies" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"data":[{"build_id":"test","duration":300,"failure_rate":0.0}]}'
```

### Test ML Model Locally

```powershell
# Install dependencies
pip install -r requirements.txt
pip install scikit-learn pandas joblib azure-ai-ml

# Run training script
python train_anomaly_detection.py

# Test scoring
python -c "
import joblib
import numpy as np

# Load model (if saved locally)
model = joblib.load('model/pipeline_anomaly_detector.pkl')

# Test prediction
X = np.array([[300, 0.0]])  # duration, failure_rate
prediction = model.predict(X)
print(f'Prediction: {prediction[0]}')  # -1 = anomaly, 1 = normal
"
```

## 🔧 Configuration Updates

### Update Terraform Variables

```powershell
# Edit terraform.tfvars
notepad terraform\terraform.tfvars

# Apply changes
cd terraform
terraform plan
terraform apply
```

### Update Azure Function Settings

```powershell
# Set single setting
az functionapp config appsettings set `
  --name <function-app-name> `
  --resource-group flask-app-rg `
  --settings "TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/..."

# Set multiple settings
az functionapp config appsettings set `
  --name <function-app-name> `
  --resource-group flask-app-rg `
  --settings `
    "ML_MODEL_NAME=pipeline-anomaly-detector" `
    "TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/..." `
    "SENDGRID_API_KEY=SG.xxx"
```

### Update GitHub Secrets

```powershell
# Update secret
gh secret set AZURE_CLIENT_ID --body "new-client-id"

# List all secrets
gh secret list

# Delete secret
gh secret delete SECRET_NAME
```

## 📈 Performance Optimization

### Optimize Terraform Apply Time

```powershell
# Use targeted apply for specific resources
terraform apply -target=azurerm_app_service.app_service

# Use parallelism flag
terraform apply -parallelism=10
```

### Optimize Azure Function Performance

```powershell
# Scale up function app
az functionapp plan update `
  --name <plan-name> `
  --resource-group flask-app-rg `
  --sku P1V2

# Enable always on
az functionapp config set `
  --name <function-app-name> `
  --resource-group flask-app-rg `
  --always-on true
```

### Optimize ML Model Training

```python
# In train_anomaly_detection.py
# Adjust these parameters for faster training:

model = IsolationForest(
    n_estimators=50,      # Reduce from 100
    max_samples=256,      # Limit samples per tree
    n_jobs=-1,           # Use all CPU cores
    random_state=42
)
```

## 🔄 Maintenance Tasks

### Monthly Checklist

```powershell
# 1. Review anomaly detection accuracy
gh issue list --label anomaly --state closed --limit 20

# 2. Retrain ML model with new data
gh workflow run train-ml-model.yml

# 3. Update dependencies
pip list --outdated
pip install --upgrade -r requirements.txt

# 4. Review Azure costs
az consumption usage list --start-date 2024-01-01 --end-date 2024-01-31

# 5. Clean up old artifacts
gh run list --status completed --limit 100 | ForEach-Object { gh run delete $_.id }
```

### Backup & Recovery

```powershell
# Backup Terraform state
az storage blob download `
  --account-name tfstatedevopsdelk `
  --container-name tfstate `
  --name flask-app.terraform.tfstate `
  --file backup-terraform.tfstate

# Backup ML models (download from Azure ML)
az ml model download `
  --name pipeline-anomaly-detector `
  --version 1 `
  --workspace-name <workspace-name> `
  --resource-group flask-app-rg

# Restore from backup
az storage blob upload `
  --account-name tfstatedevopsdelk `
  --container-name tfstate `
  --name flask-app.terraform.tfstate `
  --file backup-terraform.tfstate `
  --overwrite
```

## 📚 Additional Resources

- [Main README](./README.md) - Project overview
- [AI Overview](./AI_ANOMALY_DETECTION_OVERVIEW.md) - Detailed system architecture
- [ML Guide](./ML_ANOMALY_DETECTION_GUIDE.md) - ML model documentation
- [Function Guide](./AZURE_FUNCTION_README.md) - Azure Function details

## 💡 Pro Tips

1. **Use aliases for common commands:**
   ```powershell
   function tf { terraform $args }
   function tfp { terraform plan }
   function tfa { terraform apply -auto-approve }
   ```

2. **Set up auto-completion:**
   ```powershell
   # Add to PowerShell profile
   Register-ArgumentCompleter -Native -CommandName gh -ScriptBlock {
       param($wordToComplete, $commandAst, $cursorPosition)
       gh completion -s powershell | Out-String | Invoke-Expression
   }
   ```

3. **Monitor costs:**
   ```powershell
   # Check daily costs
   az consumption usage list `
     --start-date (Get-Date).AddDays(-1).ToString("yyyy-MM-dd") `
     --end-date (Get-Date).ToString("yyyy-MM-dd")
   ```

4. **Quick health check:**
   ```powershell
   # Create a health check script
   function Check-SystemHealth {
       Write-Host "🏥 System Health Check" -ForegroundColor Cyan
       
       Write-Host "`n1. App Service Status:" -ForegroundColor Yellow
       az webapp show --name <app-service-name> --resource-group flask-app-rg --query state
       
       Write-Host "`n2. Function App Status:" -ForegroundColor Yellow
       az functionapp show --name <function-app-name> --resource-group flask-app-rg --query state
       
       Write-Host "`n3. Latest Anomaly Detection:" -ForegroundColor Yellow
       gh issue list --label anomaly --limit 1
       
       Write-Host "`n4. Recent Pipeline Runs:" -ForegroundColor Yellow
       gh run list --workflow=ci-cd.yml --limit 3
   }
   ```

---

**Need help?** Open an issue on GitHub or check the detailed documentation files.
