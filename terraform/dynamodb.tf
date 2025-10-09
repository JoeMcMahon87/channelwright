# DynamoDB table for campaign tracking
resource "aws_dynamodb_table" "campaigns" {
  name           = "${var.project_name}-campaigns-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "guild_id"
  range_key      = "campaign_name"

  attribute {
    name = "guild_id"
    type = "S"
  }

  attribute {
    name = "campaign_name"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # GSI for querying campaigns by creation date
  global_secondary_index {
    name            = "CreatedAtIndex"
    hash_key        = "guild_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-campaigns-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# DynamoDB table for bot configuration
resource "aws_dynamodb_table" "bot_config" {
  name         = "${var.project_name}-config-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "config_key"

  attribute {
    name = "config_key"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-config-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}
