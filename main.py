from fastapi import FastAPI
from src.pie.pro.billing_routes import router as billing_router
from src.pie.pro.enterprise_routes import router as enterprise_router

app = FastAPI(
    title="Passenger Impact Engine API",
    description="Enterprise simulation and analytics platform",
    version="1.0.0"
)

# Include enterprise routes
app.include_router(enterprise_router)
app.include_router(billing_router)

@app.get("/")
async def root():
    return {
        "message": "Passenger Impact Engine API",
        "version": "1.0.0",
        "docs": "/docs",
        "enterprise_api": "/enterprise"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
