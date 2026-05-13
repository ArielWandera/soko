terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Uncomment after creating your state bucket:
  # backend "s3" {
  #   bucket = "soko-tf-state"
  #   key    = "soko/terraform.tfstate"
  #   region = "eu-west-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "soko" {
  key_name   = "soko-deploy"
  public_key = var.ssh_public_key
}

resource "aws_security_group" "soko" {
  name        = "soko-sg"
  description = "Soko server"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "soko-sg" }
}

resource "aws_instance" "soko" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.soko.key_name
  vpc_security_group_ids = [aws_security_group.soko.id]

  root_block_device {
    volume_size = 40
    volume_type = "gp3"
  }

  user_data = file("${path.module}/userdata.sh")

  tags = { Name = "soko-server" }
}

resource "aws_eip" "soko" {
  instance = aws_instance.soko.id
  domain   = "vpc"
  tags     = { Name = "soko-eip" }
}
