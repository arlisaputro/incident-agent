terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ========================
# VPC & NETWORKING
# ========================
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = { Name = "${var.project_name}-public-subnet" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project_name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ========================
# SECURITY GROUP
# ========================
resource "aws_security_group" "app" {
  name        = "${var.project_name}-app-sg"
  description = "Allow SSH and Streamlit access"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Streamlit"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-app-sg" }
}

# ========================
# EC2 INSTANCE (no IAM role - use env credentials)
# ========================
resource "aws_instance" "app" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.app.id]
  key_name               = var.key_pair_name

  user_data = <<-EOF
    #!/bin/bash
    exec > /var/log/user-data.log 2>&1
    yum update -y
    yum install -y python3 python3-pip git
    pip3 install streamlit boto3 ddtrace requests

    # Clone and setup app
    cd /home/ec2-user
    git clone https://github.com/arlisaputro/incident-agent.git app || mkdir -p app
    cd app

    # AWS credentials (no IAM role available)
    mkdir -p /home/ec2-user/.aws
    cat <<'AWSCFG' > /home/ec2-user/.aws/credentials
    [default]
    aws_access_key_id = PLACEHOLDER_ACCESS_KEY
    aws_secret_access_key = PLACEHOLDER_SECRET_KEY
    AWSCFG
    cat <<'AWSCFG2' > /home/ec2-user/.aws/config
    [default]
    region = ap-southeast-1
    output = json
    AWSCFG2
    chown -R ec2-user:ec2-user /home/ec2-user/.aws

    # Environment variables
    cat <<'ENVFILE' > /home/ec2-user/app.env
    export AWS_REGION=ap-southeast-1
    export BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
    export KNOWLEDGE_BASE_ID=
    export DD_API_KEY=
    export DD_APP_KEY=
    export DD_SITE=datadoghq.com
    export DD_LLMOBS_APP_NAME=incident-agent
    ENVFILE
    chown ec2-user:ec2-user /home/ec2-user/app.env

    echo "Setup complete" > /tmp/setup_done.txt
  EOF

  tags = { Name = "${var.project_name}-app-server" }
}

# ========================
# S3 BUCKET (Knowledge Base)
# ========================
resource "aws_s3_bucket" "knowledge" {
  bucket = "${var.project_name}-knowledge-base-${random_id.suffix.hex}"
  tags   = { Name = "${var.project_name}-knowledge-base" }
}

resource "aws_s3_bucket_versioning" "knowledge" {
  bucket = aws_s3_bucket.knowledge.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge" {
  bucket = aws_s3_bucket.knowledge.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "knowledge" {
  bucket                  = aws_s3_bucket.knowledge.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ========================
# RANDOM SUFFIX
# ========================
resource "random_id" "suffix" {
  byte_length = 4
}
