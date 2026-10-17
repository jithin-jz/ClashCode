# Remote state (bucket created by infra/terraform/bootstrap). After adding this,
# run `terraform init -migrate-state` once to move the existing local state.
terraform {
  required_version = ">= 1.11.0"

  backend "s3" {
    bucket       = "clashcode-terraform-state-317451122305"
    key          = "prod/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
