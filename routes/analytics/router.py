from fastapi import APIRouter, Depends
from core.auth import get_api_key

from routes.analytics import market_intel, simulations, strategies, scanner

public_router = APIRouter(tags=["analytics"])
router = APIRouter(tags=["analytics"], dependencies=[Depends(get_api_key)])

# Register public sub-routers
public_router.include_router(market_intel.public_router)
public_router.include_router(simulations.public_router)
public_router.include_router(strategies.public_router)
public_router.include_router(scanner.public_router)

# Register authenticated sub-routers
router.include_router(market_intel.router)
router.include_router(simulations.router)
router.include_router(scanner.router)
