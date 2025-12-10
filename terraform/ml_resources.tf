# Azure Machine Learning Workspace and Dependencies

# Log Analytics Workspace for Application Insights
resource "azurerm_log_analytics_workspace" "ml" {
  name                = "${var.ml_application_insights_name}-law"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  
  tags = var.tags
}

# Application Insights for ML Workspace
resource "azurerm_application_insights" "ml" {
  name                = var.ml_application_insights_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.ml.id
  
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

# Note: Access policies and role assignments commented out - requires special permissions
# These are automatically created by Azure ML Workspace or can be created manually
# 
# Manual commands to run after deployment (if needed):
# $ML_PRINCIPAL_ID = (az ml workspace show --name <workspace-name> --resource-group flask-app-rg --query identity.principalId -o tsv)
# $STORAGE_ID = (az storage account show --name <storage-name> --resource-group flask-app-rg --query id -o tsv)
# $ACR_ID = (az acr show --name <acr-name> --resource-group flask-app-rg --query id -o tsv)
# az role assignment create --assignee $ML_PRINCIPAL_ID --role "Storage Blob Data Contributor" --scope $STORAGE_ID
# az role assignment create --assignee $ML_PRINCIPAL_ID --role "AcrPull" --scope $ACR_ID

# Uncomment these if your service principal has User Access Administrator role:
# resource "azurerm_key_vault_access_policy" "ml_workspace" {
#   key_vault_id = azurerm_key_vault.ml.id
#   tenant_id    = data.azurerm_client_config.current.tenant_id
#   object_id    = azurerm_machine_learning_workspace.main.identity[0].principal_id
#   
#   secret_permissions = [
#     "Get",
#     "List",
#     "Set",
#     "Delete"
#   ]
#   
#   key_permissions = [
#     "Get",
#     "List",
#     "Create",
#     "Delete"
#   ]
# }
# 
# resource "azurerm_role_assignment" "ml_storage_blob_contributor" {
#   scope                = azurerm_storage_account.ml.id
#   role_definition_name = "Storage Blob Data Contributor"
#   principal_id         = azurerm_machine_learning_workspace.main.identity[0].principal_id
# }
# 
# resource "azurerm_role_assignment" "ml_acr_pull" {
#   scope                = azurerm_container_registry.acr.id
#   role_definition_name = "AcrPull"
#   principal_id         = azurerm_machine_learning_workspace.main.identity[0].principal_id
# }
