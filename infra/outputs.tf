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

output "streamlit_url" {
  description = "Streamlit app URL"
  value       = "http://${aws_instance.app.public_ip}:8501"
}

output "bedrock_kb_role_arn" {
  description = "IAM Role ARN for Bedrock Knowledge Base"
  value       = aws_iam_role.bedrock_kb_role.arn
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN (for KB data source config)"
  value       = aws_s3_bucket.knowledge.arn
}
