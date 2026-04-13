# Deployment and Infrastructure Plan

This document outlines the deployment and infrastructure plan for the EVA AI application.

## 1. Environment Setup

We will have three environments:

*   **Development:** For local development and testing.
*   **Staging:** For pre-production testing and QA.
*   **Production:** The live environment for users.

### 1.1. Development Environment

*   **Frontend:** Run locally using Vite's dev server (`npm run dev`).
*   **Backend:** Run locally using Uvicorn (`uvicorn api.main:app --reload`).
*   **Database:** PostgreSQL and Redis running in Docker containers.
*   **AI:** OpenRouter API with a development key.

### 1.2. Staging Environment

*   **Frontend:** Deployed as a static site on a cloud provider (e.g., Vercel, Netlify, or AWS S3/CloudFront).
*   **Backend:** Deployed as a containerized application on a cloud provider (e.g., AWS ECS, Google Cloud Run, or a small Kubernetes cluster).
*   **Database:** Managed PostgreSQL and Redis instances (e.g., AWS RDS, Google Cloud SQL).
*   **AI:** OpenRouter API with a staging key.

### 1.3. Production Environment

*   **Frontend:** Deployed as a static site on a CDN for global distribution.
*   **Backend:** Deployed as a containerized application with auto-scaling and load balancing.
*   **Database:** Managed, high-availability PostgreSQL and Redis instances with read replicas.
*   **AI:** OpenRouter API with a production key and rate limiting.

## 2. Containerization

We will use Docker to containerize the backend application.

### 2.1. Dockerfile

```Dockerfile
# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.2. Docker Compose (for development)

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./api:/app
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/eva_ai
      - SECRET_KEY=your-secret-key-here
      - ALGORITHM=HS256
      - JWT_SECRET=your-jwt-secret-here
      - OPENROUTER_API_KEY=your-openrouter-api-key-here
      - APP_URL=http://localhost:3000
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=eva_ai
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password

  redis:
    image: redis:6

volumes:
  postgres_data:
```

## 3. Continuous Integration and Continuous Deployment (CI/CD)

We will use a CI/CD pipeline (e.g., GitHub Actions, GitLab CI, or Jenkins) to automate the build, test, and deployment process.

### 3.1. CI Pipeline

1.  **Trigger:** On every push to the `main` or `develop` branch.
2.  **Jobs:**
    *   **Lint:** Run linters for both frontend and backend code.
    *   **Test:** Run unit and integration tests.
    *   **Build:** Build the frontend static files and the backend Docker image.
    *   **Push:** Push the Docker image to a container registry (e.g., Docker Hub, AWS ECR, Google Container Registry).

### 3.2. CD Pipeline

1.  **Trigger:** On a successful CI pipeline run on the `main` branch (for production) or `develop` branch (for staging).
2.  **Jobs:**
    *   **Deploy Frontend:** Deploy the static files to the hosting provider.
    *   **Deploy Backend:** Deploy the new Docker image to the container orchestration platform.
    *   **Run Migrations:** Apply any new database migrations.

## 4. Monitoring and Logging

*   **Monitoring:** We will use a monitoring tool (e.g., Prometheus, Grafana, Datadog) to track application performance, resource usage, and system health.
*   **Logging:** We will use a centralized logging system (e.g., ELK stack, Datadog, or a cloud provider's logging service) to collect and analyze logs from all services.

## 5. Security

*   **Infrastructure:**
    *   Use a Virtual Private Cloud (VPC) to isolate the application infrastructure.
    *   Use security groups and network access control lists (NACLs) to restrict traffic.
    *   Use a Web Application Firewall (WAF) to protect against common web vulnerabilities.
*   **Application:**
    *   Use HTTPS for all communication.
    *   Store secrets and credentials securely (e.g., using a secret management tool like HashiCorp Vault or a cloud provider's secret manager).
    *   Regularly scan for vulnerabilities in dependencies.
*   **Data:**
    *   Encrypt data at rest and in transit.
    *   Implement regular database backups.

## 6. Cost Estimation

A detailed cost estimation will be provided separately, but the main cost drivers will be:

*   **Cloud provider:** Compute, storage, and data transfer costs.
*   **Database:** Managed database service costs.
*   **AI:** OpenRouter API usage costs.
*   **Monitoring and logging:** Third-party service costs.
