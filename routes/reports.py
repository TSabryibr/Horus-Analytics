from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import Optional
import io
from core import ReportGenerator
from core import TimeUtils
from database import Trade, Position, Portfolio
from routes.portfolio import _resolve_portfolio_id

router = APIRouter(tags=["reports"])

@router.get("/api/v1/reports/portfolio/excel")
def download_portfolio_excel(portfolio_id: Optional[int] = Query(None, ge=1)):
    target_id = _resolve_portfolio_id(portfolio_id)
    if not target_id:
        raise HTTPException(404, "Portfolio not found")
        
    # Gather Data
    trades = list(Trade.select().where(Trade.portfolio == target_id).dicts())
    open_pos = list(Position.select().where((Position.portfolio == target_id) & (Position.status == 'OPEN')).dicts())
    
    # Generate
    buf = ReportGenerator.generate_portfolio_excel(target_id, trades, open_pos)
    
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Horus_Audit_P{target_id}.xlsx"}
    )

@router.get("/api/v1/reports/portfolio/summary", response_class=HTMLResponse)
def view_portfolio_summary(portfolio_id: Optional[int] = Query(None, ge=1)):
    # This uses the management report logic to get the data
    from routes.portfolio import _build_portfolio_management_report
    
    target_id = _resolve_portfolio_id(portfolio_id)
    report_data = _build_portfolio_management_report(target_id)
    
    html = ReportGenerator.generate_portfolio_html_summary(report_data)
    return html
