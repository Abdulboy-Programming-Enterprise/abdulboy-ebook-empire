# =============================================================================
# STORAGE MODULE - S3 Buckets Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# S3 Buckets (Dynamic)
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "main" {
  for_each = var.buckets
  
  bucket = each.value.name
  tags   = merge(var.tags, { Name = each.value.name })
}

# -----------------------------------------------------------------------------
# Bucket ACLs
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_acl" "main" {
  for_each = var.buckets
  
  bucket = aws_s3_bucket.main[each.key].id
  acl    = each.value.acl
}

# -----------------------------------------------------------------------------
# Bucket Versioning
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_versioning" "main" {
  for_each = {
    for k, v in var.buckets : k => v
    if v.versioning == true
  }
  
  bucket = aws_s3_bucket.main[each.key].id
  versioning_configuration {
    status = "Enabled"
  }
}

# -----------------------------------------------------------------------------
# Bucket Encryption (SSE-S3)
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  for_each = var.buckets
  
  bucket = aws_s3_bucket.main[each.key].id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# -----------------------------------------------------------------------------
# Bucket Public Access Block
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_public_access_block" "main" {
  for_each = var.buckets
  
  bucket = aws_s3_bucket.main[each.key].id
  
  block_public_acls       = each.value.acl != "public-read" ? true : false
  block_public_policy     = each.value.acl != "public-read" ? true : false
  ignore_public_acls      = each.value.acl != "public-read" ? true : false
  restrict_public_buckets = each.value.acl != "public-read" ? true : false
}

# -----------------------------------------------------------------------------
# Bucket Policy for Public Read (if configured)
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_policy" "public_read" {
  for_each = {
    for k, v in var.buckets : k => v
    if v.acl == "public-read"
  }
  
  bucket = aws_s3_bucket.main[each.key].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.main[each.key].arn}/*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Bucket CORS Configuration
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_cors_configuration" "main" {
  for_each = var.buckets
  
  bucket = aws_s3_bucket.main[each.key].id
  
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = var.cors_allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# -----------------------------------------------------------------------------
# Lifecycle Rules
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  for_each = {
    for k, v in var.buckets : k => v
    if v.lifecycle_rules != null
  }
  
  bucket = aws_s3_bucket.main[each.key].id
  
  dynamic "rule" {
    for_each = each.value.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"
      
      dynamic "transition" {
        for_each = rule.value.transition != null ? rule.value.transition : []
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }
      
      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days = expiration.value.days
        }
      }
    }
  }
}

# -----------------------------------------------------------------------------
# Website Configuration (for static hosting)
# -----------------------------------------------------------------------------
resource "aws_s3_bucket_website_configuration" "main" {
  for_each = {
    for k, v in var.buckets : k => v
    if v.website_config != null
  }
  
  bucket = aws_s3_bucket.main[each.key].id
  
  index_document {
    suffix = each.value.website_config.index_document
  }
  
  error_document {
    key = each.value.website_config.error_document
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "bucket_names" {
  value = {
    for k, v in aws_s3_bucket.main : k => v.bucket
  }
}

output "bucket_arns" {
  value = {
    for k, v in aws_s3_bucket.main : k => v.arn
  }
}

output "bucket_domains" {
  value = {
    for k, v in aws_s3_bucket.main : k => "s3-${var.region}.amazonaws.com/${v.bucket}"
  }
}

output "bucket_website_endpoints" {
  value = {
    for k, v in aws_s3_bucket_website_configuration.main : k => v.website_endpoint
  }
}
