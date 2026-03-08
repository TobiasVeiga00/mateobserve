# Example: FastAPI + MateObserve

This is a minimal FastAPI application demonstrating MateObserve integration.

## Setup

```bash
cd examples/fastapi-demo
uv venv && source .venv/bin/activate
uv pip install -e .
```

## Run

```bash
# Make sure the collector is running first
# docker compose up  (from repo root)

# Set environment variables (optional)
export MATEOBSERVE_SERVICE_NAME=user-api
export MATEOBSERVE_COLLECTOR_URL=http://localhost:8001

# Start the demo API
uvicorn main:app --reload --port 8000
```

## Test endpoints

```bash
curl http://localhost:8000/users
curl http://localhost:8000/users/1
curl http://localhost:8000/slow
curl http://localhost:8000/error
```

Open the dashboard at http://localhost:4000 to see your metrics.
