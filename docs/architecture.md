# Architecture

MateObserve has three core components that work together to provide instant API observability.

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Your FastAPI    │     │   MateObserve    │     │   MateObserve    │
│  Application     │────▶│   Collector      │────▶│   Dashboard      │
│  + SDK Middleware│     │   (FastAPI)      │     │   (Next.js)      │
└─────────────────┘     └──────────────────┘     └──────────────────┘
                               │                         │
                        ┌──────┴──────┐                  │
                        │  PostgreSQL │◀─────────────────┘
                        │  + Redis    │
                        └─────────────┘
```

## Components

### 1. SDK / Middleware (`sdk/`)

A Python package (`mateobserve`) that developers install in their API.

**Responsibilities:**
- Capture incoming HTTP requests as ASGI middleware
- Measure response latency with `time.perf_counter()`
- Record status codes and errors
- Buffer events in memory
- Flush batches to the collector asynchronously

**Key design decisions:**
- Uses `httpx.AsyncClient` for non-blocking HTTP
- Batches events (default: 100 events or 5 seconds)
- Silently degrades if collector is unreachable — never impacts API performance
- Zero config required (sensible defaults from env vars)

### 2. Metrics Collector (`collector/`)

A FastAPI service that receives, stores, and aggregates metrics.

**Stack:**
- FastAPI (async API framework)
- PostgreSQL via SQLAlchemy async (persistent storage)
- Redis (optional caching layer)
- Alembic (database migrations)

**API Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| POST | `/metrics` | Receive batch of metric events |
| GET | `/services` | List monitored services |
| GET | `/metrics/overview` | High-level stats (RPM, latency, errors) |
| GET | `/metrics/latency` | Per-endpoint latency percentiles |
| GET | `/metrics/errors` | Per-endpoint error rates |
| GET | `/metrics/traffic` | Requests over time (bucketed) |
| GET | `/health` | Health check |

**Aggregation:**
A background task runs every 60 seconds, grouping raw events into per-minute
buckets with pre-computed percentiles (p50, p95, p99). This keeps dashboard
queries fast even with millions of events.

### 3. Dashboard (`dashboard/`)

A Next.js (React) SPA showing real-time API health.

**Features:**
- Requests per minute
- Average latency
- Error rate percentage
- Traffic over time chart
- Error rate by endpoint chart
- Endpoint latency table with percentiles
- Service selector dropdown
- Auto-refresh every 10 seconds

## Data Flow

1. HTTP request hits your API
2. `ObserveMiddleware` wraps the request, measures timing
3. Event is buffered in SDK memory
4. Every 5s (or when buffer is full), batch is POSTed to collector
5. Collector inserts raw events into `metric_events` table
6. Background task aggregates into `aggregated_metrics` every 60s
7. Dashboard polls collector API and renders charts

## Security

- API key authentication via `X-API-Key` header
- Set `MATEOBSERVE_API_KEY` on both SDK and collector
- In production, deploy collector on private network
