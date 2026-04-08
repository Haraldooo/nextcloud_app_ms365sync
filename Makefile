IMAGE := ghcr.io/haraldooo/ms365sync-exapp
PLATFORMS := linux/amd64,linux/arm64

.PHONY: release buildx-init build push ship

# Bump version across info.xml, pyproject.toml, package.json.
# Usage: make release VERSION=1.0.1
release:
	@test -n "$(VERSION)" || (echo "usage: make release VERSION=x.y.z" && exit 1)
	@uv run --no-project python -c "import re,pathlib; \
p=pathlib.Path('appinfo/info.xml'); \
p.write_text(re.sub(r'<version>[^<]+</version>', '<version>$(VERSION)</version>', \
            re.sub(r'<image-tag>[^<]+</image-tag>', '<image-tag>$(VERSION)</image-tag>', p.read_text()), count=1))"
	@uv run --no-project python -c "import re,pathlib; \
p=pathlib.Path('pyproject.toml'); \
p.write_text(re.sub(r'^version = \"[^\"]+\"', 'version = \"$(VERSION)\"', p.read_text(), count=1, flags=re.M))"
	@uv run --no-project python -c "import re,pathlib; \
p=pathlib.Path('package.json'); \
p.write_text(re.sub(r'\"version\":\s*\"[^\"]+\"', '\"version\": \"$(VERSION)\"', p.read_text(), count=1))"
	@echo "Bumped to $(VERSION). Review: git diff"

buildx-init:
	@docker buildx inspect multi >/dev/null 2>&1 || docker buildx create --name multi --use
	@docker buildx use multi

# Multi-arch build + push in one step (buildx can't load multi-arch into the
# local docker daemon, so push and build are combined).
# Usage: make build VERSION=1.0.1
build push: buildx-init
	@test -n "$(VERSION)" || (echo "usage: make $@ VERSION=x.y.z" && exit 1)
	docker buildx build \
		--platform $(PLATFORMS) \
		-t $(IMAGE):$(VERSION) \
		-t $(IMAGE):latest \
		--push .

# End-to-end release: bump versions, commit, tag, push branch+tag, build & push image.
# After this finishes, in the sib-io-nextcloud-saas repo:
#   1. set exapps[ms365sync].info_xml in vars/sib-io.yml to the v$(VERSION) raw URL
#   2. run ./update.sh sib-io
# Usage: make ship VERSION=1.0.2
ship:
	@test -n "$(VERSION)" || (echo "usage: make ship VERSION=x.y.z" && exit 1)
	@if ! git diff --quiet || ! git diff --cached --quiet; then \
		echo "ERROR: working tree is dirty - commit or stash first"; exit 1; \
	fi
	@if git rev-parse "v$(VERSION)" >/dev/null 2>&1; then \
		echo "ERROR: tag v$(VERSION) already exists"; exit 1; \
	fi
	$(MAKE) release VERSION=$(VERSION)
	git add appinfo/info.xml pyproject.toml package.json
	git commit -m "Release $(VERSION)"
	git tag "v$(VERSION)"
	git push origin HEAD "v$(VERSION)"
	$(MAKE) push VERSION=$(VERSION)
	@echo
	@echo "Shipped v$(VERSION)."
	@echo "Next: in sib-io-nextcloud-saas, set info_xml to:"
	@echo "  https://raw.githubusercontent.com/Haraldooo/nextcloud_app_ms365sync/v$(VERSION)/appinfo/info.xml"
	@echo "Then: ./update.sh sib-io"
