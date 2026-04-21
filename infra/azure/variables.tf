variable "resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = "rg-multi-agent"
}

variable "location" {
  description = "Azure location"
  type        = string
  default     = "westeurope"
}

# --- Cost Controller ---

variable "cost_limit_eur" {
  description = "Monthly budget limit in EUR — resources are killed when exceeded"
  type        = number
  default     = 5
}

variable "alert_email" {
  description = "Email address for budget alerts (80% warning + 100% kill notification)"
  type        = string
}
