# ─── Redis Cache ───────────────────────────────────────────────

resource "azurerm_redis_cache" "multi_agent" {
  name                = "redis-multi-agent"
  location            = azurerm_resource_group.multi_agent.location
  resource_group_name = azurerm_resource_group.multi_agent.name
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"
  minimum_tls_version = "1.2"
}
