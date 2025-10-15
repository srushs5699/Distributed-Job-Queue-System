.PHONY: help build up down restart logs test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services starting..."
	@echo "API: http://localhost:5000"
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Tail logs from all services
	docker-compose logs -f

logs-api: ## Tail API logs
	docker-compose logs -f api

logs-workers: ## Tail worker logs
	docker-compose logs -f worker_high_1 worker_default_1 worker_low_1

test: ## Run tests with coverage
	pytest --cov=. --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	pytest -m unit

test-integration: ## Run integration tests only
	pytest -m integration

test-watch: ## Run tests in watch mode
	pytest-watch

clean: ## Remove containers, volumes, and images
	docker-compose down -v
	docker system prune -f

status: ## Show status of all services
	docker-compose ps

health: ## Check health of API
	@curl -s http://localhost:5000/health | python -m json.tool

metrics: ## Get current metrics
	@curl -s http://localhost:5000/api/v1/metrics | python -m json.tool

submit-job: ## Submit a test job
	@curl -X POST http://localhost:5000/api/v1/jobs \
		-H "Content-Type: application/json" \
		-d '{"task": "process_data", "data": {"items": 100}, "priority": "high", "retry": true}' \
		| python -m json.tool

scale-workers: ## Scale workers (usage: make scale-workers COUNT=3)
	docker-compose up -d --scale worker_default=$(COUNT)

install: ## Install Python dependencies
	pip install -r requirements.txt

dev: ## Start development environment
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

benchmark: ## Run performance benchmarks
	python scripts/benchmark.py