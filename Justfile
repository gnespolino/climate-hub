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
format:
    @echo "🎨 Formatting code..."
    poetry run black src tests
    poetry run ruff check --fix src tests

lint:
    @echo "🔍 Linting code..."
    poetry run ruff check src tests
    poetry run mypy src tests

# Testing
test:
    @echo "🧪 Running tests..."
    poetry run pytest

test-cov:
    @echo "📊 Running tests with coverage..."
    poetry run pytest --cov-report=html
    @echo "Coverage report: htmlcov/index.html"

test-watch:
    poetry run ptw -- tests/

# Building
build:
    @echo "🏗️  Building package..."
    poetry build

docker-build-cli:
    @echo "🐳 Building CLI Docker image..."
    docker build -f docker/Dockerfile.cli -t climate-cli:latest .

docker-build-webapp:
    @echo "🐳 Building Webapp Docker image..."
    docker build -f docker/Dockerfile.webapp -t climate-webapp:latest .

docker-build-all: docker-build-cli docker-build-webapp

# Running with Docker
docker-up:
    @echo "🚀 Starting Docker containers..."
    docker-compose up -d

docker-down:
    @echo "🛑 Stopping Docker containers..."
    docker-compose down

docker-logs:
    docker-compose logs -f

# Cleanup
clean:
    @echo "🧹 Cleaning build artifacts..."
    rm -rf dist
    rm -rf htmlcov
    rm -rf .pytest_cache
    rm -rf .mypy_cache
    rm -rf .ruff_cache
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete

# Pre-commit
pre-commit:
    poetry run pre-commit run --all-files
