.PHONY: dev test lint format install clean

# Development
dev:
	docker compose up --build

dev-detached:
	docker compose up --build -d

down:
	docker compose down

# Install dependencies
install:
	cd apps/api && pip install -e ".[dev]"
	cd apps/worker && pip install -e ".[dev]"
	cd apps/web && npm install

# Testing
test: test-api test-web
	@echo "All tests passed!"

test-api:
	cd apps/api && pytest tests/ -v

test-web:
	cd apps/web && npm test

# Linting
lint: lint-python lint-js
	@echo "Linting complete!"

lint-python:
	cd apps/api && ruff check . && mypy app/
	cd apps/worker && ruff check . && mypy app/

lint-js:
	cd apps/web && npm run lint

# Formatting
format: format-python format-js
	@echo "Formatting complete!"

format-python:
	cd apps/api && ruff format .
	cd apps/worker && ruff format .

format-js:
	cd apps/web && npm run format

# Clean up
clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf apps/web/.next
	rm -rf apps/web/node_modules
