# Systems Manager Parameter Store for secure configuration
resource "aws_ssm_parameter" "discord_bot_token" {
  name  = "/${var.project_name}/${var.environment}/discord/bot_token"
  type  = "SecureString"
  value = var.discord_bot_token

  tags = {
    Name        = "${var.project_name}-discord-bot-token-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ssm_parameter" "discord_application_id" {
  name  = "/${var.project_name}/${var.environment}/discord/application_id"
  type  = "String"
  value = var.discord_application_id

  tags = {
    Name        = "${var.project_name}-discord-app-id-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}
