IMAGE := ghcr.io/haraldooo/ms365sync-exapp

.PHONY: release build push deploy

# Bump version across info.xml, info.json, pyproject.toml, package.json.
# Usage: make release VERSION=1.0.1
release:
	@test -n "$(VERSION)" || (echo "usage: make release VERSION=x.y.z" && exit 1)
	@python3 -c "import re,pathlib; \
p=pathlib.Path('appinfo/info.xml'); \
p.write_text(re.sub(r'<version>[^<]+</version>', '<version>$(VERSION)</version>', \
            re.sub(r'<image-tag>[^<]+</image-tag>', '<image-tag>$(VERSION)</image-tag>', p.read_text()), count=1))"
	@python3 -c "import re,pathlib; \
p=pathlib.Path('info.json'); \
p.write_text(re.sub(r'\"version\":\s*\"[^\"]+\"', '\"version\": \"$(VERSION)\"', p.read_text(), count=1))"
	@python3 -c "import re,pathlib; \
p=pathlib.Path('pyproject.toml'); \
p.write_text(re.sub(r'^version = \"[^\"]+\"', 'version = \"$(VERSION)\"', p.read_text(), count=1, flags=re.M))"
	@python3 -c "import re,pathlib; \
p=pathlib.Path('package.json'); \
p.write_text(re.sub(r'\"version\":\s*\"[^\"]+\"', '\"version\": \"$(VERSION)\"', p.read_text(), count=1))"
	@echo "Bumped to $(VERSION). Review: git diff"

build:
	docker build -t $(IMAGE):$(VERSION) -t $(IMAGE):latest .

push:
	docker push $(IMAGE):$(VERSION)
	docker push $(IMAGE):latest

deploy:
	occ app_api:app:deploy ms365sync $(IMAGE):$(VERSION)
