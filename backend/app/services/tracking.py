from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.db.session import engine
from app.models import Sku, SkuEvent, SkuIdentity
from app.schemas.sku import (
    SkuCreate,
    SkuEventCreate,
    TimelineResponse,
)


def get_session() -> Session:
    return Session(engine)


def create_sku(payload: SkuCreate) -> Sku:
    with get_session() as session:
        sku = Sku(
            canonical_sku=payload.canonical_sku,
            name=payload.name,
            description=payload.description,
            brand=payload.brand,
        )
        session.add(sku)
        session.flush()

        for identity in payload.identities:
            session.add(
                SkuIdentity(
                    sku_id=sku.id,
                    provider=identity.provider,
                    identifier=identity.identifier,
                    confidence=identity.confidence,
                )
            )

        session.commit()
        session.refresh(sku)
        session.refresh(sku, attribute_names=["identities"])
        return sku


def record_event(payload: SkuEventCreate) -> SkuEvent:
    with get_session() as session:
        event = SkuEvent(
            sku_id=payload.sku_id,
            event_type=payload.event_type,
            provider=payload.provider,
            location=payload.location,
            payload=payload.payload,
            raw_payload=payload.raw_payload,
            observed_at=payload.observed_at or datetime.utcnow(),
            confidence=payload.confidence,
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


def get_sku_timeline(sku_id: int) -> Optional[TimelineResponse]:
    with get_session() as session:
        sku = session.get(Sku, sku_id)
        if not sku:
            return None

        events = session.exec(
            select(SkuEvent)
            .where(SkuEvent.sku_id == sku_id)
            .order_by(SkuEvent.observed_at.desc())
        ).all()

    inferred_status = events[0].event_type if events else "UNKNOWN"
    last_location = events[0].location if events else None

    return TimelineResponse(
        sku=sku,
        events=events,
        inferred_status=inferred_status,
        last_known_location=last_location,
    )


def search_skus(query: str) -> List[Sku]:
    # Placeholder implementation until OpenSearch is wired.
    with get_session() as session:
        statement = (
            select(Sku)
            .where(Sku.name.ilike(f"%{query}%"))
            .options(selectinload(Sku.identities))
        )
        return session.exec(statement).all()
