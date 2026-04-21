# ─── Log Analytics ──────────────────────────────────────────────

resource "azurerm_log_analytics_workspace" "multi_agent" {
  name                = "log-multi-agent"
  location            = azurerm_resource_group.multi_agent.location
  resource_group_name = azurerm_resource_group.multi_agent.name
  sku                 = "PerGB2018"
  retention_in_days   = 7
}

# ─── Container Registry ────────────────────────────────────────

resource "azurerm_container_registry" "multi_agent" {
  name                = replace("acrmultiagent${var.resource_group_name}", "-", "")
  resource_group_name = azurerm_resource_group.multi_agent.name
  location            = azurerm_resource_group.multi_agent.location
  sku                 = "Standard"
  admin_enabled       = true
}

# ─── Container Apps Environment ────────────────────────────────

resource "azurerm_container_app_environment" "multi_agent" {
  name                       = "cae-multi-agent"
  location                   = azurerm_resource_group.multi_agent.location
  resource_group_name        = azurerm_resource_group.multi_agent.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.multi_agent.id
}

# ─── Backend Container App ─────────────────────────────────────

resource "azurerm_container_app" "backend" {
  name                         = "multi-agent-backend"
  container_app_environment_id = azurerm_container_app_environment.multi_agent.id
  resource_group_name          = azurerm_resource_group.multi_agent.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name   = "backend"
      image  = "${azurerm_container_registry.multi_agent.login_server}/multi-agent-backend:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "CLOUD_PROVIDER"
        value = "azure"
      }
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
    }

    min_replicas = 1
    max_replicas = 3
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8400
    transport                  = "http"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}
