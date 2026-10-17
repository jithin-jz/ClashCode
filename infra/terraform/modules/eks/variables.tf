variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "public_subnets" {
  type = list(string)
}

variable "private_subnets" {
  type = list(string)
}

variable "cluster_version" {
  description = "Kubernetes version; pinned so an apply never upgrades the cluster by surprise"
  type        = string
  default     = "1.35"
}

variable "endpoint_public_access_cidrs" {
  description = "CIDRs allowed to reach the public EKS API endpoint (admin IPs, CI runners)"
  type        = list(string)
}

variable "node_instance_types" {
  type    = list(string)
  default = ["m7i-flex.large"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 4
}
