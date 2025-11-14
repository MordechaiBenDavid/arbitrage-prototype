from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SkuIdentityCreate(BaseModel):
    provider: str
    identifier: str
    confidence: float = 1.0


class SkuIdentityRead(SkuIdentityCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class SkuCreate(BaseModel):
    canonical_sku: str
    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    identities: List[SkuIdentityCreate] = []


class SkuRead(BaseModel):
    id: int
    canonical_sku: str
    name: str
    description: Optional[str]
    brand: Optional[str]
    identities: List[SkuIdentityRead]

    class Config:
        from_attributes = True


class SkuEventCreate(BaseModel):
    sku_id: int
    event_type: str
    provider: str
    location: Optional[str] = None
    payload: dict
    raw_payload: Optional[dict] = None
    observed_at: Optional[datetime] = None
    confidence: float = 1.0


class SkuEventRead(SkuEventCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimelineResponse(BaseModel):
    sku: SkuRead
    events: List[SkuEventRead]
    inferred_status: str
    last_known_location: Optional[str]
