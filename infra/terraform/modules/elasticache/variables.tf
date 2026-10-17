variable "cluster_name" {
  description = "The name of the cluster"
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "The private subnet IDs"
  type        = list(string)
}

variable "eks_node_cidr_blocks" {
  description = "The CIDR blocks of the EKS nodes"
  type        = list(string)
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.small"
}

variable "num_cache_clusters" {
  description = "Primary + replicas; 2 or more enables automatic failover"
  type        = number
  default     = 2
}
