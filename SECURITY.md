# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in MateObserve, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email the maintainer directly or use [GitHub's private vulnerability reporting](https://github.com/TobiasVeiga00/mateobserve/security/advisories/new).

We will acknowledge receipt within 48 hours and aim to release a fix promptly.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Best Practices for Deployment

- Always set `MATEOBSERVE_API_KEY` in production to require authentication for metric ingestion.
- Change all default passwords (`POSTGRES_PASSWORD`, `REDIS_PASSWORD`) before deploying.
- Run the collector on a private network — do not expose it directly to the internet.
- Use HTTPS in production (put a reverse proxy in front of the collector).
- Keep the `NEXT_PUBLIC_API_KEY` empty or use a separate read-only key for the dashboard.
