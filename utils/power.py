"""
WINDOWS EXECUTION STATE & WORKSTATION KEEP-ALIVE
================================================
Prevents Windows from entering Modern Standby or sleep during active trading sessions.
Uses Kernel32 SetThreadExecutionState without requiring external PowerShell scripts.
"""
from __future__ import annotations

import ctypes
import logging
import os

logger = logging.getLogger("horus.power")

# Windows Kernel32 Execution State Flags
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_AWAYMODE_REQUIRED = 0x00000040

_KEEPALIVE_ACTIVE = False


def set_market_keepalive(enable: bool = True) -> bool:
    """
    Sets thread execution state to keep Windows active during market hours.
    Allows the monitor display to sleep normally while keeping the CPU, background timers,
    and network connection 100% active.
    """
    global _KEEPALIVE_ACTIVE

    if os.name != "nt":
        _KEEPALIVE_ACTIVE = enable
        logger.debug(f"[Power] Non-Windows OS detected ({os.name}); keep-alive flag set to {enable}")
        return True

    try:
        if enable:
            flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
            res = ctypes.windll.kernel32.SetThreadExecutionState(flags)
            _KEEPALIVE_ACTIVE = True
            logger.info(f"[Power] Windows Market Keep-Alive ENGAGED (flags=0x{flags:X}, result=0x{res:X})")
            return res != 0
        else:
            res = ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            _KEEPALIVE_ACTIVE = False
            logger.info(f"[Power] Windows Market Keep-Alive RELEASED (result=0x{res:X})")
            return res != 0
    except Exception as exc:
        logger.warning(f"[Power] Failed to update Windows Execution State: {exc}")
        return False


def is_keepalive_active() -> bool:
    """Returns True if workstation keep-alive is currently engaged."""
    return _KEEPALIVE_ACTIVE
