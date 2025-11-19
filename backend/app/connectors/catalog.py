from __future__ import annotations

from typing import Dict, Optional

import httpx

from app.connectors.base import CatalogProduct, ConnectorError
from app.core.config import settings

DEFAULT_TIMEOUT = httpx.Timeout(30.0)


class UpcItemDbConnector:
    def __init__(self) -> None:
        if not settings.upcitemdb_api_key:
            raise ConnectorError("UPCItemDB API key missing")
        self.base_url = settings.upcitemdb_base_url.rstrip("/")

    def lookup(self, identifier: str) -> CatalogProduct:
        headers = {"user_key": settings.upcitemdb_api_key}
        resp = httpx.get(
            f"{self.base_url}/prod/trial/lookup",
            params={"upc": identifier},
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            raise ConnectorError(f"UPCItemDB lookup failed: {resp.text}")
        data = resp.json()
        item = (data.get("items") or [{}])[0]
        identifiers: Dict[str, str] = {}
        if upc := item.get("upc"):
            identifiers["upc"] = upc
        if ean := item.get("ean"):
            identifiers["ean"] = ean
        return CatalogProduct(
            title=item.get("title"),
            description=item.get("description"),
            brand=item.get("brand"),
            identifiers=identifiers,
            raw=item,
        )


class BarcodeLookupConnector:
    def __init__(self) -> None:
        if not settings.barcode_lookup_api_key:
            raise ConnectorError("Barcode Lookup API key missing")
        self.base_url = settings.barcode_lookup_base_url.rstrip("/")

    def lookup(self, identifier: str) -> CatalogProduct:
        resp = httpx.get(
            f"{self.base_url}/products",
            params={"barcode": identifier, "key": settings.barcode_lookup_api_key, "formatted": "y"},
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code != 200:
            raise ConnectorError(f"Barcode Lookup failed: {resp.text}")
        data = resp.json()
        product = (data.get("products") or [{}])[0]
        identifiers: Dict[str, str] = {}
        if barcode := product.get("barcode_number"):
            identifiers["barcode"] = barcode
        return CatalogProduct(
            title=product.get("product_name"),
            description=product.get("description"),
            brand=product.get("brand"),
            identifiers=identifiers,
            raw=product,
        )
