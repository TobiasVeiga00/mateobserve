# Releasing MateObserve

## Prerequisites

- Python 3.10+
- [hatch](https://hatch.pypa.io/) or [build](https://pypa-build.readthedocs.io/)
- [twine](https://twine.readthedocs.io/)
- A [PyPI account](https://pypi.org/account/register/) with an API token
- Push access to the GitHub repository

---

## 1. Update the Version

Update the version in both locations:

```bash
# sdk/pyproject.toml
version = "0.2.0"

# sdk/mateobserve/__init__.py
__version__ = "0.2.0"
```

Commit the version bump:

```bash
git add sdk/pyproject.toml sdk/mateobserve/__init__.py
git commit -m "chore: bump version to 0.2.0"
```

---

## 2. Run Tests

```bash
cd tests
pip install -e ../sdk[dev] -e ../collector
pytest -v
```

Make sure all tests pass before proceeding.

---

## 3. Build the Package

```bash
cd sdk
python -m build
```

This creates `dist/mateobserve-0.2.0.tar.gz` and `dist/mateobserve-0.2.0-py3-none-any.whl`.

Verify the package contents:

```bash
twine check dist/*
```

---

## 4. Publish to PyPI

### Test PyPI (recommended first)

```bash
twine upload --repository testpypi dist/*
```

Verify: https://test.pypi.org/project/mateobserve/

### Production PyPI

```bash
twine upload dist/*
```

You'll be prompted for credentials. Use `__token__` as the username and your PyPI API token as the password.

> **Tip:** Store your token in `~/.pypirc` or use `TWINE_USERNAME` and `TWINE_PASSWORD` environment variables.

---

## 5. Create a GitHub Release

### Via CLI (gh)

```bash
git tag v0.2.0
git push origin v0.2.0

gh release create v0.2.0 \
  --title "v0.2.0" \
  --notes "## What's New

- Feature description here
- Bug fix description here

**Full Changelog**: https://github.com/TobiasVeiga00/mateobserve/compare/v0.1.0...v0.2.0" \
  sdk/dist/mateobserve-0.2.0.tar.gz \
  sdk/dist/mateobserve-0.2.0-py3-none-any.whl
```

### Via GitHub UI

1. Go to **Releases** → **Draft a new release**
2. Tag: `v0.2.0` (create new tag)
3. Title: `v0.2.0`
4. Write release notes
5. Attach the `.tar.gz` and `.whl` files from `sdk/dist/`
6. Click **Publish release**

---

## First Release (v0.1.0)

For the initial release:

```bash
cd sdk
python -m build
twine check dist/*
twine upload dist/*

git tag v0.1.0
git push origin v0.1.0

gh release create v0.1.0 \
  --title "v0.1.0 — Initial Release" \
  --notes "## MateObserve v0.1.0

API observability in 30 seconds. 🧉

### Features
- Python SDK with FastAPI/Starlette middleware
- CLI to manage the observability stack (\`mateobserve up/down/status/doctor\`)
- Metrics collector with PostgreSQL storage and auto-aggregation
- Real-time dashboard with SSE streaming
- API key authentication
- Automatic data retention and cleanup

### Install
\`\`\`bash
pip install mateobserve
mateobserve up
\`\`\`
"
```

---

## Version Locations

Keep these in sync when bumping versions:

| File | Field |
|------|-------|
| `sdk/pyproject.toml` | `version = "x.y.z"` |
| `sdk/mateobserve/__init__.py` | `__version__ = "x.y.z"` |

The collector and dashboard versions are managed independently in their own `pyproject.toml` / `package.json`.
