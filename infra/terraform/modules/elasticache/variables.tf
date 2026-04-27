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
