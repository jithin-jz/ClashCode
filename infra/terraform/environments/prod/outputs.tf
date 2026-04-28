output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "redis_endpoint" {
  value = module.elasticache.redis_endpoint
}

output "dynamodb_table" {
  value = module.dynamodb.table_name
}

output "ecr_repository_urls" {
  value = {
    core      = module.ecr.core_repository_url
    chat      = module.ecr.chat_repository_url
    ai        = module.ecr.ai_repository_url
    analytics = module.ecr.analytics_repository_url
  }
}
