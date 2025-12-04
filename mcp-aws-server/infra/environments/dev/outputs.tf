# Dev Environment Outputs

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_id" {
  description = "ID of the public subnet"
  value       = module.vpc.public_subnet_id
}

# -----------------------------------------------------------------------------
# ECS
# -----------------------------------------------------------------------------
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.ecs.service_name
}

# -----------------------------------------------------------------------------
# RDS
# -----------------------------------------------------------------------------
output "rds_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = module.rds.db_endpoint
}

output "rds_address" {
  description = "Address of the RDS instance"
  value       = module.rds.db_address
}

output "rds_credentials_secret_arn" {
  description = "ARN of the Secrets Manager secret with DB credentials"
  value       = module.rds.db_credentials_secret_arn
}

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
output "audit_log_group" {
  description = "CloudWatch log group for audit logs"
  value       = module.security.audit_log_group_name
}

output "app_log_group" {
  description = "CloudWatch log group for application logs"
  value       = module.security.app_log_group_name
}

# -----------------------------------------------------------------------------
# Connection Info
# -----------------------------------------------------------------------------
output "connection_info" {
  description = "Information for connecting to the infrastructure"
  value = {
    note          = "SSH and app access restricted to allowed_ip only"
    ecs_cluster   = module.ecs.cluster_name
    rds_endpoint  = module.rds.db_endpoint
    logs_group    = module.security.app_log_group_name
  }
}
