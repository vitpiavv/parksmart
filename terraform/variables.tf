variable "project_id" {
  description = "The GCP Project ID where resources will be deployed"
  type        = string
}

variable "region" {
  description = "The primary region for resources"
  type        = string
  default     = "us-central1"
}

variable "db_password" {
  description = "The password for the Cloud SQL master user"
  type        = string
  sensitive   = true
}

variable "image_tag" {
  description = "The Docker container image tag to deploy"
  type        = string
  default     = "latest"
}