from __future__ import annotations

from datetime import datetime

from sqlmodel import Session

from app.db.session import engine
from app.models import Sku, SkuEvent, SkuIdentity

sample_skus = [
    {
        "canonical_sku": "GTIN-00012345678905",
        "name": "ACME Wireless Earbuds",
        "description": "True wireless earbuds with ANC and 24h battery",
        "brand": "ACME Audio",
        "identities": [
            {"provider": "UPC", "identifier": "012345678905"},
            {"provider": "ASIN", "identifier": "B0TEST1234"},
        ],
        "events": [
            {
                "event_type": "MANUFACTURED",
                "provider": "Factory ERP",
                "location": "Shenzhen, CN",
                "observed_at": "2024-04-02T08:15:00Z",
                "payload": {"batch": "2024-04-A"},
            },
            {
                "event_type": "ARRIVED_PORT",
                "provider": "Port Authority",
                "location": "Long Beach, CA",
                "observed_at": "2024-04-05T12:35:00Z",
                "payload": {"container": "ACME-8842"},
            },
            {
                "event_type": "DELIVERED_DC",
                "provider": "UPS",
                "location": "Dallas, TX",
                "observed_at": "2024-04-09T18:20:00Z",
                "payload": {"tracking": "1Z999AA10123456784"},
            },
        ],
    },
    {
        "canonical_sku": "GTIN-00055566677788",
        "name": "Nimbus Smartwatch",
        "description": "Rugged smartwatch with LTE and biometric sensors",
        "brand": "Nimbus Tech",
        "identities": [
            {"provider": "UPC", "identifier": "055566677788"},
            {"provider": "EAN", "identifier": "00555666777788"},
        ],
        "events": [
            {
                "event_type": "ASSEMBLED",
                "provider": "EMS",
                "location": "Ho Chi Minh City, VN",
                "observed_at": "2024-05-01T10:00:00Z",
                "payload": {"line": "HCM-4"},
            },
            {
                "event_type": "IN_TRANSIT",
                "provider": "FedEx",
                "location": "Memphis, TN",
                "observed_at": "2024-05-05T22:10:00Z",
                "payload": {"tracking": "449044304137821"},
            },
            {
                "event_type": "DELIVERED_RETAIL",
                "provider": "Retail POS",
                "location": "Austin, TX",
                "observed_at": "2024-05-07T15:45:00Z",
                "payload": {"store_id": "ATX-44"},
            },
        ],
    },
]


def seed() -> None:
    with Session(engine) as session:
        for sku_data in sample_skus:
            sku = Sku(
                canonical_sku=sku_data["canonical_sku"],
                name=sku_data["name"],
                description=sku_data["description"],
                brand=sku_data["brand"],
            )
            session.add(sku)
            session.flush()

            for identity in sku_data["identities"]:
                session.add(
                    SkuIdentity(
                        sku_id=sku.id,
                        provider=identity["provider"],
                        identifier=identity["identifier"],
                    )
                )

            for event in sku_data["events"]:
                session.add(
                    SkuEvent(
                        sku_id=sku.id,
                        event_type=event["event_type"],
                        provider=event["provider"],
                        location=event.get("location"),
                        observed_at=datetime.fromisoformat(event["observed_at"].replace("Z", "+00:00")),
                        payload=event["payload"],
                    )
                )

        session.commit()


if __name__ == "__main__":
    seed()
