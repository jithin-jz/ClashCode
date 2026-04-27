variable "aws_region" {
  description = "AWS region"
  type        = "string"
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = "string"
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = "string"
  default     = "clashcode"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = "string"
  default     = "10.0.0.0/16"
}

variable "db_host" {
  description = "Supabase DB Host"
  type        = "string"
}

variable "db_port" {
  description = "Supabase DB Port"
  type        = "string"
  default     = "6543"
}

variable "db_name" {
  description = "Supabase DB Name"
  type        = "string"
  default     = "postgres"
}

variable "db_user" {
  description = "Supabase DB User"
  type        = "string"
}

variable "db_password" {
  description = "Supabase DB Password"
  type        = "string"
  sensitive   = true
}

variable "ecr_repository_url" {
  description = "ECR repository URL"
  type        = "string"
}
