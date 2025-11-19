from __future__ import annotations

from typing import List

from app.connectors import (
    BarcodeLookupConnector,
    ConnectorError,
    FedExConnector,
    UpcItemDbConnector,
    UpsConnector,
    UspsConnector,
)
from app.models import SkuEvent
from app.schemas.connector import CatalogLookupRequest, TrackShipmentRequest
from app.schemas.sku import SkuEventCreate
from app.services.tracking import record_event


def ingest_tracking(request: TrackShipmentRequest) -> List[SkuEvent]:
    try:
        if request.provider == "fedex":
            connector = FedExConnector()
        elif request.provider == "ups":
            connector = UpsConnector()
        else:
            connector = UspsConnector()
        events = connector.track(request.tracking_number)
    except ConnectorError as exc:
        raise ValueError(str(exc)) from exc

    created: List[SkuEvent] = []
    for event in events:
        payload = SkuEventCreate(
            sku_id=request.sku_id,
            event_type=event.event_type,
            provider=event.provider,
            location=event.location,
            payload=event.payload,
            observed_at=event.observed_at,
            confidence=1.0,
        )
        created_event = record_event(payload)
        created.append(created_event)
    return created


def lookup_catalog(request: CatalogLookupRequest):
    try:
        if request.provider == "upcitemdb":
            connector = UpcItemDbConnector()
        else:
            connector = BarcodeLookupConnector()
        return connector.lookup(request.identifier)
    except ConnectorError as exc:
        raise ValueError(str(exc)) from exc
