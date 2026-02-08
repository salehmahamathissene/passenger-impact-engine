from contextlib import asynccontextmanager
from fastapi import FastAPI

from pie.pro.db import init_db
from pie.pro.routes import router as pro_router
from pie.pro.enterprise_routes import router as enterprise_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Passenger Impact Engine API",
    description="Enterprise-grade simulation and impact analysis platform",
    version="3.0.0",
    lifespan=lifespan,
)

@app.get("/")
def root():
    return {"status": "PIE is online 🚀"}

@app.get("/health")
def health():
    return {"status": "healthy"}

app.include_router(pro_router)
app.include_router(enterprise_router)
