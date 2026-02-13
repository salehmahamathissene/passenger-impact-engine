from __future__ import annotations

from fastapi import FastAPI

from pie.api.router import router as api_router

app = FastAPI(title="Passenger Impact Engine")

# SaaS API
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"status": "PIE is online 🚀"}
