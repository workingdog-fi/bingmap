# Claude Code Context Memory

## Project Overview
This is a production-ready Bing Maps tile proxy server that translates standard z/x/y tile coordinates to Bing Maps quadkey format.

## Key Components

### Core Server (`tile_server.py`)
- Multi-threaded Python HTTP server using ThreadingHTTPServer
- Converts z/x/y coordinates to quadkey format
- Validates input coordinates (zoom levels 0-23)
- Includes health check endpoint at `/health`
- Structured logging with configurable log levels
- Graceful shutdown handling (SIGTERM, SIGINT)
- Thread pool for concurrent tile fetching

### Infrastructure
- **Nginx Reverse Proxy**: Handles caching (7-day TTL), rate limiting (100 req/s per IP), and load balancing
- **Docker Setup**: Non-root user (tileserver:1000), health checks, resource limits
- **Environment Configuration**: Via `.env` file with CPU/memory limits, worker count, log level

### Deployment
- Service runs on port 8113 (configurable via EXTERNAL_PORT)
- Deploy using: `./deploy.sh`
- Uses `docker compose` (V2) commands

## API Format
- Request: `http://localhost:8113/{z}/{x}/{y}.jpg`
- Example: `http://localhost:8113/10/512/341.jpg`
- Proxies to: `http://ecn.t3.tiles.virtualearth.net/tiles/a{quadkey}.jpeg?g=1`

## Quadkey Conversion Algorithm
The server implements the standard Bing Maps quadkey algorithm:
- Each quadkey digit represents a quadrant: 0=NW, 1=NE, 2=SW, 3=SE
- Conversion iterates through zoom levels building the quadkey string

## Performance Features
- Nginx disk cache reduces upstream requests by ~90%
- Multi-threaded server for concurrent request handling
- Connection keepalive to upstream
- Cache locking to prevent thundering herd
- Background cache updates for stale content

## Security Measures
- Runs as non-root user in container
- Input validation for all tile coordinates
- Rate limiting prevents DoS attacks
- Security headers (X-Content-Type-Options, X-Frame-Options)
- No logging of sensitive data

## Monitoring
- Structured JSON logging
- X-Cache-Status header shows cache hits/misses
- X-Fetch-Time header shows upstream response time
- Health check endpoints for container orchestration

## Common Tasks
- View logs: `docker compose logs -f`
- Check cache status: Look for X-Cache-Status header in responses
- Scale workers: Adjust WORKERS env var and redeploy
- Clear cache: Remove nginx-cache volume

## Project Structure
```
bingmap/
├── tile_server.py       # Main Python server
├── nginx.conf          # Nginx configuration
├── docker-compose.yml  # Service orchestration
├── Dockerfile         # Container image
├── .env.example      # Environment template
├── deploy.sh        # Deployment script
└── README.md       # Documentation
```