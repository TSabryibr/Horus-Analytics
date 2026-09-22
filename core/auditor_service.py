from core.settings import settings
import os
import re
import json
import datetime
import requests
from core import TimeUtils
from typing import Any, Optional, Dict, List

class StrategyAuditor:
    """
    AI Service to audit backtest reports and provide strategic recommendations.
    Bridges the gap between Strategy Lab (Research) and Strategy Core (Operations).
    """

    def __init__(self):
        self.reports_dir = settings.REPORTS_DIR

    def get_latest_backtest_report(self) -> Optional[str]:
        """Finds the most recent backtest markdown report."""
        latest_file = None
        latest_time = 0
        
        # Search in the main reports dir and subdirs
        for root, dirs, files in os.walk(self.reports_dir):
            for file in files:
                if file.startswith("Backtest_Report_") and file.endswith(".md"):
                    path = os.path.join(root, file)
                    mtime = os.path.getmtime(path)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_file = path
        
        return latest_file

    def parse_report_metrics(self, file_path: str) -> Dict[str, Any]:
        """Parses the markdown report into a structured dictionary."""
        metrics = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Regex patterns for key metrics
            patterns = {
                "total_return": r"\*\*Total Return\*\*\s*\|\s*`([\d\.-]+)%`",
                "cagr": r"\*\*CAGR\*\*\s*\|\s*`([\d\.-]+)%`",
                "sharpe": r"\*\*Sharpe Ratio\*\*\s*\|\s*`([\d\.-]+)`",
                "max_drawdown": r"\*\*Max Drawdown\*\*\s*\|\s*`([\d\.-]+)%`",
                "profit_factor": r"\*\*Profit Factor\*\*\s*\|\s*`([\d\.-]+)`",
                "win_rate": r"\*\*Win Rate\*\*\s*\|\s*`([\d\.-]+)%`",
                "total_trades": r"\*\*Total Trades:\*\*\s*(\d+)",
                "exposure": r"\*\*Market Exposure:\*\*\s*([\d\.-]+)%",
                "starting_capital": r"\*\*Starting Capital:\*\*\s*([\d,]+)\s*EGP",
                "final_equity": r"\*\*Final Equity:\*\*\s*([\d,]+)\s*EGP"
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    val = match.group(1).replace(",", "")
                    metrics[key] = float(val) if "." in val or key in ["sharpe", "profit_factor"] else int(val)

            # Extract generation date
            date_match = re.search(r"\*\*Generated:\*\*\s*([\d\-\s:]+)", content)
            if date_match:
                metrics["generated_at"] = date_match.group(1).strip()

        except Exception as e:
            print(f"Error parsing report {file_path}: {e}")
            
        return metrics

    async def run_audit(self, report_path: Optional[str] = None) -> Dict[str, Any]:
        """Runs the AI audit on the specified or latest report."""
        target_path = report_path or self.get_latest_backtest_report()
        if not target_path:
            return {"status": "error", "message": "No backtest report found to audit."}

        metrics = self.parse_report_metrics(target_path)
        if not metrics:
            return {"status": "error", "message": "Failed to parse metrics from report."}

        # AI Analysis
        analysis = await self._call_ai_analyst(metrics)
        
        return {
            "status": "success",
            "metrics": metrics,
            "analysis": analysis,
            "report_file": os.path.basename(target_path)
        }

    async def _call_ai_analyst(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calls the local Ollama API to perform strategy critique."""
        import json
        
        # Build System Prompt for Quantitative Analyst
        system_prompt = """
        You are the Horus AI Quantitative Auditor. Your task is to critique backtest results.
        Analyze the provided metrics and provide:
        1. Robustness Score (0-100)
        2. Strategic Critique (3-4 sentences)
        3. Risk Warnings (list)
        4. Suggested Parameters (adjusting SL_PCT, TP1_PCT, RSI_MIN, RSI_MAX, RISK_PER_TRADE)
        
        Return a valid JSON object only.
        {
            "robustness_score": int,
            "critique": str,
            "risk_warnings": [str],
            "suggested_parameters": {
                "SL_PCT": float,
                "TP1_PCT": float,
                "RSI_MIN": int,
                "RSI_MAX": int,
                "RISK_PER_TRADE": float
            }
        }
        """
        
        user_prompt = f"Backtest Metrics to Audit:\n{json.dumps(metrics, indent=2)}"

        ollama_host = str(getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")).strip("/")
        model = str(getattr(settings, "AI_REPORT_OLLAMA_MODEL", "qwen2.5-coder")).strip()
        raw_num_ctx = getattr(
            settings,
            "AI_REPORT_OLLAMA_NUM_CTX",
            os.getenv("AI_REPORT_OLLAMA_NUM_CTX", os.getenv("OLLAMA_CONTEXT_LENGTH", "8192")),
        )
        try:
            ollama_num_ctx = int(raw_num_ctx or 0)
        except (TypeError, ValueError):
            ollama_num_ctx = 8192

        options = {"temperature": 0.2}
        if ollama_num_ctx > 0:
            options["num_ctx"] = ollama_num_ctx
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json",
            "options": options,
        }

        try:
            resp = requests.post(
                f"{ollama_host}/api/chat",
                json=payload,
                timeout=float(getattr(settings, "AI_REPORT_OLLAMA_TIMEOUT_SEC", 300)),
            )
            if resp.status_code >= 400:
                return self._get_fallback_analysis(f"Ollama API error {resp.status_code}")
            
            body = resp.json()
            message = body.get("message", {})
            content = message.get("content", "")
            
            if not content:
                return self._get_fallback_analysis("Empty Ollama response")
                
            from routes.ai_report import _strip_code_fences
            parsed = json.loads(_strip_code_fences(content))
            return parsed
        except Exception as e:
            return self._get_fallback_analysis(str(e))

    def _get_fallback_analysis(self, error_msg: str) -> Dict[str, Any]:
        return {
            "robustness_score": 0,
            "critique": f"AI Audit failed: {error_msg}",
            "risk_warnings": ["System Error: AI unavailable."],
            "suggested_parameters": {}
        }

    def save_proposal(self, audit_result: Dict[str, Any]) -> bool:
        """Pushes the AI suggested parameters to the Strategy Core proposal cache."""
        try:
            from routes.shared import STRATEGY_CACHE
            from core.analyzers.ExecutionWatchdog import  get_market_volatility
            from core.market import MarketRegime
            
            # Map Audit output to StrategyProposal schema (ExecutionWatchdog style)
            analysis = audit_result.get("analysis", {})
            suggested = analysis.get("suggested_parameters", {})
            metrics = audit_result.get("metrics", {})
            
            regime_data = MarketRegime.calculate_market_regime()
            curr_vol, avg_vol = get_market_volatility()
            
            # Build changes list
            changes = []
            for p in ['SL_PCT', 'TP1_PCT', 'RSI_MIN', 'RISK_PER_TRADE']:
                old_val = getattr(settings, p, 0)
                new_val = suggested.get(p, old_val)
                
                changes.append({
                    "parameter": p,
                    "old_value": float(round(old_val, 2)),
                    "new_value": float(round(new_val, 2)),
                    "changed": bool(old_val != new_val)
                })

            proposal = {
                "regime": regime_data['regime'],
                "regime_score": int(regime_data['score']),
                "volatility": "HIGH" if curr_vol > avg_vol * 1.5 else "NORMAL",
                "volatility_value": float(round(curr_vol, 2)),
                "reasoning": f"AI STRATEGY AUDIT: {analysis.get('critique', 'No critique available.')}",
                "risk_engine": {
                    "robustness_score": analysis.get("robustness_score", 0),
                    "audit_warnings": analysis.get("risk_warnings", [])
                },
                "proposed_settings": suggested,
                "changes": changes,
                "is_ai_audit": True,
                "audit_metrics": metrics
            }
            
            # Update Cache
            STRATEGY_CACHE["data"] = proposal
            STRATEGY_CACHE["timestamp"] = datetime.datetime.now().isoformat()
            return True
        except Exception as e:
            print(f"Error saving proposal: {e}")
            return False

auditor = StrategyAuditor()
