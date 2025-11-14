import os

from datetime import datetime
from typing import Optional, List

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, create_engine, Session, select
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the static folder (for index.html, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")
# ============================================================
# DATABASE SETUP
# ============================================================

# Absolute path to avoid "wrong working dir" issues
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'ledger.db')}"

# echo=True for SQL DDL in console; check_same_thread=False fixes SQLite + FastAPI threading
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)



# ============================================================
# LEDGER FOR ARBITRAGE / API-HOP EVENTS
# ============================================================

class LedgerEntry(SQLModel, table=True):
    """
    Original arbitrage ledger:
    Logs each hop in the orchestrated METRC → POS → Logistics → Payment → PMSI flow.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: str
    from_system: str
    to_system: str
    action: str
    status: str
    payload: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


# ============================================================
# UNIVERSAL ITEM TRACKING MODELS
# ============================================================

class ItemSource(SQLModel, table=True):
    """
    Links your internal item_id to an external provider's identifier.
    Example:
      item_id = "SKU-123"
      provider = "FedEx"
      provider_ref = "TRACKING_NUMBER"
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: str
    provider: str
    provider_ref: str


class ItemEvent(SQLModel, table=True):
    """
    Normalized event log for ANY trackable item.
    Every scan / status change / API response becomes one ItemEvent.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: str                  # Your universal ID
    provider: str                 # Which external system
    provider_ref: str             # That system's ID for this item
    event_type: str               # "CREATED", "SHIPPED", "RECEIVED", "SCANNED", etc.
    location: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_payload: str              # Raw JSON/string snapshot


def init_db():
    SQLModel.metadata.create_all(engine)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def log_to_ledger(
    asset_id: str,
    from_system: str,
    to_system: str,
    action: str,
    status: str,
    payload: str = "",
    notes: str = "",
) -> LedgerEntry:
    """
    Log a step in the arbitrage / API-hop flow.
    """
    entry = LedgerEntry(
        asset_id=asset_id,
        from_system=from_system,
        to_system=to_system,
        action=action,
        status=status,
        payload=payload,
        notes=notes,
    )
    with Session(engine) as session:
        session.add(entry)
        session.commit()
        session.refresh(entry)
    return entry


def save_item_event(
    item_id: str,
    provider: str,
    provider_ref: str,
    event_type: str,
    location: str = "",
    raw_payload: str = "",
) -> ItemEvent:
    """
    Save a normalized tracking event for a universal item.
    """
    event = ItemEvent(
        item_id=item_id,
        provider=provider,
        provider_ref=provider_ref,
        event_type=event_type,
        location=location,
        raw_payload=raw_payload,
    )
    with Session(engine) as session:
        session.add(event)
        session.commit()
        session.refresh(event)
    return event


# ============================================================
# Pydantic MODELS FOR MOCK ARBITRAGE FLOW
# ============================================================

class InventoryItem(BaseModel):
    asset_id: str
    product: str
    location: str
    quantity: int
    la_price: float
    sd_price: float
    days_in_inventory: int


class MarketData(BaseModel):
    region: str
    price: float
    stock: int


class ArbitrageResult(BaseModel):
    asset_id: str
    arbitrage_detected: bool
    message: str


class RunFlowResult(BaseModel):
    asset_id: str
    steps: List[str]
    success: bool


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Universal Item Tracker & API-Hop Arbitrage Prototype",
    description=(
        "Demo: \n"
        "- Tracks a financed asset through a mocked arbitrage flow (LA → SD).\n"
        "- Provides a generic framework to track ANY item_id across providers "
        "using ItemSource + ItemEvent."
    ),
)


@app.on_event("startup")
def on_startup():
    init_db()


# ============================================================
# MOCK EXTERNAL APIS (ARBITRAGE DEMO)
# ============================================================

@app.get("/mock/metrc/inventory", response_model=List[InventoryItem])
def mock_metrc_inventory():
    """
    Simulate METRC inventory for one financed asset stuck in LA.
    """
    item = InventoryItem(
        asset_id="1A406030000312F000001234",
        product="Live Rosin Vape - Blue Dream - 1g",
        location="LA_Distributor_Warehouse",
        quantity=2500,
        la_price=18.0,
        sd_price=45.0,
        days_in_inventory=48,
    )
    return [item]


@app.get("/mock/pos/sd-market", response_model=MarketData)
def mock_pos_sd_market():
    """
    Simulate POS data from a hot San Diego retailer.
    """
    return MarketData(region="San Diego", price=45.0, stock=8)


@app.post("/mock/metrc/create-transfer")
def mock_metrc_create_transfer(asset_id: str):
    """
    Simulate creation of a compliant transfer manifest in METRC.
    """
    manifest_id = str(uuid.uuid4())
    return {
        "manifest_id": manifest_id,
        "asset_id": asset_id,
        "status": "TRANSFER_CREATED",
    }


@app.post("/mock/logistics/dispatch")
def mock_logistics_dispatch(asset_id: str, manifest_id: str):
    """
    Simulate dispatch of secure transport.
    """
    tracking_id = str(uuid.uuid4())
    return {
        "tracking_id": tracking_id,
        "asset_id": asset_id,
        "manifest_id": manifest_id,
        "status": "IN_TRANSIT",
    }


@app.post("/mock/pos/receive")
def mock_pos_receive(asset_id: str):
    """
    Simulate retailer receiving inventory in San Diego.
    """
    return {
        "asset_id": asset_id,
        "status": "RECEIVED_AT_RETAILER",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/mock/payment/settle")
def mock_payment_settle(asset_id: str):
    """
    Simulate payment + repayment + profit share.
    """
    final_sale = 2500 * 45.0
    advance = 2500 * 15.0
    arbitrage_profit_share = 7500.0
    return {
        "asset_id": asset_id,
        "status": "PAID",
        "final_sale": final_sale,
        "advance": advance,
        "arbitrage_profit_share": arbitrage_profit_share,
    }


@app.post("/mock/pmsi/update")
def mock_pmsi_update(asset_id: str):
    """
    Simulate updating PMSI registry / lien release.
    """
    return {
        "asset_id": asset_id,
        "status": "LIEN_RELEASED",
    }


# ============================================================
# ARBITRAGE LOGIC
# ============================================================

@app.get("/detect-arbitrage", response_model=ArbitrageResult)
def detect_arbitrage():
    """
    Compare LA vs SD pricing using mock endpoints and decide
    if arbitrage opportunity exists.
    """
    inventory = mock_metrc_inventory()[0]
    market = mock_pos_sd_market()

    if market.price >= inventory.la_price * 1.5 and market.stock < 20:
        msg = (
            f"Arbitrage detected for {inventory.asset_id}: "
            f"LA ${inventory.la_price} vs SD ${market.price}"
        )
        log_to_ledger(
            asset_id=inventory.asset_id,
            from_system="ENGINE",
            to_system="ENGINE",
            action="DETECT_ARBITRAGE",
            status="ARBITRAGE_TRUE",
            payload=msg,
        )
        return ArbitrageResult(
            asset_id=inventory.asset_id,
            arbitrage_detected=True,
            message=msg,
        )

    msg = "No arbitrage opportunity under current thresholds."
    log_to_ledger(
        asset_id=inventory.asset_id,
        from_system="ENGINE",
        to_system="ENGINE",
        action="DETECT_ARBITRAGE",
        status="ARBITRAGE_FALSE",
        payload=msg,
    )
    return ArbitrageResult(
        asset_id=inventory.asset_id,
        arbitrage_detected=False,
        message=msg,
    )


@app.post("/run-flow", response_model=RunFlowResult)
def run_flow():
    """
    Run the full mocked hop:
    METRC -> transfer -> logistics -> POS receive -> payment -> PMSI.
    """
    inventory = mock_metrc_inventory()[0]
    asset_id = inventory.asset_id
    steps: List[str] = []

    # 1. Detect arbitrage
    arb = detect_arbitrage()
    if not arb.arbitrage_detected:
        return RunFlowResult(
            asset_id=asset_id,
            steps=["No arbitrage opportunity"],
            success=False,
        )
    steps.append("Arbitrage detected")

    # 2. Create METRC transfer manifest
    transfer_resp = mock_metrc_create_transfer(asset_id)
    log_to_ledger(
        asset_id=asset_id,
        from_system="ENGINE",
        to_system="METRC",
        action="CREATE_TRANSFER",
        status=transfer_resp["status"],
        payload=str(transfer_resp),
    )
    steps.append("Transfer manifest created in METRC")

    # 3. Dispatch logistics
    logistics_resp = mock_logistics_dispatch(
        asset_id=asset_id,
        manifest_id=transfer_resp["manifest_id"],
    )
    log_to_ledger(
        asset_id=asset_id,
        from_system="METRC",
        to_system="LOGISTICS",
        action="DISPATCH",
        status=logistics_resp["status"],
        payload=str(logistics_resp),
    )
    steps.append("Secure transport dispatched")

    # 4. Retailer receives
    receive_resp = mock_pos_receive(asset_id)
    log_to_ledger(
        asset_id=asset_id,
        from_system="LOGISTICS",
        to_system="POS",
        action="RECEIVE_AT_RETAIL",
        status=receive_resp["status"],
        payload=str(receive_resp),
    )
    steps.append("Retailer received inventory")

    # 5. Payment + repayment
    pay_resp = mock_payment_settle(asset_id)
    log_to_ledger(
        asset_id=asset_id,
        from_system="POS",
        to_system="PAYMENT",
        action="SETTLE",
        status=pay_resp["status"],
        payload=str(pay_resp),
        notes="Includes arbitrage profit share.",
    )
    steps.append("Payment settled, arbitrage profit shared")

    # 6. PMSI update (lien update/release)
    pmsi_resp = mock_pmsi_update(asset_id)
    log_to_ledger(
        asset_id=asset_id,
        from_system="PAYMENT",
        to_system="PMSI",
        action="UPDATE_LIEN",
        status=pmsi_resp["status"],
        payload=str(pmsi_resp),
    )
    steps.append("PMSI lien updated")

    return RunFlowResult(
        asset_id=asset_id,
        steps=steps,
        success=True,
    )


# ============================================================
# UNIVERSAL ITEM TRACKING ENDPOINTS
# ============================================================

@app.post("/register-item")
def register_item(item_id: str, provider: str, provider_ref: str):
    """
    Link a universal item_id to an external system's identifier.

    Example:
      item_id=SKU-123
      provider='FedEx'
      provider_ref='TRACKING123'
    """
    with Session(engine) as session:
        link = ItemSource(
            item_id=item_id,
            provider=provider,
            provider_ref=provider_ref,
        )
        session.add(link)
        session.commit()
    return {
        "status": "ok",
        "item_id": item_id,
        "provider": provider,
        "provider_ref": provider_ref,
    }


@app.post("/refresh-item/{item_id}")
def refresh_item(item_id: str):
    """
    MOCK:
    Look up all sources for this item and create fake ItemEvents.

    In a real system, this is where you'd:
    - call FedEx/UPS APIs for shipping events
    - call Shopify/Amazon for order status
    - call METRC/GIA/other compliance systems
    and normalize all into ItemEvent rows.
    """
    with Session(engine) as session:
        sources = session.exec(
            select(ItemSource).where(ItemSource.item_id == item_id)
        ).all()

    if not sources:
        raise HTTPException(status_code=404, detail="No sources linked to this item_id")

    created_events: List[ItemEvent] = []

    for src in sources:
        mock_payload = f"Mock update from {src.provider} for {src.provider_ref}"
        event = save_item_event(
            item_id=item_id,
            provider=src.provider,
            provider_ref=src.provider_ref,
            event_type="MOCK_UPDATE",
            location="UNKNOWN",
            raw_payload=mock_payload,
        )
        created_events.append(event)

    return {
        "status": "ok",
        "item_id": item_id,
        "events_created": len(created_events),
    }


@app.get("/item-history/{item_id}", response_model=List[ItemEvent])
def get_item_history(item_id: str):
    """
    Return the full normalized event history for a given item_id.
    This shows the journey of that item across all linked providers.
    """
    with Session(engine) as session:
        statement = (
            select(ItemEvent)
            .where(ItemEvent.item_id == item_id)
            .order_by(ItemEvent.timestamp)
        )
        events = session.exec(statement).all()

    if not events:
        raise HTTPException(status_code=404, detail="No events found for this item_id")
    return events


# ============================================================
# VIEW RAW ARBITRAGE LEDGER
# ============================================================

@app.get("/ledger", response_model=List[LedgerEntry])
def get_ledger():
    """
    Get all arbitrage ledger entries.
    """
    with Session(engine) as session:
        statement = select(LedgerEntry).order_by(LedgerEntry.timestamp)
        results = session.exec(statement).all()
        return results
@app.get("/", response_class=FileResponse)
def serve_frontend():
    """
    Serve the SKU Tracker UI.
    """
    return FileResponse("static/index.html")
