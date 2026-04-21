variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "development"
}

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
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
