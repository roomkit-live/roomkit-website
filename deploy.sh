#!/bin/bash
# =============================================================================
# RoomKit Website Deployment Script
# =============================================================================

set -e

# Configuration
REGISTRY="quintana"
IMAGE_NAME="roomkit-web"
K8S_HOST="root@192.168.50.6"
NAMESPACE="roomkit"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
ACTION=${1:-"deploy"}

case $ACTION in
    build)
        log_info "Building Docker image..."
        docker build -f Dockerfile.website -t ${REGISTRY}/${IMAGE_NAME}:latest .

        log_info "Pushing image to registry..."
        docker push ${REGISTRY}/${IMAGE_NAME}:latest

        log_info "Build complete!"
        ;;

    deploy)
        log_info "Deploying to Kubernetes..."

        # Apply Kubernetes manifests
        ssh ${K8S_HOST} "kubectl apply -f -" < k8s.yml

        # Restart deployments to pull latest images
        ssh ${K8S_HOST} "kubectl rollout restart deployment/roomkit-web -n ${NAMESPACE}"
        ssh ${K8S_HOST} "kubectl rollout restart deployment/caddy -n ${NAMESPACE}"

        log_info "Waiting for rollout to complete..."
        ssh ${K8S_HOST} "kubectl rollout status deployment/roomkit-web -n ${NAMESPACE} --timeout=120s"
        ssh ${K8S_HOST} "kubectl rollout status deployment/caddy -n ${NAMESPACE} --timeout=120s"

        log_info "Deployment complete!"
        log_info "Website available at: https://www.roomkit.live"
        ;;

    full)
        log_info "Running full deployment (build + deploy)..."
        $0 build
        $0 deploy
        ;;

    status)
        log_info "Checking deployment status..."
        ssh ${K8S_HOST} "kubectl get all -n ${NAMESPACE}"
        ;;

    logs)
        POD=${2:-"roomkit-web"}
        log_info "Fetching logs for ${POD}..."
        ssh ${K8S_HOST} "kubectl logs -n ${NAMESPACE} -l app=${POD} --tail=100 -f"
        ;;

    *)
        echo "Usage: $0 {build|deploy|full|status|logs}"
        echo ""
        echo "Commands:"
        echo "  build   - Build and push Docker image"
        echo "  deploy  - Deploy to Kubernetes"
        echo "  full    - Build and deploy"
        echo "  status  - Check deployment status"
        echo "  logs    - View logs (optionally specify pod: logs caddy)"
        exit 1
        ;;
esac
