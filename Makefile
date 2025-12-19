.PHONY: help install dev test test-backend test-coverage lint migrate seed docker-build deploy-dev deploy-staging deploy-prod venv run setup workers worker-risk worker-audit worker-webhook docker-up docker-down check-services reset-db format check logs-backend logs-frontend logs-workers

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
	@echo '  ${YELLOW}test${RESET}           Run backend tests'
	@echo '  ${YELLOW}test-backend${RESET}    Alias for test (backend tests)'
	@echo '  ${YELLOW}test-coverage${RESET}   Run tests with detailed coverage report'
	@echo '  ${YELLOW}lint${RESET}           Run linters'
	@echo '  ${YELLOW}migrate${RESET}        Run database migrations'
	@echo '  ${YELLOW}seed${RESET}           Seed database with demo users'
	@echo '  ${YELLOW}docker-build${RESET}   Build Docker images'
	@echo '  ${YELLOW}deploy-dev${RESET}     Deploy to development'
	@echo '  ${YELLOW}deploy-staging${RESET} Deploy to staging'
	@echo '  ${YELLOW}deploy-prod${RESET}    Deploy to production'
	@echo '  ${YELLOW}setup${RESET}          Complete initial setup (install + migrate + seed)'
	@echo '  ${YELLOW}run${RESET}            Alias for dev (start development servers)'
	@echo '  ${YELLOW}workers${RESET}        Run all background workers'
	@echo '  ${YELLOW}worker-risk${RESET}    Run risk evaluation worker'
	@echo '  ${YELLOW}worker-audit${RESET}   Run audit worker'
	@echo '  ${YELLOW}worker-webhook${RESET} Run webhook worker'
	@echo '  ${YELLOW}docker-up${RESET}      Start all services with Docker Compose'
	@echo '  ${YELLOW}docker-down${RESET}    Stop all Docker Compose services'
	@echo '  ${YELLOW}check-services${RESET} Check if required services are running'
	@echo '  ${YELLOW}reset-db${RESET}       Reset database (drop + migrate + seed)'
	@echo '  ${YELLOW}format${RESET}         Format code (black + isort)'
	@echo '  ${YELLOW}check${RESET}          Verify configuration and services'
	@echo '  ${YELLOW}logs-backend${RESET}   Show backend logs'
	@echo '  ${YELLOW}logs-frontend${RESET}  Show frontend logs'
	@echo '  ${YELLOW}logs-workers${RESET}  Show workers logs'
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

## Run tests (backend only)
test: venv
	@echo "${GREEN}Running backend tests...${RESET}"
	@cd backend && .venv/bin/pytest -v --cov=app --cov-report=html --cov-report=term
	@echo ""
	@echo "${GREEN}✅ Test execution complete${RESET}"

## Run backend tests only (alias for test)
test-backend: test

## Run tests with coverage report
test-coverage: venv
	@echo "${GREEN}Running tests with coverage...${RESET}"
	@cd backend && .venv/bin/pytest -v --cov=app --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "${GREEN}Coverage report generated in backend/htmlcov/index.html${RESET}"

## Run linters
lint: venv
	@echo "${GREEN}Linting backend...${RESET}"
	cd backend && .venv/bin/black app/ tests/
	cd backend && .venv/bin/isort app/ tests/
	cd backend && .venv/bin/flake8 app/ tests/
	cd backend && .venv/bin/mypy app/
	@echo "${GREEN}Linting frontend...${RESET}"
	cd frontend && npm run lint

## Run database migrations
migrate: venv
	@echo "${GREEN}Running migrations...${RESET}"
	cd backend && .venv/bin/alembic upgrade head

## Create new migration
migrate-create: venv
	@echo "${GREEN}Creating migration: $(msg)${RESET}"
	cd backend && .venv/bin/alembic revision --autogenerate -m "$(msg)"

## Seed database with demo data
seed: venv
	@echo "${GREEN}Seeding database...${RESET}"
	cd backend && .venv/bin/python -m app.db.seed

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

## Alias for dev (as mentioned in requirements)
run: dev

## Complete initial setup
setup: venv install migrate seed
	@echo "${GREEN}✅ Setup complete!${RESET}"
	@echo ""
	@echo "${YELLOW}Next steps:${RESET}"
	@echo "  1. Start services: ${GREEN}make docker-up${RESET} or ${GREEN}make dev${RESET}"
	@echo "  2. Access frontend: ${GREEN}http://localhost:3000${RESET}"
	@echo "  3. Access API docs: ${GREEN}http://localhost:8000/docs${RESET}"

## Run all background workers
workers: venv
	@echo "${GREEN}Starting all background workers...${RESET}"
	cd backend && .venv/bin/python -m app.workers.run --all

## Run risk evaluation worker
worker-risk: venv
	@echo "${GREEN}Starting risk evaluation worker...${RESET}"
	cd backend && .venv/bin/python -m app.workers.run --queue risk_evaluation

## Run audit worker
worker-audit: venv
	@echo "${GREEN}Starting audit worker...${RESET}"
	cd backend && .venv/bin/python -m app.workers.run --queue audit

## Run webhook worker
worker-webhook: venv
	@echo "${GREEN}Starting webhook worker...${RESET}"
	cd backend && .venv/bin/python -m app.workers.run --queue webhook

## Start all services with Docker Compose
docker-up:
	@echo "${GREEN}Starting all services with Docker Compose...${RESET}"
	docker compose up -d
	@echo "${GREEN}✅ Services started${RESET}"
	@echo ""
	@echo "${YELLOW}Services:${RESET}"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - Backend: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - pgAdmin: http://localhost:5050 (if enabled)"

## Stop all Docker Compose services
docker-down:
	@echo "${GREEN}Stopping all Docker Compose services...${RESET}"
	docker compose down
	@echo "${GREEN}✅ Services stopped${RESET}"

## Check if required services are running
check-services:
	@echo "${GREEN}Checking services...${RESET}"
	@echo ""
	@echo "PostgreSQL:"
	@docker compose ps postgres | grep -q "Up" && echo "  ${GREEN}✅ Running${RESET}" || echo "  ${YELLOW}⚠️  Not running${RESET}"
	@echo ""
	@echo "Redis:"
	@docker compose ps redis | grep -q "Up" && echo "  ${GREEN}✅ Running${RESET}" || echo "  ${YELLOW}⚠️  Not running${RESET}"
	@echo ""
	@echo "Backend:"
	@docker compose ps backend 2>/dev/null | grep -q "Up" && echo "  ${GREEN}✅ Running${RESET}" || echo "  ${YELLOW}⚠️  Not running (optional)${RESET}"
	@echo ""
	@echo "Frontend:"
	@docker compose ps frontend 2>/dev/null | grep -q "Up" && echo "  ${GREEN}✅ Running${RESET}" || echo "  ${YELLOW}⚠️  Not running (optional)${RESET}"

## Reset database (drop + migrate + seed)
## Usage: make reset-db [CONFIRM=y]
reset-db: venv
	@if [ "$(CONFIRM)" != "y" ]; then \
		echo "${YELLOW}⚠️  This will reset the database!${RESET}"; \
		echo "${YELLOW}Run with CONFIRM=y to proceed: make reset-db CONFIRM=y${RESET}"; \
		exit 1; \
	fi
	@echo "${GREEN}Resetting database...${RESET}"
	@cd backend && .venv/bin/alembic downgrade base 2>/dev/null || true
	@cd backend && .venv/bin/alembic upgrade head
	@cd backend && .venv/bin/python -m app.db.seed
	@echo "${GREEN}✅ Database reset complete${RESET}"

## Format code (black + isort only)
format: venv
	@echo "${GREEN}Formatting backend code...${RESET}"
	cd backend && .venv/bin/black app/ tests/
	cd backend && .venv/bin/isort app/ tests/
	@echo "${GREEN}✅ Formatting complete${RESET}"

## Verify configuration and services
check: venv check-services
	@echo ""
	@echo "${GREEN}Checking configuration...${RESET}"
	@if [ ! -f "backend/.env" ]; then \
		echo "${YELLOW}⚠️  backend/.env not found. Copy from backend/.env.example${RESET}"; \
	else \
		echo "${GREEN}✅ backend/.env exists${RESET}"; \
	fi
	@if [ ! -f "frontend/.env" ]; then \
		echo "${YELLOW}⚠️  frontend/.env not found. Copy from frontend/.env.example${RESET}"; \
	else \
		echo "${GREEN}✅ frontend/.env exists${RESET}"; \
	fi
	@echo ""
	@echo "${GREEN}Checking Python virtual environment...${RESET}"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "${GREEN}✅ Virtual environment exists${RESET}"; \
	else \
		echo "${YELLOW}⚠️  Virtual environment not found. Run: make venv${RESET}"; \
	fi
	@echo ""
	@echo "${GREEN}✅ Configuration check complete${RESET}"

## Show backend logs
logs-backend:
	docker compose logs -f backend

## Show frontend logs
logs-frontend:
	docker compose logs -f frontend

## Show workers logs
logs-workers:
	docker compose logs -f worker-risk worker-audit worker-webhook
