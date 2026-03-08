# Contributing to MateObserve

Thanks for your interest in contributing! 🧉

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/mateobserve.git`
3. Create a branch: `git checkout -b feature/your-feature`

## Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Setup

```bash
# Start infrastructure
docker compose up postgres redis -d

# Collector
cd collector
uv venv && source .venv/bin/activate
uv pip install -e .
uvicorn collector.main:app --reload --port 8001

# Dashboard (new terminal)
cd dashboard
npm install
npm run dev

# Run tests
cd ../tests
pytest
```

## Code Style

- **Python**: Follow PEP 8. Use type hints. Format with `ruff`.
- **TypeScript**: Follow ESLint config. Use functional components.
- **Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, etc.)

## Pull Requests

1. Keep PRs focused — one feature or fix per PR
2. Add tests for new functionality
3. Update docs if needed
4. Ensure CI passes

## Project Structure

```
sdk/              Python SDK and middleware
collector/        FastAPI collector service
dashboard/        Next.js dashboard
docker/           Docker configuration
examples/         Example integrations
docs/             Documentation
tests/            Test suites
```

## Reporting Issues

- Use GitHub Issues
- Include steps to reproduce
- Include Python/Node versions
- Include error messages and logs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
