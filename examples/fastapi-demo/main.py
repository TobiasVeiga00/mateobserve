"""Example FastAPI application with MateObserve integration.

This demonstrates the simplest possible setup — just add the middleware.
Run with:
    uvicorn main:app --reload --port 8000
"""

import random
import asyncio

from fastapi import FastAPI, HTTPException

from mateobserve import ObserveMiddleware

app = FastAPI(title="User API", description="Example API monitored by MateObserve 🧉")

# ── One line to add observability ─────────────────────────────────────────────
app.add_middleware(ObserveMiddleware)
# That's it! Metrics are now being collected automatically.

# ── Example endpoints ─────────────────────────────────────────────────────────

USERS = {
    1: {"id": 1, "name": "Lionel Messi", "email": "leo@example.com"},
    2: {"id": 2, "name": "Diego Maradona", "email": "diego@example.com"},
    3: {"id": 3, "name": "Juan Martín del Potro", "email": "delpo@example.com"},
}


@app.get("/")
async def root():
    return {"service": "user-api", "status": "ok", "message": "🧉 Tomando mate"}


@app.get("/users")
async def list_users():
    # Simulate variable latency
    await asyncio.sleep(random.uniform(0.01, 0.05))
    return list(USERS.values())


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    await asyncio.sleep(random.uniform(0.005, 0.02))
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users")
async def create_user(name: str, email: str):
    await asyncio.sleep(random.uniform(0.02, 0.08))
    new_id = max(USERS.keys()) + 1
    user = {"id": new_id, "name": name, "email": email}
    USERS[new_id] = user
    return user


@app.get("/slow")
async def slow_endpoint():
    """Intentionally slow for testing latency tracking."""
    await asyncio.sleep(random.uniform(0.5, 2.0))
    return {"message": "This was slow on purpose"}


@app.get("/error")
async def error_endpoint():
    """Intentionally fails for testing error tracking."""
    if random.random() > 0.3:
        raise HTTPException(status_code=500, detail="Random failure")
    return {"message": "Lucky! No error this time."}


@app.get("/health")
async def health():
    return {"status": "healthy"}
