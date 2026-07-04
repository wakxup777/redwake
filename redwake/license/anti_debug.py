"""Anti-debugging checks. Call at process startup before doing any real work."""
from __future__ import annotations

import ctypes
import os
import sys
import time


def _is_traced_ptrace() -> bool:
    """Returns True if process is being ptraced (gdb, strace, ltrace)."""
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        # PTRACE_TRACEME = 0
        # If already traced, ptrace(PTRACE_TRACEME) returns -1 with EPERM
        PTRACE_TRACEME = 0
        if libc.ptrace(PTRACE_TRACEME, 0, 0, 0) == -1:
            err = ctypes.get_errno()
            if err == 1:  # EPERM — already being traced
                return True
    except Exception:
        pass
    return False


def _has_debugger_in_maps() -> bool:
    """Scans /proc/self/maps for loaded debugger/analysis libraries."""
    debugger_patterns = (
        b"gdb",
        b"ltrace",
        b"strace",
        b"lldb",
        b"libdebugger",
        b"frida",
        b"ida",
        b"ghidra",
        b"radare",
        b"rizin",
        b"capstone",
    )
    try:
        with open("/proc/self/maps", "rb") as f:
            content = f.read()
        for pat in debugger_patterns:
            if pat in content:
                return True
    except OSError:
        pass
    return False


def _has_ld_preload() -> bool:
    """Detects LD_PRELOAD-based injection."""
    return bool(os.environ.get("LD_PRELOAD"))


def _timing_anomaly() -> bool:
    """Sleep 50ms; if delta > 200ms, debugger likely slowed execution."""
    start = time.perf_counter()
    time.sleep(0.05)
    delta = time.perf_counter() - start
    return delta > 0.2


def check() -> None:
    """Run all anti-debug checks. Exits with code 137 if anything detected.

    Silent exit — no traceback, no error message — to deny attacker feedback.
    """
    if _is_traced_ptrace() or _has_debugger_in_maps() or _has_ld_preload() or _timing_anomaly():
        os._exit(137)
