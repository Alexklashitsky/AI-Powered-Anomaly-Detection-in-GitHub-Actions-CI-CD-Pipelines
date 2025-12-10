# AI-Powered Anomaly Detection - Complete Solution

## 🎯 Overview

This project implements a complete DevOps solution with AI-powered anomaly detection for GitHub Actions CI/CD pipelines. It combines infrastructure as code, containerized applications, and machine learning to detect unusual patterns in pipeline metrics.

## 📦 Components Created

### 1. **Azure ML Anomaly Detection Script** (`train_anomaly_detection.py`)
- Connects to Azure ML workspace using OIDC
- Loads pipeline metrics (build_id, duration, failure_rate)
- Trains Isolation Forest model for anomaly detection
- Registers model in Azure ML
- Supports deployment to Azure Container Instances
- Includes comprehensive error handling and logging

### 2. **Model Scoring Script** (`scoring/score.py`)
- Real-time inference endpoint
- Accepts pipeline metrics via REST API
- Returns anomaly predictions and scores
- Deployed with Azure ML online endpoints

### 3. **Terraform ML Resources** (`terraform/ml_resources.tf`)
Complete Azure ML infrastructure:
- **Azure Machine Learning Workspace**
- **Application Insights** - For ML monitoring
- **Key Vault** - For secrets and keys
- **Storage Account** - For ML artifacts and data
- **Role Assignments** - Proper RBAC for ML workspace
- **ACR Integration** - For model container images

### 4. **ML Training Workflow** (`.github/workflows/train-ml-model.yml`)
- Automated weekly training
- Manual trigger support
- Retrieves ML workspace config from Terraform
- Trains and registers model
- Uploads artifacts for review

### 5. **Environment Files**
- `environment.yml` - Conda environment for ML deployment
- Updated `requirements.txt` with Azure ML SDK v2

## 🔧 How It Works

### Anomaly Detection Flow

```
GitHub Actions Metrics
        ↓
Collect metrics (duration, failure_rate, build_id)
        ↓
Store in pipeline_metrics.csv
        ↓
ML Training Workflow (weekly)
        ├─ Load metrics
        ├─ Train Isolation Forest
        ├─ Normalize features
        ├─ Detect anomalies
        └─ Register model in Azure ML
        ↓
Model Deployment (optional)
        ├─ Create online endpoint
        ├─ Deploy to ACI
        └─ Enable real-time scoring
        ↓
Production Usage
        └─ API calls to detect pipeline anomalies
```

### Infrastructure Provisioning

```
Terraform Apply
    ├─ Resource Group
    ├─ Storage Accounts (App + ML)
    ├─ Container Registry
    ├─ App Service Plan & App
    ├─ Key Vault
    ├─ Application Insights
    └─ Azure ML Workspace
            ├─ System Managed Identity
            ├─ Access to Key Vault
            ├─ Access to Storage
            └─ Access to ACR
```

## 🚀 Quick Start

### 1. Deploy Infrastructure (Including ML Workspace)

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This creates:
- Flask app infrastructure
- Azure ML workspace
- All dependencies

### 2. Train Anomaly Detection Model

**Option A: Manual trigger**
- Go to GitHub Actions → "Train Anomaly Detection Model" → Run workflow

**Option B: Run locally**
```bash
export AZURE_ML_WORKSPACE="ml-workspace-anomaly-detection"
export AZURE_RESOURCE_GROUP="flask-app-rg"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

python train_anomaly_detection.py
```

### 3. Use the Model

**Check for anomalies in your pipeline:**
```python
import requests
import json

# Prepare metrics
metrics = {
    "data": [
        {"build_id": "build_001", "duration": 300, "failure_rate": 0.05},
        {"build_id": "build_002", "duration": 900, "failure_rate": 0.45}  # Anomaly!
    ]
}

# Call prediction endpoint (after deployment)
response = requests.post(
    endpoint_url,
    headers={"Authorization": f"Bearer {api_key}"},
    json=metrics
)

results = response.json()
# results['predictions'] = [False, True]  # Second build is anomalous
```

## 📊 Features

### ML Model Capabilities
- ✅ Unsupervised anomaly detection (Isolation Forest)
- ✅ Feature scaling for normalization
- ✅ Configurable contamination threshold
- ✅ Anomaly scores and binary predictions
- ✅ Batch and real-time inference

### Infrastructure Features
- ✅ Fully managed Azure ML workspace
- ✅ Integrated monitoring with Application Insights
- ✅ Secure secrets management with Key Vault
- ✅ Managed identities for secure access
- ✅ Container registry integration
- ✅ OIDC authentication (no secrets in GitHub)

### Automation Features
- ✅ Weekly automated training
- ✅ Manual trigger support
- ✅ Artifact retention
- ✅ Model versioning in Azure ML
- ✅ Infrastructure as code

## 🔒 Security

- **OIDC Authentication**: No client secrets stored in GitHub
- **Managed Identities**: ML workspace uses managed identity
- **Key Vault**: Sensitive data encrypted
- **RBAC**: Least privilege access
- **Private ACR**: Container images not public

## 📝 Configuration

### Required Terraform Variables

```hcl
# In terraform.tfvars
ml_workspace_name            = "ml-workspace-anomaly-detection"
ml_storage_account_name      = "mlstorageanomalydet"  # Lowercase, 3-24 chars
ml_key_vault_name           = "mlkv-anomaly-det"      # 3-24 chars
ml_application_insights_name = "ml-appinsights-anomaly"
```

### Environment Variables for Training

```bash
AZURE_ML_WORKSPACE      # ML workspace name
AZURE_RESOURCE_GROUP    # Resource group name
AZURE_SUBSCRIPTION_ID   # Azure subscription ID
```

## 🧪 Testing

### Generate Sample Data
The script automatically generates sample data if `pipeline_metrics.csv` doesn't exist:
- 1000 records
- 95% normal pipelines (~5 min duration, low failure rate)
- 5% anomalies (~15 min duration, high failure rate)

### Train Locally
```bash
pip install -r requirements.txt
python train_anomaly_detection.py
```

### Check Results
```bash
# Model files
ls model/
# isolation_forest_model.pkl
# scaler.pkl

# Generated data
cat pipeline_metrics.csv
```

## 📈 Monitoring

### Application Insights
- ML workspace operations
- Model training metrics
- Endpoint performance
- Error rates

### Azure ML Studio
- Experiment tracking
- Model versioning
- Deployment status
- Endpoint metrics

## 🛠️ Troubleshooting

### ML Workspace Connection Issues
```bash
# Verify workspace exists
az ml workspace show --name ml-workspace-anomaly-detection \
  --resource-group flask-app-rg

# Check managed identity
az ml workspace show --name ml-workspace-anomaly-detection \
  --resource-group flask-app-rg \
  --query identity
```

### Training Failures
- Check Python version (3.11 required)
- Verify Azure credentials
- Ensure workspace is provisioned
- Check logs in GitHub Actions

### Model Registration Issues
- Verify ML workspace is accessible
- Check managed identity permissions
- Ensure model files exist in `model/` directory

## 📚 Resources

- [Azure ML SDK v2 Documentation](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-ml-readme)
- [Isolation Forest Algorithm](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
- [Azure ML Managed Online Endpoints](https://learn.microsoft.com/en-us/azure/machine-learning/concept-endpoints)

## 🎓 Next Steps

1. **Collect Real Pipeline Data**: Replace sample data with actual GitHub Actions metrics
2. **Deploy the Model**: Uncomment deployment code to create online endpoint
3. **Integrate with Alerts**: Set up notifications for detected anomalies
4. **Tune the Model**: Adjust contamination parameter based on your data
5. **Add More Features**: Include test coverage, code complexity, etc.

---

**Note**: The anomaly detection model is trained on CI/CD pipeline metrics to identify unusual build patterns such as:
- Unexpectedly slow builds
- High failure rates
- Resource consumption anomalies
- Build time regressions

This helps teams proactively identify and fix pipeline issues before they impact delivery timelines.
