output "core_repository_url" {
  value = aws_ecr_repository.core.repository_url
}

output "chat_repository_url" {
  value = aws_ecr_repository.chat.repository_url
}

output "ai_repository_url" {
  value = aws_ecr_repository.ai.repository_url
}

output "analytics_repository_url" {
  value = aws_ecr_repository.analytics.repository_url
}
