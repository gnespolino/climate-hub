# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Climate Hub is a modern, modular Python 3.12 application for controlling AC Freedom compatible HVAC devices. It provides both a command-line interface (CLI) and web API for device control. Compatible with multiple brands including AUX, Coolwell, Ballu, Energolux, and others using the AC Freedom Cloud API. The project follows clean architecture principles with strict separation of concerns.

**Tech Stack**: Python 3.12, Poetry, Pydantic v2, FastAPI, aiohttp, Textual (TUI), Tenacity (retry), Keyring (secure storage)

## Common Commands

### Development
```bash
# Install all dependencies (including dev)
just install

# Run CLI
just run [COMMAND] [ARGS]
# Example: just run list

# Run webapp in dev mode
just webapp-dev
# Access at http://localhost:8000 (dashboard) or http://localhost:8000/health

# Run TUI real-time dashboard
just run watch
# Interactive terminal dashboard with auto-refresh every 10s

# Format code
just format

# Lint code
just lint

# Run tests with coverage
just test-cov
```

### Docker
```bash
# Build Docker images
just docker-build-all

# Start services
just docker-up

# Stop services
just docker-down

# View logs
just docker-logs
```

### Pre-commit
```bash
# Run all pre-commit hooks
just pre-commit
```

## Architecture

### Module Structure
```
src/climate_hub/
├── api/              # Low-level cloud API (HTTP, WebSocket, protocol)
├── acfreedom/        # Business logic (device management, control)
├── cli/              # User interface (commands, config, formatters, TUI)
│   └── tui/          # Textual-based terminal UI (watch command)
└── webapp/           # FastAPI REST API + Bootstrap dashboard
```

### Dependency Flow
```
cli/ → acfreedom/ → api/
webapp/ → acfreedom/ → api/
```

**Key Principle**: No circular dependencies. Clean layered architecture.

### api/ - Cloud API Layer
- **client.py**: AuxCloudAPI HTTP client with tenacity retry logic (login, get_families, get_devices, set_device_params)
- **websocket.py**: Real-time updates via WebSocket (with async context manager)
- **protocol.py**: Request/response builders (directive headers, control requests)
- **models.py**: Pydantic models (Device, Family, ACMode, ACFanSpeed enums)
- **types.py**: TypedDict definitions for API responses (strict mypy compliance)
- **constants.py**: API URLs, encryption keys, parameter names
- **crypto.py**: AES-CBC encryption for login
- **exceptions.py**: AuxAPIError, ExpiredTokenError, ServerBusyError, etc.

**Usage**:
```python
from climate_hub.api import AuxCloudAPI

api = AuxCloudAPI(region="eu")
await api.login("email", "password")
families = await api.get_families()
```

### acfreedom/ - Business Logic Layer
- **coordinator.py**: DeviceCoordinator singleton orchestrates device discovery (Type 1 tasks) and active monitoring (Type 2 tasks), maintaining the Digital Twin cache.
- **control.py**: DeviceControl validates temperatures, modes, fan speeds.
- **device.py**: DeviceFinder searches by ID/name (exact, partial, case-insensitive).
- **exceptions.py**: ClimateHubError, DeviceNotFoundError, DeviceOfflineError, etc.
- **manager.py**: Legacy/CLI DeviceManager for direct API orchestration.

### webapp/ - FastAPI REST API + Real-Time Digital Twin
- **main.py**: FastAPI app with lifespan events that start the DeviceCoordinator and wait for initial sync.
- **dependencies.py**: DI for ConfigManager and DeviceCoordinator.
- **background.py**: CloudListener task - bridges Cloud AUX WebSocket -> Coordinator triggers.
- **websocket.py**: ConnectionManager - in-memory WebSocket connection manager for frontend clients.


### logging_config.py - Structured Logging
- **CustomJsonFormatter**: JSON formatter with custom fields (timestamp, level, logger, request_id)
- **setup_logging()**: Configure logging (level, format, file output)
- **configure_from_env()**: Auto-configure from environment variables
- **get_logger()**: Get logger instance

## Key Implementation Details

### Temperature Handling
API stores temperatures as tenths of degrees:
- User input: 22°C
- API format: 220 (integer)
- Use `DeviceControl.celsius_to_api()` and `api_to_celsius()`
- **Note**: Sending whole numbers (e.g., 22) causes "server busy" errors. Always convert to tenths.

### Device Lookup Strategy
`DeviceFinder.find_device()` tries in order:
1. Exact endpoint ID match
2. Exact friendly name (case-insensitive)
3. Partial name substring (case-insensitive)

### Performance & Caching Strategy
- **Startup**: Pre-populates cache with full device parameters (`fetch_params=True`). Takes ~8-10s but ensures instant UI load.
- **Runtime**: Uses in-memory cache with 60s TTL.
- **WebSocket**: Real-time updates invalidate cache (or push partial updates).
- **Frontend**:
  - **Optimistic UI**: Updates UI immediately on user interaction.
  - **Debouncing**: 800ms delay on temperature controls to batch rapid clicks.
  - **Smart Merging**: Merges incoming partial updates with existing state.

### WebSocket with Resource Management
```python
async with AuxCloudWebSocket(region, headers, session, userid) as ws:
    ws.add_websocket_listener(my_callback)
    # Session automatically closed on exit
```

### Pydantic Models
All data structures are Pydantic v2 models with validation:
```python
from climate_hub.api.models import Device, ACMode

device = Device(**api_data)  # Validates on creation
temp = device.get_temperature_target()  # Returns float in Celsius
```

### Custom Exceptions
Catch specific exceptions for better error handling:
```python
from climate_hub.acfreedom.exceptions import (
    DeviceNotFoundError,
    DeviceOfflineError,
    InvalidParameterError
)
```

### Real-Time WebSocket Architecture

**Overview**: Hybrid approach combining WebSocket for real-time updates with intelligent polling for offline devices, managed by a central **Digital Twin Coordinator**.

**Flow**:
```
Cloud AUX → CloudListener (background.py) → DeviceCoordinator (coordinator.py) → ConnectionManager → Frontend
                                                ↓
                                      Trigger Type 2 Monitor Task
                                                ↓
                                      Fetch fresh params & Notify
```

**Components**:

1. **CloudListener** (`background.py`):
   - Connects to Cloud AUX WebSocket with required headers.
   - Receives push messages (msgtype: "push").
   - Calls `coordinator.trigger_update(device_id)` immediately.
   - Exponential backoff retry.

2. **DeviceCoordinator** (`coordinator.py`):
   - **Singleton "Digital Twin"**: Maintains `_devices` cache.
   - **Type 2 Monitors**: Per-device async tasks waiting for triggers.
   - **Action**: When triggered, fetches fresh params from Cloud API.
   - **Notification**: Calls registered callbacks (`ConnectionManager.broadcast_device_update`).

3. **ConnectionManager** (`webapp/websocket.py`):
   - Receives updated Device object from Coordinator.
   - Broadcasts to all connected frontend clients via WebSocket.

4. **Frontend** (`dashboard.js`):
   - Receives update message.
   - Updates UI instantly (optimistic or driven by server message).

**Optimizations**:
- **Zero-Latency Reads**: REST API reads always hit the Coordinator's in-memory cache.
- **Event-Driven**: Updates happen only when needed (User action or Cloud push).
- **Debouncing (300ms)**: Batches rapid consecutive triggers to prevent API storms when multiple push messages arrive in quick succession.
- **Exponential Backoff**: Monitor loops retry with increasing delays (5s → 10s → 20s → 40s → 60s max) on errors, preventing log spam and API overload during failures.
- **Smart Error Recovery**: Error counters reset on successful fetches, allowing quick recovery from transient issues.

**Message Format**:
```javascript
// Backend → Frontend
{type: "device_update", deviceId: "00000000000000000000ec0bae3f027c"}

// Frontend → Backend (GET /devices/{id})
// Returns full device status with all fields (including envtemp)
```

**Key Features**:
- Device turned on/off: Real-time update (<100ms)
- Device offline: Ambient temp still updated (60s polling)
- Message bursts: Deduplicated to single API call
- Network resilience: Auto-reconnect with exponential backoff

### Configuration & Security

**Storage Locations**:
- **Config file**: `~/.config/climate-hub/config.json` (email, region, cached devices)
- **Passwords**: System keyring (via `keyring` library) - NOT in config file
- **Environment variables**: `CLIMATE_HUB_EMAIL`, `CLIMATE_HUB_PASSWORD` (override config)

**Priority Order** (ConfigManager.get_credentials()):
1. Environment variables (`CLIMATE_HUB_EMAIL`, `CLIMATE_HUB_PASSWORD`)
2. System keyring (password stored securely)
3. Legacy plaintext fallback (deprecated, auto-migrated)

**Usage**:
```python
from climate_hub.cli.config import ConfigManager

config = ConfigManager()
# Auto-detects credentials from env vars, keyring, or config file
email, password = config.get_credentials()
```

**Headless Deployment**:
```bash
export CLIMATE_HUB_EMAIL="user@example.com"
export CLIMATE_HUB_PASSWORD="secure_password"
just webapp-dev  # Auto-authenticates on startup
```

**CORS Configuration**:
- **Environment Variable**: `CORS_ORIGINS` controls allowed origins for cross-origin requests
- **Default**: `http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000,http://127.0.0.1:3000`
- **Production**: Set to specific domains (comma-separated): `CORS_ORIGINS="https://app.example.com,https://www.example.com"`
- **Development**: Use `CORS_ORIGINS="*"` to allow all origins (not recommended for production)

```bash
# Production example
export CORS_ORIGINS="https://climate.example.com,https://app.example.com"
just webapp-dev

# Development (allow all)
export CORS_ORIGINS="*"
just webapp-dev
```

### Structured Logging

**Environment Variables**:
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - default: INFO
- `LOG_FORMAT`: Output format ("json" or "text") - default: text
- `LOG_FILE`: Optional file path to write logs to

**Text Format** (human-readable, development):
```bash
export LOG_LEVEL=DEBUG
export LOG_FORMAT=text
just webapp-dev
# Output: 2025-12-29 23:59:13 - climate_hub.webapp.main - INFO - Starting Climate Hub v0.2.0
```

**JSON Format** (structured, production):
```bash
export LOG_LEVEL=INFO
export LOG_FORMAT=json
just webapp-dev
# Output: {"timestamp": "2025-12-29 23:59:13", "level": "INFO", "logger": "climate_hub.webapp.main", "message": "Starting Climate Hub v0.2.0"}
```

**Request Logging** (automatic with middleware):
- Every HTTP request gets a unique `X-Request-ID` header
- Logs include: method, path, status_code, duration_ms, client_ip
- Example JSON log:
```json
{
  "timestamp": "2025-12-29 23:59:15",
  "level": "INFO",
  "logger": "climate_hub.webapp.middleware",
  "message": "Request completed",
  "request_id": "abc-123-def-456",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration_ms": 45.23
}
```

**Programmatic Usage**:
```python
from climate_hub.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Operation started", extra={"user_id": "123", "device_id": "xyz"})
```

## Testing

Run tests:
```bash
just test          # Quick test
just test-cov      # With coverage report (htmlcov/index.html)
```

Fixtures in `tests/conftest.py`:
- `mock_api`: Mock AuxCloudAPI
- `mock_device`: Sample Device object
- `mock_family`: Sample Family object

## Security Notes

- **Credentials**: Passwords stored in system keyring (secure) or environment variables
  - **Legacy**: Old `config.json` files with plaintext passwords still supported (deprecated)
  - **Recommended**: Use `climate login` to migrate to keyring automatically
- **Environment Variables**: Use `CLIMATE_HUB_EMAIL` and `CLIMATE_HUB_PASSWORD` for CI/CD
- **Cloud Dependency**: Requires internet and AUX cloud servers
- **API Keys**: Hardcoded in `api/constants.py` (from reverse engineering)
- **CORS**: Webapp allows all origins by default - configure for production

## Migration from Old Structure

Old files **deleted**:
- `cli.py` → split into `cli/{main,commands,config,formatters}.py`
- `api/aux_cloud.py` → split into `api/{client,protocol}.py`
- `api/aux_cloud_ws.py` → `api/websocket.py` (with fixes)
- `api/const.py` → split into `api/{constants,models}.py`
- `api/util.py` → `api/crypto.py`

**CLI Commands**:
```bash
# Authentication (stores password in keyring)
climate login <email> <password> --region EU

# Device management
climate list                    # List all devices
climate status <device>         # Show device details

# Control commands
climate on/off <device>         # Power control
climate temp <device> <temp>    # Set temperature (16-30°C)
climate mode <device> <mode>    # Set mode (cool/heat/dry/fan/auto)
climate fan <device> <speed>    # Set fan speed (auto/low/medium/high/turbo/mute)
climate swing <device> <mode>   # Set swing mode

# Real-time monitoring
climate watch                   # Launch Textual TUI dashboard
```

**Web API Endpoints**:
```bash
GET  /health                    # Comprehensive health check (status, version, config, auth, cloud API)
GET  /                          # Bootstrap dashboard (HTML)
GET  /devices                   # List all devices (JSON)
GET  /devices/{id}              # Get device status
POST /devices/{id}/power        # {"on": true/false}
POST /devices/{id}/temperature  # {"temperature": 22}
POST /devices/{id}/mode         # {"mode": "cool"}
POST /devices/{id}/fan          # {"speed": "auto"}
```

**Health Check Response**:
```json
{
  "status": "healthy",  // "healthy", "degraded", or "unhealthy"
  "version": "0.2.0",
  "config": {
    "available": true,
    "message": "Configuration loaded successfully"
  },
  "authentication": {
    "available": true,
    "message": "Credentials configured"
  },
  "cloud_api": {
    "available": true,
    "message": "Cloud API responding"
  }
}
```

## Code Quality Standards

- **Type Hints**: 100% coverage (mypy --strict)
- **Line Length**: Max 100 (black, ruff)
- **File Size**: Target <200 lines (exceptions: client.py ~350, manager.py ~250)
- **Docstrings**: All public functions/classes
- **Linting**: ruff + mypy + black
- **Pre-commit**: Hooks enforce standards

## Troubleshooting

### "Module not found" errors
```bash
poetry install
poetry run climate list
```

### "No credentials" error
```bash
poetry run climate login <email> <password>
```

### WebSocket connection issues
Check region setting in config (`~/.config/climate-hub/config.json`)

### Type errors
```bash
just lint  # Run mypy
```

## Development Workflow

1. Create feature branch
2. Make changes
3. Run `just format` and `just lint`
4. Run `just test`
5. Commit (pre-commit hooks run automatically)
6. Push (GitHub Actions CI runs tests + build)

## Resources

- Original project: [maeek/ha-aux-cloud](https://github.com/maeek/ha-aux-cloud)
- Poetry docs: https://python-poetry.org/
- Pydantic v2: https://docs.pydantic.dev/
- FastAPI: https://fastapi.tiangolo.com/
