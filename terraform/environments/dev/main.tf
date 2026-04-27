module "vpc" {
  source = "../../modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
}

module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
}

module "eks" {
  source = "../../modules/eks"

  project_name    = var.project_name
  environment     = var.environment
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets
}

module "elasticache" {
  source = "../../modules/elasticache"

  cluster_name         = module.eks.cluster_name
  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnets
  eks_node_cidr_blocks = [var.vpc_cidr] # Simplified for dev, allowing from within VPC
}

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
