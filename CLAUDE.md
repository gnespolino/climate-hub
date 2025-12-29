# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Climate Hub is a modern, modular Python 3.12 application for controlling AC Freedom compatible HVAC devices. It provides both a command-line interface (CLI) and web API for device control. Compatible with multiple brands including AUX, Coolwell, Ballu, Energolux, and others using the AC Freedom Cloud API. The project follows clean architecture principles with strict separation of concerns.

**Tech Stack**: Python 3.12, Poetry, Pydantic v2, FastAPI, aiohttp

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
# Access at http://localhost:8000/health

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
├── cli/              # User interface (commands, config, formatters)
└── webapp/           # FastAPI REST API
```

### Dependency Flow
```
cli/ → acfreedom/ → api/
webapp/ → acfreedom/ → api/
```

**Key Principle**: No circular dependencies. Clean layered architecture.

### api/ - Cloud API Layer
- **client.py**: AuxCloudAPI HTTP client (login, get_families, get_devices, set_device_params)
- **websocket.py**: Real-time updates via WebSocket (with async context manager)
- **protocol.py**: Request/response builders (directive headers, control requests)
- **models.py**: Pydantic models (Device, Family, ACMode, ACFanSpeed enums)
- **constants.py**: API URLs, encryption keys, parameter names
- **crypto.py**: AES-CBC encryption for login
- **exceptions.py**: AuxAPIError, ExpiredTokenError, etc.

**Usage**:
```python
from climate_hub.api import AuxCloudAPI

api = AuxCloudAPI(region="eu")
await api.login("email", "password")
families = await api.get_families()
```

### acfreedom/ - Business Logic Layer
- **manager.py**: DeviceManager orchestrates API calls, caches devices
- **control.py**: DeviceControl validates temperatures, modes, fan speeds
- **device.py**: DeviceFinder searches by ID/name (exact, partial, case-insensitive)
- **exceptions.py**: ClimateHubError, DeviceNotFoundError, DeviceOfflineError, etc.

**Usage**:
```python
from climate_hub.acfreedom.manager import DeviceManager

manager = DeviceManager(region="eu")
await manager.login("email", "password")
devices = await manager.refresh_devices()
await manager.set_temperature("living_room", 22)
```

### cli/ - User Interface Layer
- **main.py**: Argparse setup, command routing, entry point
- **commands.py**: CLICommands implements all commands (login, list, status, on/off, temp, mode, fan, swing)
- **config.py**: ConfigManager handles ~/.config/climate-hub/config.json (Pydantic validated)
- **formatters.py**: OutputFormatter formats device lists, status, success/error messages

### webapp/ - FastAPI REST API
- **main.py**: FastAPI app with CORS, health endpoint
- **routes/health.py**: GET /health → {status, version}

**Future**: Add device control endpoints

## Key Implementation Details

### Temperature Handling
API stores temperatures as tenths of degrees:
- User input: 22°C
- API format: 220
- Use `DeviceControl.celsius_to_api()` and `api_to_celsius()`

### Device Lookup Strategy
`DeviceFinder.find_device()` tries in order:
1. Exact endpoint ID match
2. Exact friendly name (case-insensitive)
3. Partial name substring (case-insensitive)

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

### Configuration
- **Location**: `~/.config/climate-hub/config.json`
- **Format**: JSON with email, password (plaintext), region, cached devices
- **Management**: ConfigManager with Pydantic validation

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

- **Credentials**: Stored in plaintext in `~/.config/climate-hub/config.json` - protect this file
- **Cloud Dependency**: Requires internet and AUX cloud servers
- **API Keys**: Hardcoded in `api/constants.py` (from reverse engineering)

## Migration from Old Structure

Old files **deleted**:
- `cli.py` → split into `cli/{main,commands,config,formatters}.py`
- `api/aux_cloud.py` → split into `api/{client,protocol}.py`
- `api/aux_cloud_ws.py` → `api/websocket.py` (with fixes)
- `api/const.py` → split into `api/{constants,models}.py`
- `api/util.py` → `api/crypto.py`

**Backward Compatibility**: CLI commands unchanged
```bash
climate login <email> <password> --region EU
climate list
climate status <device>
climate on/off/temp/mode/fan/swing <device> [args]
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
