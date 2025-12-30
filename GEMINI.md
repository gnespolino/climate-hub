# Climate Hub Context for Gemini

## Project Overview
**Climate Hub** is a modern, modular Python 3.12 application designed to control AC Freedom compatible HVAC devices (e.g., AUX, Coolwell, Ballu, Energolux). It offers both a comprehensive Command Line Interface (CLI) and a RESTful Web API via FastAPI.

-   **Core Functionality:** Device discovery, status monitoring, and control (power, temperature, mode, fan speed) via the AC Freedom Cloud API.
-   **Tech Stack:** Python 3.12, Poetry (dependency management), Pydantic v2 (validation), FastAPI (Web API), aiohttp (Async HTTP), Docker.
-   **UI/UX:** Web Dashboard (Bootstrap 5) and Terminal UI (Textual).

## Architecture
The project follows a strict Clean Architecture pattern with unidirectional dependency flow:

`cli / webapp` -> `acfreedom` -> `api`

1.  **`src/climate_hub/api`**: Low-level infrastructure layer. Handles HTTP/WebSocket communication, protocol encoding/decoding, encryption (AES-CBC), and Pydantic models for API data.
2.  **`src/climate_hub/acfreedom`**: Business logic layer. Manages device state, validation, and higher-level control operations (`DeviceManager`, `DeviceControl`).
3.  **`src/climate_hub/cli`**: Presentation layer. Implements the CLI commands using `argparse` and the TUI using `textual`.
4.  **`src/climate_hub/webapp`**: Presentation layer. Implements the REST API endpoints using FastAPI and serves the Web Dashboard.

**Key Principle:** No circular dependencies. Upper layers depend on lower layers.

## Development Environment

### Setup & Dependencies
Managed via **Poetry** and **Just**.

```bash
# Install dependencies and pre-commit hooks
just install
```

### Running the Application
```bash
# Run CLI commands
just run [COMMAND] [ARGS]
# Example: just run list
# Real-time TUI: just run watch

# Run Web API (dev mode with reload)
just webapp-dev
# Access at http://localhost:8000/
```

### Docker
```bash
# Build all images
just docker-build-all

# Start services (CLI + Webapp)
just docker-up

# View logs
just docker-logs
```

## Conventions & Standards

-   **Code Style:** strict adherence to **Ruff** (linting) and **Black** (formatting).
-   **Type Safety:** **Mypy** is configured in strict mode. All code must be fully type-hinted.
-   **Testing:** **Pytest** is used for unit and integration tests.
    -   Run tests: `just test`
    -   Run with coverage: `just test-cov`
-   **Pre-commit:** Git hooks enforce formatting, linting, and type checking before commits.
    -   Run manually: `just pre-commit`

## Key Files & Directories

-   **`src/climate_hub/`**: Source code root.
    -   **`api/client.py`**: Main `AuxCloudAPI` client with retry logic.
    -   **`acfreedom/manager.py`**: `DeviceManager` logic.
    -   **`cli/commands.py`**: CLI command implementations.
    -   **`cli/tui/`**: Textual-based Terminal UI.
    -   **`webapp/`**: FastAPI app, routes, and static/templates for the Dashboard.
-   **`tests/`**: Test suite mirroring the source structure.
-   **`Justfile`**: Command runner configuration (central hub for all dev tasks).
-   **`pyproject.toml`**: Project configuration (dependencies, tool settings).
-   **`docker-compose.yaml`**: Container orchestration config.
-   **`TODO.md`**: Tracks bugs, features, and improvements.

## Current Status & Roadmap (as of Dec 30, 2025)
-   **Completed Features:**
    -   **Core Stability:** Implemented `tenacity` retry logic, robust error handling, and strict type definitions (TypedDicts).
    -   **Web API:** Full CRUD for devices and control endpoints.
    -   **Web Dashboard:** Responsive HTML/JS dashboard with real-time updates via WebSocket (Phase 3).
    -   **Performance:** In-memory TTL caching (66% reduction) and smart polling strategies implemented.
    -   **TUI:** Interactive "Watch Mode" for the terminal.
    -   **Security:** Integrated `keyring` for secure password storage and added support for Environment Variables.
    -   **DevOps:** Docker infrastructure optimized for production; CI/CD pipelines (GitHub Actions) configured.
    -   **Testing:** Established a unit test suite and migrated Pydantic models to V2 `ConfigDict`.
-   **Next Steps:**
    1.  Implement comprehensive **Integration Tests** with real API interactions.
    2.  Add **Authentication** (JWT/API Key) to protect Web API endpoints.
    3.  Configure **CORS** for production deployment.
