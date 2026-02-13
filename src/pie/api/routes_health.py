from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def api_health():
    return {"status": "ok", "scope": "api-v1"}
