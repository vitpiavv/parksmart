output "cloud_run_url" {
  description = "The public URL of the deployed ParkSmart frontend web app"
  value       = google_cloud_run_v2_service.flask_app.uri
}

output "db_connection_name" {
  description = "The connection string used by the app to connect to Cloud SQL"
  value       = google_sql_database_instance.postgres.connection_name
}