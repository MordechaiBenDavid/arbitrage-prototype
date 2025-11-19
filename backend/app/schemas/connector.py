from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel

from app.schemas.sku import SkuEventRead

ShipmentProvider = Literal["fedex", "ups", "usps"]
CatalogProvider = Literal["upcitemdb", "barcodelookup"]


class TrackShipmentRequest(BaseModel):
    sku_id: int
    tracking_number: str
    provider: ShipmentProvider


class TrackShipmentResponse(BaseModel):
    events: List[SkuEventRead]


class CatalogLookupRequest(BaseModel):
    identifier: str
    provider: CatalogProvider


class CatalogLookupResponse(BaseModel):
    title: Optional[str]
    description: Optional[str]
    brand: Optional[str]
    identifiers: dict
    raw: dict
