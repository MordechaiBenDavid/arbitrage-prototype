from fastapi import APIRouter

from app.api.v1.endpoints import skus

api_router = APIRouter()
api_router.include_router(skus.router)
