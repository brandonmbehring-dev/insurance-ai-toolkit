# Deployment Guide

**Purpose**: Instructions for deploying the InsuranceAI Toolkit Streamlit web UI in various environments.

**Audience**: DevOps, system administrators, Guardian IT team

**Version**: v0.1.0

---

## Deployment Options

The InsuranceAI Toolkit can be deployed in multiple ways depending on your environment and requirements:

| Option | Best For | Setup Time | Cost | Notes |
|--------|----------|-----------|------|-------|
| **Local** | Development, demos | <5 min | $0 | Single machine, no persistence |
| **Docker** | CI/CD, testing | 5-10 min | $0 | Containerized, reproducible |
| **Docker Compose** | Full stack demos | 5-10 min | $0 | Multi-service orchestration |
| **Streamlit Cloud** | Public sharing | 10-15 min | Free tier | Managed hosting, limited resources |
| **AWS EC2** | Production | 15-30 min | $0.01-1/hr | Full control, scaling options |
| **Kubernetes** | Enterprise | 30-60 min | $$ | Auto-scaling, high availability |

---

## Option 1: Local Development

**Best for**: Individual development, testing, Guardian demos

### Prerequisites
- Python 3.11+
- pip or uv package manager
- ~500MB disk space

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/insurance_ai_toolkit.git
cd insurance_ai_toolkit

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with web extras
pip install -e ".[web]"
```

### Launch

```bash
streamlit run src/insurance_ai/web/app.py
```

**Access**: http://localhost:8501

### Performance
- **Startup**: ~3-5 seconds
- **Page load**: <2 seconds
- **Chart render**: <500ms
- **Memory**: ~300-500MB

### Notes
- **Offline mode** by default (no API keys needed)
- Hot reload enabled (edit code → instant refresh)
- Perfect for Guardian technical hiring demo

---

## Option 2: Docker (Single Container)

**Best for**: Reproducible deployments, testing, CI/CD pipelines

### Prerequisites
- Docker 20.10+ installed
- ~1GB disk space (for image + data)

### Build Docker Image

```bash
# Build image (one-time)
docker build -t insurance-ai-toolkit:latest .

# Verify
docker images | grep insurance-ai
```

### Run Container

```bash
# Run in foreground (for demos)
docker run -p 8501:8501 insurance-ai-toolkit:latest

# Run in background (for production)
docker run -d --name insurance-ai \
  -p 8501:8501 \
  insurance-ai-toolkit:latest

# Check logs
docker logs -f insurance-ai

# Stop container
docker stop insurance-ai
docker rm insurance-ai
```

**Access**: http://localhost:8501 or http://{host-ip}:8501

### Configuration

Docker image respects environment variables:

```bash
docker run -p 8501:8501 \
  -e INSURANCE_AI_MODE=offline \
  -e STREAMLIT_SERVER_PORT=8501 \
  insurance-ai-toolkit:latest
```

### Dockerfile Structure

The provided `Dockerfile`:
- Uses Python 3.11-slim base image (~300MB)
- Installs system dependencies (poppler-utils for PDF)
- Installs Python dependencies with web extras
- Exposes port 8501
- Sets STREAMLIT_SERVER_HEADLESS=true (for non-interactive mode)
- Runs `streamlit run src/insurance_ai/web/app.py`

### Notes
- **Image size**: ~500MB (slim base + dependencies)
- **Build time**: ~2-3 minutes
- **Container startup**: ~5 seconds
- **Health check**: Built-in (checks `/_stcore/health` endpoint)

---

## Option 3: Docker Compose (Recommended for Demos)

**Best for**: Multi-service deployments, demo environments, team collaboration

### Prerequisites
- Docker & Docker Compose installed
- ~1GB disk space

### Launch

```bash
# Start services (detached)
docker-compose up -d

# View logs
docker-compose logs -f insurance-ai-web

# Stop services
docker-compose down
```

**Access**: http://localhost:8501

### Configuration

Edit `docker-compose.yml` for environment-specific settings:

```yaml
# Default: Offline mode (demo)
environment:
  - INSURANCE_AI_MODE=offline

# For online mode: Add API keys via .env file
environment:
  - INSURANCE_AI_MODE=online
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

Create `.env` file for secrets:

```bash
# .env (DO NOT COMMIT TO GIT)
ANTHROPIC_API_KEY=sk-...
FRED_API_KEY=...
YFINANCE_API_KEY=...
```

### Health Check

Docker Compose includes automatic health checking:

```bash
# Check status
docker-compose ps

# Should show:
# insurance-ai-web   Up (healthy)
```

### Scaling

For load balancing (production):

```yaml
# docker-compose.yml
services:
  insurance-ai-web:
    deploy:
      replicas: 3  # Run 3 instances
      placement:
        max_replicas_per_node: 1
```

---

## Option 4: Streamlit Cloud (Public Sharing)

**Best for**: Sharing demos publicly, GitHub integration, managed hosting

### Prerequisites
- GitHub account
- GitHub repository (public or private)
- Streamlit Cloud account (free)

### Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for Streamlit Cloud"
   git push origin main
   ```

2. **Create Streamlit Secrets**
   - Navigate to: https://share.streamlit.io/
   - Click "New app"
   - Select repository: `yourusername/insurance_ai_toolkit`
   - Select branch: `main`
   - Set main file: `src/insurance_ai/web/app.py`

3. **Configure Secrets**
   - In Streamlit Cloud dashboard
   - Settings → Secrets
   - Add API keys (if using online mode):
     ```
     ANTHROPIC_API_KEY = "sk-..."
     FRED_API_KEY = "..."
     ```

4. **Deploy**
   - Click "Deploy"
   - App available at: `https://yourusername-insurance-ai-toolkit.streamlit.app`

### Performance
- **Startup**: ~10-15 seconds (cold start)
- **CPU**: Shared (limited)
- **Memory**: 1GB max
- **Data**: 1GB max storage

### Limitations
- No local file write access (fixtures must be in Git)
- Limited background task support
- Requires GitHub public/private repo

### Notes
- **Free tier**: Perfect for demos
- **Pro tier**: $5/month per app, more resources
- **Auto-deploy**: Updates on Git push

---

## Option 5: AWS EC2 (Production)

**Best for**: Production deployments, custom infrastructure, scalability

### Prerequisites
- AWS account
- EC2 instance (t2.medium recommended)
- Security group configured (port 8501 open)
- SSH key pair

### Setup

1. **Launch EC2 Instance**
   ```bash
   # Ubuntu 22.04 LTS, t2.medium
   # Configure security group to allow 8501 (and 22 for SSH)
   ```

2. **SSH into Instance**
   ```bash
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3-pip docker.io docker-compose

   # Optional: Install nginx as reverse proxy
   sudo apt install -y nginx
   ```

4. **Clone & Deploy**
   ```bash
   git clone https://github.com/yourusername/insurance_ai_toolkit.git
   cd insurance_ai_toolkit

   # Option A: Local installation
   pip install -e ".[web]"
   streamlit run src/insurance_ai/web/app.py &

   # Option B: Docker (recommended)
   docker-compose up -d
   ```

5. **Configure Reverse Proxy (Optional)**
   ```nginx
   # /etc/nginx/sites-available/default
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

6. **Enable HTTPS (Let's Encrypt)**
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

### Instance Sizing

| Size | vCPU | Memory | Monthly Cost | Use Case |
|------|------|--------|--------------|----------|
| t2.micro | 1 | 1GB | ~$9 | Personal demos (limited) |
| t2.small | 1 | 2GB | ~$18 | Small team demos |
| t2.medium | 2 | 4GB | ~$35 | Production app (10-20 users) |
| t2.large | 2 | 8GB | ~$69 | High-traffic app (20-50 users) |

### Auto-Scaling (Advanced)

```bash
# Create AMI from configured instance
# Launch auto-scaling group
# Configure load balancer (ALB) on port 80
# CloudWatch monitoring
```

---

## Option 6: Kubernetes (Enterprise)

**Best for**: Large-scale deployments, high availability, multi-region

### Prerequisites
- Kubernetes cluster (EKS, GKE, AKS)
- kubectl configured
- Docker image pushed to registry (ECR, DockerHub)

### Kubernetes Manifest

```yaml
# insurance-ai-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: insurance-ai
spec:
  replicas: 3  # 3 pods for HA
  selector:
    matchLabels:
      app: insurance-ai
  template:
    metadata:
      labels:
        app: insurance-ai
    spec:
      containers:
      - name: insurance-ai
        image: your-registry/insurance-ai-toolkit:latest
        ports:
        - containerPort: 8501
        env:
        - name: INSURANCE_AI_MODE
          value: "offline"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: insurance-ai-service
spec:
  type: LoadBalancer
  selector:
    app: insurance-ai
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
```

### Deploy

```bash
# Apply manifest
kubectl apply -f insurance-ai-deployment.yaml

# Verify
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/insurance-ai
```

### Auto-Scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: insurance-ai-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: insurance-ai
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Performance Considerations

### Memory Usage

| Environment | Base | Per User | Total for 10 Users |
|-------------|------|----------|-------------------|
| Local | 300MB | ~50MB | ~800MB |
| Docker | 350MB | ~50MB | ~850MB |
| Kubernetes | 256MB | ~50MB | ~750MB |

### CPU Usage

| Operation | CPU | Duration |
|-----------|-----|----------|
| App startup | 50-100% | 3-5 seconds |
| Page load | 20-30% | <1 second |
| Chart render | 40-60% | <500ms |
| Idle | <5% | — |

### Optimization Tips

1. **Use Streamlit caching** (`@st.cache_resource` for fixtures)
2. **Lazy load charts** (render on demand, not page init)
3. **Compress images** (if adding custom assets)
4. **Monitor memory** (watch for leaks with long-running apps)
5. **CDN for static assets** (if serving publicly)

---

## Maintenance & Updates

### Local Development

```bash
# Update code
git pull origin main

# Update dependencies
pip install --upgrade -e ".[web]"

# Run tests
pytest tests/ -v

# Restart app (Streamlit auto-reloads on file changes)
```

### Docker/Docker Compose

```bash
# Rebuild image with new code
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Or in one command
docker-compose up -d --build
```

### AWS EC2

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Pull latest code
cd insurance_ai_toolkit
git pull origin main

# Restart service
docker-compose down
docker-compose up -d
```

### Health Monitoring

```bash
# Check Streamlit health endpoint
curl http://localhost:8501/_stcore/health

# Should return: {"status": "ok"}
```

---

## Security Best Practices

1. **Never Commit Secrets**
   - API keys in `.env` (add to `.gitignore`)
   - Use environment variables in production
   - Consider AWS Secrets Manager or HashiCorp Vault

2. **HTTPS in Production**
   - Use reverse proxy (nginx)
   - Enable SSL/TLS (Let's Encrypt free)
   - Set `Strict-Transport-Security` header

3. **Authentication** (optional, for team use)
   - Streamlit doesn't have built-in auth
   - Solutions:
     - Nginx basic auth
     - Streamlit Community Cloud (automatic)
     - Custom middleware (advanced)

4. **Network Security**
   - Close port 8501 except from trusted IPs
   - Use VPC/security groups
   - Enable WAF (Web Application Firewall)

5. **Data Security**
   - Fixtures use synthetic data (no PHI)
   - No sensitive data hardcoded
   - Clear data on logout (for multi-user)

6. **Dependency Updates**
   - Regular `pip install --upgrade`
   - Monitor security advisories
   - Use dependabot (GitHub) for auto-updates

---

## Troubleshooting Deployments

### Port Already in Use

```bash
# Find process using port 8501
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run app.py --server.port 8502
```

### Out of Memory

```bash
# Check memory usage
top  # or docker stats

# Increase if possible
# Docker: --memory 2g
# Kubernetes: set memory limits higher
```

### Slow Performance

```bash
# Profile page load
# 1. Browser DevTools (F12 → Network)
# 2. Streamlit logger: --logger.level=debug
# 3. Check fixture file sizes
```

### App Won't Start

```bash
# Check logs
docker logs insurance-ai
# or
kubectl logs deployment/insurance-ai

# Common issues:
# 1. Port in use
# 2. Missing dependencies
# 3. Configuration error
```

---

## Migration Guide

### From Local → Docker

```bash
# 1. Build Docker image
docker build -t insurance-ai-toolkit:latest .

# 2. Test locally
docker run -p 8501:8501 insurance-ai-toolkit:latest

# 3. Push to registry (if needed)
docker tag insurance-ai-toolkit:latest yourusername/insurance-ai:latest
docker push yourusername/insurance-ai:latest

# 4. Use in production
docker run -p 8501:8501 yourusername/insurance-ai:latest
```

### From Local → Streamlit Cloud

```bash
# 1. Ensure .env is in .gitignore
echo ".env" >> .gitignore
echo "secrets.toml" >> .gitignore

# 2. Commit and push
git add -A
git commit -m "Ready for Streamlit Cloud"
git push origin main

# 3. Deploy via https://share.streamlit.io/
# Add secrets in dashboard

# 4. Share link: https://yourusername-insurance-ai.streamlit.app
```

### From Docker → Kubernetes

```bash
# 1. Push Docker image to registry
docker push your-registry/insurance-ai:latest

# 2. Create Kubernetes manifests (see Option 6 above)

# 3. Deploy
kubectl apply -f insurance-ai-deployment.yaml

# 4. Verify
kubectl get deployments
kubectl get services
```

---

## Cost Estimation

### Annual Deployment Costs

| Option | Setup | Monthly | Annual |
|--------|-------|---------|--------|
| Local | $0 | $0 | $0 |
| Docker Compose (dev machine) | $0 | $0 | $0 |
| Streamlit Cloud (free) | $0 | $0 | $0 |
| Streamlit Cloud (Pro) | $0 | $5 | $60 |
| AWS EC2 (t2.medium) | $5 | $35 | $420 |
| AWS ECS/Fargate | $10 | $50-200 | $600-2,400 |
| Kubernetes (managed) | $20 | $200-500 | $2,400-6,000 |

### Recommended for Guardian

- **Development**: Local (`make run`)
- **Demos**: Docker Compose (`docker-compose up`)
- **Production**: AWS EC2 + RDS (if data persistence needed)

---

## Next Steps

1. **Choose Deployment Option** (local for demo, Docker for production)
2. **Test Locally** (`make validate`)
3. **Configure Environment** (API keys, if needed)
4. **Deploy** (`docker-compose up` or EC2 setup)
5. **Monitor** (health checks, logs, performance)

---

**Last Updated**: 2025-12-15
**Version**: InsuranceAI Toolkit v0.1.0
**Status**: ✅ Deployment Guide Complete
