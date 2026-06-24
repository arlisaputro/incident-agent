# 🔒 Security Notice

This repository has been sanitized to remove sensitive information including:

- AWS Account IDs and credentials
- Datadog API keys and application keys
- EC2 instance IDs and public IP addresses
- SSH key information
- Dashboard IDs
- Personal IP addresses

## ⚠️ Before Using This Code

1. **Copy configuration templates:**
   ```bash
   cp .env.example .env
   cp infra/terraform.tfvars.example infra/terraform.tfvars
   ```

2. **Fill in your actual values** in the copied files

3. **Never commit sensitive information** to version control

4. **Use environment variables** for sensitive data in production

## 📝 Configuration Required

- AWS credentials and region
- Datadog API keys
- EC2 key pairs
- Your public IP for security groups
- S3 bucket names (must be globally unique)

## 🛡️ Security Best Practices

- Keep `.env` and `terraform.tfvars` in `.gitignore`
- Use AWS IAM roles instead of hardcoded credentials when possible
- Rotate API keys regularly
- Use AWS Secrets Manager or similar for production deployments