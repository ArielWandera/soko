variable "aws_region" {
  description = "AWS region. eu-west-1 (Ireland) has good latency to East Africa and full service coverage."
  default     = "eu-west-1"
}

variable "instance_type" {
  description = "EC2 instance type. t3.xlarge (4 vCPU / 16 GB) fits the full stack. Upgrade to t3.2xlarge if ML services feel sluggish."
  default     = "t3.xlarge"
}

variable "ssh_public_key" {
  description = "Contents of your SSH public key (~/.ssh/id_ed25519.pub). Used for the EC2 key pair."
  sensitive   = true
}
