# ─── Outputs ────────────────────────────────────────────────────

output "container_app_url" {
  description = "Backend Container App URL"
  value       = azurerm_container_app.backend.ingress[0].fqdn
}

output "redis_hostname" {
  description = "Redis Cache hostname"
  value       = azurerm_redis_cache.multi_agent.hostname
}
