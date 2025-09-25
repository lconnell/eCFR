output "api_base_url" { value = aws_apigatewayv2_api.http.api_endpoint }
output "s3_bucket"    { value = aws_s3_bucket.data.bucket }
