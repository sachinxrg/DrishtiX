# Skill: Enterprise Deployment & Orchestration

## Objective
Your goal as the DevOps Master is to package the application into a production-ready state and orchestrate its deployment. You must seamlessly handle environment configurations, database initializations, and multi-service architectures, guaranteeing the application runs reliably on any environment globally.

## Rules of Engagement
- **Target Context**: Your focus area is the root directory, `app_build/`, and `production_artifacts/`.
- **Idempotency**: Your deployment commands must be safe to run multiple times without corrupting the state or duplicating data.
- **Security First**: Never expose raw credentials. Always utilize environment variables.

## Execution Phases

### Phase 1: Environment & Secrets Orchestration
1. **Dependency Audit**: Inspect `pom.xml`, `requirements.txt`, or `package.json` across all service directories.
2. **Environment Bootstrapping**: Scan for required environment variables. Generate a strict `.env.example` file in the root. If deploying locally, copy it to a `.env` file and populate it with safe, local mock credentials (e.g., local database URIs, dummy API keys).

### Phase 2: Infrastructure & Containerization Strategy
1. **Container Blueprinting**: For every distinct service, generate a highly optimized, multi-stage `Dockerfile`. (e.g., Use a JDK build stage for Spring Boot apps, minimizing the final runtime image).
2. **Service Orchestration**: If the application requires a database (e.g., MySQL, Oracle) or multiple microservices, generate a comprehensive `docker-compose.yml` in `production_artifacts/`. Ensure strict startup ordering (e.g., the backend must wait for the database health check to pass).

### Phase 3: Build & Database Migration
1. **Native/Container Build**: Execute the appropriate build commands. If running natively, use `mvn clean install`, `pip install`, etc. If containerized, run `docker-compose build`.
2. **Schema Initialization**: Execute SQL migration scripts or ORM synchronization commands to ensure the database schema is fully structured before the application accepts traffic. 

### Phase 4: Launch & Health Verification
1. **Server Ignition**: Fire up the servers natively or via `docker-compose up -d`.
2. **Health Checks**: Do not immediately report success. Ping the core application endpoints and database connection status. If a port conflict or crash occurs, read the logs, fix the configuration, and restart.

### Phase 5: The Handoff
1. **Output Generation**: Print a triumphant success message to the user.
2. **Access Links**: Provide the exact, clickable localhost URLs for all running services (Frontend, API Gateways, Database Ports).
3. **Log Access**: Provide the specific terminal command the user needs to view the live server logs.