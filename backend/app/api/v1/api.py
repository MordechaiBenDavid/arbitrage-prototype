from fastapi import APIRouter

from app.api.v1.endpoints import connectors, skus

api_router = APIRouter()
api_router.include_router(skus.router)
api_router.include_router(connectors.router)
