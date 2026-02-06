#!/bin/bash
# =============================================================================
# RoomKit Website Deployment Script
# Thin wrapper around Makefile targets for backward compatibility.
# =============================================================================

set -e

ACTION=${1:-"full"}

case $ACTION in
    build|deploy|full|clean|status|gather)
        exec make -C "$(dirname "$0")" "$ACTION"
        ;;
    logs)
        exec make -C "$(dirname "$0")" logs
        ;;
    *)
        echo "Usage: $0 {build|deploy|full|clean|status|logs|gather}"
        echo ""
        echo "Commands:"
        echo "  gather  - Assemble build context from sibling repos"
        echo "  build   - Gather + build and push Docker image"
        echo "  deploy  - Deploy to Kubernetes"
        echo "  full    - Build and deploy (default)"
        echo "  clean   - Remove build context"
        echo "  status  - Check deployment status"
        echo "  logs    - View pod logs"
        exit 1
        ;;
esac
