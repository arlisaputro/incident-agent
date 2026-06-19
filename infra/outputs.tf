output "ec2_public_ip" {
  description = "Public IP of the app server"
  value       = aws_instance.app.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the app server"
  value       = aws_instance.app.public_dns
}

output "s3_bucket_name" {
  description = "S3 bucket for knowledge base docs"
  value       = aws_s3_bucket.knowledge.bucket
}

output "dynamodb_table_name" {
  description = "DynamoDB table for known issues"
  value       = aws_dynamodb_table.known_issues.name
}

output "streamlit_url" {
  description = "Streamlit app URL"
  value       = "http://${aws_instance.app.public_ip}:8501"
}
