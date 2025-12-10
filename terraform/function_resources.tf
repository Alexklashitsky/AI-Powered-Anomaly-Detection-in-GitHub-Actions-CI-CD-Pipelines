# Azure Function for Anomaly Detection and Alerting

# Storage Account for Azure Function
resource "azurerm_storage_account" "function" {
  name                     = var.function_storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  tags = var.tags
}

# App Service Plan for Function App (Linux Basic plan)
resource "azurerm_service_plan" "function" {
  name                = var.function_app_service_plan_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1"  # Basic tier (more reliable than Consumption)
  
  tags = var.tags
}

# Linux Function App
resource "azurerm_linux_function_app" "anomaly_detector" {
  name                = var.function_app_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.function.id
  
  storage_account_name       = azurerm_storage_account.function.name
  storage_account_access_key = azurerm_storage_account.function.primary_access_key
  
  site_config {
    application_stack {
      python_version = "3.11"
    }
    
    application_insights_connection_string = azurerm_application_insights.ml.connection_string
    application_insights_key               = azurerm_application_insights.ml.instrumentation_key
  }
  
  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"       = "python"
    "ML_ENDPOINT_URL"                = var.ml_endpoint_url
    "ML_API_KEY"                     = var.ml_api_key
    "TEAMS_WEBHOOK_URL"              = var.teams_webhook_url
    "LOG_ANALYTICS_WORKSPACE_ID"     = var.log_analytics_workspace_id
    "SENDGRID_API_KEY"               = var.sendgrid_api_key
    "SENDGRID_FROM_EMAIL"            = var.sendgrid_from_email
    "SENDGRID_TO_EMAIL"              = var.sendgrid_to_email
    "ML_STUDIO_URL"                  = "https://ml.azure.com"
    "WEBSITE_RUN_FROM_PACKAGE"       = "1"
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  https_only = true
  
  tags = merge(var.tags, {
    Purpose = "Anomaly Detection and Alerting"
  })
}

# Grant Function App access to ML Workspace
resource "azurerm_role_assignment" "function_ml_reader" {
  scope                = azurerm_machine_learning_workspace.main.id
  role_definition_name = "Reader"
  principal_id         = azurerm_linux_function_app.anomaly_detector.identity[0].principal_id
}

# Grant Function App access to Monitor
resource "azurerm_role_assignment" "function_monitoring_reader" {
  scope                = azurerm_resource_group.main.id
  role_definition_name = "Monitoring Reader"
  principal_id         = azurerm_linux_function_app.anomaly_detector.identity[0].principal_id
}
