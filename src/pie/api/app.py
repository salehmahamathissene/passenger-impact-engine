from __future__ import annotations

from fastapi import FastAPI

# Core / Pro API routes
from pie.pro.routes import router as pro_router

# Enterprise + Billing routes
from pie.pro.enterprise_routes import router as enterprise_router
from pie.pro.billing_routes import router as billing_router

app = FastAPI(
    title="Passenger Impact Engine",
    version="1.0.0",
)

# Mount routers
app.include_router(pro_router)
app.include_router(enterprise_router)
app.include_router(billing_router)


@app.get("/healthz")
def healthz():
    return {"ok": True}
