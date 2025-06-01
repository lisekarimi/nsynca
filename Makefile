# =====================================
# 🌱 Project & Environment Configuration
# =====================================

include .env
export

# Read from pyproject.toml using grep (works on all platforms)
PROJECT_NAME = $(shell python -c "import re; print(re.search('name = \"(.*)\"', open('pyproject.toml').read()).group(1))")
VERSION = $(shell python -c "import re; print(re.search('version = \"(.*)\"', open('pyproject.toml').read()).group(1))")

DOCKER_IMAGE = $(DOCKER_USERNAME)/$(PROJECT_NAME)
TAG = v$(VERSION)
CONTAINER_NAME = $(PROJECT_NAME)-container

# =====================================
# 🛠️  Environment Setup (using UV)
# =====================================
# uv add package-name - Add a new dependency
# uv add --dev package-name - Add a development dependency
# uv sync - Install/sync all dependencies
# uv remove package-name - Remove a dependency
# uv remove --dev package-name - Remove a development dependency
# uv cache clean - Clear the cache

# =======================
# 🪝 Hooks
# =======================

install-hooks:	## Install pre-commit hooks
	uvx pre-commit install
	uvx pre-commit install --hook-type commit-msg


# =====================================
# ✨ Code Quality
# =====================================

lint:	## Run code linting and formatting
	uvx ruff check .
	uvx ruff format .

fix:	## Fix code issues and format
	uvx ruff check --fix .
	uvx ruff format .


# =====================================
# 🚀 Run App Locally
# =====================================

# Note: uv run automatically creates venv and installs dependencies if needed

run:	## Runs all updaters (default behavior)
	uv run main.py

run-deploy:	## Run the deployment updater
	uv run main.py --updaters deployment

run-task:	## Run the task updater
	uv run main.py --updaters task

run-debug:	## Run the app in debug mode
	uv run main.py --log-level DEBUG

gui:	## Run the GUI script
	uv run gui.py


# =====================================
# 🐳 Docker Commands
# =====================================

docker-build:	## Build the Docker image
	docker build -t $(DOCKER_IMAGE):$(TAG) .

docker-ls: ## List files in Docker image
	docker run --rm $(DOCKER_IMAGE):$(TAG) ls -la /app

docker-run:	## Run the Docker container
	docker run --rm \
		--name $(CONTAINER_NAME) \
		--env-file .env \
		$(DOCKER_IMAGE):$(TAG)


# =====================================
#  🚀 Publish Docker Image to GitHub (GH) Packages
# 1. Build the image
# 2. Tag the image
# 3. Push the image to GitHub Packages
# =====================================

gh-login: ## Login to GitHub Container Registry
	@python -c "import os; os.system('echo ' + [line.split('=')[1].strip() for line in open('.env') if 'GITHUB_TOKEN' in line][0] + ' | docker login ghcr.io -u $(GITHUB_USERNAME) --password-stdin')"

gh-tag: ## Tag Docker image for GitHub Packages
	docker tag $(DOCKER_IMAGE):$(TAG) ghcr.io/$(GITHUB_USERNAME)/$(PROJECT_NAME):$(TAG)
	docker tag $(DOCKER_IMAGE):$(TAG) ghcr.io/$(GITHUB_USERNAME)/$(PROJECT_NAME):latest

gh-push: gh-login gh-tag ## Push Docker image to GitHub Packages 
	docker push ghcr.io/$(GITHUB_USERNAME)/$(PROJECT_NAME):$(TAG)
	docker push ghcr.io/$(GITHUB_USERNAME)/$(PROJECT_NAME):latest

gh-debug: ## Show all variables
	@echo "DOCKER_IMAGE: $(DOCKER_IMAGE)"
	@echo "TAG: $(TAG)"
	@echo "GITHUB_USERNAME: $(GITHUB_USERNAME)"
	@echo "PROJECT_NAME: $(PROJECT_NAME)"
	@echo "Full command would be:"
	@echo "docker tag $(DOCKER_IMAGE):$(TAG) ghcr.io/$(GITHUB_USERNAME)/$(PROJECT_NAME):$(TAG)"


# =====================================
# 📦 Build & Distribution
# =====================================

build-exe: ## Build the executable using PyInstaller
	uv run pyi-makespec --onefile --windowed \
		--icon=assets/img/notion_updater.ico \
		--name="nsynca" \
		--hidden-import=pkg_resources \
		--hidden-import=packaging \
		--hidden-import=packaging.version \
		--hidden-import=packaging.specifiers \
		--hidden-import=packaging.requirements \
		gui.py

compile-exe:	## Compile the executable from spec file
	uv run pyinstaller "nsynca.spec"
	@echo "Executable compiled successfully. You can find it in the dist/ folder."


# =====================================
# 📚 Documentation & Help
# =====================================

help: ## Show this help message
	@echo Available commands:
	@echo.
	@python -c "import re; lines=open('Makefile', encoding='utf-8').readlines(); targets=[re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$',l) for l in lines]; [print(f'  make {m.group(1):<20} {m.group(2)}') for m in targets if m]"


# =====================================
# 🎯 Phony Targets
# =====================================
.PHONY: $(shell python -c "import re; print(' '.join(re.findall(r'^([a-zA-Z_-]+):\s*.*?##', open('Makefile', encoding='utf-8').read(), re.MULTILINE)))")

# Test the PHONY generation
# test-phony:
# 	@echo "$(shell python -c "import re; print(' '.join(sorted(set(re.findall(r'^([a-zA-Z0-9_-]+):', open('act.mk', encoding='utf-8').read(), re.MULTILINE)))))")"