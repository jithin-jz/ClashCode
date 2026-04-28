module "vpc" {
  source = "../../modules/vpc"

  project_name = var.project_name
  environment  = "prod"
  vpc_cidr     = var.vpc_cidr
}

module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name = var.project_name
  environment  = "prod"
}

module "eks" {
  source = "../../modules/eks"

  project_name    = var.project_name
  environment     = "prod"
  public_subnets  = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets
}

module "elasticache" {
  source = "../../modules/elasticache"

  cluster_name         = module.eks.cluster_name
  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnets
  eks_node_cidr_blocks = [var.vpc_cidr]
}

module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = "prod"
}

# TODO: Add RDS module here to replace Supabase for Prod
# module "rds" {
#   source = "../../modules/rds"
#   ...
# }


# ECR Repository outputs are now in outputs.tf
