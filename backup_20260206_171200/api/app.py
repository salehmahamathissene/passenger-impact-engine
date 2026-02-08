import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import pro modules
from pie.pro.db import init_db
from pie.pro.routes import router as pro_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting PIE API...")
    init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("👋 Shutting down PIE API...")


app = FastAPI(
    title="Passenger Impact Engine API",
    description="Professional simulation engine for airline impact analysis",
    version="2.0.0",
    lifespan=lifespan
)


class RunRequest(BaseModel):
    client_id: str
    runs: int = 2000
    key: str


class HealthResponse(BaseModel):
    status: str


@app.get("/")
async def root():
    return {"status": "PIE is online 🚀"}


@app.get("/health")
async def health():
    return HealthResponse(status="healthy")


@app.post("/run-demo")
async def run_demo():
    """Run demo simulation (no auth required)"""
    from pie.simulation.runner import run_simulation
    from pie.reporting.dashboard import create_dashboard
    
    print("🏃 Running demo simulation...")
    results = run_simulation(iterations=1000)
    
    # Create dashboard
    dashboard_path = create_dashboard(results, output_dir="out_api")
    
    return {
        "message": "Demo simulation complete",
        "dashboard": dashboard_path,
        "stats": results["stats"]
    }


@app.post("/run")
async def run(req: RunRequest):
    """Run simulation with API key authentication"""
    from pie.simulation.runner import run_simulation
    from pie.reporting.dashboard import create_dashboard
    
    # Check API key
    expected = os.environ.get("PIE_API_KEY", "demo_key")
    if req.key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    print(f"🏃 Running simulation for {req.client_id} ({req.runs} iterations)")
    results = run_simulation(iterations=req.runs)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = f"out_api"
    
    # Create dashboard
    dashboard_path = create_dashboard(results, output_dir=out_dir, title=f"Client: {req.client_id}")
    
    print(f"✅ Dashboard written: {dashboard_path}")
    
    return {
        "message": "Simulation complete",
        "client_id": req.client_id,
        "runs": req.runs,
        "dashboard": f"/{dashboard_path}",
        "stats": f"/out_api/stats.json"
    }


@app.get("/invoice/{client_id}")
async def get_invoice(client_id: str, runs: int, amount: float):
    """Generate invoice for client"""
    invoice_html = f"""
    <html>
    <head><title>Invoice - {client_id}</title></head>
    <body>
    <h1>INVOICE</h1>
    <p><strong>Client:</strong> {client_id}</p>
    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
    <p><strong>Description:</strong> Passenger Impact Analysis Service</p>
    <p><strong>Runs:</strong> {runs} simulation iterations</p>
    <p><strong>Amount:</strong> {amount} EUR</p>
    </body>
    </html>
    """
    return HTMLResponse(content=invoice_html)


# Include pro routes
app.include_router(pro_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
