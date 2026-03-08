<div align="center">

<br />

<img src="https://em-content.zobj.net/source/apple/391/mate_1f9c9.png" width="80" alt="mate" />

# MateObserve

**API observability in 30 seconds. No config. No Grafana.**

One command spins up a full monitoring stack.  
One line of code instruments your FastAPI app.

[![PyPI](https://img.shields.io/pypi/v/mateobserve?color=3d6b4f&style=flat-square)](https://pypi.org/project/mateobserve/)
[![Python](https://img.shields.io/badge/python-3.10+-3d6b4f?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-3d6b4f?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-3d6b4f?style=flat-square)]()

</div>

---

## Quick Start

```bash
pip install mateobserve
mateobserve up
```

Open **http://localhost:4000** — your dashboard is ready.

---

## Add to Your App

```python
from fastapi import FastAPI
from mateobserve import ObserveMiddleware

app = FastAPI()
app.add_middleware(ObserveMiddleware)
```

That's it. Latency, errors, and traffic metrics flow to the dashboard in real time via SSE.

---

## What It Runs

`mateobserve up` launches a Docker-based observability stack:

| Component    | Purpose                               |
|--------------|---------------------------------------|
| **Collector** | FastAPI service that receives metrics |
| **PostgreSQL** | Stores raw and aggregated data       |
| **Redis**     | Caching and background processing    |
| **Dashboard** | Real-time web UI (Next.js + SSE)     |

Everything runs locally. Designed for development and small projects.

---

## Architecture

```
Your App (SDK middleware)
    │
    ▼
Collector (FastAPI) ──► PostgreSQL
    │                       │
    ├── Aggregation loop    │
    └── SSE stream ◄────────┘
         │
         ▼
    Dashboard (Next.js)
```

---

## CLI

```bash
mateobserve init      # Initialize stack files (~/.mateobserve/)
mateobserve up        # Start the observability stack
mateobserve down      # Stop everything
mateobserve status    # Show running containers
mateobserve doctor    # Check environment readiness
```

---

## Features

- **Zero config** — sensible defaults, works out of the box
- **One command** — `mateobserve up` starts the full stack
- **One line integration** — add the middleware, done
- **Real-time dashboard** — live updates via Server-Sent Events
- **API key auth** — protect your collector endpoints
- **Auto-aggregation** — background rollup for fast queries
- **Data retention** — automatic cleanup of old metrics

---

## Configuration

Set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MATEOBSERVE_API_KEY` | *(empty)* | API key for endpoint auth |
| `MATEOBSERVE_COLLECTOR_URL` | `http://localhost:8001` | Collector endpoint |
| `MATEOBSERVE_FLUSH_INTERVAL` | `5.0` | Seconds between metric flushes |
| `MATEOBSERVE_MAX_BUFFER_SIZE` | `10000` | Max buffered metrics before drop |
| `MATEOBSERVE_EXCLUDE_PATHS` | *(empty)* | Comma-separated paths to ignore |

---

## Project Structure

```
sdk/           Python SDK & CLI (pip install mateobserve)
collector/     FastAPI metrics collector
dashboard/     Next.js real-time dashboard
docker/        Docker Compose & Dockerfiles
tests/         Test suite
docs/          Documentation
examples/      Example integrations
```

---

## Contributing

See [docs/contributing.md](docs/contributing.md) for guidelines.

---

## License

[MIT](LICENSE) — MateObserve Contributors
