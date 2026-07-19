# Skill: Production-Grade Cloud Run Deployment

## Objective
Your goal as the DevOps Master is to deploy the application to Google Cloud Run using enterprise best practices. You must ensure zero-downtime rollouts, ironclad secret management, explicit container registry usage, and secure database connectivity. 

## Rules of Engagement
- **Target Context**: Your focus area is the GCP CLI (`gcloud`), the `production_artifacts/` directory, and the target service directories (e.g., `services/booking_engine/`).
- **No Black Boxes**: Do not use `--source .` deployments. You must explicitly build containers, push them to a registry, and deploy the specific image tag.
- **Strict Security**: Never inject raw API keys or database passwords as plain-text environment variables. Use Google Cloud Secret Manager.

## Execution Phases

### Phase 1: Pre-Flight & Infrastructure Audit
1. **API Verification**: Ensure the required GCP APIs are enabled: Cloud Run, Cloud Build, Artifact Registry, Secret Manager, and Cloud SQL Admin API.
2. **Service Account Setup**: Verify or create a dedicated runtime Service Account with the principle of least privilege (e.g., it can access the database and secrets, but cannot delete the project).

### Phase 2: Secrets & Database Orchestration
1. **Secret Injection**: Scan the local `.env` or application configuration for sensitive keys (e.g., database credentials, payment gateway keys). Push these to GCP Secret Manager.
2. **Database Connectivity**: If the service relies on a relational database (Oracle/MySQL), configure the Cloud Run service to securely connect via the Cloud SQL Auth Proxy or a Serverless VPC Access Connector. 

### Phase 3: Explicit Build & Registry
1. **Container Compilation**: Navigate to the specific service directory containing the multi-stage `Dockerfile`. 
2. **Artifact Registry Push**: Use Cloud Build (`gcloud builds submit`) to compile the container and push the versioned image to Google Artifact Registry. Tag the image explicitly (e.g., `v1.0.0` or a Git commit hash) rather than just `latest`.

### Phase 4: Zero-Downtime Deployment
1. **Service Rollout**: Execute `gcloud run deploy` pointing strictly to the image in Artifact Registry. 
2. **Configuration Binding**: Attach the runtime Service Account, bind the secrets from Secret Manager to environment variables, and set the Cloud SQL connection flags.
3. **Traffic Splitting (Optional but Preferred)**: If updating an existing service, initially route only 10% of traffic to the new revision to monitor for crash loops before migrating 100%.

### Phase 5: Verification & Handoff
1. **Health Verification**: Do not immediately report success. Read the Cloud Logging output for the new revision. Verify the Spring Boot application or Python service has successfully connected to the database and initialized.
2. **Report Generation**: Output the live production URL. Provide the exact commands the user can run to tail the production logs or rollback the traffic if an emergency occurs.