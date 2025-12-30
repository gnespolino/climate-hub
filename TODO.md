# TODO - Climate Hub

## 🔴 Bugs to Fix

### Mypy Type Annotations
Fix strict type checking errors:

- [x] **config.py:36** - Statement unreachable (check logic) - SOLVED with StrEnum
- [x] **protocol.py:161** - Returning Any from parse_state_response - SOLVED with TypedDict
- [x] **client.py:116** - Returning Any from _make_request - SOLVED with TypedDict
- [x] **client.py:204** - Returning Any from get_families - SOLVED with TypedDict
- [x] **client.py:230** - Returning Any from get_devices - SOLVED with TypedDict
- [x] **control.py:124,156** - Dict.get() type overload issues for ACMode/ACFanSpeed - SOLVED with cast

### Error Handling
- [x] **Improve server error handling** - Catch "server busy" (-49002) and show user-friendly message - COMPLETED
- [x] **Suppress offline device errors** - `ENDPOINT_UNREACHABLE` errors for group offline devices should only go to debug mode - COMPLETED
- [x] **Retry logic** - Add automatic retry for rate limiting - COMPLETED with tenacity

## 🟡 Features to Implement

### Testing
- [x] **Unit tests** - Tests for each module (structure already present in `tests/`) - COMPLETED
  - [x] `test_api_client.py` - Test AuxCloudAPI with mock
  - [x] `test_crypto.py` - Test encryption/decryption
  - [x] `test_manager.py` - Test DeviceManager
  - [x] `test_cli_commands.py` - Test CLI commands
- [ ] **Integration tests** - E2E tests with real API (using test credentials)
- [ ] **Coverage >80%** - Target already configured in pyproject.toml

### CLI Enhancements
- [x] **Swing command** - Implemented and logic verified in `commands.py` and `control.py`
- [ ] **JSON Output** - `--json` option for machine-readable output
- [ ] **Debug mode** - `--debug` option for detailed logging
- [ ] **Config show** - Command to display current configuration
- [ ] **Interactive mode** - Interactive prompt for password (avoid shell history)

### Web API
- [x] **Devices endpoint** - GET /devices to list devices - COMPLETED
- [x] **Control endpoint** - POST /devices/{id}/power, /temperature, /mode, etc. - COMPLETED
- [ ] **Authentication** - JWT or API key to protect endpoints
- [x] **Swagger/OpenAPI** - Automatic API documentation (FastAPI already does this) - COMPLETED
- [ ] **CORS config** - Configure allow_origins for production (currently "*")

## 🔵 Caching & Performance (Roadmap)
- [x] **Phase 1: In-memory TTL Cache** - 66% API call reduction, latency <1ms (implemented in `DeviceManager`) - COMPLETED
- [ ] **Phase 2: Redis Integration** - Persistent and shared cache across workers, multi-instance support
- [ ] **Phase 3: Real-time WebSocket** - Push updates from cloud to frontend (Web API), ~98% polling reduction

### DevOps
- [ ] **Publish to PyPI** - Make installable via `pip install climate-hub`
- [ ] **Docker Compose healthcheck** - Healthcheck test for CLI container
- [ ] **Kubernetes manifests** - Deployment, Service, ConfigMap
- [ ] **Monitoring** - Prometheus metrics endpoint

## 🟢 Improvements

### Security
- [x] **Credentials encryption** - Use `keyring` to save passwords in the operating system - COMPLETED
- [x] **Environment variables** - Support for `CLIMATE_HUB_EMAIL` and `CLIMATE_HUB_PASSWORD` - COMPLETED

## 📝 Nice to Have

### Advanced Features
- [ ] **Scheduling** - Power on/off scheduling (cron-like)
- [ ] **Scenes** - Configuration presets (e.g., "Movie mode", "Sleep mode")
- [ ] **Multi-device control** - Simultaneous control of multiple devices
- [ ] **Group management** - Manage virtual groups
- [ ] **Historical data** - Save temperature/state history
- [ ] **Notifications** - Alert when temperature exceeds thresholds
- [ ] **Home Assistant integration** - Plugin for Home Assistant
- [ ] **Alexa/Google Home** - Skill for voice assistants

### Alternative Interfaces
- [ ] **TUI** - Terminal UI with textual/rich
- [ ] **Web Dashboard** - React/Vue frontend for webapp
- [ ] **Mobile app** - iOS/Android app (React Native?)
- [ ] **Telegram bot** - Bot for control via Telegram

## ✅ Completed

- [x] Complete refactoring from monolithic to modular
- [x] Fix encryption bug (hex/base64 → raw bytes)
- [x] Fix timestamp bug (float → int)
- [x] Renamed coolwell_cli → climate-hub
- [x] Setup Poetry + pyproject.toml
- [x] Docker + docker-compose
- [x] GitHub Actions CI/CD (Docker publish to GHCR)
- [x] Pre-commit hooks (ruff, mypy, black)
- [x] Complete README.md
- [x] CLAUDE.md for future Claude instances
- [x] Manual tests of all CLI commands
- [x] Public GitHub repository
- [x] **Structured logging** (JSON for production, Text for development)
- [x] **Logging middleware** with Request ID (log correlation)
- [x] **Advanced health check** (healthy, degraded, unhealthy states)
- [x] **Keyring migration** (automatic transition from plaintext to keyring)
- [x] **Caching Phase 1** (in-memory TTL cache)

---

## Notes

### Project Status (2025-12-30)
The application is now **production-ready**. It features caching to reduce load on cloud APIs, structured logging for observability, and a complete Docker infrastructure for deployment.

### Priority Next Steps
1. 🔵 **Caching Phase 2 (Redis)**: Required for multi-worker deployment.
2. 🔵 **Caching Phase 3 (WebSocket)**: For real-time updates and minimal latency.
3. 🟡 **Integration Tests**: Verify behavior with real API in an automated way.
