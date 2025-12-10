terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  # Backend configuration for Azure Storage
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstatedevopsdelk"
    container_name       = "tfstate"
    key                  = "flask-app.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
  
  # Use OIDC authentication when running in GitHub Actions
  # These are set via environment variables (ARM_CLIENT_ID, ARM_SUBSCRIPTION_ID, ARM_TENANT_ID, ARM_USE_OIDC)
  use_oidc = true
}
