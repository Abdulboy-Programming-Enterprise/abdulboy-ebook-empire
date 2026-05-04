# =============================================================================
# TERRAFORM VARIABLES - Abdulboy Ebook Empire
# =============================================================================

# -----------------------------------------------------------------------------
# Environment Configuration
# -----------------------------------------------------------------------------
variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "abdulboy-ebook.com"
}

# -----------------------------------------------------------------------------
# VPC Configuration
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnets" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# -----------------------------------------------------------------------------
# EKS Configuration
# -----------------------------------------------------------------------------
variable "api_desired_capacity" {
  description = "API node group desired capacity"
  type        = number
  default     = 3
}

variable "api_max_capacity" {
  description = "API node group max capacity"
  type        = number
  default     = 10
}

variable "api_min_capacity" {
  description = "API node group min capacity"
  type        = number
  default     = 3
}

variable "worker_desired_capacity" {
  description = "Worker node group desired capacity"
  type        = number
  default     = 2
}

variable "worker_max_capacity" {
  description = "Worker node group max capacity"
  type        = number
  default     = 20
}

variable "worker_min_capacity" {
  description = "Worker node group min capacity"
  type        = number
  default     = 2
}

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.large"
  
  validation {
    condition     = can(regex("^db\\.", var.db_instance_class))
    error_message = "Instance class must start with 'db.'"
  }
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

# -----------------------------------------------------------------------------
# Redis Configuration
# -----------------------------------------------------------------------------
variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 1
}

# -----------------------------------------------------------------------------
# Application Variables
# -----------------------------------------------------------------------------
variable "app_version" {
  description = "Application version"
  type        = string
  default     = "1.0.0"
}

variable "jwt_secret" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
  default     = null
}

variable "stripe_secret_key" {
  description = "Stripe secret key"
  type        = string
  sensitive   = true
  default     = null
}

variable "stripe_public_key" {
  description = "Stripe public key"
  type        = string
  default     = null
}

variable "opay_secret_key" {
  description = "OPay secret key"
  type        = string
  sensitive   = true
  default     = null
}

variable "opay_merchant_id" {
  description = "OPay merchant ID"
  type        = string
  default     = null
}

variable "sendgrid_api_key" {
  description = "SendGrid API key"
  type        = string
  sensitive   = true
  default     = null
}

variable "sentry_dsn" {
  description = "Sentry DSN"
  type        = string
  sensitive   = true
  default     = null
}

# -----------------------------------------------------------------------------
# Monitoring Variables
# -----------------------------------------------------------------------------
variable "enable_monitoring" {
  description = "Enable monitoring stack"
  type        = bool
  default     = true
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
  default     = null
}

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "AbdulboyEbookEmpire"
    ManagedBy   = "Terraform"
    Team        = "Platform"
  }
}
