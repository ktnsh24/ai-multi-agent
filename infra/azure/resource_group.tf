# ─── Resource Group ─────────────────────────────────────────────

resource "azurerm_resource_group" "multi_agent" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    project    = "ai-portfolio"
    service    = "ai-multi-agent"
    managed_by = "terraform"
  }
}
