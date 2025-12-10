# Data source for existing Azure Container Registry
data "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = var.acr_resource_group
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
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
      docker_image_name   = "${data.azurerm_container_registry.acr.login_server}/${var.container_image_name}:${var.container_image_tag}"
      docker_registry_url = "https://${data.azurerm_container_registry.acr.login_server}"
    }
    
    # Health check configuration
    health_check_path = "/health"
  }
  
  # Configure ACR credentials for pulling images
  app_settings = {
    "DOCKER_REGISTRY_SERVER_URL"      = "https://${data.azurerm_container_registry.acr.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME" = data.azurerm_container_registry.acr.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD" = data.azurerm_container_registry.acr.admin_password
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
resource "azurerm_role_assignment" "acr_pull" {
  scope                = data.azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}
