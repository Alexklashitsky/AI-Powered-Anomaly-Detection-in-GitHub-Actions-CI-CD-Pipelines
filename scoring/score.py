"""
Scoring script for the anomaly detection model deployment.
This script is used by Azure ML for real-time inference.
"""

import json
import joblib
import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init():
    """
    Initialize the model and scaler.
    This function is called when the container is initialized/started.
    """
    global model, scaler
    
    try:
        logger.info("Initializing model...")
        
        # Load the model and scaler
        model = joblib.load('model/isolation_forest_model.pkl')
        scaler = joblib.load('model/scaler.pkl')
        
        logger.info("Model initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing model: {str(e)}")
        raise


def run(raw_data):
    """
    Make predictions on input data.
    
    Args:
        raw_data: JSON string with pipeline metrics
        
    Returns:
        JSON string with predictions
    """
    try:
        logger.info("Processing request...")
        
        # Parse input data
        data = json.loads(raw_data)
        
        # Convert to DataFrame
        df = pd.DataFrame(data['data'])
        
        # Extract features
        feature_cols = ['duration', 'failure_rate']
        X = df[feature_cols].values
        
        # Scale features
        X_scaled = scaler.transform(X)
        
        # Make predictions
        predictions = model.predict(X_scaled)
        anomaly_scores = model.score_samples(X_scaled)
        
        # Convert predictions (-1 for anomaly, 1 for normal)
        is_anomaly = (predictions == -1).tolist()
        
        # Prepare response
        response = {
            'predictions': is_anomaly,
            'anomaly_scores': anomaly_scores.tolist(),
            'build_ids': df.get('build_id', [f'build_{i}' for i in range(len(df))]).tolist()
        }
        
        logger.info(f"Processed {len(df)} records, found {sum(is_anomaly)} anomalies")
        
        return json.dumps(response)
        
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        return json.dumps({'error': str(e)})
