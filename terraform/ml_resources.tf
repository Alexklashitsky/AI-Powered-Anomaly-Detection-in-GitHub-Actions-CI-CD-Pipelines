# Azure Machine Learning Workspace and Dependencies

# Application Insights for ML Workspace
resource "azurerm_application_insights" "ml" {
  name                = var.ml_application_insights_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  
  tags = var.tags
}

# Key Vault for ML Workspace
resource "azurerm_key_vault" "ml" {
  name                        = var.ml_key_vault_name
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "standard"
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  
  tags = var.tags
}

# Storage Account for ML Workspace
resource "azurerm_storage_account" "ml" {
  name                     = var.ml_storage_account_name
  location                 = azurerm_resource_group.main.location
  resource_group_name      = azurerm_resource_group.main.name
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  tags = var.tags
}

# Azure Machine Learning Workspace
resource "azurerm_machine_learning_workspace" "main" {
  name                    = var.ml_workspace_name
  location                = azurerm_resource_group.main.location
  resource_group_name     = azurerm_resource_group.main.name
  application_insights_id = azurerm_application_insights.ml.id
  key_vault_id            = azurerm_key_vault.ml.id
  storage_account_id      = azurerm_storage_account.ml.id
  container_registry_id   = azurerm_container_registry.acr.id
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = merge(var.tags, {
    Purpose = "Anomaly Detection for CI/CD Pipelines"
  })
}

# Data source to get current Azure config
data "azurerm_client_config" "current" {}

# Grant ML Workspace access to Key Vault
resource "azurerm_key_vault_access_policy" "ml_workspace" {
  key_vault_id = azurerm_key_vault.ml.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_machine_learning_workspace.main.identity[0].principal_id
  
  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete"
  ]
  
  key_permissions = [
    "Get",
    "List",
    "Create",
    "Delete"
  ]
}

# Grant ML Workspace access to Storage Account
resource "azurerm_role_assignment" "ml_storage_blob_contributor" {
  scope                = azurerm_storage_account.ml.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_machine_learning_workspace.main.identity[0].principal_id
}

# Grant ML Workspace access to ACR
resource "azurerm_role_assignment" "ml_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_machine_learning_workspace.main.identity[0].principal_id
}
