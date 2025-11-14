from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas.sku import (
    SkuCreate,
    SkuEventCreate,
    SkuEventRead,
    SkuRead,
    TimelineResponse,
)
from app.services import tracking

router = APIRouter(prefix="/skus", tags=["skus"])


@router.post("", response_model=SkuRead, status_code=201)
def create_sku(payload: SkuCreate):
    sku = tracking.create_sku(payload)
    return sku


@router.post("/{sku_id}/events", response_model=SkuEventRead, status_code=201)
def add_event(sku_id: int, payload: SkuEventCreate):
    if payload.sku_id != sku_id:
        raise HTTPException(status_code=400, detail="SKU ID mismatch")
    return tracking.record_event(payload)


@router.get("/{sku_id}/timeline", response_model=TimelineResponse)
def get_timeline(sku_id: int):
    timeline = tracking.get_sku_timeline(sku_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="SKU not found")
    return timeline


@router.get("/search", response_model=List[SkuRead])
def search_sku(q: str):
    return tracking.search_skus(q)
