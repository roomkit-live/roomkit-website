# =============================================================================
# RoomKit Website — cross-repo build & deploy
# =============================================================================
# Assembles a Docker build context from sibling repos, builds the image,
# and deploys to Kubernetes.
#
# Repo layout (sibling dirs under roomkit-live/):
#   roomkit/          → src/, llms.txt, pyproject.toml
#   roomkit-docs/     → docs/, mkdocs.yml
#   roomkit-specs/    → roomkit-rfc.md
#   roomkit-website/  → this repo (index.html, css/, js/, deploy.sh, …)
# =============================================================================

REGISTRY   := quintana
IMAGE      := roomkit-web
TAG        := latest
K8S_HOST   := root@192.168.50.6
NAMESPACE  := roomkit
BUILD_DIR  := .build

WEBSITE_FILES := index.html 404.html favicon.svg og-image.svg robots.txt sitemap.xml css js

.PHONY: gather build deploy full clean status logs

# ---------------------------------------------------------------------------
# gather — assemble .build/ from sibling repos + local static files
# ---------------------------------------------------------------------------
gather:
	@echo "==> Gathering build context into $(BUILD_DIR)/"
	rm -rf $(BUILD_DIR)
	mkdir -p $(BUILD_DIR)/website $(BUILD_DIR)/docs

	# Source code & metadata from roomkit
	cp -R ../roomkit/src       $(BUILD_DIR)/src
	cp    ../roomkit/pyproject.toml $(BUILD_DIR)/pyproject.toml
	cp    ../roomkit/llms.txt  $(BUILD_DIR)/llms.txt

	# Documentation from roomkit-docs
	cp -R ../roomkit-docs/docs/. $(BUILD_DIR)/docs/
	cp    ../roomkit-docs/mkdocs.yml $(BUILD_DIR)/mkdocs.yml

	# RFC spec from roomkit-specs
	cp    ../roomkit-specs/roomkit-rfc.md $(BUILD_DIR)/docs/roomkit-rfc.md

	# Local static website files
	$(foreach f,$(WEBSITE_FILES),cp -R $(f) $(BUILD_DIR)/website/$(f);)

	# Dockerfile (renamed so `docker build .build` just works)
	cp Dockerfile.website $(BUILD_DIR)/Dockerfile

	@echo "==> Build context ready."

# ---------------------------------------------------------------------------
# build — build & push Docker image
# ---------------------------------------------------------------------------
build: gather
	@echo "==> Building Docker image $(REGISTRY)/$(IMAGE):$(TAG)"
	docker build -t $(REGISTRY)/$(IMAGE):$(TAG) $(BUILD_DIR)
	@echo "==> Pushing image…"
	docker push $(REGISTRY)/$(IMAGE):$(TAG)
	@echo "==> Build complete."

# ---------------------------------------------------------------------------
# deploy — apply k8s manifests & rollout restart
# ---------------------------------------------------------------------------
deploy:
	@echo "==> Deploying to Kubernetes…"
	ssh $(K8S_HOST) "kubectl apply -f -" < k8s.yml
	ssh $(K8S_HOST) "kubectl rollout restart deployment/roomkit-web -n $(NAMESPACE)"
	ssh $(K8S_HOST) "kubectl rollout restart deployment/caddy -n $(NAMESPACE)"
	@echo "==> Waiting for rollout…"
	ssh $(K8S_HOST) "kubectl rollout status deployment/roomkit-web -n $(NAMESPACE) --timeout=120s"
	ssh $(K8S_HOST) "kubectl rollout status deployment/caddy -n $(NAMESPACE) --timeout=120s"
	@echo "==> Deployment complete — https://www.roomkit.live"

# ---------------------------------------------------------------------------
# full — gather + build + deploy
# ---------------------------------------------------------------------------
full: build deploy

# ---------------------------------------------------------------------------
# clean — remove assembled build context
# ---------------------------------------------------------------------------
clean:
	rm -rf $(BUILD_DIR)
	@echo "==> Cleaned $(BUILD_DIR)/"

# ---------------------------------------------------------------------------
# status / logs — k8s helpers
# ---------------------------------------------------------------------------
status:
	ssh $(K8S_HOST) "kubectl get all -n $(NAMESPACE)"

logs:
	ssh $(K8S_HOST) "kubectl logs -n $(NAMESPACE) -l app=roomkit-web --tail=100 -f"
