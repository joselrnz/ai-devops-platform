# VPC Module Variables

variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
}

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
  description = "CIDR block for the secondary private subnet (required for RDS)"
  type        = string
  default     = "10.0.3.0/24"
}

variable "availability_zone" {
  description = "Primary availability zone"
  type        = string
}

variable "availability_zone_secondary" {
  description = "Secondary availability zone (for RDS multi-AZ support)"
  type        = string
}

variable "allowed_ip" {
  description = "Your public IP address with CIDR notation (e.g., 1.2.3.4/32)"
  type        = string

  validation {
    condition     = can(cidrhost(var.allowed_ip, 0))
    error_message = "The allowed_ip must be a valid CIDR notation (e.g., 1.2.3.4/32)."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
