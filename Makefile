# Makefile for Operator Certification Test Dashboard
# Uses OpenShift CLI (oc) for building and deploying

# Configuration - can be overridden via environment or command line
NAMESPACE ?= operator-certification-test-dashboard
APP_NAME ?= operator-test-dashboard
IMAGE_NAME ?= $(APP_NAME)
IMAGE_TAG ?= latest

# Helm values
REMOTE_HOST ?= rdu2
SSH_USER ?= root
REMOTE_BASE_DIR ?= /root/test-rose/certsuite
REPORT_DIR ?= /var/www/html

# ImageStream reference (internal OpenShift registry)
IMAGE_STREAM = image-registry.openshift-image-registry.svc:5000/$(NAMESPACE)/$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Namespace and Prerequisites
# ============================================================================

.PHONY: create-namespace
create-namespace: ## Create the namespace if it doesn't exist
	@echo "Creating namespace $(NAMESPACE)..."
	@oc create namespace $(NAMESPACE) --dry-run=client -o yaml | oc apply -f -

.PHONY: create-ssh-secret
create-ssh-secret: ## Create SSH key secret (requires SSH_KEY_PATH env var)
ifndef SSH_KEY_PATH
	$(error SSH_KEY_PATH is not set. Usage: make create-ssh-secret SSH_KEY_PATH=~/.ssh/id_rsa)
endif
	@echo "Creating SSH key secret in $(NAMESPACE)..."
	@oc create secret generic $(APP_NAME)-ssh-key \
		--from-file=id_rsa=$(SSH_KEY_PATH) \
		--namespace $(NAMESPACE) \
		--dry-run=client -o yaml | oc apply -f -

# ============================================================================
# OpenShift Build
# ============================================================================

.PHONY: create-imagestream
create-imagestream: create-namespace ## Create ImageStream for the application
	@echo "Creating ImageStream $(IMAGE_NAME) in $(NAMESPACE)..."
	@oc create imagestream $(IMAGE_NAME) \
		--namespace $(NAMESPACE) \
		--dry-run=client -o yaml | oc apply -f -

.PHONY: create-buildconfig
create-buildconfig: create-imagestream ## Create BuildConfig using Dockerfile
	@echo "Creating BuildConfig for $(APP_NAME)..."
	@echo 'apiVersion: build.openshift.io/v1\n\
kind: BuildConfig\n\
metadata:\n\
  name: $(APP_NAME)\n\
  namespace: $(NAMESPACE)\n\
  labels:\n\
    app: $(APP_NAME)\n\
spec:\n\
  source:\n\
    type: Binary\n\
  strategy:\n\
    type: Docker\n\
    dockerStrategy:\n\
      dockerfilePath: Dockerfile\n\
  output:\n\
    to:\n\
      kind: ImageStreamTag\n\
      name: $(IMAGE_NAME):$(IMAGE_TAG)\n\
  resources:\n\
    limits:\n\
      cpu: "1"\n\
      memory: 1Gi\n\
    requests:\n\
      cpu: 500m\n\
      memory: 512Mi' | oc apply -f -

.PHONY: build
build: create-buildconfig ## Build the application using OpenShift (binary build)
	@echo "Starting binary build from local source..."
	@oc start-build $(APP_NAME) \
		--from-dir=. \
		--namespace $(NAMESPACE) \
		--follow \
		--wait

.PHONY: build-status
build-status: ## Check the status of the latest build
	@oc get builds -n $(NAMESPACE) -l buildconfig=$(APP_NAME) --sort-by=.metadata.creationTimestamp
	@echo ""
	@echo "Latest build logs:"
	@oc logs -f bc/$(APP_NAME) -n $(NAMESPACE) 2>/dev/null || echo "No active build"

.PHONY: build-logs
build-logs: ## Show logs from the latest build
	@oc logs bc/$(APP_NAME) -n $(NAMESPACE)

# ============================================================================
# Helm Deployment
# ============================================================================

.PHONY: deploy
deploy: ## Deploy using Helm with ImageStream
	@echo "Deploying $(APP_NAME) to $(NAMESPACE)..."
	@helm upgrade --install $(APP_NAME) ./helm/operator-test-dashboard \
		--namespace $(NAMESPACE) \
		--set image.repository=$(IMAGE_STREAM) \
		--set image.tag="" \
		--set image.pullPolicy=Always \
		--set config.remoteHost=$(REMOTE_HOST) \
		--set config.sshUser=$(SSH_USER) \
		--set config.remoteBaseDir=$(REMOTE_BASE_DIR) \
		--set config.reportDir=$(REPORT_DIR) \
		--set sshKey.existingSecret=$(APP_NAME)-ssh-key \
		--set route.enabled=true

.PHONY: deploy-dry-run
deploy-dry-run: ## Show what Helm would deploy (dry-run)
	@helm upgrade --install $(APP_NAME) ./helm/operator-test-dashboard \
		--namespace $(NAMESPACE) \
		--set image.repository=$(IMAGE_STREAM) \
		--set image.tag="" \
		--set image.pullPolicy=Always \
		--set config.remoteHost=$(REMOTE_HOST) \
		--set config.sshUser=$(SSH_USER) \
		--set config.remoteBaseDir=$(REMOTE_BASE_DIR) \
		--set config.reportDir=$(REPORT_DIR) \
		--set sshKey.existingSecret=$(APP_NAME)-ssh-key \
		--set route.enabled=true \
		--dry-run

.PHONY: undeploy
undeploy: ## Remove Helm deployment
	@echo "Removing $(APP_NAME) deployment..."
	@helm uninstall $(APP_NAME) --namespace $(NAMESPACE) || true

# ============================================================================
# Combined Targets
# ============================================================================

.PHONY: all
all: build deploy ## Build and deploy the application

.PHONY: rebuild
rebuild: build deploy ## Rebuild and redeploy the application

.PHONY: setup
setup: create-namespace create-ssh-secret create-imagestream create-buildconfig ## Setup all prerequisites

# ============================================================================
# Status and Debugging
# ============================================================================

.PHONY: status
status: ## Show deployment status
	@echo "=== ImageStream ==="
	@oc get imagestream $(IMAGE_NAME) -n $(NAMESPACE) 2>/dev/null || echo "ImageStream not found"
	@echo ""
	@echo "=== BuildConfig ==="
	@oc get buildconfig $(APP_NAME) -n $(NAMESPACE) 2>/dev/null || echo "BuildConfig not found"
	@echo ""
	@echo "=== Recent Builds ==="
	@oc get builds -n $(NAMESPACE) -l buildconfig=$(APP_NAME) --sort-by=.metadata.creationTimestamp 2>/dev/null | tail -5 || echo "No builds found"
	@echo ""
	@echo "=== Deployment ==="
	@oc get deployment $(APP_NAME) -n $(NAMESPACE) 2>/dev/null || echo "Deployment not found"
	@echo ""
	@echo "=== Pods ==="
	@oc get pods -n $(NAMESPACE) -l app.kubernetes.io/name=$(APP_NAME) 2>/dev/null || echo "No pods found"
	@echo ""
	@echo "=== Route ==="
	@oc get route $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.host}' 2>/dev/null && echo "" || echo "Route not found"

.PHONY: logs
logs: ## Show application logs
	@oc logs -f deployment/$(APP_NAME) -n $(NAMESPACE)

.PHONY: describe
describe: ## Describe the deployment
	@oc describe deployment/$(APP_NAME) -n $(NAMESPACE)

.PHONY: get-route
get-route: ## Get the application route URL
	@echo "Dashboard URL:"
	@echo "https://$$(oc get route $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.host}')"

.PHONY: port-forward
port-forward: ## Port-forward to access locally (localhost:5001)
	@echo "Access dashboard at http://localhost:5001"
	@oc port-forward deployment/$(APP_NAME) 5001:5001 -n $(NAMESPACE)

# ============================================================================
# Cleanup
# ============================================================================

.PHONY: clean
clean: undeploy ## Remove deployment and build artifacts
	@echo "Cleaning up build artifacts..."
	@oc delete buildconfig $(APP_NAME) -n $(NAMESPACE) 2>/dev/null || true
	@oc delete imagestream $(IMAGE_NAME) -n $(NAMESPACE) 2>/dev/null || true
	@oc delete secret $(APP_NAME)-ssh-key -n $(NAMESPACE) 2>/dev/null || true

.PHONY: clean-builds
clean-builds: ## Remove old builds (keeps last 3)
	@echo "Cleaning old builds..."
	@oc get builds -n $(NAMESPACE) -l buildconfig=$(APP_NAME) -o name --sort-by=.metadata.creationTimestamp | head -n -3 | xargs -r oc delete -n $(NAMESPACE)

.PHONY: clean-all
clean-all: clean ## Remove everything including namespace
	@echo "Removing namespace $(NAMESPACE)..."
	@oc delete namespace $(NAMESPACE) 2>/dev/null || true

# ============================================================================
# Local Development
# ============================================================================

.PHONY: docker-build
docker-build: ## Build Docker image locally
	@docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: docker-run
docker-run: ## Run Docker image locally
	@docker run -p 5001:5001 \
		-e REMOTE_HOST=$(REMOTE_HOST) \
		-e SSH_USER=$(SSH_USER) \
		-v ~/.ssh/id_rsa:/home/dashboard/.ssh/id_rsa:ro \
		$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: run-local
run-local: ## Run the application locally (requires venv)
	@cd scripts && python web-dashboard.py
