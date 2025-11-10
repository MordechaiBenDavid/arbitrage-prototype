from datetime import datetime
from typing import Optional, List

import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, create_engine, Session, select

# -------------------------------------------------------------------
# DATABASE + LEDGER MODEL
# -------------------------------------------------------------------

DATABASE_URL = "sqlite:///./ledger.db"
engine = create_engine(DATABASE_URL, echo=False)


class LedgerEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: str
    from_system: str
    to_system: str
    action: str
    status: str
    payload: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


def init_db():
    SQLModel.metadata.create_all(engine)


def log_to_ledger(
    asset_id: str,
    from_system: str,
    to_system: str,
    action: str,
    status: str,
    payload: str = "",
    notes: str = "",
):
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


# -------------------------------------------------------------------
# MOCK DATA MODELS
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# FASTAPI APP
# -------------------------------------------------------------------

app = FastAPI(title="API Hop Arbitrage Prototype")


@app.on_event("startup")
def on_startup():
    init_db()


# -------------------------------------------------------------------
# MOCK EXTERNAL APIS
# These simulate METRC, POS, Logistics, Payment, PMSI registry.
# In production you replace these with real API calls.
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# CORE LOGIC: DETECT ARBITRAGE
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# CORE LOGIC: RUN FULL API-HOP FLOW
# -------------------------------------------------------------------

@app.post("/run-flow", response_model=RunFlowResult)
def run_flow():
    """
    Run the full mocked hop:
    METRC -> transfer -> logistics -> POS receive -> payment -> PMSI.
    This is the exact orchestrated chain your contact wants to "test".
    """
    inventory = mock_metrc_inventory()[0]
    asset_id = inventory.asset_id
    steps = []

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

    # 6. PMSI update (lien released/updated)
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


# -------------------------------------------------------------------
# VIEW LEDGER
# -------------------------------------------------------------------

@app.get("/ledger", response_model=List[LedgerEntry])
def get_ledger():
    """
    Get all ledger entries (for your simple dashboard / for him to inspect).
    """
    with Session(engine) as session:
        statement = select(LedgerEntry).order_by(LedgerEntry.timestamp)
        results = session.exec(statement).all()
        return results
