from fastapi import APIRouter, HTTPException

from app.schemas import (
    CatalogLookupRequest,
    CatalogLookupResponse,
    TrackShipmentRequest,
    TrackShipmentResponse,
)
from app.services import ingestion

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.post("/track", response_model=TrackShipmentResponse)
def trigger_tracking(request: TrackShipmentRequest):
    try:
        events = ingestion.ingest_tracking(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TrackShipmentResponse(events=events)


@router.post("/catalog", response_model=CatalogLookupResponse)
def lookup_catalog(request: CatalogLookupRequest):
    try:
        product = ingestion.lookup_catalog(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CatalogLookupResponse(
        title=product.title,
        description=product.description,
        brand=product.brand,
        identifiers=product.identifiers,
        raw=product.raw,
    )
