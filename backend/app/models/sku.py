from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


class Timestamped(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SkuBase(SQLModel):
    name: str
    description: Optional[str] = None
    canonical_sku: str = Field(index=True)
    brand: Optional[str] = None


class Sku(SkuBase, Timestamped, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    identities: list["SkuIdentity"] = Relationship(back_populates="sku")
    events: list["SkuEvent"] = Relationship(back_populates="sku")


class SkuIdentityBase(SQLModel):
    provider: str
    identifier: str = Field(index=True)
    confidence: float = Field(default=1.0)


class SkuIdentity(SkuIdentityBase, Timestamped, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sku_id: int = Field(foreign_key="sku.id", index=True)
    sku: Optional[Sku] = Relationship(back_populates="identities")


class SkuEventBase(SQLModel):
    event_type: str
    provider: str
    location: Optional[str] = Field(default=None)
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    raw_payload: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    observed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    confidence: float = Field(default=1.0)


class SkuEvent(SkuEventBase, Timestamped, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sku_id: int = Field(foreign_key="sku.id", index=True)
    sku: Optional[Sku] = Relationship(back_populates="events")
