"""
Azure Function for CI/CD Pipeline Anomaly Detection and Alerting
Monitors GitHub Actions pipelines and sends alerts when anomalies are detected.
"""

import logging
import json
import os
from datetime import datetime, timedelta
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
import requests

# Configure logging
app = func.FunctionApp()


def query_pipeline_metrics(logger: logging.Logger) -> list:
    """
    Query Azure Monitor for recent GitHub Actions pipeline metrics.
    
    Args:
        logger: Azure Functions logger
        
    Returns:
        List of pipeline metrics
    """
    try:
        logger.info("Querying Azure Monitor for pipeline metrics")
        
        # Initialize Azure Monitor client
        credential = DefaultAzureCredential()
        logs_client = LogsQueryClient(credential)
        
        # Workspace ID from environment variable
        workspace_id = os.environ.get('LOG_ANALYTICS_WORKSPACE_ID')
        
        if not workspace_id:
            logger.warning("LOG_ANALYTICS_WORKSPACE_ID not set, using sample data")
            return get_sample_metrics()
        
        # Query for pipeline metrics from the last 5 minutes
        query = """
        let startTime = ago(5m);
        let endTime = now();
        ContainerInsights
        | where TimeGenerated between(startTime .. endTime)
        | where Name contains "github-runner"
        | summarize 
            duration = avg(todouble(DurationMs) / 1000),
            failure_rate = countif(ExitCode != 0) * 1.0 / count()
            by RunId = tostring(CorrelationId)
        | extend build_id = RunId
        | project build_id, duration, failure_rate
        """
        
        response = logs_client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=timedelta(minutes=5)
        )
        
        if response.status == LogsQueryStatus.SUCCESS:
            metrics = []
            for row in response.tables[0].rows:
                metrics.append({
                    'build_id': row[0],
                    'duration': float(row[1]) if row[1] else 300.0,
                    'failure_rate': float(row[2]) if row[2] else 0.0
                })
            
            logger.info(f"Retrieved {len(metrics)} pipeline metrics")
            return metrics
        else:
            logger.error(f"Query failed: {response.status}")
            return get_sample_metrics()
            
    except Exception as e:
        logger.error(f"Error querying metrics: {str(e)}")
        return get_sample_metrics()


def get_sample_metrics() -> list:
    """
    Generate sample metrics for testing when Azure Monitor is not available.
    
    Returns:
        List of sample pipeline metrics
    """
    import random
    
    metrics = []
    for i in range(5):
        # Occasionally inject an anomaly
        is_anomaly = random.random() < 0.2
        
        if is_anomaly:
            duration = random.uniform(800, 1200)  # Slow build
            failure_rate = random.uniform(0.3, 0.6)  # High failure rate
        else:
            duration = random.uniform(250, 350)  # Normal build
            failure_rate = random.uniform(0.0, 0.1)  # Low failure rate
        
        metrics.append({
            'build_id': f'build_{datetime.now().strftime("%Y%m%d%H%M%S")}_{i}',
            'duration': duration,
            'failure_rate': failure_rate
        })
    
    return metrics


def predict_anomalies(metrics: list, logger: logging.Logger) -> dict:
    """
    Call Azure ML endpoint to predict anomalies.
    
    Args:
        metrics: List of pipeline metrics
        logger: Azure Functions logger
        
    Returns:
        Dictionary with predictions
    """
    try:
        ml_endpoint_url = os.environ.get('ML_ENDPOINT_URL')
        ml_api_key = os.environ.get('ML_API_KEY')
        
        if not ml_endpoint_url:
            logger.warning("ML_ENDPOINT_URL not set, using mock predictions")
            return mock_predictions(metrics)
        
        logger.info(f"Calling ML endpoint: {ml_endpoint_url}")
        
        # Prepare request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {ml_api_key}' if ml_api_key else ''
        }
        
        payload = {
            'data': metrics
        }
        
        # Call ML endpoint
        response = requests.post(
            ml_endpoint_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        
        predictions = response.json()
        logger.info(f"Received predictions for {len(metrics)} builds")
        
        return predictions
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling ML endpoint: {str(e)}")
        return mock_predictions(metrics)
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {str(e)}")
        return mock_predictions(metrics)


def mock_predictions(metrics: list) -> dict:
    """
    Generate mock predictions for testing.
    
    Args:
        metrics: List of pipeline metrics
        
    Returns:
        Dictionary with mock predictions
    """
    predictions = []
    anomaly_scores = []
    build_ids = []
    
    for metric in metrics:
        # Simple rule-based mock: slow builds or high failure rates are anomalies
        is_anomaly = metric['duration'] > 600 or metric['failure_rate'] > 0.2
        
        predictions.append(is_anomaly)
        anomaly_scores.append(-0.5 if is_anomaly else 0.5)
        build_ids.append(metric['build_id'])
    
    return {
        'predictions': predictions,
        'anomaly_scores': anomaly_scores,
        'build_ids': build_ids
    }


def send_teams_alert(anomalies: list, logger: logging.Logger):
    """
    Send alert to Microsoft Teams via webhook.
    
    Args:
        anomalies: List of detected anomalies
        logger: Azure Functions logger
    """
    try:
        teams_webhook = os.environ.get('TEAMS_WEBHOOK_URL')
        
        if not teams_webhook:
            logger.warning("TEAMS_WEBHOOK_URL not set, skipping Teams notification")
            return
        
        logger.info(f"Sending Teams alert for {len(anomalies)} anomalies")
        
        # Build Teams message card
        facts = []
        for anomaly in anomalies:
            facts.append({
                "name": f"Build: {anomaly['build_id']}",
                "value": f"Duration: {anomaly['duration']:.1f}s | Failure Rate: {anomaly['failure_rate']:.1%}"
            })
        
        message = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": "FF0000",
            "summary": f"⚠️ {len(anomalies)} Pipeline Anomal{'y' if len(anomalies) == 1 else 'ies'} Detected",
            "sections": [{
                "activityTitle": "🚨 CI/CD Pipeline Anomaly Alert",
                "activitySubtitle": f"Detected at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                "facts": facts,
                "markdown": True
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name": "View in Azure ML",
                "targets": [{
                    "os": "default",
                    "uri": os.environ.get('ML_STUDIO_URL', 'https://ml.azure.com')
                }]
            }]
        }
        
        # Send to Teams
        response = requests.post(
            teams_webhook,
            headers={'Content-Type': 'application/json'},
            json=message,
            timeout=10
        )
        
        response.raise_for_status()
        logger.info("Teams alert sent successfully")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Teams alert: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending alert: {str(e)}")


def send_email_alert(anomalies: list, logger: logging.Logger):
    """
    Send alert email via SendGrid.
    
    Args:
        anomalies: List of detected anomalies
        logger: Azure Functions logger
    """
    try:
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        sendgrid_from_email = os.environ.get('SENDGRID_FROM_EMAIL')
        sendgrid_to_email = os.environ.get('SENDGRID_TO_EMAIL')
        
        if not all([sendgrid_api_key, sendgrid_from_email, sendgrid_to_email]):
            logger.warning("SendGrid config not complete, skipping email notification")
            return
        
        logger.info(f"Sending email alert for {len(anomalies)} anomalies")
        
        # Build email content
        anomaly_details = "\n".join([
            f"- Build: {a['build_id']}, Duration: {a['duration']:.1f}s, Failure Rate: {a['failure_rate']:.1%}"
            for a in anomalies
        ])
        
        email_data = {
            "personalizations": [{
                "to": [{"email": sendgrid_to_email}],
                "subject": f"⚠️ {len(anomalies)} Pipeline Anomal{'y' if len(anomalies) == 1 else 'ies'} Detected"
            }],
            "from": {"email": sendgrid_from_email},
            "content": [{
                "type": "text/plain",
                "value": f"""
CI/CD Pipeline Anomaly Alert

Detected {len(anomalies)} anomal{'y' if len(anomalies) == 1 else 'ies'} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Anomalies Detected:
{anomaly_details}

Please investigate these pipeline runs for potential issues.

This is an automated alert from the AI-Powered Anomaly Detection system.
                """
            }]
        }
        
        # Send via SendGrid API
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={
                'Authorization': f'Bearer {sendgrid_api_key}',
                'Content-Type': 'application/json'
            },
            json=email_data,
            timeout=10
        )
        
        response.raise_for_status()
        logger.info("Email alert sent successfully")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email alert: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")


@app.route(route="detect_anomalies", methods=["GET", "POST"])
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for manual anomaly detection.
    
    Args:
        req: HTTP request
        
    Returns:
        HTTP response with detection results
    """
    logging.info('HTTP trigger: Anomaly detection started')
    
    try:
        # Query metrics
        metrics = query_pipeline_metrics(logging)
        
        if not metrics:
            return func.HttpResponse(
                json.dumps({'message': 'No metrics available'}),
                status_code=200,
                mimetype='application/json'
            )
        
        # Predict anomalies
        predictions = predict_anomalies(metrics, logging)
        
        # Find anomalies
        anomalies = []
        for i, is_anomaly in enumerate(predictions['predictions']):
            if is_anomaly:
                anomalies.append({
                    'build_id': predictions['build_ids'][i],
                    'duration': metrics[i]['duration'],
                    'failure_rate': metrics[i]['failure_rate'],
                    'anomaly_score': predictions['anomaly_scores'][i]
                })
        
        # Send alerts if anomalies detected
        if anomalies:
            logging.warning(f"Detected {len(anomalies)} anomalies")
            send_teams_alert(anomalies, logging)
            send_email_alert(anomalies, logging)
        else:
            logging.info("No anomalies detected")
        
        # Return results
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics_analyzed': len(metrics),
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies
        }
        
        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logging.error(f"Error in HTTP trigger: {str(e)}")
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )


@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
def timer_trigger(timer: func.TimerRequest) -> None:
    """
    Timer trigger for automated anomaly detection every 5 minutes.
    
    Args:
        timer: Timer request context
    """
    logging.info('Timer trigger: Anomaly detection started')
    
    try:
        # Query metrics
        metrics = query_pipeline_metrics(logging)
        
        if not metrics:
            logging.info("No metrics available, skipping detection")
            return
        
        # Predict anomalies
        predictions = predict_anomalies(metrics, logging)
        
        # Find anomalies
        anomalies = []
        for i, is_anomaly in enumerate(predictions['predictions']):
            if is_anomaly:
                anomalies.append({
                    'build_id': predictions['build_ids'][i],
                    'duration': metrics[i]['duration'],
                    'failure_rate': metrics[i]['failure_rate'],
                    'anomaly_score': predictions['anomaly_scores'][i]
                })
        
        # Send alerts if anomalies detected
        if anomalies:
            logging.warning(f"Detected {len(anomalies)} anomalies")
            send_teams_alert(anomalies, logging)
            send_email_alert(anomalies, logging)
        else:
            logging.info("No anomalies detected")
        
        logging.info(f"Timer trigger completed: {len(metrics)} metrics analyzed, {len(anomalies)} anomalies found")
        
    except Exception as e:
        logging.error(f"Error in timer trigger: {str(e)}")


if __name__ == '__main__':
    # For local testing
    import sys
    
    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    logger = MockLogger()
    
    print("Testing anomaly detection...")
    metrics = query_pipeline_metrics(logger)
    predictions = predict_anomalies(metrics, logger)
    
    anomalies = []
    for i, is_anomaly in enumerate(predictions['predictions']):
        if is_anomaly:
            anomalies.append({
                'build_id': predictions['build_ids'][i],
                'duration': metrics[i]['duration'],
                'failure_rate': metrics[i]['failure_rate'],
                'anomaly_score': predictions['anomaly_scores'][i]
            })
    
    print(f"\nResults: {len(anomalies)} anomalies detected out of {len(metrics)} metrics")
    if anomalies:
        for anomaly in anomalies:
            print(f"  - {anomaly}")
