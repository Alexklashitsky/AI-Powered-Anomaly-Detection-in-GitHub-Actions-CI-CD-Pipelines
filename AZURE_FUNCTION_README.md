# Azure Function - CI/CD Anomaly Detection & Alerting

## Overview

This Azure Function provides real-time monitoring and alerting for CI/CD pipeline anomalies. It runs every 5 minutes to detect unusual patterns in GitHub Actions workflows and sends alerts via Microsoft Teams and/or email.

## Features

- **🔄 Automatic Monitoring**: Timer trigger runs every 5 minutes
- **🌐 HTTP Endpoint**: Manual trigger for on-demand detection
- **🤖 ML Integration**: Calls Azure ML endpoint for predictions
- **📊 Azure Monitor Integration**: Queries pipeline metrics
- **🔔 Multiple Alert Channels**: Teams webhooks and SendGrid email
- **🔐 Secure**: Uses Managed Identity for Azure authentication

## Architecture

```
Timer Trigger (Every 5 min) / HTTP Trigger
            ↓
Query Azure Monitor for pipeline metrics
            ↓
Call Azure ML Endpoint for predictions
            ↓
Anomalies detected?
    ├─ Yes → Send Alerts (Teams + Email)
    └─ No → Log success
```

## Triggers

### 1. Timer Trigger
- **Schedule**: Every 5 minutes (`0 */5 * * * *`)
- **Purpose**: Automated monitoring
- **Logs**: Check Application Insights

### 2. HTTP Trigger
- **Endpoint**: `https://your-function-app.azurewebsites.net/api/detect_anomalies`
- **Methods**: GET, POST
- **Purpose**: Manual testing and on-demand detection
- **Response**: JSON with detection results

## Configuration

### Environment Variables

Set these in Azure Function App Settings or `local.settings.json`:

```json
{
  "ML_ENDPOINT_URL": "https://your-ml-endpoint.azureml.ms/score",
  "ML_API_KEY": "your-ml-api-key",
  "TEAMS_WEBHOOK_URL": "https://outlook.office.com/webhook/...",
  "LOG_ANALYTICS_WORKSPACE_ID": "your-workspace-id",
  "SENDGRID_API_KEY": "your-sendgrid-api-key",
  "SENDGRID_FROM_EMAIL": "alerts@yourcompany.com",
  "SENDGRID_TO_EMAIL": "devops@yourcompany.com",
  "ML_STUDIO_URL": "https://ml.azure.com"
}
```

### Teams Webhook Setup

1. Go to your Teams channel
2. Click "⋯" → "Connectors"
3. Find "Incoming Webhook" and click "Configure"
4. Name it "Pipeline Anomaly Alerts"
5. Copy the webhook URL
6. Add to Function App settings as `TEAMS_WEBHOOK_URL`

### SendGrid Setup (Optional)

1. Create SendGrid account: https://sendgrid.com
2. Generate API key
3. Verify sender email address
4. Add credentials to Function App settings

## Local Development

### Prerequisites
- Python 3.11
- Azure Functions Core Tools v4
- Azure CLI

### Setup

```bash
# Install dependencies
pip install -r azure_function_requirements.txt

# Install Azure Functions Core Tools
# Windows: choco install azure-functions-core-tools
# Mac: brew tap azure/functions && brew install azure-functions-core-tools@4

# Configure local settings
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your values

# Start function locally
func start
```

### Test HTTP Trigger

```bash
# Test locally
curl http://localhost:7071/api/detect_anomalies

# Test deployed function
curl https://your-function-app.azurewebsites.net/api/detect_anomalies
```

### Test with Sample Data

```bash
# Run function manually
python function_app.py
```

## Deployment

### Via Azure CLI

```bash
# Create function app (if not using Terraform)
az functionapp create \
  --resource-group flask-app-rg \
  --name func-anomaly-detector \
  --storage-account funcstorageanomalydet \
  --consumption-plan-location westeurope \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4

# Deploy function code
func azure functionapp publish func-anomaly-detector
```

### Via Terraform

```bash
cd terraform
terraform apply

# After Terraform creates the Function App, deploy code:
func azure functionapp publish func-anomaly-detector
```

### Via GitHub Actions (Recommended)

See `.github/workflows/deploy-function.yml` for automated deployment.

## Monitoring

### Application Insights

View logs and metrics:
```bash
az monitor app-insights query \
  --app ml-appinsights-anomaly \
  --analytics-query "traces | where message contains 'anomaly' | order by timestamp desc | take 50"
```

### Check Function Logs

```bash
# Stream logs
func azure functionapp logstream func-anomaly-detector

# Or in Azure Portal:
# Function App → Monitor → Log stream
```

### Metrics to Monitor

- **Function execution count**
- **Function execution duration**
- **Failure rate**
- **Anomalies detected per run**
- **Alert delivery success rate**

## Alert Examples

### Teams Alert

```
🚨 CI/CD Pipeline Anomaly Alert
Detected at 2025-12-10 14:30:00 UTC

Build: build_20251210143000_1
Duration: 892.3s | Failure Rate: 35.2%

Build: build_20251210143000_3
Duration: 1024.7s | Failure Rate: 42.8%

[View in Azure ML]
```

### Email Alert

```
Subject: ⚠️ 2 Pipeline Anomalies Detected

CI/CD Pipeline Anomaly Alert

Detected 2 anomalies at 2025-12-10 14:30:00 UTC

Anomalies Detected:
- Build: build_20251210143000_1, Duration: 892.3s, Failure Rate: 35.2%
- Build: build_20251210143000_3, Duration: 1024.7s, Failure Rate: 42.8%

Please investigate these pipeline runs for potential issues.
```

## Troubleshooting

### Function Not Triggering

1. Check timer trigger schedule in logs
2. Verify Function App is running (not stopped)
3. Check Application Insights for errors

### No Metrics Retrieved

1. Verify `LOG_ANALYTICS_WORKSPACE_ID` is set
2. Check Function App managed identity has "Monitoring Reader" role
3. Review query syntax in `query_pipeline_metrics()`

### ML Endpoint Errors

1. Verify `ML_ENDPOINT_URL` and `ML_API_KEY` are correct
2. Check endpoint is deployed and running
3. Test endpoint manually with Postman/curl

### Alerts Not Sending

**Teams:**
- Verify webhook URL is valid and not expired
- Test webhook with manual POST request
- Check Teams channel settings

**Email:**
- Verify SendGrid API key is valid
- Check sender email is verified
- Review SendGrid activity dashboard

## Cost Optimization

### Consumption Plan Benefits
- Pay only for executions
- Automatic scaling
- ~$0.20 per million executions

### Estimated Costs (Monthly)
- Function executions: ~8,640 (every 5 min)
- Execution time: ~1s average
- Storage: ~1GB
- **Total: ~$1-2/month**

## Security Best Practices

- ✅ Use Managed Identity for Azure resources
- ✅ Store secrets in Azure Key Vault (not env variables)
- ✅ Use HTTPS only
- ✅ Restrict HTTP trigger with function keys
- ✅ Enable Application Insights for monitoring
- ✅ Implement rate limiting for HTTP trigger

## Integration with CI/CD

### GitHub Actions Example

```yaml
# In your CI/CD workflow
- name: Report Metrics to Function
  if: always()
  run: |
    curl -X POST https://func-anomaly-detector.azurewebsites.net/api/detect_anomalies \
      -H "Content-Type: application/json" \
      -d '{
        "build_id": "${{ github.run_id }}",
        "duration": "${{ steps.build.outputs.duration }}",
        "failure_rate": "${{ steps.test.outputs.failure_rate }}"
      }'
```

## Advanced Features

### Custom Metrics

Modify `query_pipeline_metrics()` to add:
- Test coverage percentage
- Code complexity
- Deployment frequency
- Mean time to recovery (MTTR)

### Custom Alerting Logic

Modify `send_teams_alert()` or `send_email_alert()` to:
- Add severity levels
- Include historical context
- Suggest remediation steps
- Create Azure DevOps work items

### Integration with Other Tools

- **Slack**: Replace Teams webhook with Slack webhook
- **PagerDuty**: Call PagerDuty API for critical anomalies
- **Jira**: Create tickets for recurring issues
- **Grafana**: Send metrics to Grafana for visualization

## Resources

- [Azure Functions Python Developer Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Azure Monitor Query API](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/api/overview)
- [Teams Incoming Webhooks](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook)
- [SendGrid API Documentation](https://docs.sendgrid.com/api-reference)

## Support

For issues or questions:
1. Check Application Insights logs
2. Review this documentation
3. Contact DevOps team
4. Create GitHub issue in this repository
