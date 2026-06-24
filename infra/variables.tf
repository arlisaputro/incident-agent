variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "incident-agent"
}

variable "my_ip" {
  description = "Your public IP for SSH access (CIDR format, e.g. 103.x.x.x/32)"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for EC2 (Amazon Linux 2023)"
  type        = string
  default     = "ami-0672fd5b9210aa093"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "key_pair_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
}
