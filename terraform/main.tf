terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "parksmart-498918-tf-state" # Must match the bucket you just created
    prefix = "terraform/state"
  }
}
# Note: For production, configure a GCS backend here to store your state file securely

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required GCP APIs
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. Artifact Registry for Container Storage
resource "google_artifact_registry_repository" "repo" {
  depends_on    = [google_project_service.services]
  location      = var.region
  repository_id = "parksmart-repo"
  description   = "Docker repository for ParkSmart application images"
  format        = "DOCKER"
}

# 3. Secure Cloud SQL Instance (PostgreSQL)
resource "google_sql_database_instance" "postgres" {
  depends_on       = [google_project_service.services]
  name             = "parksmart-db-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro" # Highly cost-effective tier for testing/dev workloads
    ip_configuration {
      ipv4_enabled = true # Enabled for access, can be restricted to private IP later
    }
  }
  deletion_protection = false # Set to true for production to prevent accidental loss
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

# 4. Create Cloud Run Service Account (Least Privilege)
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

# 5. Cloud Run Deployment
resource "google_cloud_run_v2_service" "flask_app" {
  depends_on = [google_artifact_registry_repository.repo]
  name       = "parksmart-frontend"
  location   = var.region
  ingress    = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloud_run_sa.email

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      # Inject database connection variables natively
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

    # Standard Cloud SQL Sidecar connection hook
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
# 6. Google Cloud Storage Bucket for ParkSmart
resource "google_storage_bucket" "parksmart_bucket" {
  name                        = "${var.project_id}-parksmart-storage"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = true # Allows terraform destroy to clear files during testing
}

# Grant Cloud Run Service Account IAM access to the bucket
resource "google_storage_bucket_iam_member" "bucket_uploader" {
  bucket = google_storage_bucket.parksmart_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

