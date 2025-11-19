from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


class ConnectorError(Exception):
    """Raised when an upstream provider returns an unexpected response."""


@dataclass
class ConnectorEvent:
    event_type: str
    observed_at: datetime
    provider: str
    location: Optional[str]
    payload: Dict[str, Any]


@dataclass
class CatalogProduct:
    title: Optional[str]
    description: Optional[str]
    brand: Optional[str]
    identifiers: Dict[str, str]
    raw: Dict[str, Any]
