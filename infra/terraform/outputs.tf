# =============================================================================
# TERRAFORM OUTPUTS - Abdulboy Ebook Empire
# =============================================================================

# -----------------------------------------------------------------------------
# Networking Outputs
# -----------------------------------------------------------------------------
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

# -----------------------------------------------------------------------------
# EKS Outputs
# -----------------------------------------------------------------------------
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

# -----------------------------------------------------------------------------
# Database Outputs
# -----------------------------------------------------------------------------
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = module.rds.port
}

output "database_name" {
  description = "Database name"
  value       = module.rds.database_name
}

output "database_user" {
  description = "Database user"
  value       = module.rds.database_user
  sensitive   = true
}

output "database_password" {
  description = "Database password"
  value       = random_password.db_password.result
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Redis Outputs
# -----------------------------------------------------------------------------
output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.endpoint
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.redis.port
}

output "redis_password" {
  description = "Redis password"
  value       = random_password.redis_password.result
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Storage Outputs
# -----------------------------------------------------------------------------
output "s3_buckets" {
  description = "S3 bucket names"
  value       = module.s3_buckets.bucket_names
}

output "s3_bucket_arns" {
  description = "S3 bucket ARNs"
  value       = module.s3_buckets.bucket_arns
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront hosted zone ID"
  value       = aws_cloudfront_distribution.main.hosted_zone_id
}

# -----------------------------------------------------------------------------
# DNS Outputs
# -----------------------------------------------------------------------------
output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = data.aws_route53_zone.main.zone_id
}

output "domain_name" {
  description = "Domain name"
  value       = var.domain_name
}

# -----------------------------------------------------------------------------
# Application URLs
# -----------------------------------------------------------------------------
output "website_url" {
  description = "Website URL"
  value       = "https://${var.domain_name}"
}

output "api_url" {
  description = "API URL"
  value       = "https://api.${var.domain_name}"
}

output "admin_url" {
  description = "Admin URL"
  value       = "https://admin.${var.domain_name}"
}

output "grafana_url" {
  description = "Grafana URL"
  value       = var.enable_monitoring ? "https://monitoring.${var.domain_name}" : null
}

# -----------------------------------------------------------------------------
# Security Outputs (for secret management)
# -----------------------------------------------------------------------------
output "jwt_secret" {
  description = "JWT secret key"
  value       = var.jwt_secret != null ? var.jwt_secret : random_password.jwt_secret.result
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Configuration Output (for deployment scripts)
# -----------------------------------------------------------------------------
output "kubeconfig" {
  description = "Kubeconfig for EKS cluster"
  value       = module.eks.kubeconfig
  sensitive   = true
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}
