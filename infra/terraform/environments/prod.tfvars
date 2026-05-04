# =============================================================================
# PRODUCTION ENVIRONMENT VARIABLES
# =============================================================================

environment = "prod"

# VPC Configuration
vpc_cidr          = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
private_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnets    = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# EKS Node Groups
api_desired_capacity    = 5
api_max_capacity        = 20
api_min_capacity        = 5
worker_desired_capacity = 5
worker_max_capacity     = 30
worker_min_capacity     = 5

# Database Configuration
db_instance_class    = "db.r6g.large"  # Graviton2 for better price/performance
db_allocated_storage = 500
multi_az             = true
backup_retention_period = 30

# Redis Configuration
redis_node_type  = "cache.r6g.large"
redis_num_nodes  = 3  # 1 primary + 2 replicas

# Application URLs
domain_name = "abdulboy-ebook.com"

# Feature Flags
enable_monitoring = true

# Tags
tags = {
  Environment = "production"
  CostCenter  = "enterprise"
  Compliance  = "gdpr-pci"
}
