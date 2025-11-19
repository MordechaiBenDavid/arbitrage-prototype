from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree

import httpx
from dateutil import parser as dateparser

from app.connectors.base import ConnectorError, ConnectorEvent
from app.core.config import settings

DEFAULT_TIMEOUT = httpx.Timeout(30.0)


def _parse_timestamp(value: Optional[str]) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return dateparser.isoparse(value)
    except Exception:
        return datetime.utcnow()


class FedExConnector:
    def __init__(self) -> None:
        if not settings.fedex_client_id or not settings.fedex_client_secret:
            raise ConnectorError("FedEx credentials are not configured")
        self.base_url = settings.fedex_base_url.rstrip("/")

    def _fetch_token(self) -> str:
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.fedex_client_id,
            "client_secret": settings.fedex_client_secret,
        }
        resp = httpx.post(f"{self.base_url}/oauth/token", data=data, timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            raise ConnectorError(f"FedEx auth failed: {resp.text}")
        return resp.json().get("access_token")

    def track(self, tracking_number: str) -> List[ConnectorEvent]:
        token = self._fetch_token()
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "trackingInfo": [
                {
                    "trackingNumberInfo": {
                        "trackingNumber": tracking_number,
                    }
                }
            ],
            "includeDetailedScans": True,
        }
        resp = httpx.post(
            f"{self.base_url}/track/v1/trackingnumbers",
            json=payload,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            raise ConnectorError(f"FedEx track failed: {resp.text}")
        data = resp.json()
        events: List[ConnectorEvent] = []
        results = data.get("output", {}).get("completeTrackResults", [])
        for result in results:
            for track_result in result.get("trackResults", []):
                for scan_event in track_result.get("scanEvents", []):
                    events.append(
                        ConnectorEvent(
                            event_type=scan_event.get("eventType", "SCAN"),
                            observed_at=_parse_timestamp(scan_event.get("date") or scan_event.get("dateTime")),
                            provider="FedEx",
                            location=scan_event.get("scanLocation", {}).get("city")
                            or scan_event.get("scanLocation", {}).get("locationId"),
                            payload=scan_event,
                        )
                    )
        return events


class UpsConnector:
    def __init__(self) -> None:
        if not settings.ups_client_id or not settings.ups_client_secret:
            raise ConnectorError("UPS credentials are not configured")
        self.base_url = settings.ups_base_url.rstrip("/")

    def _fetch_token(self) -> str:
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.ups_client_id,
            "client_secret": settings.ups_client_secret,
        }
        resp = httpx.post(f"{self.base_url}/security/v1/oauth/token", data=data, timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            raise ConnectorError(f"UPS auth failed: {resp.text}")
        return resp.json().get("access_token")

    def track(self, tracking_number: str) -> List[ConnectorEvent]:
        token = self._fetch_token()
        headers = {"Authorization": f"Bearer {token}", "transId": tracking_number, "transactionSrc": "sku-tracker"}
        resp = httpx.get(
            f"{self.base_url}/api/track/v1/details/{tracking_number}",
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            raise ConnectorError(f"UPS track failed: {resp.text}")
        data = resp.json()
        activities = data.get("trackResponse", {}).get("shipment", [{}])[0].get("package", [{}])[0].get("activity", [])
        events: List[ConnectorEvent] = []
        for act in activities:
            location = act.get("location", {}).get("address", {})
            city = location.get("city")
            events.append(
                ConnectorEvent(
                    event_type=act.get("status", {}).get("type", "ACTIVITY"),
                    observed_at=_parse_timestamp(act.get("dateTime")),
                    provider="UPS",
                    location=city,
                    payload=act,
                )
            )
        return events


class UspsConnector:
    def __init__(self) -> None:
        if not settings.usps_user_id:
            raise ConnectorError("USPS USERID is not configured")
        self.base_url = settings.usps_base_url

    def track(self, tracking_number: str) -> List[ConnectorEvent]:
        xml = f"""<TrackRequest USERID=\"{settings.usps_user_id}\"><TrackID ID=\"{tracking_number}\"></TrackID></TrackRequest>"""
        params = {"API": "TrackV2", "XML": xml}
        resp = httpx.get(self.base_url, params=params, timeout=DEFAULT_TIMEOUT)
        if resp.status_code != 200:
            raise ConnectorError(f"USPS track failed: {resp.text}")
        root = ElementTree.fromstring(resp.text)
        events: List[ConnectorEvent] = []
        for event in root.findall(".//TrackDetail"):
            text = event.text or ""
            events.append(
                ConnectorEvent(
                    event_type="USPS_EVENT",
                    observed_at=_parse_timestamp(None),  # USPS details often omit timestamps
                    provider="USPS",
                    location=None,
                    payload={"detail": text},
                )
            )
        return events
