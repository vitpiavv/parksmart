terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "parksmart-498918-tf-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required GCP APIs (Added Compute & Service Networking)
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
    "vpcaccess.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# ==========================================
# NEW NETWORKING RESOURCES FOR PRIVATE VPC
# ==========================================

# Create the Private VPC Network
resource "google_compute_network" "vpc_network" {
  depends_on              = [google_project_service.services]
  name                    = "parksmart-vpc"
  auto_create_subnetworks = true # Keeps it simple, provisions standard subnets automatically
}

# Allocate an internal IP range for Google Services (like Cloud SQL) inside our VPC
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "parksmart-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id
}

# Establish the Private Services Connection (VPC Peering with Google Services)
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# Create a Serverless VPC Access Connector so Cloud Run can talk to the VPC
resource "google_vpc_access_connector" "vpc_connector" {
  depends_on = [google_service_networking_connection.private_vpc_connection]
  name       = "parksmart-connector"
  region     = var.region
  
  # The connector requires its own dedicated /28 subnet slice not used elsewhere
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc_network.name
  
  min_instances = 2
  max_instances = 3
}

# ==========================================
# EXISTING INFRASTRUCTURE (UPDATED FOR VPC)
# ==========================================

# Artifact Registry for Container Storage
resource "google_artifact_registry_repository" "repo" {
  depends_on    = [google_project_service.services]
  location      = var.region
  repository_id = "parksmart-repo"
  description   = "Docker repository for ParkSmart application images"
  format        = "DOCKER"
}

# UPDATED: Secure Cloud SQL Instance (Now 100% Private)
resource "google_sql_database_instance" "postgres" {
  # Strictly depends on the private connection being fully established first
  depends_on       = [google_service_networking_connection.private_vpc_connection]
  name             = "parksmart-db-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    
    ip_configuration {
      ipv4_enabled    = false # DISBALE PUBLIC INTERNET IP
      private_network = google_compute_network.vpc_network.id # Route inside our VPC
    }
  }
  deletion_protection = false # Set to true for production later
}

variable "container_image" {
  type        = string
  description = "The full Artifact Registry path and tag for the frontend container"
}

resource "google_sql_database" "database" {
  name     = "parksmart"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "db_user" {
  name     = "parkuser"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# Create Cloud Run Service Account
resource "google_service_account" "cloud_run_sa" {
  account_id   = "parksmart-runner"
  display_name = "Cloud Run Service Account for ParkSmart"
}

# Grant Service Account access to act as a Cloud SQL Client
resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# UPDATED: Cloud Run Deployment
resource "google_cloud_run_v2_service" "flask_app" {
  depends_on = [google_artifact_registry_repository.repo]
  name       = "parksmart-frontend"
  location   = var.region
  ingress    = "INGRESS_TRAFFIC_ALL" # Web traffic can still come in publicly from the internet

  template {
    service_account = google_service_account.cloud_run_sa.email

    # NEW: Tell Cloud Run to route traffic through the VPC connector
    vpc_access {
      connector = google_vpc_access_connector.vpc_connector.id
      egress    = "PRIVATE_RANGES_ONLY" # Send only internal/database traffic through the VPC
    }

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      env {
        name  = "FLASK_ENV"
        value = "production"
      }
      env {
        name  = "DATABASE_URL"
        value = "postgresql://parkuser:${var.db_password}@localhost/parksmart?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.parksmart_bucket.name
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }
  }
}

# Allow public unauthenticated access to the web interface
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = google_cloud_run_v2_service.flask_app.name
  location = google_cloud_run_v2_service.flask_app.location
  role     = "roles/run.viewer"
  member   = "allUsers"
}

# Google Cloud Storage Bucket for ParkSmart
resource "google_storage_bucket" "parksmart_bucket" {
  name                        = "${var.project_id}-parksmart-storage"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = true 
}

# Grant Cloud Run Service Account IAM access to the bucket
resource "google_storage_bucket_iam_member" "bucket_uploader" {
  bucket = google_storage_bucket.parksmart_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "db_password" {
  type      = string
  sensitive = true
}