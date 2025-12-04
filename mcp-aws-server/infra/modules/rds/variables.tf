# RDS Module Variables

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
}

variable "db_subnet_group_name" {
  description = "Name of the DB subnet group"
  type        = string
}

variable "security_group_id" {
  description = "ID of the security group for RDS"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # Free tier eligible
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20 # Free tier allows up to 20GB
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage in GB (for autoscaling)"
  type        = number
  default     = 20 # Keep at 20 for free tier
}

variable "db_name" {
  description = "Name of the database to create"
  type        = string
  default     = "mcpdb"
}

variable "db_username" {
  description = "Master username for the database"
  type        = string
  default     = "mcpadmin"
}

variable "backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
