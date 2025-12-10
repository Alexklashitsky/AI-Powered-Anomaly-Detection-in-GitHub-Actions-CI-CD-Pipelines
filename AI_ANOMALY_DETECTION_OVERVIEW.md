# AI-Powered Anomaly Detection System - Complete Overview

## 🎯 System Summary

This project implements a **production-ready, AI-powered anomaly detection system** for CI/CD pipelines that automatically monitors GitHub Actions workflows, detects unusual behavior, and alerts teams in real-time.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI/CD                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐      │
│  │  Build   │───▶│  Deploy  │───▶│  AI Anomaly Monitor  │      │
│  └──────────┘    └──────────┘    └──────────┬───────────┘      │
└──────────────────────────────────────────────┼──────────────────┘
                                               │
                                               ▼
                        ┌─────────────────────────────────┐
                        │   Azure Function (Serverless)   │
                        │   - Collects metrics            │
                        │   - Calls ML endpoint           │
                        │   - Sends alerts                │
                        └────────────┬────────────────────┘
                                     │
                ┌────────────────────┴──────────────────┐
                ▼                                       ▼
    ┌──────────────────────┐              ┌────────────────────────┐
    │  Azure ML Workspace  │              │  Alerting Channels     │
    │  - Isolation Forest  │              │  - Microsoft Teams     │
    │  - Real-time scoring │              │  - Email (SendGrid)    │
    │  - Auto-scaling      │              │  - GitHub Issues       │
    └──────────────────────┘              └────────────────────────┘
```

## 🚀 Key Features

### 1. **Automated ML Training** (`.github/workflows/train-ml-model.yml`)
- Trains an **Isolation Forest** model on historical pipeline metrics
- Runs weekly or on-demand
- Automatically registers models in Azure ML
- Features analyzed:
  - Build duration (seconds)
  - Failure rate (0-1)
  - Test pass/fail patterns
  - Deployment success metrics

### 2. **Real-time Anomaly Detection** (Azure Function)
- Serverless function triggered by:
  - HTTP requests from GitHub Actions
  - Timer trigger (every 5 minutes)
- Queries Azure Monitor for live metrics
- Scores metrics against trained ML model
- Returns anomaly predictions with confidence scores

### 3. **Intelligent Monitoring** (`.github/workflows/ci-cd.yml` - Monitor Job)
- Runs after every deployment
- Collects pipeline metrics:
  ```yaml
  - build_id: Unique identifier
  - duration: Total execution time
  - failure_rate: Success/failure ratio
  - timestamp: When the build ran
  ```
- Calls Azure Function anomaly detection endpoint
- Analyzes results and takes action

### 4. **Multi-Channel Alerting**
- **GitHub Issues**: Automatically creates issues with detailed analysis
- **Microsoft Teams**: Real-time notifications with webhook integration
- **Email**: SendGrid integration for critical alerts
- **Build Failures**: Optional - fail builds on anomalies

## 📊 How It Works

### Step 1: Metric Collection
```yaml
# From ci-cd.yml monitor job
- name: Query Pipeline Metrics from Azure Monitor
  run: |
    # Get workflow duration
    DURATION=$((CURRENT_TIME - START_TIMESTAMP))
    
    # Calculate failure rate
    if [ "${{ needs.deploy.result }}" == "success" ]; then
      FAILURE_RATE=0.0
    else
      FAILURE_RATE=1.0
    fi
```

### Step 2: Anomaly Detection
```yaml
- name: Call Anomaly Detection Function
  run: |
    # Prepare metrics payload
    METRICS_JSON=$(cat <<EOF
    {
      "data": [{
        "build_id": "$BUILD_ID",
        "duration": $DURATION,
        "failure_rate": $FAILURE_RATE
      }]
    }
    EOF
    )
    
    # Call Azure Function
    curl -X POST "$FUNCTION_URL" -d "$METRICS_JSON"
```

### Step 3: Alert & Report
```yaml
- name: Create GitHub Issue for Anomaly
  if: steps.anomaly_check.outputs.anomalies_detected > 0
  uses: actions/github-script@v7
  with:
    script: |
      await github.rest.issues.create({
        title: '🚨 Pipeline Anomaly Detected',
        body: 'Detailed anomaly report...',
        labels: ['anomaly', 'ci-cd', 'automated']
      });
```

## 🧠 Machine Learning Details

### Model: Isolation Forest
**Why Isolation Forest?**
- Excellent for unsupervised anomaly detection
- No labeled data required
- Fast training and inference
- Works well with small datasets
- Handles multi-dimensional data

### Training Process (`train_anomaly_detection.py`)
```python
class PipelineAnomalyDetector:
    def train_model(self, data: pd.DataFrame):
        # Feature engineering
        X = data[['duration', 'failure_rate']]
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )
        self.model.fit(X_scaled)
```

### Prediction (`function_app.py`)
```python
def detect_anomalies(metrics: list):
    # Load trained model from Azure ML
    model = load_model()
    
    # Predict anomalies (-1 = anomaly, 1 = normal)
    predictions = model.predict(metrics)
    
    # Calculate anomaly scores
    scores = model.score_samples(metrics)
    
    return predictions, scores
```

## 🔧 Infrastructure Components

### Terraform Resources
```hcl
# ML Workspace
resource "azurerm_machine_learning_workspace" "ml_workspace"

# Azure Function
resource "azurerm_linux_function_app" "anomaly_detector"

# Storage for ML artifacts
resource "azurerm_storage_account" "ml_storage"

# Key Vault for secrets
resource "azurerm_key_vault" "ml_keyvault"

# Application Insights for monitoring
resource "azurerm_application_insights" "ml_insights"
```

### Azure Function Configuration
```python
# Environment variables
- ML_WORKSPACE_NAME
- ML_RESOURCE_GROUP
- ML_MODEL_NAME
- TEAMS_WEBHOOK_URL
- SENDGRID_API_KEY
- LOG_ANALYTICS_WORKSPACE_ID
```

## 📈 Metrics & Features

### Current Features
1. **Build Duration**: Time from start to completion
2. **Failure Rate**: Percentage of failed steps/jobs

### Extensible for:
- CPU usage patterns
- Memory consumption
- Network latency
- Test execution time
- Code coverage trends
- Deployment frequency
- Mean time to recovery (MTTR)

## 🎨 Alert Format

### GitHub Issue Example
```markdown
## 🚨 Pipeline Anomaly Alert

An anomaly was detected in the CI/CD pipeline by our AI-powered monitoring system.

### Run Details
- **Workflow**: Flask CI/CD Pipeline
- **Run ID**: 1234567890
- **Triggered by**: @username
- **Commit**: abc123def
- **Branch**: main

### Anomaly Details
- **Build**: 1234567890
  - Duration: 450s (expected: ~200s)
  - Failure Rate: 0.0%
  - Anomaly Score: -0.43 (threshold: -0.3)

### Recommendations
1. Review the workflow execution logs
2. Check for infrastructure issues in Azure
3. Compare with recent successful runs
4. Investigate any recent code or configuration changes
```

### Microsoft Teams Card
```json
{
  "@type": "MessageCard",
  "themeColor": "FF0000",
  "title": "🚨 Pipeline Anomaly Detected",
  "sections": [{
    "facts": [
      {"name": "Build ID", "value": "1234567890"},
      {"name": "Duration", "value": "450s"},
      {"name": "Anomaly Score", "value": "-0.43"}
    ]
  }]
}
```

## 🔐 Security Features

### OIDC Authentication
- **No client secrets** stored in GitHub
- Federated credentials for secure Azure access
- Short-lived tokens (automatic refresh)

### Managed Identity
- Azure Function uses managed identity
- No credential management needed
- Automatic RBAC integration

### Secrets Management
- Azure Key Vault integration
- SendGrid API keys secured
- Teams webhooks encrypted

## 📋 Setup Checklist

- [x] Terraform infrastructure deployed
- [x] Azure ML Workspace configured
- [x] ML model trained and registered
- [x] Azure Function deployed
- [x] GitHub Actions workflows configured
- [x] OIDC authentication setup
- [x] Alert channels configured (Teams/Email)
- [x] Documentation complete

## 🚀 Quick Start

### 1. Deploy Infrastructure
```bash
cd terraform
terraform init
terraform apply
```

### 2. Train ML Model
```bash
# Trigger via GitHub Actions
gh workflow run train-ml-model.yml

# Or run locally
python train_anomaly_detection.py
```

### 3. Deploy Azure Function
```bash
# Trigger via GitHub Actions
gh workflow run deploy-function.yml

# Or deploy locally
func azure functionapp publish <function-app-name>
```

### 4. Run CI/CD Pipeline
```bash
# Push to main branch
git push origin main

# Monitor job runs automatically after deployment
```

## 📊 Monitoring & Observability

### View Anomaly Reports
- **GitHub**: Check Issues with label `anomaly`
- **Azure Portal**: View Application Insights logs
- **ML Studio**: Monitor model performance
- **Function Logs**: Review detection history

### Dashboards
```bash
# Azure Portal
https://portal.azure.com → Application Insights → Logs

# Kusto query for anomalies
traces
| where message contains "anomaly_detected"
| project timestamp, build_id, anomaly_score
| order by timestamp desc
```

## 🔄 Workflow Integration

### Full Pipeline Flow
1. **Developer pushes code** → GitHub Actions triggered
2. **Build & Test** → Collect metrics (duration, results)
3. **Deploy to Azure** → Update running application
4. **Monitor Job** → Query metrics from deployment
5. **Call Azure Function** → Send metrics for analysis
6. **ML Model Prediction** → Detect anomalies
7. **Alert if needed** → Create issue, send notifications
8. **Artifact Upload** → Save detailed report

### Conditional Execution
```yaml
# Run only if deployment succeeded
if: always() && needs.deploy.result != 'skipped'

# Create issue only if anomalies found
if: steps.anomaly_check.outputs.anomalies_detected > 0

# Fail build on critical anomalies (optional)
if: steps.anomaly_check.outputs.anomalies_detected > 0
```

## 🎯 Benefits

### For Development Teams
- **Early Detection**: Catch performance issues before they escalate
- **Reduced MTTR**: Faster identification of problems
- **Automated Alerts**: No manual monitoring required
- **Historical Analysis**: Track trends over time

### For DevOps Teams
- **Infrastructure Monitoring**: Detect resource issues
- **Cost Optimization**: Identify inefficient pipelines
- **Capacity Planning**: Predict scaling needs
- **SLA Compliance**: Ensure pipeline reliability

### For Leadership
- **Visibility**: Real-time pipeline health metrics
- **Risk Mitigation**: Proactive issue detection
- **Cost Savings**: Reduce downtime and incident response
- **Data-Driven**: ML-powered insights

## 🔮 Future Enhancements

### Potential Additions
- [ ] **Advanced Features**: Add CPU, memory, network metrics
- [ ] **Multi-model Ensemble**: Combine multiple ML algorithms
- [ ] **Predictive Analytics**: Forecast future failures
- [ ] **Custom Thresholds**: Per-project anomaly sensitivity
- [ ] **Integration Testing**: Automated anomaly testing
- [ ] **Slack Integration**: Additional alert channel
- [ ] **PagerDuty**: Incident management integration
- [ ] **Auto-remediation**: Automatic rollback on anomalies

### Roadmap
```
Q1 2024: ✅ Core anomaly detection
Q2 2024: 🔄 Advanced metrics & multi-model
Q3 2024: 📊 Predictive analytics
Q4 2024: 🤖 Auto-remediation
```

## 📚 Additional Resources

- [ML_ANOMALY_DETECTION_GUIDE.md](./ML_ANOMALY_DETECTION_GUIDE.md) - Detailed ML documentation
- [AZURE_FUNCTION_README.md](./AZURE_FUNCTION_README.md) - Function app guide
- [README.md](./README.md) - General project documentation
- [Azure ML Documentation](https://learn.microsoft.com/azure/machine-learning/)
- [GitHub Actions Documentation](https://docs.github.com/actions)

## 💡 Best Practices

### Model Training
- **Frequency**: Retrain weekly or when data changes significantly
- **Data Quality**: Ensure metrics are accurate and complete
- **Validation**: Use historical data to validate predictions
- **Monitoring**: Track model performance over time

### Alert Management
- **Threshold Tuning**: Adjust contamination rate based on false positives
- **Priority Levels**: Categorize anomalies (critical, warning, info)
- **Alert Fatigue**: Don't over-alert, consolidate notifications
- **Action Items**: Include remediation steps in alerts

### Production Deployment
- **Gradual Rollout**: Test on non-production pipelines first
- **Rollback Plan**: Have a quick way to disable anomaly detection
- **Documentation**: Keep runbooks updated
- **Team Training**: Ensure teams understand how to respond

## 🤝 Contributing

We welcome contributions! Areas of interest:
- Additional ML algorithms
- New metrics and features
- Alert channel integrations
- Dashboard development
- Documentation improvements

## 📝 License

This project is provided as-is for educational and production use.

---

**Built with ❤️ using Azure, GitHub Actions, and Machine Learning**

For questions or support, please open an issue on GitHub.
