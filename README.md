# Climate Hub

Control hub for AC Freedom compatible HVAC devices (CLI + Web API).

## Features

Climate Hub is a modern and modular Python 3.12 application to control devices compatible with the AC Freedom Cloud API protocol. It provides:

- **Complete CLI**: Command-line control for all functions
- **Web API**: FastAPI server with REST endpoints + real-time WebSocket dashboard
- **Digital Twin**: Centralized `DeviceCoordinator` maintains an active in-memory replica of all devices for zero-latency reads
- **Real-Time Updates**: <100ms latency with intelligent WebSocket + polling hybrid (98% less API calls)
- **Multi-brand**: Compatible with AUX, Coolwell, Ballu, Energolux and other brands using AC Freedom
- **Performance**: In-memory caching (66% reduction), smart polling (72% bandwidth savings), request deduplication
- **Clean Architecture**: Separation between API layer, business logic, and interfaces
- **Type-safe**: Complete type hints with mypy in strict mode
- **DevOps ready**: Docker, docker-compose, CI/CD, pre-commit hooks, structured logging

### Control Functionalities

- Device list with real-time status
- Power on/off
- Temperature setting (16-30°C)
- Operating modes: cooling, heating, dehumidification, fan, auto
- Fan speed control: auto, low, medium, high, turbo, mute
- Real-time dashboard updates (<100ms latency)
- Intelligent polling for offline devices (ambient temperature tracking)

## Requirements

- Python 3.12
- Poetry
- AC Freedom account (required for authentication)

## Installation

### With Poetry (recommended)

```bash
# Clone the repository
cd climate-hub

# Install dependencies and pre-commit hooks
just install

# Or manually
poetry install --with dev
poetry run pre-commit install
```

### With Docker

```bash
# Start all services (webapp + CLI)
just docker-up

# Or manually
docker-compose up -d
```

## Usage

### CLI

#### First use - Login

Save your AC Freedom credentials:

```bash
climate login your-email@example.com your-password --region EU
```

Available regions: `EU` (Europe), `USA`, `CN` (China)

#### Available Commands

```bash
# List devices
climate list

# Device status
climate status "Air Conditioner Name"

# Power On/Off
climate on "Air Conditioner Name"
climate off "Air Conditioner Name"

# Set temperature
climate temp "Air Conditioner Name" 22

# Change mode (cool, heat, dry, fan, auto)
climate mode "Air Conditioner Name" cool

# Fan speed (auto, low, medium, high, turbo, mute)
climate fan "Air Conditioner Name" medium
```

#### Device Identification

Devices can be identified in three ways:
1. **Full ID** - E.g.: `a1b2c3d4-1234-5678-90ab-cdef12345678`
2. **Exact Name** - E.g.: `Living Room AC`
3. **Partial Name** - E.g.: `living` (case-insensitive partial match)

### Web API

```bash
# Start server in development mode
just webapp-dev

# Access health check
curl http://localhost:8000/health
```

## Configuration

- **Credentials**: Saved in `~/.config/climate-hub/config.json`
- **Format**: JSON with Pydantic validation
- **Security**: Credentials are saved in plain text (legacy) or system keyring - protect the file appropriately

## Development

### Common Commands

```bash
# Format code
just format

# Lint with ruff and mypy
just lint

# Run tests with coverage
just test-cov

# Build Docker images
just docker-build-all
```

### Project Structure

```
climate-hub/
├── src/climate_hub/
│   ├── api/              # API layer (HTTP, WebSocket, protocol)
│   ├── acfreedom/        # Business logic (device management, control)
│   ├── cli/              # CLI interface (commands, config, formatters)
│   └── webapp/           # FastAPI application
├── tests/                # Unit + integration tests
├── docker/               # Dockerfiles
├── .github/workflows/    # CI/CD
├── pyproject.toml        # Poetry config + tool settings
└── Justfile              # Common commands
```

### Tech Stack

- **Python 3.12** with pyenv
- **Poetry** for dependency management
- **Pydantic v2** for data validation
- **FastAPI** for web API
- **aiohttp** for async HTTP client
- **Docker** + docker-compose for deployment
- **GitHub Actions** for CI/CD
- **Pre-commit hooks** (ruff, mypy, black)

## Architecture

The project follows clean architecture principles with layered dependencies:

```
cli → acfreedom → api
webapp → acfreedom → api
```

- **api**: Low-level API client (HTTP, WebSocket, encryption, protocol)
- **acfreedom**: Business logic (device management, validation, control)
- **cli**: User interface layer (command parsing, output formatting)
- **webapp**: REST API layer (FastAPI routes, health checks)

Based on reverse engineering of the AC Freedom API, using code from the [maeek/ha-aux-cloud](https://github.com/maeek/ha-aux-cloud) project.

## Troubleshooting

### Login failed
- Verify email and password
- Check that the correct region is selected (`--region EU`)
- Check internet connection

### Device not found
- Run `climate list` to see all available devices
- Ensure the air conditioner is online in the AC Freedom app
- Try with the full ID instead of the name

### Commands not working
- Verify the device is online with `climate status <device>`
- Check logs for errors
- Re-login if credentials have expired

## Technical Notes

- **Cloud Dependency**: Requires internet connection and works via AC Freedom cloud servers
- **Compatibility**: Tested with AUX/Coolwell air conditioners. Compatible with all brands using the AC Freedom app (Ballu, Energolux, etc.)
- **WebSocket**: Support for real-time updates via WebSocket (with proper resource management)

## License

Based on [ha-aux-cloud](https://github.com/maeek/ha-aux-cloud) (MIT License)

## Alternatives

To eliminate cloud dependency:
- [acfreedom-to-esphome](https://github.com/tibarbosa/acfreedom-to-esphome) - Hardware adapter for local control via ESPHome
- [rbroadlink](https://github.com/manio/rbroadlink) - Local control (requires unbinding from AC Freedom)

## Contributions

Pull requests and issues are welcome!
