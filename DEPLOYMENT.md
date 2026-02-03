# Deployment Guide

This guide covers deploying the Operator Certification Test Dashboard using Docker and Kubernetes/OpenShift with Helm.

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Kubernetes/OpenShift Deployment with Helm](#kubernetsopenshift-deployment-with-helm)
3. [Configuration Reference](#configuration-reference)

---

## Docker Deployment

### Prerequisites

- Docker installed
- SSH key for accessing the remote OpenShift cluster

### Quick Start with Docker

```bash
# Build the image
docker build -t operator-test-dashboard:latest .

# Run with environment variables
docker run -d \
  --name operator-dashboard \
  -p 5001:5001 \
  -e REMOTE_HOST=your-cluster-host \
  -e SSH_USER=root \
  -v ~/.ssh/id_rsa:/home/dashboard/.ssh/id_rsa:ro \
  operator-test-dashboard:latest
```

### Using Docker Compose

```bash
# Set environment variables (optional - has defaults)
export REMOTE_HOST=your-cluster-host
export SSH_USER=root
export SSH_KEY_PATH=~/.ssh/your-key

# Start the dashboard
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Kubernetes/OpenShift Deployment with Helm

### Prerequisites

- Kubernetes cluster or OpenShift cluster
- Helm 3.x installed
- kubectl or oc CLI configured
- SSH key for accessing the remote cluster

### Step 1: Build and Push the Container Image

```bash
# Build the image
docker build -t quay.io/your-org/operator-test-dashboard:latest .

# Push to registry
docker push quay.io/your-org/operator-test-dashboard:latest
```

### Step 2: Create SSH Key Secret

```bash
# Create namespace
kubectl create namespace operator-dashboard

# Create secret from SSH private key
kubectl create secret generic operator-dashboard-ssh-key \
  --from-file=id_rsa=/path/to/your/ssh/private/key \
  --namespace operator-dashboard
```

### Step 3: Create values override file

Create a `my-values.yaml` file:

```yaml
# Image configuration
image:
  repository: quay.io/your-org/operator-test-dashboard
  tag: latest

# SSH key secret
sshKey:
  existingSecret: operator-dashboard-ssh-key
  key: id_rsa

# Dashboard configuration
config:
  remoteHost: "your-cluster-bastion-host"
  sshUser: "root"
  remoteBaseDir: "/root/test-rose/certsuite"
  reportDir: "/var/www/html"

# Enable OpenShift Route (instead of Ingress)
route:
  enabled: true

# Or enable Ingress for Kubernetes
# ingress:
#   enabled: true
#   hosts:
#     - host: dashboard.example.com
#       paths:
#         - path: /
#           pathType: Prefix
```

### Step 4: Deploy with Helm

```bash
# Install the chart
helm install operator-dashboard ./helm/operator-test-dashboard \
  --namespace operator-dashboard \
  --values my-values.yaml

# Or upgrade existing release
helm upgrade operator-dashboard ./helm/operator-test-dashboard \
  --namespace operator-dashboard \
  --values my-values.yaml
```

### Step 5: Access the Dashboard

**For OpenShift Route:**
```bash
oc get route operator-dashboard -n operator-dashboard -o jsonpath='{.spec.host}'
```

**For Kubernetes Ingress:**
```bash
kubectl get ingress operator-dashboard -n operator-dashboard
```

**For port-forward (development):**
```bash
kubectl port-forward svc/operator-dashboard 5001:5001 -n operator-dashboard
# Then open http://localhost:5001
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REMOTE_HOST` | SSH host for the remote cluster | `rdu2` |
| `SSH_USER` | SSH username | (none) |
| `SSH_KEY_PATH` | Path to SSH private key | (none) |
| `REMOTE_BASE_DIR` | Directory where certsuite is installed | `/root/test-rose/certsuite` |
| `REPORT_DIR` | Directory where reports are stored | `/var/www/html` |
| `DASHBOARD_PORT` | Port for the web dashboard | `5001` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_DIR` | Directory for log files | `/app/logs` |
| `REDHAT_CATALOG_INDEX` | Red Hat operator catalog index | `registry.redhat.io/redhat/redhat-operator-index:v4.20` |
| `CERTIFIED_CATALOG_INDEX` | Certified operator catalog index | `registry.redhat.io/redhat/certified-operator-index:v4.20` |
| `REDHAT_OPERATORS` | Comma-separated list of Red Hat operators | (defaults in code) |
| `CERTIFIED_OPERATORS` | Comma-separated list of certified operators | (defaults in code) |

### Helm Values

See `helm/operator-test-dashboard/values.yaml` for all available configuration options.

Key sections:
- `image` - Container image configuration
- `config` - Dashboard configuration
- `sshKey` - SSH key secret configuration
- `service` - Kubernetes service configuration
- `ingress` - Ingress configuration (for Kubernetes)
- `route` - Route configuration (for OpenShift)
- `resources` - CPU/memory limits and requests
- `persistence` - Persistent volume for logs

---

## Troubleshooting

### SSH Connection Issues

1. Verify the SSH key is mounted correctly:
   ```bash
   kubectl exec -it <pod-name> -n operator-dashboard -- ls -la /home/dashboard/.ssh/
   ```

2. Test SSH connection from the pod:
   ```bash
   kubectl exec -it <pod-name> -n operator-dashboard -- ssh -i /home/dashboard/.ssh/id_rsa root@your-host 'echo test'
   ```

### View Logs

```bash
# Kubernetes
kubectl logs -f deployment/operator-dashboard -n operator-dashboard

# Docker
docker logs -f operator-dashboard
```

### Common Issues

- **SSH permission denied**: Ensure the SSH key has correct permissions (600)
- **Connection timeout**: Verify network connectivity to the remote host
- **Pod CrashLoopBackOff**: Check logs for Python/Flask errors
