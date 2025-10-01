# Multi-Tier Application with CI/CD on Kubernetes

This project demonstrates a complete DevOps workflow for deploying a multi-tier application on Kubernetes with automated CI/CD, monitoring, and advanced deployment strategies.

## 🏗️ Architecture Overview

The project consists of:

- **Frontend**: Nginx-served static HTML/JS application
- **Backend**: Python Flask API server
- **Infrastructure**: Kubernetes cluster (can be deployed on AWS EKS or locally)
- **CI/CD**: GitHub Actions pipeline with automated Docker builds
- **Monitoring**: Prometheus + Grafana stack
- **Logging**: Elasticsearch + Kibana (EFK stack)
- **Advanced Features**: Auto-scaling, secrets management, canary deployments

## 📁 Project Structure

```
eks-project/
├── backend/                    # Flask API application
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Static web application
│   ├── index.html
│   └── Dockerfile
├── terraform/                  # Infrastructure as Code
│   ├── main.tf
│   ├── eks-cluster.tf
│   ├── iam.tf
│   └── networking.tf
├── k8s/                       # Kubernetes manifests
│   ├── namespace.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   └── ingress.yaml
├── monitoring/                # Prometheus & Grafana configs
│   ├── prometheus-config.yaml
│   ├── prometheus-deployment.yaml
│   └── grafana-deployment.yaml
├── logging/                   # EFK stack configs
│   ├── elasticsearch-deployment.yaml
│   └── kibana-deployment.yaml
├── advanced-deployment/       # Advanced K8s features
│   ├── hpa.yaml
│   ├── secrets.yaml
│   └── canary-deployment.yaml
└── .github/workflows/         # CI/CD pipeline
    └── ci-cd.yaml
```

## 🚀 Key Features

### 1. Containerization

- Dockerized frontend and backend applications
- Multi-stage builds for optimization
- Lightweight base images (Alpine Linux)

### 2. Infrastructure as Code (Terraform)

- Complete AWS EKS cluster setup
- VPC, subnets, and security groups
- IAM roles and policies
- Network routing and internet gateway

### 3. Kubernetes Orchestration

- Deployments with replica sets
- Services for internal communication
- Ingress for external access
- Namespace isolation
- Resource requests and limits

### 4. CI/CD Pipeline

- Automated builds on code changes
- Docker image building and pushing to registry
- Kubernetes manifest updates
- Rolling deployments
- Branch protection and PR workflows

### 5. Monitoring & Observability

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Dashboard visualization
- Service discovery and scraping configuration
- Custom metrics and alerts

### 6. Centralized Logging

- **Elasticsearch**: Log storage and indexing
- **Kibana**: Log visualization and search
- Structured logging across services

### 7. Advanced Deployment Strategies

#### Horizontal Pod Autoscaler (HPA)

- CPU and memory-based scaling
- Custom scaling policies
- Stabilization windows for smooth scaling

#### Secrets Management

- Kubernetes Secrets for sensitive data
- ConfigMaps for application configuration
- Base64 encoding and secure storage

#### Canary Deployments

- Traffic splitting between versions
- Header-based routing for testing
- Gradual rollout strategy

## 🛠️ Local Development Setup

### Prerequisites

- Docker Desktop with Kubernetes enabled
- kubectl configured
- Git for version control

### Quick Start

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/eks-project.git
   cd eks-project
   ```

2. **Build Docker images**:

   ```bash
   # Build backend
   docker build -t eks-project-backend:latest ./backend

   # Build frontend
   docker build -t eks-project-frontend:latest ./frontend
   ```

3. **Deploy to Kubernetes**:

   ```bash
   # Create namespace
   kubectl apply -f k8s/namespace.yaml

   # Deploy applications
   kubectl apply -f k8s/

   # Deploy monitoring
   kubectl apply -f monitoring/

   # Deploy logging
   kubectl apply -f logging/
   ```

4. **Access the application**:

   ```bash
   # Get service URLs
   kubectl get services -n eks-project

   # Port forward to access locally
   kubectl port-forward -n eks-project svc/frontend-service 8080:80
   kubectl port-forward -n eks-project svc/grafana-service 3000:3000
   ```

## 🔧 Configuration

### CI/CD Setup

1. Fork this repository
2. Set up Docker Hub account and create repository
3. Add GitHub secrets:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_TOKEN`: Your Docker Hub access token
4. Push changes to trigger pipeline

### Monitoring Access

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601

## 📊 Monitoring & Alerting

The monitoring stack includes:

- Application metrics (request rate, response time, errors)
- Infrastructure metrics (CPU, memory, disk, network)
- Kubernetes cluster metrics (pod status, resource usage)
- Custom business metrics

### Sample Grafana Dashboards

- Application Performance Dashboard
- Kubernetes Cluster Overview
- Resource Utilization Trends
- Error Rate and Latency Tracking

## 🔐 Security Considerations

- Secrets stored in Kubernetes Secrets (base64 encoded)
- RBAC for service accounts
- Network policies for pod communication
- Container security contexts
- Image vulnerability scanning in CI/CD

## 🚀 Production Deployment

### AWS EKS Deployment

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan infrastructure
terraform plan

# Apply (creates AWS resources - costs may apply)
terraform apply
```

### Post-deployment Steps

1. Configure kubectl for EKS cluster
2. Update image registry URLs in manifests
3. Set up DNS records for ingress
4. Configure SSL/TLS certificates
5. Set up backup and disaster recovery

## 📈 Scaling & Performance

### Horizontal Scaling

- HPA configured for both frontend and backend
- Scales based on CPU and memory utilization
- Custom metrics scaling available

### Vertical Scaling

- Resource requests and limits configured
- Automatic resource recommendation available
- Node autoscaling for cluster expansion

## 🧪 Testing

### Local Testing

```bash
# Test backend
curl http://localhost:5000

# Test frontend
curl http://localhost:8080

# Health checks
kubectl get pods -n eks-project
kubectl describe pod <pod-name> -n eks-project
```

### Load Testing

- Use tools like Apache Bench, JMeter, or k6
- Monitor scaling behavior during load tests
- Verify monitoring and alerting functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [GitHub Actions](https://docs.github.com/en/actions)

---
