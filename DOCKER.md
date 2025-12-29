# Docker Deployment Guide

This guide covers deploying Climate Hub using Docker and Docker Compose.

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+ (or `docker-compose` 1.29+)
- AC Freedom cloud account (AUX, Coolwell, Ballu, etc.)

### 1. Pull the Image

```bash
docker pull ghcr.io/gnespolino/climate-hub:latest
```

### 2. Configure Credentials

**Option A: Using Config File (Recommended)**

First, login using the CLI to create your config file:

```bash
docker run --rm -it \
  -v $(pwd)/config:/root/.config/climate-hub \
  ghcr.io/gnespolino/climate-hub:latest \
  climate login your-email@example.com your-password --region eu
```

**Option B: Using Environment Variables**

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
CLIMATE_EMAIL=your-email@example.com
CLIMATE_PASSWORD=your-password
CLIMATE_REGION=eu
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 3. Start the Webapp

```bash
docker-compose up -d
```

The webapp will be available at: **http://localhost:8090**

**Note**: Using port 8090 by default to avoid conflicts with common services (Nextcloud on 8080, etc.)

### 4. Verify Deployment

Check the health endpoint:

```bash
curl http://localhost:8090/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "config": {"available": true, "message": "Configuration loaded successfully"},
  "authentication": {"available": true, "message": "Credentials configured"},
  "cloud_api": {"available": true, "message": "Cloud API responding"}
}
```

## Docker Compose Configuration

### Basic Setup

The default `docker-compose.yml` configuration:

```yaml
services:
  webapp:
    image: ghcr.io/gnespolino/climate-hub:latest
    ports:
      - "8090:8000"  # Host:Container
    volumes:
      - ./config:/root/.config/climate-hub
    environment:
      - LOG_LEVEL=INFO
      - LOG_FORMAT=json
```

### Custom Port

To use a different port (e.g., 8091):

```yaml
services:
  webapp:
    ports:
      - "8091:8000"  # Host:Container
```

### Enable File Logging

Uncomment the logs volume in `docker-compose.yml`:

```yaml
volumes:
  - ./config:/root/.config/climate-hub
  - ./logs:/app/logs
```

Then set the log file in `.env`:

```bash
LOG_FILE=/app/logs/climate-hub.log
```

### Production Setup

For production, use:

```yaml
services:
  webapp:
    image: ghcr.io/gnespolino/climate-hub:latest
    restart: always
    ports:
      - "127.0.0.1:8090:8000"  # Bind to localhost only
    volumes:
      - ./config:/root/.config/climate-hub:ro  # Read-only
    environment:
      - LOG_LEVEL=WARNING
      - LOG_FORMAT=json
      - LOG_FILE=/app/logs/climate-hub.log
    healthcheck:
      interval: 30s
      timeout: 3s
      retries: 3
```

Then use a reverse proxy (nginx, Caddy) for HTTPS.

## Management Commands

### View Logs

```bash
docker-compose logs -f webapp
```

### Restart Service

```bash
docker-compose restart webapp
```

### Stop Service

```bash
docker-compose down
```

### Update to Latest Version

```bash
docker-compose pull
docker-compose up -d
```

### Execute CLI Commands

```bash
docker-compose exec webapp climate list
docker-compose exec webapp climate status "Living Room"
```

## Building from Source

### Build Locally

```bash
# Build webapp image
just docker-build-webapp

# Or using docker directly
docker build -f docker/Dockerfile.webapp -t climate-webapp:local .
```

### Use Local Image

Update `docker-compose.yml`:

```yaml
services:
  webapp:
    build:
      context: .
      dockerfile: docker/Dockerfile.webapp
    # image: ghcr.io/gnespolino/climate-hub:latest  # Comment this out
```

Then start:

```bash
docker-compose up -d --build
```

## GitHub Container Registry

Images are automatically built and published to GitHub Container Registry on every push to `main`.

### Available Tags

- `latest` - Latest stable build from main branch
- `main-<sha>` - Specific commit (e.g., `main-abc1234`)
- `v1.0.0` - Semantic version tags (when tagged)

### Pull Specific Version

```bash
docker pull ghcr.io/gnespolino/climate-hub:v1.0.0
```

## Network Configuration

### Home Network Deployment

To access the webapp from other devices on your home network:

1. Find your server's IP address:
   ```bash
   hostname -I
   ```

2. Update `docker-compose.yml` to bind to all interfaces:
   ```yaml
   ports:
     - "8090:8000"  # Accessible from network
   ```

3. Access from other devices:
   ```
   http://192.168.1.100:8090
   ```

### Using Reverse Proxy

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name climate.home.local;

    location / {
        proxy_pass http://localhost:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker-compose logs webapp
```

Common issues:
- Missing credentials: Configure `.env` or mount config file
- Port already in use: Change port in `docker-compose.yml`
- Permission errors: Check volume mount permissions

### Health Check Failing

```bash
docker-compose exec webapp curl http://localhost:8000/health
```

If cloud API is unavailable:
- Verify credentials are correct
- Check internet connectivity
- Verify AC Freedom cloud service is operational

### Can't Access from Other Devices

- Check firewall rules: `sudo ufw allow 8090`
- Verify port binding: Should be `8090:8000`, not `127.0.0.1:8090:8000`
- Check Docker network: `docker network inspect climate-hub_climate-hub`

### Credentials Not Persisting

Ensure the config volume is mounted:
```bash
docker-compose exec webapp ls -la /root/.config/climate-hub
```

Should show `config.json` if using config file method.

## Security Considerations

1. **Never commit `.env` file** - It contains plaintext credentials
2. **Use read-only volumes** in production: `:ro` flag
3. **Bind to localhost** when using reverse proxy: `127.0.0.1:8000:8000`
4. **Prefer config file** over environment variables for credentials
5. **Use HTTPS** with reverse proxy for remote access
6. **Update regularly**: `docker-compose pull && docker-compose up -d`

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
