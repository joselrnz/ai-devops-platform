# Dev Environment - Main Configuration
# Orchestrates all modules for development environment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Uncomment to use S3 backend (recommended for team use)
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "mcp-server/dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# Local Variables
# -----------------------------------------------------------------------------
locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# -----------------------------------------------------------------------------
# VPC Module
# -----------------------------------------------------------------------------
module "vpc" {
  source = "../../modules/vpc"

  project_name                  = var.project_name
  vpc_cidr                      = var.vpc_cidr
  public_subnet_cidr            = var.public_subnet_cidr
  private_subnet_cidr           = var.private_subnet_cidr
  private_subnet_secondary_cidr = var.private_subnet_secondary_cidr
  availability_zone             = "${var.aws_region}a"
  availability_zone_secondary   = "${var.aws_region}b"
  allowed_ip                    = var.allowed_ip
  tags                          = local.tags
}

# -----------------------------------------------------------------------------
# Security Module
# -----------------------------------------------------------------------------
module "security" {
  source = "../../modules/security"

  project_name = var.project_name
  tags         = local.tags
}

# -----------------------------------------------------------------------------
# ECS Module
# -----------------------------------------------------------------------------
module "ecs" {
  source = "../../modules/ecs"

  project_name          = var.project_name
  environment           = var.environment
  subnet_id             = module.vpc.public_subnet_id
  security_group_id     = module.vpc.ecs_security_group_id
  instance_type         = var.ecs_instance_type
  desired_capacity      = var.ecs_desired_capacity
  min_size              = var.ecs_min_size
  max_size              = var.ecs_max_size
  execution_role_arn    = module.security.ecs_execution_role_arn
  task_role_arn         = module.security.ecs_task_role_arn
  container_image       = var.container_image
  task_cpu              = var.task_cpu
  task_memory           = var.task_memory
  service_desired_count = var.service_desired_count
  log_group_name        = module.security.app_log_group_name
  tags                  = local.tags
}

# -----------------------------------------------------------------------------
# RDS Module
# -----------------------------------------------------------------------------
module "rds" {
  source = "../../modules/rds"

  project_name             = var.project_name
  db_subnet_group_name     = module.vpc.db_subnet_group_name
  security_group_id        = module.vpc.rds_security_group_id
  instance_class           = var.rds_instance_class
  allocated_storage        = var.rds_allocated_storage
  max_allocated_storage    = var.rds_max_allocated_storage
  db_name                  = var.db_name
  db_username              = var.db_username
  backup_retention_period  = var.rds_backup_retention_period
  tags                     = local.tags
}
