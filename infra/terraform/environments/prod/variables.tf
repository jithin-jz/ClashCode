variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "clashcode"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.1.0.0/16" # Different CIDR for prod to avoid overlap if peered
}

variable "db_host" {
  description = "DB Host"
  type        = string
}

variable "db_port" {
  description = "DB Port"
  type        = string
  default     = "5432"
}

variable "db_name" {
  description = "DB Name"
  type        = string
  default     = "clashcode_prod"
}

variable "db_user" {
  description = "DB User"
  type        = string
}

variable "db_password" {
  description = "DB Password"
  type        = string
  sensitive   = true
}

variable "ecr_repository_url" {
  description = "ECR repository URL"
  type        = string
}
