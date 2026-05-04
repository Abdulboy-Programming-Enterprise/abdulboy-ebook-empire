# =============================================================================
# TERRAFORM MAIN CONFIGURATION - AWS Infrastructure
# =============================================================================
# Abdulboy Ebook Empire - Production Infrastructure as Code
# =============================================================================

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
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
  }
  
  # Remote state storage (S3 + DynamoDB for locking)
  backend "s3" {
    bucket         = "abdulboy-terraform-state"
    key            = "abdulboy-ebook-empire/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# =============================================================================
# Provider Configuration
# =============================================================================
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "AbdulboyEbookEmpire"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Team        = "Platform"
      CostCenter  = "EbookPlatform"
    }
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# =============================================================================
# Data Sources
# =============================================================================
data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# =============================================================================
# Random Generators
# =============================================================================
resource "random_password" "db_password" {
  length  = 24
  special = false
  numeric = true
  upper   = true
  lower   = true
}

resource "random_password" "redis_password" {
  length  = 24
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# =============================================================================
# VPC Module
# =============================================================================
module "vpc" {
  source = "./modules/networking"
  
  environment        = var.environment
  vpc_cidr          = var.vpc_cidr
  availability_zones = var.availability_zones
  private_subnets   = var.private_subnets
  public_subnets    = var.public_subnets
  
  tags = {
    Name = "abdulboy-ebook-${var.environment}"
  }
}

# =============================================================================
# EKS Cluster Module
# =============================================================================
module "eks" {
  source = "./modules/compute"
  
  cluster_name    = "abdulboy-ebook-${var.environment}"
  cluster_version = "1.28"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  
  node_groups = {
    api = {
      desired_capacity = var.api_desired_capacity
      max_capacity     = var.api_max_capacity
      min_capacity     = var.api_min_capacity
      instance_types   = ["t3.large", "t3.xlarge"]
      capacity_type    = "ON_DEMAND"
    }
    worker = {
      desired_capacity = var.worker_desired_capacity
      max_capacity     = var.worker_max_capacity
      min_capacity     = var.worker_min_capacity
      instance_types   = ["t3.medium", "t3.large"]
      capacity_type    = "SPOT"
    }
  }
  
  tags = {
    Environment = var.environment
  }
}

# =============================================================================
# RDS PostgreSQL Module
# =============================================================================
module "rds" {
  source = "./modules/database"
  
  environment       = var.environment
  database_name    = "abdulboy_ebook_empire"
  database_user    = "abdulboy_admin"
  database_password = random_password.db_password.result
  
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_encrypted = true
  
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  security_groups = [module.vpc.database_security_group_id]
  
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = var.environment == "prod" ? true : false
  
  tags = {
    Name = "abdulboy-ebook-db-${var.environment}"
  }
}

# =============================================================================
# ElastiCache Redis Module
# =============================================================================
module "redis" {
  source = "./modules/cache"
  
  environment    = var.environment
  node_type     = var.redis_node_type
  num_cache_nodes = var.redis_num_nodes
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  password = random_password.redis_password.result
  
  tags = {
    Name = "abdulboy-ebook-redis-${var.environment}"
  }
}

# =============================================================================
# S3 Buckets Module
# =============================================================================
module "s3_buckets" {
  source = "./modules/storage"
  
  environment = var.environment
  
  buckets = {
    uploads = {
      name     = "abdulboy-ebook-uploads-${random_string.suffix.result}"
      acl      = "private"
      versioning = true
      lifecycle_rules = [
        {
          id      = "transition-to-glacier"
          enabled = true
          transition = [
            {
              days          = 90
              storage_class = "GLACIER"
            }
          ]
        }
      ]
    }
    backups = {
      name     = "abdulboy-ebook-backups-${random_string.suffix.result}"
      acl      = "private"
      versioning = true
      lifecycle_rules = [
        {
          id      = "delete-old-backups"
          enabled = true
          expiration = {
            days = 30
          }
        }
      ]
    }
    static = {
      name     = "abdulboy-ebook-static-${random_string.suffix.result}"
      acl      = "public-read"
      website_config = {
        index_document = "index.html"
        error_document = "404.html"
      }
    }
  }
}

# =============================================================================
# CloudFront CDN
# =============================================================================
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled    = true
  price_class        = "PriceClass_100"
  default_root_object = "index.html"
  
  origin {
    domain_name = module.s3_buckets.bucket_domains["static"]
    origin_id   = "S3StaticOrigin"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }
  
  origin {
    domain_name = module.eks.cluster_endpoint
    origin_id   = "EKSAPIOrigin"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }
  
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3StaticOrigin"
    
    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl               = 0
    default_ttl           = 3600
    max_ttl               = 86400
    
    compress = true
  }
  
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
  
  tags = {
    Name = "abdulboy-ebook-cdn"
  }
}

resource "aws_cloudfront_origin_access_identity" "main" {
  comment = "Abdulboy Ebook Empire CDN Origin Access"
}

# =============================================================================
# Route53 DNS Configuration
# =============================================================================
data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

resource "aws_route53_record" "main" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  
  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  
  alias {
    name                   = module.eks.cluster_endpoint
    zone_id                = module.eks.cluster_hosted_zone_id
    evaluate_target_health = true
  }
}

# =============================================================================
# Outputs
# =============================================================================
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.endpoint
  sensitive   = true
}

output "s3_buckets" {
  description = "S3 bucket names"
  value       = module.s3_buckets.bucket_names
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}
