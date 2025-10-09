output "lambda_function_url" {
  description = "URL for Discord webhook"
  value       = aws_lambda_function_url.discord_bot_url.function_url
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.discord_bot.function_name
}

output "dynamodb_campaigns_table" {
  description = "Name of the campaigns DynamoDB table"
  value       = aws_dynamodb_table.campaigns.name
}

output "dynamodb_config_table" {
  description = "Name of the config DynamoDB table"
  value       = aws_dynamodb_table.bot_config.name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}
