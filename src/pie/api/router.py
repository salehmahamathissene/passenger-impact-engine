from fastapi import APIRouter
from pie.api.routes_health import router as health_router
from pie.api.routes_companies import router as companies_router

router = APIRouter()

router.include_router(health_router)
router.include_router(companies_router)
