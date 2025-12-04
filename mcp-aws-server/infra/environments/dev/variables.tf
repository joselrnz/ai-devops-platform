# Dev Environment Variables

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "mcp-server"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
variable "allowed_ip" {
  description = "Your public IP address with CIDR notation (e.g., 1.2.3.4/32)"
  type        = string

  validation {
    condition     = can(cidrhost(var.allowed_ip, 0))
    error_message = "The allowed_ip must be a valid CIDR notation (e.g., 1.2.3.4/32)."
  }
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for the private subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_secondary_cidr" {
  description = "CIDR block for the secondary private subnet"
  type        = string
  default     = "10.0.3.0/24"
}

# -----------------------------------------------------------------------------
# ECS
# -----------------------------------------------------------------------------
variable "ecs_instance_type" {
  description = "EC2 instance type for ECS"
  type        = string
  default     = "t2.micro" # Free tier
}

variable "ecs_desired_capacity" {
  description = "Desired number of EC2 instances"
  type        = number
  default     = 1
}

variable "ecs_min_size" {
  description = "Minimum number of EC2 instances"
  type        = number
  default     = 1
}

variable "ecs_max_size" {
  description = "Maximum number of EC2 instances"
  type        = number
  default     = 1 # Keep at 1 for free tier
}

variable "container_image" {
  description = "Docker image for the MCP server"
  type        = string
  default     = "python:3.11-slim"
}

variable "task_cpu" {
  description = "CPU units for the task"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memory for the task in MB"
  type        = number
  default     = 512
}

variable "service_desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

# -----------------------------------------------------------------------------
# RDS
# -----------------------------------------------------------------------------
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # Free tier
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20 # Free tier max
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage in GB"
  type        = number
  default     = 20 # Keep at 20 for free tier
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "mcpdb"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "mcpadmin"
}

variable "rds_backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}
