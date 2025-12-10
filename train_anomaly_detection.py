"""
Azure ML Anomaly Detection for CI/CD Pipeline Metrics
This script trains an Isolation Forest model to detect anomalies in GitHub Actions pipeline metrics.
"""

import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from pathlib import Path

# Azure ML SDK v2 imports
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model, ManagedOnlineEndpoint, ManagedOnlineDeployment, Environment, CodeConfiguration
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineAnomalyDetector:
    """Anomaly detection for CI/CD pipeline metrics using Isolation Forest."""
    
    def __init__(self, workspace_name: str, resource_group: str, subscription_id: str):
        """
        Initialize the anomaly detector.
        
        Args:
            workspace_name: Name of the Azure ML workspace
            resource_group: Azure resource group name
            subscription_id: Azure subscription ID
        """
        self.workspace_name = workspace_name
        self.resource_group = resource_group
        self.subscription_id = subscription_id
        self.model = None
        self.scaler = StandardScaler()
        self.ml_client = None
        
    def connect_to_workspace(self):
        """Connect to Azure ML workspace using DefaultAzureCredential."""
        try:
            logger.info(f"Connecting to Azure ML workspace: {self.workspace_name}")
            credential = DefaultAzureCredential()
            
            self.ml_client = MLClient(
                credential=credential,
                subscription_id=self.subscription_id,
                resource_group_name=self.resource_group,
                workspace_name=self.workspace_name
            )
            
            logger.info("Successfully connected to Azure ML workspace")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to workspace: {str(e)}")
            raise
    
    def load_data(self, csv_path: str = 'pipeline_metrics.csv') -> pd.DataFrame:
        """
        Load pipeline metrics data from CSV file.
        
        Args:
            csv_path: Path to CSV file containing metrics
            
        Returns:
            DataFrame with pipeline metrics
        """
        try:
            logger.info(f"Loading data from {csv_path}")
            
            if not os.path.exists(csv_path):
                logger.warning(f"File {csv_path} not found, generating sample data")
                return self._generate_sample_data()
            
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} records with columns: {df.columns.tolist()}")
            
            # Validate required columns
            required_cols = ['build_id', 'duration', 'failure_rate']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def _generate_sample_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Generate sample pipeline metrics data for demonstration.
        
        Args:
            n_samples: Number of sample records to generate
            
        Returns:
            DataFrame with synthetic pipeline metrics
        """
        logger.info(f"Generating {n_samples} sample records")
        
        np.random.seed(42)
        
        # Normal pipeline metrics
        normal_duration = np.random.normal(300, 50, int(n_samples * 0.95))  # ~5 minutes
        normal_failure_rate = np.random.beta(2, 50, int(n_samples * 0.95))  # Low failure rate
        
        # Anomalous metrics (5% of data)
        anomaly_duration = np.random.normal(900, 100, int(n_samples * 0.05))  # ~15 minutes (slow)
        anomaly_failure_rate = np.random.beta(10, 5, int(n_samples * 0.05))  # High failure rate
        
        # Combine normal and anomalous data
        duration = np.concatenate([normal_duration, anomaly_duration])
        failure_rate = np.concatenate([normal_failure_rate, anomaly_failure_rate])
        
        # Shuffle
        indices = np.random.permutation(n_samples)
        duration = duration[indices]
        failure_rate = failure_rate[indices]
        
        df = pd.DataFrame({
            'build_id': [f'build_{i:04d}' for i in range(n_samples)],
            'duration': duration,
            'failure_rate': failure_rate,
            'timestamp': pd.date_range(start='2025-01-01', periods=n_samples, freq='1H')
        })
        
        # Save sample data
        df.to_csv('pipeline_metrics.csv', index=False)
        logger.info("Sample data saved to pipeline_metrics.csv")
        
        return df
    
    def train_model(self, data: pd.DataFrame, contamination: float = 0.05):
        """
        Train Isolation Forest model for anomaly detection.
        
        Args:
            data: DataFrame with pipeline metrics
            contamination: Expected proportion of outliers in the dataset
        """
        try:
            logger.info("Training Isolation Forest model")
            
            # Select features for training
            feature_cols = ['duration', 'failure_rate']
            X = data[feature_cols].values
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.model = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100,
                max_samples='auto',
                verbose=1
            )
            
            self.model.fit(X_scaled)
            
            # Evaluate on training data
            predictions = self.model.predict(X_scaled)
            n_anomalies = np.sum(predictions == -1)
            
            logger.info(f"Model trained successfully")
            logger.info(f"Detected {n_anomalies} anomalies in training data ({n_anomalies/len(data)*100:.2f}%)")
            
            # Save model locally
            self._save_model_locally()
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    def _save_model_locally(self, output_dir: str = 'model'):
        """Save trained model and scaler locally."""
        try:
            Path(output_dir).mkdir(exist_ok=True)
            
            model_path = os.path.join(output_dir, 'isolation_forest_model.pkl')
            scaler_path = os.path.join(output_dir, 'scaler.pkl')
            
            joblib.dump(self.model, model_path)
            joblib.dump(self.scaler, scaler_path)
            
            logger.info(f"Model saved to {model_path}")
            logger.info(f"Scaler saved to {scaler_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def register_model(self, model_name: str = 'pipeline-anomaly-detector'):
        """
        Register the trained model in Azure ML.
        
        Args:
            model_name: Name for the registered model
        """
        try:
            logger.info(f"Registering model: {model_name}")
            
            model = Model(
                path='model',
                name=model_name,
                description='Isolation Forest model for CI/CD pipeline anomaly detection',
                tags={
                    'framework': 'sklearn',
                    'algorithm': 'isolation_forest',
                    'purpose': 'anomaly_detection'
                }
            )
            
            registered_model = self.ml_client.models.create_or_update(model)
            
            logger.info(f"Model registered successfully: {registered_model.name} (version {registered_model.version})")
            return registered_model
            
        except Exception as e:
            logger.error(f"Error registering model: {str(e)}")
            raise
    
    def deploy_model(self, model_name: str = 'pipeline-anomaly-detector', 
                     endpoint_name: str = 'anomaly-detection-endpoint'):
        """
        Deploy model as online endpoint with Azure Container Instances.
        
        Args:
            model_name: Name of the registered model
            endpoint_name: Name for the deployment endpoint
        """
        try:
            # Create or update endpoint
            endpoint = self._create_endpoint(endpoint_name)
            
            # Create deployment
            deployment = self._create_deployment(endpoint_name, model_name)
            
            logger.info(f"Model deployed successfully to endpoint: {endpoint_name}")
            logger.info(f"Scoring URI: {endpoint.scoring_uri}")
            
            return endpoint
            
        except Exception as e:
            logger.error(f"Error deploying model: {str(e)}")
            raise
    
    def _create_endpoint(self, endpoint_name: str) -> ManagedOnlineEndpoint:
        """Create or get existing online endpoint."""
        try:
            logger.info(f"Creating endpoint: {endpoint_name}")
            
            # Check if endpoint exists
            try:
                endpoint = self.ml_client.online_endpoints.get(endpoint_name)
                logger.info(f"Endpoint {endpoint_name} already exists")
                return endpoint
            except ResourceNotFoundError:
                pass
            
            # Create new endpoint
            endpoint = ManagedOnlineEndpoint(
                name=endpoint_name,
                description='Anomaly detection endpoint for CI/CD pipeline metrics',
                auth_mode='key',
                tags={'purpose': 'anomaly_detection', 'environment': 'production'}
            )
            
            endpoint = self.ml_client.online_endpoints.begin_create_or_update(endpoint).result()
            logger.info(f"Endpoint created: {endpoint_name}")
            
            return endpoint
            
        except Exception as e:
            logger.error(f"Error creating endpoint: {str(e)}")
            raise
    
    def _create_deployment(self, endpoint_name: str, model_name: str) -> ManagedOnlineDeployment:
        """Create deployment on the endpoint."""
        try:
            logger.info(f"Creating deployment for model: {model_name}")
            
            # Get latest model version
            model = self.ml_client.models.get(name=model_name, label='latest')
            
            # Create deployment
            deployment = ManagedOnlineDeployment(
                name='blue',
                endpoint_name=endpoint_name,
                model=model,
                instance_type='Standard_DS2_v2',
                instance_count=1,
                environment=self._get_environment(),
                code_configuration=CodeConfiguration(
                    code='scoring',
                    scoring_script='score.py'
                )
            )
            
            deployment = self.ml_client.online_deployments.begin_create_or_update(deployment).result()
            
            # Set traffic to 100% for this deployment
            endpoint = self.ml_client.online_endpoints.get(endpoint_name)
            endpoint.traffic = {'blue': 100}
            self.ml_client.online_endpoints.begin_create_or_update(endpoint).result()
            
            logger.info(f"Deployment created successfully")
            return deployment
            
        except Exception as e:
            logger.error(f"Error creating deployment: {str(e)}")
            raise
    
    def _get_environment(self) -> Environment:
        """Get or create the environment for deployment."""
        try:
            env = Environment(
                name='anomaly-detection-env',
                description='Environment for anomaly detection model',
                conda_file='environment.yml',
                image='mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest'
            )
            
            return env
            
        except Exception as e:
            logger.error(f"Error creating environment: {str(e)}")
            raise


def main():
    """Main execution function."""
    try:
        # Configuration (these should come from environment variables in production)
        WORKSPACE_NAME = os.getenv('AZURE_ML_WORKSPACE', 'ml-workspace-anomaly-detection')
        RESOURCE_GROUP = os.getenv('AZURE_RESOURCE_GROUP', 'flask-app-rg')
        SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID', 'your-subscription-id')
        
        logger.info("Starting Pipeline Anomaly Detection Training")
        
        # Initialize detector
        detector = PipelineAnomalyDetector(
            workspace_name=WORKSPACE_NAME,
            resource_group=RESOURCE_GROUP,
            subscription_id=SUBSCRIPTION_ID
        )
        
        # Connect to Azure ML workspace
        detector.connect_to_workspace()
        
        # Load data
        data = detector.load_data('pipeline_metrics.csv')
        
        # Train model
        detector.train_model(data, contamination=0.05)
        
        # Register model
        registered_model = detector.register_model('pipeline-anomaly-detector')
        
        # Deploy model (commented out for now - uncomment when ready to deploy)
        # detector.deploy_model('pipeline-anomaly-detector', 'anomaly-detection-endpoint')
        
        logger.info("Pipeline anomaly detection training completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise


if __name__ == '__main__':
    main()
