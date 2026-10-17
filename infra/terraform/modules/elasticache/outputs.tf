output "redis_endpoint" {
  description = "Primary endpoint of the Redis replication group"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  description = "The port of the Redis replication group"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_url" {
  description = "TLS connection URL with AUTH token, for REDIS_URL in the app secrets"
  value       = "rediss://:${random_password.redis_auth.result}@${aws_elasticache_replication_group.redis.primary_endpoint_address}:6379/0?ssl_cert_reqs=required"
  sensitive   = true
}
