# Climate Hub

Control hub per dispositivi HVAC compatibili con AC Freedom (CLI + Web API).

## Caratteristiche

Climate Hub è un'applicazione Python 3.12 moderna e modulare per controllare dispositivi compatibili con il protocollo AC Freedom Cloud API. Fornisce:

- **CLI completa**: Controllo da linea di comando per tutte le funzioni
- **Web API**: Server FastAPI con endpoint REST
- **Multi-brand**: Compatibile con AUX, Coolwell, Ballu, Energolux e altri brand che usano AC Freedom
- **Architettura pulita**: Separazione tra API layer, business logic e interfacce
- **Type-safe**: Type hints completi con mypy in strict mode
- **DevOps ready**: Docker, docker-compose, CI/CD, pre-commit hooks

### Funzionalità di controllo

- Lista dispositivi con stato in tempo reale
- Accensione/spegnimento
- Impostazione temperatura (16-30°C)
- Modalità operative: raffreddamento, riscaldamento, deumidificazione, ventilazione, auto
- Controllo velocità ventola: auto, low, medium, high, turbo, mute
- WebSocket per aggiornamenti in tempo reale

## Requisiti

- Python 3.12
- Poetry
- Account AC Freedom (richiesto per l'autenticazione)

## Installazione

### Con Poetry (raccomandato)

```bash
# Clona il repository
cd climate-hub

# Installa dipendenze e pre-commit hooks
just install

# Oppure manualmente
poetry install --with dev
poetry run pre-commit install
```

### Con Docker

```bash
# Avvia tutti i servizi (webapp + CLI)
just docker-up

# Oppure manualmente
docker-compose up -d
```

## Utilizzo

### CLI

#### Primo utilizzo - Login

Salva le tue credenziali AC Freedom:

```bash
climate login tua-email@example.com tua-password --region EU
```

Regioni disponibili: `EU` (Europa), `USA`, `CN` (Cina)

#### Comandi disponibili

```bash
# Lista dispositivi
climate list

# Stato dispositivo
climate status "Nome Condizionatore"

# Accendere/Spegnere
climate on "Nome Condizionatore"
climate off "Nome Condizionatore"

# Impostare temperatura
climate temp "Nome Condizionatore" 22

# Cambiare modalità (cool, heat, dry, fan, auto)
climate mode "Nome Condizionatore" cool

# Velocità ventola (auto, low, medium, high, turbo, mute)
climate fan "Nome Condizionatore" medium
```

#### Identificazione dispositivi

I dispositivi possono essere identificati in tre modi:
1. **ID completo** - Es: `a1b2c3d4-1234-5678-90ab-cdef12345678`
2. **Nome esatto** - Es: `Condizionatore Sala`
3. **Nome parziale** - Es: `sala` (match parziale case-insensitive)

### Web API

```bash
# Avvia server in modalità development
just webapp-dev

# Accedi all'health check
curl http://localhost:8000/health
```

## Configurazione

- **Credenziali**: Salvate in `~/.config/climate-hub/config.json`
- **Formato**: JSON con validazione Pydantic
- **Sicurezza**: Le credenziali sono salvate in chiaro - proteggere il file appropriatamente

## Development

### Comandi comuni

```bash
# Formatta codice
just format

# Lint con ruff e mypy
just lint

# Esegui test con coverage
just test-cov

# Build Docker images
just docker-build-all
```

### Struttura del progetto

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

- **Python 3.12** con pyenv
- **Poetry** per dependency management
- **Pydantic v2** per validazione dati
- **FastAPI** per web API
- **aiohttp** per async HTTP client
- **Docker** + docker-compose per deployment
- **GitHub Actions** per CI/CD
- **Pre-commit hooks** (ruff, mypy, black)

## Architettura

Il progetto segue i principi di clean architecture con dipendenze a strati:

```
cli → acfreedom → api
webapp → acfreedom → api
```

- **api**: Low-level API client (HTTP, WebSocket, encryption, protocol)
- **acfreedom**: Business logic (device management, validation, control)
- **cli**: User interface layer (command parsing, output formatting)
- **webapp**: REST API layer (FastAPI routes, health checks)

Basato sul reverse engineering dell'API AC Freedom, utilizzando il codice del progetto [maeek/ha-aux-cloud](https://github.com/maeek/ha-aux-cloud).

## Troubleshooting

### Login fallito
- Verifica email e password
- Controlla di aver selezionato la region corretta (`--region EU`)
- Verifica la connessione internet

### Dispositivo non trovato
- Esegui `climate list` per vedere tutti i dispositivi disponibili
- Assicurati che il condizionatore sia online nell'app AC Freedom
- Prova con l'ID completo invece del nome

### Comandi non funzionano
- Verifica che il dispositivo sia online con `climate status <device>`
- Controlla i log per errori
- Ri-esegui il login se le credenziali sono scadute

## Note tecniche

- **Dipendenza cloud**: Richiede connessione internet e funziona tramite i server cloud AC Freedom
- **Compatibilità**: Testato con condizionatori AUX/Coolwell. Compatibile con tutti i brand che usano l'app AC Freedom (Ballu, Energolux, ecc.)
- **WebSocket**: Supporto per aggiornamenti in tempo reale tramite WebSocket (con gestione corretta delle risorse)

## Licenza

Basato su [ha-aux-cloud](https://github.com/maeek/ha-aux-cloud) (MIT License)

## Alternative

Per eliminare la dipendenza dal cloud:
- [acfreedom-to-esphome](https://github.com/tibarbosa/acfreedom-to-esphome) - Adapter hardware per controllo locale via ESPHome
- [rbroadlink](https://github.com/manio/rbroadlink) - Controllo locale (richiede dissociazione da AC Freedom)

## Contributi

Pull requests e issues sono benvenute!
