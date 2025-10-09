# Lambda function for Discord bot
resource "aws_lambda_function" "discord_bot" {
  filename         = "../dist/channelwright.zip"
  source_code_hash = filebase64sha256("../dist/channelwright.zip")
  function_name    = "${var.project_name}-bot-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT           = var.environment
      DYNAMODB_CAMPAIGNS_TABLE = aws_dynamodb_table.campaigns.name
      DYNAMODB_CONFIG_TABLE    = aws_dynamodb_table.bot_config.name
      DISCORD_APPLICATION_ID   = var.discord_application_id
      SSM_PARAMETER_PREFIX     = "/${var.project_name}/${var.environment}"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_iam_role_policy.lambda_ssm_policy,
  ]

  tags = {
    Name        = "${var.project_name}-bot-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Lambda function URL for Discord webhook
resource "aws_lambda_function_url" "discord_bot_url" {
  function_name      = aws_lambda_function.discord_bot.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "discord_bot_logs" {
  name              = "/aws/lambda/${aws_lambda_function.discord_bot.function_name}"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-bot-logs-${var.environment}"
    Environment = var.environment
    Project     = var.project_name
  }
}
