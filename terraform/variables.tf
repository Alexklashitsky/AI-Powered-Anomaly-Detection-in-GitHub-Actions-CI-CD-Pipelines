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
  description = "Name of the App Service"
  type        = string
  default     = "flask-app-service"
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
