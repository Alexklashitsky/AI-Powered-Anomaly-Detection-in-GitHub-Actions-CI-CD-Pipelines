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
  
  subscription_id = var.subscription_id
  client_id       = var.client_id
  client_secret   = var.client_secret
  tenant_id       = var.tenant_id
}
