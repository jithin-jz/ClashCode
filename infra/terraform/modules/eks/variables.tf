variable "project_name" {
  type = "string"
}

variable "environment" {
  type = "string"
}

variable "public_subnets" {
  type = list(string)
}

variable "private_subnets" {
  type = list(string)
}
