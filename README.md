# Bing Maps Tile Proxy Server

A high-performance HTTP proxy server that translates z/x/y tile requests to Bing Maps quadkey format. Built for production use with caching, rate limiting, and containerized deployment.

## Features

- **Tile Format Translation**: Converts standard z/x/y tile coordinates to Bing Maps quadkey format
- **High Performance**: Multi-threaded Python server with Nginx reverse proxy
- **Caching**: 7-day tile cache to reduce upstream requests
- **Rate Limiting**: 100 requests/second per IP address
- **Health Monitoring**: Built-in health check endpoints
- **Production Ready**: Non-root container, graceful shutdown, structured logging
- **Resource Management**: Configurable CPU and memory limits

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd bingmap
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Deploy:
```bash
./deploy.sh
```

The service will be available at `http://localhost:8113`

## Usage

Request tiles using standard z/x/y format:
```
http://localhost:8113/{z}/{x}/{y}.jpg
```

Example:
```
http://localhost:8113/10/512/341.jpg
```

The proxy automatically converts these coordinates to Bing Maps quadkey format and fetches the corresponding aerial imagery tile.

## Configuration

Edit `.env` file to customize:

```env
# External port for the service
EXTERNAL_PORT=8113

# Number of worker processes
WORKERS=4

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Resource limits
CPU_LIMIT=2
MEMORY_LIMIT=1G
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Client    │────▶│    Nginx    │────▶│   Tile Server   │
└─────────────┘     └─────────────┘     └─────────────────┘
                           │                      │
                           ▼                      ▼
                    ┌─────────────┐      ┌─────────────────┐
                    │    Cache    │      │   Bing Maps    │
                    └─────────────┘      └─────────────────┘
```

- **Nginx**: Handles caching, rate limiting, and load balancing
- **Tile Server**: Python service that performs coordinate translation
- **Cache**: Local disk cache with 7-day TTL

## Management Commands

View logs:
```bash
docker compose logs -f
```

Stop services:
```bash
docker compose down
```

Restart services:
```bash
docker compose restart
```

Scale workers:
```bash
docker compose up -d --scale tile-server=4
```

## API Endpoints

### Tiles
- `GET /{z}/{x}/{y}.jpg` - Fetch a tile

### Health Check
- `GET /health` - Service health status

## Performance

- Nginx caching reduces upstream requests by ~90%
- Multi-threaded server handles concurrent requests
- Rate limiting prevents abuse
- Typical response time: <100ms for cached tiles

## Security

- Runs as non-root user in container
- Input validation for tile coordinates
- Rate limiting to prevent DoS
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)

## Monitoring

The server provides structured JSON logging with:
- Request details (coordinates, quadkey)
- Response times
- Error tracking
- Cache hit/miss statistics (via X-Cache-Status header)

## Development

To run locally without Docker:
```bash
export PORT=8080
export LOG_LEVEL=DEBUG
python3 tile_server.py
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]