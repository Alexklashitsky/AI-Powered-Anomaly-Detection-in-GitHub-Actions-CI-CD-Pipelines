# Testing & Validation Guide

Complete testing procedures for the AI-Powered Anomaly Detection System.

## 📋 Table of Contents

1. [Pre-Deployment Testing](#pre-deployment-testing)
2. [Infrastructure Testing](#infrastructure-testing)
3. [ML Model Testing](#ml-model-testing)
4. [Azure Function Testing](#azure-function-testing)
5. [CI/CD Pipeline Testing](#cicd-pipeline-testing)
6. [End-to-End Testing](#end-to-end-testing)
7. [Alert Testing](#alert-testing)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)

---

## 🧪 Pre-Deployment Testing

### Local Flask Application Testing

```powershell
# 1. Setup environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Run unit tests
pytest --cov=. --cov-report=term --cov-report=html

# 3. Check coverage report
Start-Process .\htmlcov\index.html

# 4. Test application locally
python app.py

# 5. Test health endpoint
Invoke-WebRequest -Uri "http://localhost:8000/health" | Select-Object -ExpandProperty Content

# Expected output:
# {"status":"healthy"}

# 6. Test main endpoint
Invoke-WebRequest -Uri "http://localhost:8000/" | Select-Object -ExpandProperty Content

# Expected output:
# {"message":"Hello from Flask on Azure!"}
```

### Docker Build Testing

```powershell
# 1. Build Docker image
docker build -t flask-app:test .

# 2. Run container locally
docker run -d -p 8000:8000 --name flask-test flask-app:test

# 3. Test container
Start-Sleep -Seconds 3
Invoke-WebRequest -Uri "http://localhost:8000/health"

# 4. Check container logs
docker logs flask-test

# 5. Stop and remove container
docker stop flask-test
docker rm flask-test

# 6. Clean up image (optional)
docker rmi flask-app:test
```

### Terraform Validation

```powershell
cd terraform

# 1. Format check
terraform fmt -check -recursive

# 2. Validate syntax
terraform validate

# 3. Initialize (if not already done)
terraform init

# 4. Run plan (without applying)
terraform plan -out=tfplan

# 5. Review plan output
# Check for:
# - No unexpected resource deletions
# - All resources have correct configuration
# - No sensitive data in outputs

# Expected output:
# Plan: X to add, Y to change, 0 to destroy.
```

---

## 🏗️ Infrastructure Testing

### Verify Azure Resources

```powershell
# 1. Check resource group exists
az group show --name flask-app-rg

# 2. List all resources
az resource list --resource-group flask-app-rg --output table

# 3. Verify App Service
$appService = az webapp show --name <app-service-name> --resource-group flask-app-rg | ConvertFrom-Json
Write-Host "App Service State: $($appService.state)"
Write-Host "App Service URL: https://$($appService.defaultHostName)"

# Expected: state = "Running"

# 4. Verify Container Registry
az acr show --name <acr-name> --resource-group flask-app-rg

# 5. Verify ML Workspace
az ml workspace show --name <workspace-name> --resource-group flask-app-rg

# 6. Verify Function App
az functionapp show --name <function-app-name> --resource-group flask-app-rg

# 7. Test App Service endpoint
Invoke-WebRequest -Uri "https://<app-service-name>.azurewebsites.net/health"

# Expected: {"status":"healthy"}
```

### Verify OIDC Configuration

```powershell
# 1. Get service principal
$appId = $env:AZURE_CLIENT_ID
az ad sp show --id $appId

# 2. List federated credentials
az ad app federated-credential list --id $appId

# Expected: See credential with subject matching your repo

# 3. Check role assignments
az role assignment list --assignee $appId --output table

# Expected: See "Contributor" role at subscription scope
```

### Verify Terraform State

```powershell
cd terraform

# 1. Check state file exists
az storage blob exists `
  --account-name tfstatedevopsdelk `
  --container-name tfstate `
  --name flask-app.terraform.tfstate

# Expected: {"exists": true}

# 2. List state resources
terraform state list

# Expected output (partial):
# azurerm_resource_group.rg
# azurerm_container_registry.acr
# azurerm_linux_web_app.app_service
# azurerm_machine_learning_workspace.ml_workspace
# azurerm_linux_function_app.function_app

# 3. Verify specific resource
terraform state show azurerm_machine_learning_workspace.ml_workspace
```

---

## 🤖 ML Model Testing

### Local Model Training

```powershell
# 1. Install dependencies
pip install scikit-learn pandas joblib azure-ai-ml azure-identity numpy

# 2. Set Azure credentials
$env:AZURE_CLIENT_ID = "<your-client-id>"
$env:AZURE_TENANT_ID = "<your-tenant-id>"
$env:AZURE_SUBSCRIPTION_ID = "<your-subscription-id>"

# 3. Run training script
python train_anomaly_detection.py

# Expected output:
# ✅ Connected to Azure ML Workspace
# ✅ Generated X training samples
# ✅ Model trained successfully
# ✅ Model registered: pipeline-anomaly-detector version X
```

### Model Prediction Testing

```powershell
# Create test script
@"
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler

# Test data: [duration, failure_rate]
normal_data = np.array([
    [180, 0.0],  # Normal build
    [200, 0.0],  # Normal build
    [195, 0.0],  # Normal build
])

anomaly_data = np.array([
    [650, 0.0],  # Slow build (anomaly)
    [180, 1.0],  # Failed build (anomaly)
    [800, 0.5],  # Very slow + partial failure (anomaly)
])

print('Testing model predictions...')
print('\nNormal builds (should predict 1):')
# Load your model here if saved locally
# model = joblib.load('model/pipeline_anomaly_detector.pkl')
# predictions = model.predict(normal_data)
# print(predictions)

print('\nAnomaly builds (should predict -1):')
# predictions = model.predict(anomaly_data)
# print(predictions)
"@ | Out-File -FilePath test_model.py -Encoding utf8

python test_model.py
```

### Verify Model in Azure ML

```powershell
# 1. List registered models
az ml model list `
  --workspace-name <workspace-name> `
  --resource-group flask-app-rg

# 2. Get model details
az ml model show `
  --name pipeline-anomaly-detector `
  --workspace-name <workspace-name> `
  --resource-group flask-app-rg

# 3. Download model (optional)
az ml model download `
  --name pipeline-anomaly-detector `
  --version 1 `
  --workspace-name <workspace-name> `
  --resource-group flask-app-rg `
  --download-path ./downloaded_model
```

---

## ⚡ Azure Function Testing

### Local Function Testing

```powershell
# 1. Install Azure Functions Core Tools
# Download from: https://docs.microsoft.com/azure/azure-functions/functions-run-local

# 2. Install dependencies
pip install -r azure_function_requirements.txt

# 3. Configure local settings
Copy-Item local.settings.json.example local.settings.json
# Edit local.settings.json with your values

# 4. Start function locally
func start

# Expected output:
# Functions:
#   detect_anomalies: [POST,GET] http://localhost:7071/api/detect_anomalies
#   monitor_pipelines: [timer trigger]

# 5. Test HTTP trigger
$body = @{
    data = @(
        @{
            build_id = "test-123"
            duration = 450
            failure_rate = 0.0
        }
    )
} | ConvertTo-Json

Invoke-WebRequest `
  -Uri "http://localhost:7071/api/detect_anomalies" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body

# Expected response:
# {
#   "anomalies_detected": 1,
#   "anomalies": [...],
#   "timestamp": "..."
# }
```

### Deployed Function Testing

```powershell
# 1. Get function URL
$functionUrl = "https://<function-app-name>.azurewebsites.net/api/detect_anomalies"

# 2. Test with normal metrics
$normalMetrics = @{
    data = @(
        @{
            build_id = "test-normal"
            duration = 180
            failure_rate = 0.0
        }
    )
} | ConvertTo-Json

$response = Invoke-WebRequest `
  -Uri $functionUrl `
  -Method POST `
  -ContentType "application/json" `
  -Body $normalMetrics

$response.Content | ConvertFrom-Json

# Expected: anomalies_detected = 0

# 3. Test with anomaly metrics
$anomalyMetrics = @{
    data = @(
        @{
            build_id = "test-anomaly"
            duration = 800
            failure_rate = 0.0
        }
    )
} | ConvertTo-Json

$response = Invoke-WebRequest `
  -Uri $functionUrl `
  -Method POST `
  -ContentType "application/json" `
  -Body $anomalyMetrics

$response.Content | ConvertFrom-Json

# Expected: anomalies_detected = 1

# 4. Check function logs
az webapp log tail `
  --name <function-app-name> `
  --resource-group flask-app-rg
```

### Function Performance Testing

```powershell
# Load test the function
$functionUrl = "https://<function-app-name>.azurewebsites.net/api/detect_anomalies"
$testData = @{
    data = @(
        @{
            build_id = "perf-test"
            duration = 200
            failure_rate = 0.0
        }
    )
} | ConvertTo-Json

# Run 10 concurrent requests
1..10 | ForEach-Object -Parallel {
    $result = Measure-Command {
        Invoke-WebRequest `
          -Uri $using:functionUrl `
          -Method POST `
          -ContentType "application/json" `
          -Body $using:testData `
          -ErrorAction SilentlyContinue
    }
    Write-Host "Request $_ : $($result.TotalMilliseconds) ms"
} -ThrottleLimit 10

# Expected: All requests < 5000ms
```

---

## 🔄 CI/CD Pipeline Testing

### Trigger Workflows Manually

```powershell
# 1. Trigger Terraform deployment
gh workflow run terraform-deploy.yml

# 2. Trigger ML model training
gh workflow run train-ml-model.yml

# 3. Trigger function deployment
gh workflow run deploy-function.yml

# 4. Trigger full CI/CD
git commit --allow-empty -m "Test CI/CD pipeline"
git push origin main

# 5. Watch workflow progress
gh run watch
```

### Verify Workflow Steps

```powershell
# 1. List recent runs
gh run list --limit 5

# 2. View specific run
gh run view <run-id>

# 3. View logs for specific job
gh run view <run-id> --log --job <job-id>

# 4. Check if monitor job ran
gh run view <run-id> --log | Select-String -Pattern "AI-Powered Anomaly Detection"

# 5. Download artifacts
gh run download <run-id> --name anomaly-detection-report
```

### Test Monitor Job Logic

```powershell
# Create a test that simulates the monitor job

@"
# Simulate metrics collection
`$duration = 450  # Anomaly: too slow
`$failureRate = 0.0

Write-Host "📊 Testing metrics:"
Write-Host "  Duration: `$duration s"
Write-Host "  Failure Rate: `$failureRate"

# Simulate function call
`$body = @{
    data = @(
        @{
            build_id = "test-123"
            duration = `$duration
            failure_rate = `$failureRate
        }
    )
} | ConvertTo-Json

`$response = Invoke-WebRequest ``
  -Uri "https://<function-app-name>.azurewebsites.net/api/detect_anomalies" ``
  -Method POST ``
  -ContentType "application/json" ``
  -Body `$body

`$result = `$response.Content | ConvertFrom-Json
Write-Host "🤖 Anomalies detected: `$(`$result.anomalies_detected)"

if (`$result.anomalies_detected -gt 0) {
    Write-Host "🚨 ANOMALY DETECTED!"
    Write-Host "This would trigger:"
    Write-Host "  - GitHub Issue creation"
    Write-Host "  - Teams notification"
    Write-Host "  - Email alert"
} else {
    Write-Host "✅ No anomalies - pipeline behavior is normal"
}
"@ | Out-File -FilePath test_monitor.ps1 -Encoding utf8

.\test_monitor.ps1
```

---

## 🎯 End-to-End Testing

### Complete System Test

```powershell
# Test the entire flow from code push to alert

Write-Host "🚀 Starting End-to-End Test" -ForegroundColor Cyan

# Step 1: Deploy infrastructure (if needed)
Write-Host "`n1️⃣ Checking infrastructure..." -ForegroundColor Yellow
cd terraform
terraform plan -detailed-exitcode
if ($LASTEXITCODE -eq 2) {
    Write-Host "Changes detected, applying..." -ForegroundColor Yellow
    terraform apply -auto-approve
}
cd ..

# Step 2: Train ML model
Write-Host "`n2️⃣ Training ML model..." -ForegroundColor Yellow
gh workflow run train-ml-model.yml
Start-Sleep -Seconds 10
$trainRun = gh run list --workflow=train-ml-model.yml --limit 1 --json databaseId | ConvertFrom-Json
gh run watch $trainRun[0].databaseId

# Step 3: Deploy Azure Function
Write-Host "`n3️⃣ Deploying Azure Function..." -ForegroundColor Yellow
gh workflow run deploy-function.yml
Start-Sleep -Seconds 10
$funcRun = gh run list --workflow=deploy-function.yml --limit 1 --json databaseId | ConvertFrom-Json
gh run watch $funcRun[0].databaseId

# Step 4: Trigger CI/CD with anomaly simulation
Write-Host "`n4️⃣ Triggering CI/CD pipeline..." -ForegroundColor Yellow
git commit --allow-empty -m "E2E test: Trigger CI/CD"
git push origin main

# Step 5: Monitor workflow
Write-Host "`n5️⃣ Monitoring workflow execution..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
$cicdRun = gh run list --workflow=ci-cd.yml --limit 1 --json databaseId | ConvertFrom-Json
gh run watch $cicdRun[0].databaseId

# Step 6: Check for anomaly detection
Write-Host "`n6️⃣ Checking anomaly detection results..." -ForegroundColor Yellow
$logs = gh run view $cicdRun[0].databaseId --log
if ($logs -match "anomaly") {
    Write-Host "✅ Anomaly detection executed" -ForegroundColor Green
    
    # Check if issue was created
    $issues = gh issue list --label anomaly --limit 1 --json number | ConvertFrom-Json
    if ($issues.Count -gt 0) {
        Write-Host "✅ GitHub issue created: #$($issues[0].number)" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️ Anomaly detection may not have run" -ForegroundColor Yellow
}

Write-Host "`n✅ End-to-End Test Complete!" -ForegroundColor Cyan
```

---

## 🚨 Alert Testing

### Test GitHub Issue Creation

```powershell
# Manual test of issue creation logic
$issueBody = @"
## Pipeline Anomaly Alert

An anomaly was detected in the CI/CD pipeline by our AI-powered monitoring system.

### Run Details
- **Workflow**: Test Workflow
- **Run ID**: 123456
- **Triggered by**: @testuser
- **Commit**: abc123
- **Branch**: main

### Anomaly Details
- **Build**: 123456
  - Duration: 450s
  - Failure Rate: 0.0%
  - Anomaly Score: -0.43

This is a test alert.
"@

gh issue create `
  --title "🧪 TEST: Pipeline Anomaly Detected" `
  --body $issueBody `
  --label "test,anomaly,ci-cd,automated"

# Verify issue created
gh issue list --label test

# Clean up test issue
gh issue close <issue-number> --comment "Test completed, closing issue"
```

### Test Teams Webhook

```powershell
# Test Teams notification
$teamsWebhook = "<YOUR_TEAMS_WEBHOOK_URL>"

$teamsMessage = @{
    "@type" = "MessageCard"
    "@context" = "https://schema.org/extensions"
    themeColor = "FF0000"
    title = "🧪 TEST: Pipeline Anomaly Detected"
    summary = "Test alert from anomaly detection system"
    sections = @(
        @{
            activityTitle = "Test Alert"
            activitySubtitle = "Build #123456"
            facts = @(
                @{ name = "Duration"; value = "450s" }
                @{ name = "Failure Rate"; value = "0.0%" }
                @{ name = "Anomaly Score"; value = "-0.43" }
            )
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-WebRequest `
  -Uri $teamsWebhook `
  -Method POST `
  -ContentType "application/json" `
  -Body $teamsMessage

# Expected: Message appears in Teams channel
```

### Test Email Alert (SendGrid)

```powershell
# Test email via SendGrid API
$sendGridKey = $env:SENDGRID_API_KEY

$emailBody = @{
    personalizations = @(
        @{
            to = @(
                @{ email = "your-email@example.com" }
            )
            subject = "🧪 TEST: Pipeline Anomaly Detected"
        }
    )
    from = @{
        email = "alerts@yourdomain.com"
        name = "CI/CD Anomaly Detector"
    }
    content = @(
        @{
            type = "text/html"
            value = "<h2>Test Alert</h2><p>This is a test email from the anomaly detection system.</p>"
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-WebRequest `
  -Uri "https://api.sendgrid.com/v3/mail/send" `
  -Method POST `
  -Headers @{ "Authorization" = "Bearer $sendGridKey" } `
  -ContentType "application/json" `
  -Body $emailBody

# Expected: Email received in inbox
```

---

## ⚡ Performance Testing

### Pipeline Execution Time

```powershell
# Measure pipeline execution times
Write-Host "Analyzing recent pipeline performance..." -ForegroundColor Cyan

$runs = gh run list --workflow=ci-cd.yml --limit 20 --json databaseId,conclusion,createdAt,updatedAt | ConvertFrom-Json

$durations = @()
foreach ($run in $runs) {
    if ($run.conclusion -eq "success") {
        $start = [DateTime]::Parse($run.createdAt)
        $end = [DateTime]::Parse($run.updatedAt)
        $duration = ($end - $start).TotalSeconds
        $durations += $duration
    }
}

if ($durations.Count -gt 0) {
    $avg = ($durations | Measure-Object -Average).Average
    $min = ($durations | Measure-Object -Minimum).Minimum
    $max = ($durations | Measure-Object -Maximum).Maximum
    
    Write-Host "`nPipeline Performance Statistics:" -ForegroundColor Yellow
    Write-Host "  Average Duration: $([math]::Round($avg, 2)) seconds"
    Write-Host "  Minimum Duration: $([math]::Round($min, 2)) seconds"
    Write-Host "  Maximum Duration: $([math]::Round($max, 2)) seconds"
    Write-Host "  Total Runs Analyzed: $($durations.Count)"
}
```

### Azure Function Response Time

```powershell
# Test function response times
$functionUrl = "https://<function-app-name>.azurewebsites.net/api/detect_anomalies"
$testData = @{
    data = @(@{ build_id = "perf-test"; duration = 200; failure_rate = 0.0 })
} | ConvertTo-Json

Write-Host "Testing function response times (10 requests)..." -ForegroundColor Cyan

$times = 1..10 | ForEach-Object {
    $measure = Measure-Command {
        Invoke-WebRequest -Uri $functionUrl -Method POST -ContentType "application/json" -Body $testData -ErrorAction SilentlyContinue
    }
    $measure.TotalMilliseconds
}

$avgTime = ($times | Measure-Object -Average).Average
Write-Host "`nAverage Response Time: $([math]::Round($avgTime, 2)) ms" -ForegroundColor Green

# Expected: < 2000ms
```

---

## 🔐 Security Testing

### Verify OIDC Configuration

```powershell
# Test OIDC token request (manual simulation)
Write-Host "Verifying OIDC configuration..." -ForegroundColor Cyan

# 1. Check federated credentials
az ad app federated-credential list --id $env:AZURE_CLIENT_ID --output table

# 2. Verify no client secrets exist
$secrets = az ad app credential list --id $env:AZURE_CLIENT_ID | ConvertFrom-Json
if ($secrets.Count -eq 0) {
    Write-Host "✅ No client secrets found (using OIDC)" -ForegroundColor Green
} else {
    Write-Host "⚠️ Client secrets detected" -ForegroundColor Yellow
}

# 3. Check role assignments
az role assignment list --assignee $env:AZURE_CLIENT_ID --output table
```

### Test Managed Identity

```powershell
# Verify App Service managed identity
$appName = "<app-service-name>"
$identity = az webapp identity show --name $appName --resource-group flask-app-rg | ConvertFrom-Json

if ($identity.type -eq "SystemAssigned") {
    Write-Host "✅ System-assigned managed identity enabled" -ForegroundColor Green
    Write-Host "   Principal ID: $($identity.principalId)"
    
    # Check role assignments for managed identity
    az role assignment list --assignee $identity.principalId --output table
} else {
    Write-Host "❌ Managed identity not configured" -ForegroundColor Red
}
```

### Scan for Secrets in Code

```powershell
# Basic secret scanning
Write-Host "Scanning for potential secrets in code..." -ForegroundColor Cyan

$patterns = @(
    "password\s*=",
    "api[_-]?key\s*=",
    "secret\s*=",
    "token\s*=",
    "connectionstring"
)

Get-ChildItem -Recurse -Include *.py,*.yml,*.tf,*.json |
    Select-String -Pattern $patterns |
    ForEach-Object {
        Write-Host "⚠️ Potential secret found: $($_.Path):$($_.LineNumber)" -ForegroundColor Yellow
        Write-Host "   $($_.Line.Trim())"
    }

Write-Host "`n✅ Scan complete" -ForegroundColor Green
```

---

## 📊 Test Results Summary

### Generate Test Report

```powershell
@"
# Test Results Summary
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Infrastructure Tests
- [ ] Resource Group exists
- [ ] App Service running
- [ ] Container Registry accessible
- [ ] ML Workspace configured
- [ ] Function App deployed
- [ ] Terraform state valid

## Application Tests
- [ ] Unit tests passing
- [ ] Docker build successful
- [ ] Health endpoint responding
- [ ] Application accessible

## ML Model Tests
- [ ] Model training successful
- [ ] Model registered in Azure ML
- [ ] Predictions working correctly
- [ ] Normal data classified correctly
- [ ] Anomaly data detected

## Function Tests
- [ ] HTTP trigger working
- [ ] Timer trigger configured
- [ ] ML model loading
- [ ] Predictions accurate
- [ ] Response time < 2000ms

## Pipeline Tests
- [ ] Build job successful
- [ ] Deploy job successful
- [ ] Monitor job executed
- [ ] Anomaly detection ran
- [ ] Artifacts uploaded

## Alert Tests
- [ ] GitHub issues created
- [ ] Teams notifications sent
- [ ] Email alerts delivered
- [ ] Alert content accurate

## Security Tests
- [ ] OIDC authentication working
- [ ] No client secrets in code
- [ ] Managed identity configured
- [ ] Role assignments correct
- [ ] Secrets properly managed

## Performance Tests
- [ ] Pipeline duration acceptable
- [ ] Function response time good
- [ ] Resource utilization normal
- [ ] No memory leaks

## Notes
Add any additional observations or issues here.
"@ | Out-File -FilePath TEST_RESULTS.md -Encoding utf8

Write-Host "Test results template created: TEST_RESULTS.md" -ForegroundColor Green
Write-Host "Please fill in the checklist as you complete each test." -ForegroundColor Yellow
```

---

## 🎓 Best Practices

### Testing Checklist

- ✅ **Test locally first** before pushing to GitHub
- ✅ **Use meaningful test data** that represents real scenarios
- ✅ **Document test results** for future reference
- ✅ **Automate repetitive tests** with scripts
- ✅ **Test failure scenarios** not just happy paths
- ✅ **Monitor costs** during testing in Azure
- ✅ **Clean up test resources** after completion
- ✅ **Version control test scripts** alongside code

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Function times out | Increase timeout in host.json |
| Model not found | Ensure model is registered in Azure ML |
| OIDC auth fails | Verify federated credentials |
| Alerts not sending | Check webhook URLs and API keys |
| Pipeline slow | Optimize Docker builds with caching |
| High Azure costs | Use cheaper tiers for dev/test |

---

## 📚 Additional Resources

- [GitHub Actions Testing Documentation](https://docs.github.com/actions/automating-builds-and-tests)
- [Azure Functions Testing](https://learn.microsoft.com/azure/azure-functions/functions-test-a-function)
- [ML Model Testing Best Practices](https://learn.microsoft.com/azure/machine-learning/how-to-test-models)
- [Terraform Testing](https://www.terraform.io/docs/language/modules/testing-experiment.html)

---

**Need help?** Check the [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) for common commands or open an issue on GitHub.
