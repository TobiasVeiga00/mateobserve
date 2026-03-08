# Installation

## Quick Start (Docker)

The fastest way to get the full stack running:

```bash
git clone https://github.com/TobiasVeiga00/mateobserve.git
cd mateobserve
docker compose up
```

This starts:
- **Collector** at http://localhost:8001
- **Dashboard** at http://localhost:4000
- **PostgreSQL** at localhost:5432
- **Redis** at localhost:6379

## Install the SDK

Add MateObserve to your Python API:

```bash
pip install mateobserve
```

## Add to Your FastAPI App

```python
from fastapi import FastAPI
from mateobserve import ObserveMiddleware

app = FastAPI()
app.add_middleware(ObserveMiddleware)
```

That's it! Your API is now sending metrics to the collector.

## Configuration

All configuration is via environment variables:

### SDK (your API)

| Variable | Default | Description |
|----------|---------|-------------|
| `MATEOBSERVE_SERVICE_NAME` | `default` | Name of your service |
| `MATEOBSERVE_COLLECTOR_URL` | `http://localhost:8001` | Collector URL |
| `MATEOBSERVE_API_KEY` | *(empty)* | API key for authentication |
| `MATEOBSERVE_FLUSH_INTERVAL` | `5.0` | Seconds between batch flushes |
| `MATEOBSERVE_BATCH_SIZE` | `100` | Max events per batch |
| `MATEOBSERVE_ENABLED` | `true` | Enable/disable metrics collection |

### Collector

| Variable | Default | Description |
|----------|---------|-------------|
| `MATEOBSERVE_DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection |
| `MATEOBSERVE_REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `MATEOBSERVE_API_KEY` | *(empty)* | Required API key for ingestion |
| `MATEOBSERVE_CORS_ORIGINS` | `["http://localhost:3000","http://localhost:4000"]` | CORS origins |
| `MATEOBSERVE_AGGREGATION_INTERVAL_SECONDS` | `60` | Aggregation frequency |

### Dashboard

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_COLLECTOR_URL` | `http://localhost:8001` | Collector API URL |

## Development Setup

### Collector

```bash
cd collector
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uvicorn collector.main:app --reload --port 8001
```

### Dashboard

```bash
cd dashboard
npm install
npm run dev
```

### Example App

```bash
cd examples/fastapi-demo
uv venv && source .venv/bin/activate
uv pip install -e .
uvicorn main:app --reload --port 8000
```
