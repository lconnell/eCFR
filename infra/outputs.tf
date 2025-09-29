output "api_base_url" {
  description = "Base URL for the API Gateway HTTP API"
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "s3_bucket" {
  description = "S3 bucket name for data storage"
  value       = aws_s3_bucket.data.bucket
}

output "s3_data_url" {
  description = "S3 URL for the current data file"
  value       = "s3://${local.bucket_name}/${local.s3_key}"
}

output "ingestor_function_name" {
  description = "Name of the ingestor Lambda function"
  value       = aws_lambda_function.ingestor.function_name
}

output "api_function_name" {
  description = "Name of the API Lambda function"
  value       = aws_lambda_function.api.function_name
}

output "ingestor_log_group" {
  description = "CloudWatch log group for the ingestor Lambda"
  value       = "/aws/lambda/${aws_lambda_function.ingestor.function_name}"
}
