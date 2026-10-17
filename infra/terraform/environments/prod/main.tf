data "aws_caller_identity" "current" {}

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

  project_name                 = var.project_name
  environment                  = "prod"
  public_subnets               = module.vpc.public_subnets
  private_subnets              = module.vpc.private_subnets
  endpoint_public_access_cidrs = var.eks_public_access_cidrs
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

# --- IRSA roles (pods get scoped AWS access; no static keys in secrets) ---

# chat -> DynamoDB chat table only. Name must match the SA annotation in infra/k8s/overlays/prod.
module "irsa_chat" {
  source = "../../modules/irsa"

  role_name         = "${var.project_name}-prod-chat-irsa"
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  namespace         = "clashcode"
  service_account   = "chat"
  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:DescribeTable",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWriteItem",
      ]
      Resource = [module.dynamodb.table_arn, "${module.dynamodb.table_arn}/index/*"]
    }]
  })
}

# External Secrets Operator -> read-only access to clashcode/prod/* in Secrets Manager.
module "irsa_external_secrets" {
  source = "../../modules/irsa"

  role_name         = "${var.project_name}-prod-external-secrets-irsa"
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  namespace         = "external-secrets"
  service_account   = "external-secrets"
  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
      Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:clashcode/prod/*"
    }]
  })
}

# TODO: Add RDS module here to replace Supabase for Prod
# module "rds" {
#   source = "../../modules/rds"
#   ...
# }
