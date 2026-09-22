import os
import json
import time
from fastapi import APIRouter, Request, HTTPException
from utils.redis_client import redis_client
from pathlib import Path

router = APIRouter(tags=["compliance"])

SIGNATURES_FILE = Path("data/compliance_signatures.json")

DISCLAIMER_TEXT = (
    "WARNING: EDUCATIONAL AND RESEARCH USE ONLY\n\n"
    "Horus Analytics II is an educational research tool designed to analyze quantitative "
    "patterns in the Egyptian Exchange (EGX) and simulate historical portfolios. "
    "Under Egyptian Law and Financial Regulatory Authority (FRA) regulations:\n"
    "1. This software does NOT provide investment advice or licensed financial recommendations.\n"
    "2. All signals, breakouts, and scores are for academic/testing purposes and should not "
    "be used for live executions or real investment decisions.\n"
    "3. Past performance is not indicative of future results.\n\n"
    "By accepting this terms, you acknowledge that you are solely responsible for your own "
    "investment decisions and agree to hold the authors harmless from any legal or financial liability."
)

@router.get("/api/v1/compliance/disclaimer")
def get_compliance_disclaimer():
    """
    Returns the required educational and regulatory disclaimer text.
    """
    return {
        "status": "success",
        "disclaimer": DISCLAIMER_TEXT
    }

@router.post("/api/v1/compliance/accept")
async def accept_compliance_terms(request: Request):
    """
    Records acceptance of the compliance disclaimer.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
        
    client_id = body.get("client_id") or request.client.host
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id or host IP is required")

    timestamp = time.time()
    record = {
        "client_id": client_id,
        "accepted": True,
        "timestamp": timestamp,
        "user_agent": request.headers.get("user-agent", "")
    }

    # Store in Redis
    try:
        redis_client.set(f"compliance_accepted:{client_id}", json.dumps(record))
    except Exception:
        pass

    # Save to local file as secondary persistent storage
    try:
        os.makedirs("data", exist_ok=True)
        signatures = {}
        if SIGNATURES_FILE.exists():
            try:
                with open(SIGNATURES_FILE, "r") as f:
                    signatures = json.load(f)
            except Exception:
                pass
        
        signatures[client_id] = record
        with open(SIGNATURES_FILE, "w") as f:
            json.dump(signatures, f, indent=4)
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Disclaimer accepted",
        "client_id": client_id,
        "timestamp": timestamp
    }

@router.get("/api/v1/compliance/check")
def check_compliance_status(request: Request, client_id: str = None):
    """
    Checks if a client has accepted the educational disclaimers.
    """
    target_id = client_id or request.client.host
    if not target_id:
        return {"status": "success", "accepted": False}

    # Check Redis
    try:
        record_str = redis_client.get(f"compliance_accepted:{target_id}")
        if record_str:
            return {"status": "success", "accepted": True, "record": json.loads(record_str)}
    except Exception:
        pass

    # Check File
    if SIGNATURES_FILE.exists():
        try:
            with open(SIGNATURES_FILE, "r") as f:
                signatures = json.load(f)
            if target_id in signatures:
                return {"status": "success", "accepted": True, "record": signatures[target_id]}
        except Exception:
            pass

    return {"status": "success", "accepted": False}
