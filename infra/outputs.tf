output "ec2_public_ip" {
  description = "EC2 public IP"
  value       = aws_instance.app.public_ip
}

output "s3_bucket_name" {
  description = "S3 knowledge base bucket name"
  value       = aws_s3_bucket.knowledge.bucket
}

output "streamlit_url" {
  description = "Streamlit app URL"
  value       = "http://${aws_instance.app.public_ip}:8501"
}
