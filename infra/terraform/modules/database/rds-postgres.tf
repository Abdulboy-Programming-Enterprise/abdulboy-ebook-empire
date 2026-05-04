# =============================================================================
# DATABASE MODULE - RDS PostgreSQL Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# DB Subnet Group
# -----------------------------------------------------------------------------
resource "aws_db_subnet_group" "main" {
  name        = "abdulboy-ebook-${var.environment}-db-subnet-group"
  description = "Database subnet group for Abdulboy Ebook Empire"
  subnet_ids  = var.subnet_ids
  
  tags = merge(var.tags, {
    Name = "abdulboy-ebook-${var.environment}-db-subnet"
  })
}

# -----------------------------------------------------------------------------
# DB Parameter Group
# -----------------------------------------------------------------------------
resource "aws_db_parameter_group" "main" {
  name        = "abdulboy-ebook-${var.environment}-db-params"
  family      = "postgres15"
  description = "Custom parameter group for Abdulboy Ebook Empire"
  
  # Performance optimizations
  parameter {
    name  = "max_connections"
    value = "500"
  }
  
  parameter {
    name  = "shared_buffers"
    value = "131072" # 1GB in 8KB blocks
  }
  
  parameter {
    name  = "effective_cache_size"
    value = "393216" # 3GB in 8KB blocks
  }
  
  parameter {
    name  = "work_mem"
    value = "16384" # 16MB
  }
  
  parameter {
    name  = "maintenance_work_mem"
    value = "65536" # 64MB
  }
  
  parameter {
    name  = "random_page_cost"
    value = "1.1"
  }
  
  parameter {
    name  = "log_statement"
    value = "ddl"
  }
  
  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }
  
  parameter {
    name  = "log_checkpoints"
    value = "1"
  }
  
  parameter {
    name  = "log_connections"
    value = "1"
  }
  
  parameter {
    name  = "log_disconnections"
    value = "1"
  }
  
  parameter {
    name  = "log_lock_waits"
    value = "1"
  }
  
  parameter {
    name  = "log_temp_files"
    value = "1024"
  }
  
  parameter {
    name  = "log_autovacuum_min_duration"
    value = "0"
  }
  
  parameter {
    name         = "track_activity_query_size"
    value        = "4096"
    apply_method = "pending-reboot"
  }
  
  tags = merge(var.tags, {
    Name = "abdulboy-ebook-${var.environment}-db-params"
  })
}

# -----------------------------------------------------------------------------
# DB Option Group (for extensions)
# -----------------------------------------------------------------------------
resource "aws_db_option_group" "main" {
  name                 = "abdulboy-ebook-${var.environment}-db-options"
  engine_name          = "postgres"
  major_engine_version = "15"
  
  option {
    option_name = "pg_stat_statements"
  }
  
  tags = merge(var.tags, {
    Name = "abdulboy-ebook-${var.environment}-db-options"
  })
}

# -----------------------------------------------------------------------------
# RDS Instance
# -----------------------------------------------------------------------------
resource "aws_db_instance" "main" {
  identifier = "abdulboy-ebook-${var.environment}-db"
  
  # Database configuration
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = var.instance_class
  
  # Storage
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage != null ? var.max_allocated_storage : var.allocated_storage * 2
  storage_encrypted     = var.storage_encrypted
  storage_type          = var.storage_type
  
  # Database credentials
  db_name  = var.database_name
  username = var.database_user
  password = var.database_password
  
  # Networking
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_groups
  publicly_accessible    = false
  
  # High Availability
  multi_az = var.multi_az
  
  # Backup configuration
  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window
  
  # Monitoring
  monitoring_interval = var.environment == "prod" ? 60 : 0
  monitoring_role_arn = var.environment == "prod" ? aws_iam_role.rds_monitoring[0].arn : null
  
  # Performance insights
  performance_insights_enabled          = var.environment == "prod" ? true : false
  performance_insights_retention_period = var.environment == "prod" ? 7 : null
  
  # Deletion protection
  deletion_protection      = var.deletion_protection
  skip_final_snapshot      = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "abdulboy-ebook-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  # Parameter and option groups
  parameter_group_name = aws_db_parameter_group.main.name
  option_group_name    = aws_db_option_group.main.name
  
  # Additional settings
  auto_minor_version_upgrade = true
  allow_major_version_upgrade = false
  apply_immediately          = false
  copy_tags_to_snapshot      = true
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  tags = merge(var.tags, {
    Name = "abdulboy-ebook-${var.environment}-db"
  })
  
  lifecycle {
    ignore_changes = [
      # Prevent recreation when these change
      final_snapshot_identifier,
    ]
  }
}

# -----------------------------------------------------------------------------
# Read Replica (for production scaling)
# -----------------------------------------------------------------------------
resource "aws_db_instance" "replica" {
  count = var.environment == "prod" && var.read_replica_count > 0 ? var.read_replica_count : 0
  
  identifier = "abdulboy-ebook-${var.environment}-db-replica-${count.index + 1}"
  
  replicate_source_db = aws_db_instance.main.identifier
  instance_class      = var.read_replica_instance_class != null ? var.read_replica_instance_class : var.instance_class
  
  vpc_security_group_ids = var.security_groups
  publicly_accessible    = false
  
  backup_retention_period = 0
  storage_encrypted       = true
  monitoring_interval     = 60
  monitoring_role_arn     = aws_iam_role.rds_monitoring[0].arn
  
  tags = merge(var.tags, {
    Name = "abdulboy-ebook-${var.environment}-db-replica-${count.index + 1}"
  })
}

# -----------------------------------------------------------------------------
# IAM Role for Enhanced Monitoring
# -----------------------------------------------------------------------------
resource "aws_iam_role" "rds_monitoring" {
  count = var.environment == "prod" ? 1 : 0
  
  name = "abdulboy-ebook-${var.environment}-rds-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  count = var.environment == "prod" ? 1 : 0
  
  role       = aws_iam_role.rds_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms for Database
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_metric_alarm" "db_cpu" {
  count = var.environment == "prod" ? 1 : 0
  
  alarm_name          = "abdulboy-ebook-${var.environment}-db-cpu-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Database CPU utilization is high"
  alarm_actions       = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "db_connections" {
  count = var.environment == "prod" ? 1 : 0
  
  alarm_name          = "abdulboy-ebook-${var.environment}-db-connections-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 400
  alarm_description   = "Database connections are high"
  alarm_actions       = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "db_free_storage" {
  count = var.environment == "prod" ? 1 : 0
  
  alarm_name          = "abdulboy-ebook-${var.environment}-db-storage-alarm"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 10 * 1024 * 1024 * 1024 # 10GB
  alarm_description   = "Database free storage is low"
  alarm_actions       = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }
  
  tags = var.tags
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "endpoint" {
  value = aws_db_instance.main.endpoint
}

output "port" {
  value = aws_db_instance.main.port
}

output "database_name" {
  value = aws_db_instance.main.db_name
}

output "database_user" {
  value = aws_db_instance.main.username
  sensitive = true
}

output "instance_id" {
  value = aws_db_instance.main.id
}

output "replica_endpoints" {
  value = aws_db_instance.replica[*].endpoint
}

output "arn" {
  value = aws_db_instance.main.arn
}
