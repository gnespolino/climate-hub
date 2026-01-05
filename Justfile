# Justfile - Common development commands

# Default recipe to display help information
default:
    @just --list

# Development setup
install:
    @echo "📦 Installing dependencies with Poetry..."
    poetry install --with dev
    @echo "🔗 Installing pre-commit hooks..."
    poetry run pre-commit install
    @echo "✅ Setup complete!"

# Run CLI in dev mode
run *ARGS:
    poetry run climate {{ARGS}}

# Run webapp in dev mode
webapp-dev:
    poetry run uvicorn climate_hub.webapp.main:app --reload --host 0.0.0.0 --port 8000

# Code quality
format-code:
    @echo "🎨 Formatting code..."
    poetry run black src tests
    poetry run ruff check --fix src tests

lint-code:
    @echo "🔍 Linting code..."
    poetry run ruff check src tests
    poetry run mypy src tests

# Testing
run-tests:
    @echo "🧪 Running tests..."
    poetry run pytest

test-coverage:
    @echo "📊 Running tests with coverage..."
    poetry run pytest --cov-report=html
    @echo "Coverage report: htmlcov/index.html"

watch-tests:
    poetry run ptw -- tests/

# Building
build-package:
    @echo "🏗️  Building package..."
    poetry build

docker-build-cli-image:
    @echo "🐳 Building CLI Docker image..."
    docker build -f docker/Dockerfile.cli -t climate-cli:latest .

docker-build-webapp-image:
    @echo "🐳 Building Webapp Docker image..."
    docker build -f docker/Dockerfile.webapp -t climate-webapp:latest .

docker-build-all-images: docker-build-cli-image docker-build-webapp-image

# Running with Docker
start-docker-containers:
    @echo "🚀 Starting Docker containers..."
    docker-compose up -d

stop-docker-containers:
    @echo "🛑 Stopping Docker containers..."
    docker-compose down

view-docker-logs:
    docker-compose logs -f

# Cleanup
clean-build-artifacts:
    @echo "🧹 Cleaning build artifacts..."
    rm -rf dist
    rm -rf htmlcov
    rm -rf .pytest_cache
    rm -rf .mypy_cache
    rm -rf .ruff_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete

# Pre-commit
run-pre-commit:
    poetry run pre-commit run --all-files
