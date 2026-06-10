# ParkSmart

**Smart Parking Management System** by ParkWise Solutions.

ParkSmart helps drivers locate, reserve, and manage parking spaces online. Administrators monitor availability, manage users, update spot status, and view reservation activity through a REST API.

This repository contains the **backend API**, **GCP infrastructure (Terraform)**, and **CI/CD pipelines**. Frontend and additional integrations can be added alongside this codebase.



Security

ParkSmart follows secure software development and DevSecOps practices throughout the application lifecycle. Security controls have been implemented across authentication, cloud infrastructure, secret management, container security, and CI/CD automation.
Authentication and Authorization

    User passwords are hashed using bcrypt before being stored in the database.
    JWT Bearer authentication is used to protect API endpoints.
    Access tokens contain user identity, role information, and expiration timestamps.
    Protected routes require authentication before access is granted.
    Role-based access control supports both User and Administrator permissions.
    Deactivated accounts are prevented from authenticating.

Secret Management

    Sensitive credentials are not hardcoded in source code.
    Database passwords are generated automatically and stored in Google Secret Manager.
    JWT signing secrets are stored in Google Secret Manager.
    Cloud Run retrieves secrets securely through Secret Manager references during deployment.

Infrastructure Security

    Google Cloud Run uses dedicated service accounts.
    IAM permissions follow the Principle of Least Privilege.
    Cloud Run receives only the permissions required to access Cloud SQL and Secret Manager.
    Workload Identity Federation is used for GitHub Actions authentication, eliminating the need for long-lived service account keys.
    Cloud SQL connectivity is configured through private networking and Cloud SQL connectors.

Container Security

    Production containers use the python:3.12-slim-bookworm base image.
    Containers run as non-root users.
    Resource limits are configured to reduce abuse and improve stability.
    Startup and liveness probes are configured to improve application availability and monitoring.

CI/CD Security

Security scanning is integrated directly into the GitHub Actions pipeline.

Implemented controls include:

    Snyk dependency scanning
    Snyk Docker container scanning
    Snyk Terraform (Infrastructure-as-Code) scanning
    Trivy vulnerability scanning
    Terraform validation

Security findings are uploaded to GitHub Code Scanning through SARIF reports. High and critical vulnerabilities can prevent deployment until remediation occurs.
Security Testing and Review

Security reviews were performed on:

    Authentication implementation
    Password hashing controls
    JWT token management
    IAM permissions
    Secret Manager integration
    Cloud Run configuration
    Workload Identity Federation
    CI/CD security scanning workflows

Additional security testing, including SQL Injection, Cross-Site Scripting (XSS), authentication, and authorization testing, will be completed prior to final deployment.
Security Reviewer

Security reviews, compliance validation, and final security testing are conducted by:

Cadar Maxamed Security Reviewer