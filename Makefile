.PHONY: help install dev test lint migrate seed docker-build deploy-dev deploy-staging deploy-prod venv

# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

# Python
PYTHON := python3
VENV_DIR := backend/.venv
VENV_BIN := $(VENV_DIR)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

## Show help
help:
	@echo ''
	@echo '${GREEN}Loan System - Makefile Commands${RESET}'
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@echo '  ${YELLOW}venv${RESET}           Create Python virtual environment'
	@echo '  ${YELLOW}install${RESET}        Install all dependencies (backend + frontend)'
	@echo '  ${YELLOW}dev${RESET}            Start development servers'
	@echo '  ${YELLOW}dev-backend${RESET}    Start only backend server'
	@echo '  ${YELLOW}dev-frontend${RESET}   Start only frontend server'
	@echo '  ${YELLOW}test${RESET}           Run all tests'
	@echo '  ${YELLOW}lint${RESET}           Run linters'
	@echo '  ${YELLOW}migrate${RESET}        Run database migrations'
	@echo '  ${YELLOW}seed${RESET}           Seed database with demo users'
	@echo '  ${YELLOW}docker-build${RESET}   Build Docker images'
	@echo '  ${YELLOW}deploy-dev${RESET}     Deploy to development'
	@echo '  ${YELLOW}deploy-staging${RESET} Deploy to staging'
	@echo '  ${YELLOW}deploy-prod${RESET}    Deploy to production'
	@echo '  ${YELLOW}clean${RESET}          Clean up generated files'
	@echo ''

## Create virtual environment
venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "${GREEN}Creating virtual environment...${RESET}"; \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "${GREEN}✅ Virtual environment created at $(VENV_DIR)${RESET}"; \
	else \
		echo "${YELLOW}Virtual environment already exists${RESET}"; \
	fi

## Install dependencies
install: venv
	@echo "${GREEN}Installing backend dependencies...${RESET}"
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install --only-binary :all: -r backend/requirements-dev.txt || $(VENV_PIP) install -r backend/requirements-dev.txt
	@echo "${GREEN}Installing frontend dependencies...${RESET}"
	cd frontend && npm install --legacy-peer-deps
	@echo "${GREEN}✅ Installation complete${RESET}"
	@echo ""
	@echo "${YELLOW}To activate the virtual environment manually:${RESET}"
	@echo "  source $(VENV_BIN)/activate"

## Start development servers
dev: venv
	@echo "${GREEN}Ensuring services are running (postgres, redis)...${RESET}"
	@docker compose up -d postgres redis 2>/dev/null || true
	@echo "${GREEN}Starting backend...${RESET}"
	$(VENV_BIN)/uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000 --app-dir backend &
	@echo "${GREEN}Starting frontend...${RESET}"
	cd frontend && npm run dev

## Start only backend
dev-backend: venv
	@echo "${GREEN}Starting backend...${RESET}"
	$(VENV_BIN)/uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000 --app-dir backend

## Start only frontend
dev-frontend:
	@echo "${GREEN}Starting frontend...${RESET}"
	cd frontend && npm run dev

## Run tests
test: venv
	@echo "${GREEN}Running backend tests...${RESET}"
	cd backend && ../$(VENV_BIN)/pytest -v --cov=app --cov-report=html
	@echo "${GREEN}Running frontend tests...${RESET}"
	cd frontend && npm test

## Run backend tests only
test-backend: venv
	cd backend && ../$(VENV_BIN)/pytest -v --cov=app --cov-report=html

## Run frontend tests only
test-frontend:
	cd frontend && npm test

## Run linters
lint: venv
	@echo "${GREEN}Linting backend...${RESET}"
	cd backend && ../$(VENV_BIN)/black app/ tests/
	cd backend && ../$(VENV_BIN)/isort app/ tests/
	cd backend && ../$(VENV_BIN)/flake8 app/ tests/
	cd backend && ../$(VENV_BIN)/mypy app/
	@echo "${GREEN}Linting frontend...${RESET}"
	cd frontend && npm run lint

## Run database migrations
migrate: venv
	@echo "${GREEN}Running migrations...${RESET}"
	cd backend && ../$(VENV_BIN)/alembic upgrade head

## Create new migration
migrate-create: venv
	@echo "${GREEN}Creating migration: $(msg)${RESET}"
	cd backend && ../$(VENV_BIN)/alembic revision --autogenerate -m "$(msg)"

## Seed database with demo data
seed: venv
	@echo "${GREEN}Seeding database...${RESET}"
	cd backend && ../$(VENV_BIN)/python -m app.db.seed

## Build Docker images
docker-build:
	@echo "${GREEN}Building Docker images...${RESET}"
	docker build -t loan-api:latest -f backend/Dockerfile ./backend
	docker build -t loan-frontend:latest -f frontend/Dockerfile ./frontend
	docker build -t loan-workers:latest -f backend/Dockerfile.workers ./backend
	@echo "${GREEN}✅ Docker build complete${RESET}"

## Deploy to development
deploy-dev:
	@echo "${GREEN}Deploying to development...${RESET}"
	kubectl apply -k k8s/overlays/development

## Deploy to staging
deploy-staging:
	@echo "${GREEN}Deploying to staging...${RESET}"
	kubectl apply -k k8s/overlays/staging

## Deploy to production
deploy-prod:
	@echo "${GREEN}Deploying to production...${RESET}"
	kubectl apply -k k8s/overlays/production

## Show logs
logs:
	kubectl logs -f -l app=loan-api --all-containers

## Open shell in backend pod
shell:
	kubectl exec -it deploy/loan-api -- /bin/sh

## Clean up
clean:
	@echo "${GREEN}Cleaning up...${RESET}"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	@echo "${GREEN}✅ Clean complete${RESET}"

## Remove virtual environment
clean-venv:
	@echo "${GREEN}Removing virtual environment...${RESET}"
	rm -rf $(VENV_DIR)
	@echo "${GREEN}✅ Virtual environment removed${RESET}"

## Full clean (including venv)
clean-all: clean clean-venv
	@echo "${GREEN}✅ Full clean complete${RESET}"
