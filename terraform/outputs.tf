# Resource Group outputs
output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "resource_group_location" {
  description = "Location of the resource group"
  value       = azurerm_resource_group.main.location
}

# App Service outputs
output "app_service_name" {
  description = "Name of the App Service"
  value       = azurerm_linux_web_app.main.name
}

output "app_service_default_hostname" {
  description = "Default hostname of the App Service"
  value       = azurerm_linux_web_app.main.default_hostname
}

output "app_service_url" {
  description = "Full URL of the App Service"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "app_service_id" {
  description = "ID of the App Service"
  value       = azurerm_linux_web_app.main.id
}

# App Service Plan outputs
output "app_service_plan_id" {
  description = "ID of the App Service Plan"
  value       = azurerm_service_plan.main.id
}

# ACR outputs
output "acr_login_server" {
  description = "Login server URL of the Azure Container Registry"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_name" {
  description = "Name of the Azure Container Registry"
  value       = azurerm_container_registry.acr.name
}

output "acr_id" {
  description = "ID of the Azure Container Registry"
  value       = azurerm_container_registry.acr.id
}

output "acr_admin_username" {
  description = "Admin username for ACR"
  value       = azurerm_container_registry.acr.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "Admin password for ACR"
  value       = azurerm_container_registry.acr.admin_password
  sensitive   = true
}

# Managed Identity outputs
output "app_service_principal_id" {
  description = "Principal ID of the App Service managed identity"
  value       = azurerm_linux_web_app.main.identity[0].principal_id
}

output "app_service_tenant_id" {
  description = "Tenant ID of the App Service managed identity"
  value       = azurerm_linux_web_app.main.identity[0].tenant_id
}

# Azure ML outputs
output "ml_workspace_id" {
  description = "ID of the Azure ML workspace"
  value       = azurerm_machine_learning_workspace.main.id
}

output "ml_workspace_name" {
  description = "Name of the Azure ML workspace"
  value       = azurerm_machine_learning_workspace.main.name
}

output "ml_workspace_discovery_url" {
  description = "Discovery URL of the Azure ML workspace"
  value       = azurerm_machine_learning_workspace.main.discovery_url
}

output "ml_storage_account_name" {
  description = "Name of the ML storage account"
  value       = azurerm_storage_account.ml.name
}

output "ml_key_vault_name" {
  description = "Name of the ML Key Vault"
  value       = azurerm_key_vault.ml.name
}

output "ml_application_insights_name" {
  description = "Name of the ML Application Insights"
  value       = azurerm_application_insights.ml.name
}

# Azure Function outputs
output "function_app_name" {
  description = "Name of the Azure Function App"
  value       = azurerm_linux_function_app.anomaly_detector.name
}

output "function_app_url" {
  description = "Default hostname of the Function App"
  value       = "https://${azurerm_linux_function_app.anomaly_detector.default_hostname}"
}

output "function_app_id" {
  description = "ID of the Function App"
  value       = azurerm_linux_function_app.anomaly_detector.id
}

output "function_app_principal_id" {
  description = "Principal ID of the Function App managed identity"
  value       = azurerm_linux_function_app.anomaly_detector.identity[0].principal_id
}
