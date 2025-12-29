# TODO - Climate Hub

## 🔴 Bugs da Fixare

### Mypy Type Annotations
Fixare gli errori di strict type checking:

- [x] **config.py:36** - Statement unreachable (controllare logica) - RISOLTO con StrEnum
- [x] **protocol.py:161** - Returning Any from parse_state_response - RISOLTO con TypedDict
- [x] **client.py:116** - Returning Any from _make_request - RISOLTO con TypedDict
- [x] **client.py:204** - Returning Any from get_families - RISOLTO con TypedDict
- [x] **client.py:230** - Returning Any from get_devices - RISOLTO con TypedDict
- [x] **control.py:124,156** - Dict.get() type overload issues per ACMode/ACFanSpeed - RISOLTO con cast

### Error Handling
- [x] **Migliorare gestione errori server** - Catturare "server busy" (-49002) e mostrare messaggio user-friendly - COMPLETATO
- [x] **Sopprimere errori dispositivi offline** - Gli errori `ENDPOINT_UNREACHABLE` per dispositivi gruppo offline dovrebbero andare solo in debug mode - COMPLETATO
- [x] **Retry logic** - Aggiungere retry automatico per rate limiting - COMPLETATO con tenacity

## 🟡 Features da Implementare

### Testing
- [x] **Unit tests** - Test per ogni modulo (struttura già presente in `tests/`) - COMPLETATO
  - [x] `test_api_client.py` - Test AuxCloudAPI con mock
  - [x] `test_crypto.py` - Test encryption/decryption
  - [x] `test_manager.py` - Test DeviceManager
  - [x] `test_cli_commands.py` - Test comandi CLI
- [ ] **Integration tests** - Test E2E con API reale (usando credentials di test)
- [ ] **Coverage >80%** - Target già configurato in pyproject.toml

### CLI Enhancements
- [ ] **Comando swing** - Implementato ma mai testato (controllare se funziona)
- [ ] **Output JSON** - Opzione `--json` per output machine-readable
- [ ] **Debug mode** - Opzione `--debug` per logging dettagliato
- [ ] **Config show** - Comando per visualizzare configurazione corrente
- [ ] **Interactive mode** - Prompt interattivo per password (evitare shell history)

### Web API
- [x] **Endpoint dispositivi** - GET /devices per listare dispositivi - COMPLETATO
- [x] **Endpoint controllo** - POST /devices/{id}/power, /temperature, /mode, etc. - COMPLETATO
- [ ] **WebSocket endpoint** - Per aggiornamenti real-time
- [ ] **Authentication** - JWT o API key per proteggere endpoint
- [x] **Swagger/OpenAPI** - Documentazione API automatica (FastAPI lo fa già) - COMPLETATO
- [ ] **CORS config** - Configurare allow_origins per produzione (ora è "*")

### DevOps
- [ ] **Publish to PyPI** - Rendere installabile via `pip install climate-hub`
- [ ] **Docker Compose healthcheck** - Test healthcheck per CLI container
- [ ] **Kubernetes manifests** - Deployment, Service, ConfigMap
- [ ] **Monitoring** - Prometheus metrics endpoint

## 🟢 Improvements

### Security
- [x] **Credentials encryption** - Usare `keyring` per salvare password nel sistema operativo - COMPLETATO
- [x] **Environment variables** - Supporto per `CLIMATE_HUB_EMAIL` e `CLIMATE_HUB_PASSWORD` - COMPLETATO

## 📝 Nice to Have

### Features Avanzate
- [ ] **Scheduling** - Programmazione accensione/spegnimento (cron-like)
- [ ] **Scenes** - Preset di configurazioni (es. "Movie mode", "Sleep mode")
- [ ] **Multi-device control** - Controllo simultaneo di più dispositivi
- [ ] **Group management** - Gestire gruppi virtuali
- [ ] **Historical data** - Salvare storico temperature/stati
- [ ] **Notifications** - Alert quando temperatura supera soglie
- [ ] **Home Assistant integration** - Plugin per Home Assistant
- [ ] **Alexa/Google Home** - Skill per assistenti vocali

### Alternative Interfaces
- [ ] **TUI** - Terminal UI con textual/rich
- [ ] **Web Dashboard** - Frontend React/Vue per webapp
- [ ] **Mobile app** - App iOS/Android (React Native?)
- [ ] **Telegram bot** - Bot per controllo via Telegram

## ✅ Completato

- [x] Refactoring completo da monolithic a modular
- [x] Fix encryption bug (hex/base64 → raw bytes)
- [x] Fix timestamp bug (float → int)
- [x] Rinominazione coolwell_cli → climate-hub
- [x] Setup Poetry + pyproject.toml
- [x] Docker + docker-compose
- [x] GitHub Actions CI/CD
- [x] Pre-commit hooks (ruff, mypy, black)
- [x] README.md completo
- [x] CLAUDE.md per future Claude instances
- [x] Test manuali di tutti i comandi CLI
- [x] Repository GitHub pubblico

---

## Note

### Bug Critico Risolto (2025-12-29)
**Problema**: Login falliva con errore `-1005` ("数据错误") su tutte le regioni.

**Root Cause**: La funzione `encrypt_aes_cbc_zero_padding()` restituiva i dati criptati in formato **hex** (poi cambiato a base64), ma l'API AC Freedom si aspetta **raw bytes**.

**Fix**: Cambiato return type da `str` a `bytes` e rimosso `.hex()` / `base64.b64encode()`.

**Impatto**: Questo era il bug principale che impediva il funzionamento del login. Gli altri bug (timestamp float, padding errato) erano secondari.

### Priorità per Fix
1. 🔴 **Server busy error handling** - Impatta UX quando server è sotto carico
2. 🔴 **Mypy type annotations** - Blocca pre-commit hooks
3. 🟡 **Unit tests** - Necessari per CI/CD affidabile
4. 🟡 **Publish to PyPI** - Facilita installazione per utenti
