output "public_ip" {
  description = "Elastic IP of the Soko server (stable across reboots)"
  value       = aws_eip.soko.public_ip
}

output "ssh_command" {
  description = "Ready-to-run SSH command"
  value       = "ssh -i ~/.ssh/id_ed25519 ubuntu@${aws_eip.soko.public_ip}"
}

output "app_url" {
  description = "URL to access the app once deployed"
  value       = "http://${aws_eip.soko.public_ip}"
}
