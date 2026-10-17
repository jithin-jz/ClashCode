output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "redis_endpoint" {
  value = module.elasticache.redis_endpoint
}

output "redis_url" {
  description = "Put this in REDIS_URL (backend-secrets / chat-secrets)"
  value       = module.elasticache.redis_url
  sensitive   = true
}

output "dynamodb_table" {
  value = module.dynamodb.table_name
}

output "chat_irsa_role_arn" {
  value = module.irsa_chat.role_arn
}

output "external_secrets_irsa_role_arn" {
  description = "Annotate the external-secrets service account with this role"
  value       = module.irsa_external_secrets.role_arn
}

output "ecr_repository_urls" {
  value = {
    core      = module.ecr.core_repository_url
    chat      = module.ecr.chat_repository_url
    ai        = module.ecr.ai_repository_url
    analytics = module.ecr.analytics_repository_url
    executor  = module.ecr.executor_repository_url
  }
}
