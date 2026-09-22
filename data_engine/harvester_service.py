"""
Standalone Harvester Daemon Service for Windows/POSIX.
Manages the background Mubasher extraction process with start, stop, and status CLI actions,
and persists status metadata to json for API monitoring.
"""

import os
import sys
import time
import json
import subprocess
import signal
import datetime
from pathlib import Path
import logging

# Ensure project root is on path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.settings import settings
from data_engine.mubasher_extractor import perform_extraction

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(project_root / "data" / "harvester.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HarvesterService")

PID_FILE = project_root / "data" / "harvester.pid"
STATUS_FILE = project_root / "data" / "harvester_status.json"

def _is_process_running(pid: int) -> bool:
    try:
        if os.name == 'nt':
            # Windows specific process check
            import ctypes
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        else:
            # POSIX check
            os.kill(pid, 0)
            return True
    except OSError:
        return False

def get_service_status() -> dict:
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if _is_process_running(pid):
                # Process is active
                if STATUS_FILE.exists():
                    try:
                        status_data = json.loads(STATUS_FILE.read_text())
                        status_data["running"] = True
                        status_data["pid"] = pid
                        return status_data
                    except Exception:
                        pass
                return {"running": True, "pid": pid, "status": "active"}
        except ValueError:
            pass
            
    # Process is inactive or PID file is stale
    status_data = {"running": False, "status": "stopped"}
    if STATUS_FILE.exists():
        try:
            status_data.update(json.loads(STATUS_FILE.read_text()))
            status_data["running"] = False
        except Exception:
            pass
    return status_data

def update_status(status: str, error: str | None = None, success: bool | None = None):
    # Ensure directory exists
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    current_time = datetime.datetime.now().isoformat()
    data = {
        "status": status,
        "updated_at": current_time
    }
    
    # Load existing to preserve metadata
    if STATUS_FILE.exists():
        try:
            existing = json.loads(STATUS_FILE.read_text())
            data.update(existing)
            data["status"] = status
            data["updated_at"] = current_time
        except Exception:
            pass
            
    if status == "harvesting":
        data["last_run_started_at"] = current_time
    elif status == "idle":
        data["last_run_completed_at"] = current_time
        if success is not None:
            data["last_run_success"] = "true" if success else "false"
        if error:
            data["last_error"] = error
            
    try:
        STATUS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to write status file: {e}")

def run_harvest_loop():
    logger.info("Initializing standalone real-time Mubasher TCP-to-ZMQ streamer...")
    update_status("idle", success=True)
    
    import zmq
    from data_engine.mubasher_realtime_source import _read_latest_realtime_auth, parse_quote_messages
    from data_engine.ticker_filters import is_supported_ticker
    from core.exclusions import get_all_exclusions
    from data_engine import intraday_store, parquet_writer
    import socket

    # 1. Initialize ZeroMQ publisher socket
    zmq_context = zmq.Context()
    pub_socket = zmq_context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.LINGER, 0)
    zmq_host = getattr(settings, "ZMQ_HOST", "127.0.0.1")
    zmq_port = getattr(settings, "ZMQ_PORT", "5556")
    pub_socket.bind(f"tcp://{zmq_host}:{zmq_port}")
    logger.info(f"ZeroMQ publisher bound successfully on tcp://{zmq_host}:{zmq_port}")

    # 2. Resolve eligible symbols to subscribe to
    try:
        from data_engine.mubasher_sqlite_source import build_paths, list_intraday_symbols, list_history_symbols
        paths = build_paths(Path(settings.MUBASHER_ROOT_DIR), settings.MUBASHER_USER_ID)
        all_symbols = list(set(list_intraday_symbols(paths) + list_history_symbols(paths)))
        excluded = get_all_exclusions()
        symbols = [s for s in all_symbols if is_supported_ticker(s) and s not in excluded]
    except Exception as sym_err:
        logger.warning(f"Could not load symbol universe from SQLite database: {sym_err}. Falling back to default list.")
        symbols = ["COMI", "HRHO", "FWRY", "EAST", "ABUK", "TMGH", "EKHO", "SWDY", "ETEL", "AMOC"]

    logger.info(f"Subscribing to {len(symbols)} EGX tickers: {symbols}")

    buffer = b""
    while True:
        try:
            logger.info("Reading latest authentication credentials...")
            auth = _read_latest_realtime_auth(Path(settings.MUBASHER_ROOT_DIR))
            
            logger.info(f"Connecting to Mubasher Realtime socket server ({auth.host}:{auth.port})...")
            with socket.create_connection((auth.host, auth.port), timeout=10) as sock:
                sock.settimeout(0.5)
                
                # Send Auth Request
                sock.sendall(auth.payload + b"\n")
                
                # Drain initial authentication response
                time.sleep(0.8)
                try:
                    sock.recv(65536)
                except socket.timeout:
                    pass
                
                # Send subscriptions for all active tickers
                for s in symbols:
                    sock.sendall(b"1\x1c10\x1cCASE~" + s.encode("ascii", errors="ignore") + b"\x1c\n")
                    
                logger.info("Subscriptions sent. Sub-second market listening loop active.")
                update_status("streaming", success=True, error=None)
                
                while True:
                    try:
                        chunk = sock.recv(32768)
                        if not chunk:
                            logger.warning("Mubasher TCP stream disconnected by remote server.")
                            break
                        buffer += chunk
                        
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            if not line:
                                continue
                            
                            snapshots = parse_quote_messages(line)
                            for snap in snapshots:
                                # Update Database Intraday Cache
                                frame = snap.to_intraday_frame()
                                if not frame.empty:
                                    intraday_store.upsert_intraday(snap.symbol, frame, realm="EGX")
                                    if getattr(settings, "INTRADAY_PARQUET_MIRROR", False):
                                        parquet_writer.save_stream(snap.symbol, frame, folder="intraday")
                                
                                # Broadcast TICK to ZeroMQ (subscribers like LiveFeedManager)
                                payload = {
                                    "ticker": snap.symbol,
                                    "price": snap.last,
                                    "volume": snap.last_quantity,
                                    "timestamp": snap.timestamp.timestamp()
                                }
                                pub_socket.send_string(f"TICK {json.dumps(payload)}")
                                logger.info(f"[Stream] TICK {snap.symbol} -> Price: {snap.last:.2f}, Volume: {snap.last_quantity}")
                                
                    except socket.timeout:
                        # Socket timeout is expected during quiet hours, keep waiting
                        continue
                    except Exception as loop_err:
                        logger.error(f"Error in streaming recv loop: {loop_err}")
                        break
                        
        except Exception as conn_err:
            logger.error(f"Connection failed or socket dropped: {conn_err}. Reconnecting in 5 seconds...")
            update_status("error", error=str(conn_err))
            time.sleep(5)

def start_service():
    status = get_service_status()
    if status["running"]:
        print(f"Harvester is already running with PID {status['pid']}.")
        sys.exit(0)
        
    print("Starting background harvester service...")
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Launch self as a background process using Popen
    cmd = [sys.executable, "-m", "data_engine.harvester_service", "run"]
    # Disassociate process from console to run as a daemon
    if os.name == 'nt':
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        proc = subprocess.Popen(
            cmd,
            creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        proc = subprocess.Popen(
            cmd,
            preexec_fn=os.setpgrp,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
    PID_FILE.write_text(str(proc.pid))
    print(f"Harvester started successfully (PID: {proc.pid}).")

def stop_service():
    status = get_service_status()
    if not status["running"]:
        print("Harvester is not running.")
        if PID_FILE.exists():
            PID_FILE.unlink()
        sys.exit(0)
        
    pid = status["pid"]
    print(f"Stopping harvester service (PID: {pid})...")
    
    try:
        if os.name == 'nt':
            # Force termination on Windows safely without shell=True
            try:
                safe_pid = str(int(pid))
                subprocess.run(["taskkill", "/F", "/PID", safe_pid], shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (ValueError, TypeError):
                print(f"[Harvester] Invalid PID for termination: {pid}")
        else:
            os.kill(pid, signal.SIGTERM)
            
        # Wait up to 5 seconds for termination
        for _ in range(10):
            if not _is_process_running(pid):
                break
            time.sleep(0.5)
            
        if _is_process_running(pid):
            # Force kill if still running
            if os.name != 'nt':
                os.kill(pid, signal.SIGKILL)
    except Exception as e:
        print(f"Error stopping process: {e}")
        
    if PID_FILE.exists():
        PID_FILE.unlink()
        
    update_status("stopped")
    print("Harvester stopped successfully.")

def show_status():
    status = get_service_status()
    print("Harvester Service Status:")
    print("-------------------------")
    print(f"Running:     {status['running']}")
    if status['running']:
        print(f"PID:         {status.get('pid')}")
    print(f"State:       {status.get('status', 'stopped')}")
    print(f"Last Update: {status.get('updated_at', 'Never')}")
    print(f"Success:     {status.get('last_run_success', 'N/A')}")
    print(f"Last Run:    {status.get('last_run_completed_at', 'N/A')}")
    if status.get("last_error"):
        print(f"Last Error:  {status.get('last_error')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m data_engine.harvester_service [start|stop|status|run]")
        sys.exit(1)
        
    action = sys.argv[1].lower()
    
    if action == "start":
        start_service()
    elif action == "stop":
        stop_service()
    elif action == "status":
        show_status()
    elif action == "run":
        run_harvest_loop()
    else:
        print(f"Unknown action: {action}")
        print("Usage: python -m data_engine.harvester_service [start|stop|status|run]")
        sys.argv = [sys.argv[0]]
        sys.exit(1)
