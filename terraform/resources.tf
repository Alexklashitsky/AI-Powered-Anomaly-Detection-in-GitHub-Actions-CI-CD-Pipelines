# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# Azure Container Registry
resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  
  tags = var.tags
}

# App Service Plan (Linux, Basic tier)
resource "azurerm_service_plan" "main" {
  name                = var.app_service_plan_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1" # Basic tier
  
  tags = var.tags
}

# Linux Web App (Container-based)
resource "azurerm_linux_web_app" "main" {
  name                = var.app_service_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id
  
  site_config {
    always_on = true
    
    application_stack {
      docker_image_name   = "${azurerm_container_registry.acr.login_server}/${var.container_image_name}:${var.container_image_tag}"
      docker_registry_url = "https://${azurerm_container_registry.acr.login_server}"
    }
    
    # Health check configuration
    health_check_path = "/health"
  }
  
  # Configure ACR credentials for pulling images
  # Using admin credentials by default (simpler, no additional permissions needed)
  # To use managed identity instead, uncomment the azurerm_role_assignment block at the bottom
  app_settings = {
    "DOCKER_REGISTRY_SERVER_URL"      = "https://${azurerm_container_registry.acr.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME" = azurerm_container_registry.acr.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD" = azurerm_container_registry.acr.admin_password
    "WEBSITES_PORT"                   = "8000"
    "ENVIRONMENT"                     = var.environment
  }
  
  # Enable HTTPS only
  https_only = true
  
  # Identity for managed identity (optional, for future use)
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Role assignment to allow App Service to pull from ACR using managed identity
# Note: This requires the service principal to have "User Access Administrator" or "Owner" role
# For now, we're using admin credentials (configured in app_settings above)
# Uncomment this block if you have the necessary permissions and want to use managed identity instead

# resource "azurerm_role_assignment" "acr_pull" {
#   scope                = azurerm_container_registry.acr.id
#   role_definition_name = "AcrPull"
#   principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
# }
