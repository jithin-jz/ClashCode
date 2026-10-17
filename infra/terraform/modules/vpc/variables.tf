variable "vpc_cidr" {
  type = string
}

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "single_nat_gateway" {
  description = "One shared NAT gateway (cheaper) instead of one per AZ"
  type        = bool
  default     = true
}
