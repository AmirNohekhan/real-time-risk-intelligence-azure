variable "location" { type = string; default = "eastus2" }
variable "environment" { type = string; default = "dev"; validation { condition = contains(["dev", "staging", "prod"], var.environment); error_message = "environment must be dev, staging, or prod" } }
variable "project" { type = string; default = "rti" }
variable "tags" { type = map(string); default = { managed_by = "terraform"; workload = "risk-intelligence" } }

