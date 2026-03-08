# MateObserve 🧉

**Observability for Python apps in one command.**

MateObserve is a Python SDK + CLI that gives you instant API observability.
Install the package, run one command, and get a local monitoring stack with
Prometheus and Grafana — no manual configuration required.

## Quick Start

```bash
pip install mateobserve
mateobserve up
```

That's it. This launches the full observability stack via Docker and opens:

- **Dashboard** — [http://localhost:4000](http://localhost:4000)
- **Collector** — [http://localhost:8001](http://localhost:8001)

## What It Runs

`mateobserve up` starts a Docker Compose stack with:

- **Prometheus** — metrics collection and storage
- **Grafana** — dashboards and visualization

Both legacy (`docker-compose`) and modern (`docker compose`) syntaxes are
automatically detected.

## CLI Usage

```bash
mateobserve up       # Start the observability stack
mateobserve down     # Stop the stack
mateobserve status   # Show running containers
mateobserve doctor   # Check environment readiness
```

## Python Integration

Add the middleware to any FastAPI or Starlette app:

```python
from fastapi import FastAPI
from mateobserve import ObserveMiddleware

app = FastAPI()
app.add_middleware(ObserveMiddleware)
```

Your API will automatically send latency, error, and traffic metrics to the
MateObserve collector.

### Configuration

All settings are optional and controlled via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MATEOBSERVE_SERVICE_NAME` | auto-detected | Name of your service |
| `MATEOBSERVE_COLLECTOR_URL` | `http://localhost:8001` | Collector endpoint |
| `MATEOBSERVE_API_KEY` | *(empty)* | API key for authentication |
| `MATEOBSERVE_ENABLED` | `true` | Enable/disable metric collection |

## Why MateObserve

Setting up observability usually means stitching together multiple tools,
writing configuration files, and debugging Docker setups. MateObserve removes
that friction — one `pip install` and one command gets you a working stack so
you can focus on building your application.

## Project Status

MateObserve is in early development (v0.1.x). The core SDK and CLI are
functional and usable. Feedback and contributions are welcome.

## License

MIT — see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://github.com/TobiasVeiga00/mateobserve/tree/main/docs)
- [Source](https://github.com/TobiasVeiga00/mateobserve)
- [Issues](https://github.com/TobiasVeiga00/mateobserve/issues)
