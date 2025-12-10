# ACR variables
variable "acr_name" {
  description = "Name of the Azure Container Registry to create"
  type        = string
  default     = "delekacr"
}

# Infrastructure variables
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "flask-app-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "westeurope"
}

variable "app_service_plan_name" {
  description = "Name of the App Service Plan"
  type        = string
  default     = "flask-app-plan"
}

variable "app_service_name" {
  description = "Name of the App Service (must be globally unique)"
  type        = string
  default     = "flask-app-delek-001"
}

variable "container_image_name" {
  description = "Name of the container image"
  type        = string
  default     = "flask-app"
}

variable "container_image_tag" {
  description = "Tag of the container image"
  type        = string
  default     = "latest"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "production"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "Production"
    ManagedBy   = "Terraform"
    Project     = "Flask-CI-CD"
  }
}

# Azure ML variables
variable "ml_workspace_name" {
  description = "Name of the Azure ML workspace"
  type        = string
  default     = "ml-workspace-anomaly-detection"
}

variable "ml_storage_account_name" {
  description = "Name of the storage account for ML workspace (lowercase, alphanumeric, 3-24 chars)"
  type        = string
  default     = "mlstorageanomalydet"
}

variable "ml_key_vault_name" {
  description = "Name of the Key Vault for ML workspace (3-24 chars)"
  type        = string
  default     = "mlkv-anomaly-det"
}

variable "ml_application_insights_name" {
  description = "Name of the Application Insights for ML workspace"
  type        = string
  default     = "ml-appinsights-anomaly"
}

# Azure Function variables
variable "function_app_name" {
  description = "Name of the Azure Function App"
  type        = string
  default     = "func-anomaly-detector"
}

variable "function_storage_account_name" {
  description = "Name of the storage account for Function App (lowercase, alphanumeric, 3-24 chars)"
  type        = string
  default     = "funcstorageanomalydet"
}

variable "function_app_service_plan_name" {
  description = "Name of the App Service Plan for Function App"
  type        = string
  default     = "func-plan-anomaly"
}

# Optional variables for Function App configuration
variable "ml_endpoint_url" {
  description = "Azure ML endpoint URL for anomaly detection"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ml_api_key" {
  description = "API key for Azure ML endpoint"
  type        = string
  default     = ""
  sensitive   = true
}

variable "teams_webhook_url" {
  description = "Microsoft Teams webhook URL for alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID for querying metrics"
  type        = string
  default     = ""
}

variable "sendgrid_api_key" {
  description = "SendGrid API key for email alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "sendgrid_from_email" {
  description = "Email address to send alerts from"
  type        = string
  default     = "alerts@example.com"
}

variable "sendgrid_to_email" {
  description = "Email address to send alerts to"
  type        = string
  default     = "devops@example.com"
}
