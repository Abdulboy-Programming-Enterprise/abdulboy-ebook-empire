# =============================================================================
# DEVELOPMENT ENVIRONMENT VARIABLES
# =============================================================================

environment = "dev"

# VPC Configuration
vpc_cidr          = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
private_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnets    = ["10.0.101.0/24", "10.0.102.0/24"]

# EKS Node Groups
api_desired_capacity    = 2
api_max_capacity        = 5
api_min_capacity        = 2
worker_desired_capacity = 1
worker_max_capacity     = 3
worker_min_capacity     = 1

# Database Configuration
db_instance_class    = "db.t3.micro"
db_allocated_storage = 20
multi_az             = false
backup_retention_period = 7

# Redis Configuration
redis_node_type  = "cache.t3.micro"
redis_num_nodes  = 1

# Application URLs
domain_name = "dev.abdulboy-ebook.com"

# Feature Flags
enable_monitoring = true

# Sensitive variables (should be set via environment or vault)
# jwt_secret = ""  # Set via environment variable TF_VAR_jwt_secret

# Tags
tags = {
  Environment = "development"
  CostCenter  = "engineering"
  AutoOff     = "true"
}
