# =============================================================================
# STAGING ENVIRONMENT VARIABLES
# =============================================================================

environment = "staging"

# VPC Configuration
vpc_cidr          = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
private_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnets    = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# EKS Node Groups
api_desired_capacity    = 3
api_max_capacity        = 10
api_min_capacity        = 3
worker_desired_capacity = 2
worker_max_capacity     = 10
worker_min_capacity     = 2

# Database Configuration
db_instance_class    = "db.t3.large"
db_allocated_storage = 100
multi_az             = true
backup_retention_period = 30

# Redis Configuration
redis_node_type  = "cache.t3.medium"
redis_num_nodes  = 2

# Application URLs
domain_name = "staging.abdulboy-ebook.com"

# Feature Flags
enable_monitoring = true

# Tags
tags = {
  Environment = "staging"
  CostCenter  = "platform"
}
