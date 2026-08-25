"""Small ANSI colour helper for terminal output.

No dependencies. Colour is switched off automatically when output is piped or
redirected, so the generated result files stay clean, and it can be forced off
with NO_COLOR=1 or --no-color.

Symbols are ASCII on purpose. Fancy unicode does not render reliably in Git Bash
or the older Windows console.
"""
from __future__ import annotations

import os
import sys

CODES = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "grey": "\033[90m",
}

_enabled = False


def _enable_windows_vt() -> None:
    """Turn on ANSI escape handling in the Windows console."""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        # -11 is STD_OUTPUT_HANDLE, 0x0004 is ENABLE_VIRTUAL_TERMINAL_PROCESSING.
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:  # pragma: no cover - best effort only
        pass


def init(force: bool | None = None) -> bool:
    """Decide whether to colour, once, at start-up.

    Args:
        force: True to always colour, False to never. None to auto-detect.
    """
    global _enabled
    if force is False or os.environ.get("NO_COLOR"):
        _enabled = False
        return _enabled
    if force is True or os.environ.get("FORCE_COLOR"):
        _enable_windows_vt()
        _enabled = True
        return _enabled
    _enabled = bool(getattr(sys.stdout, "isatty", lambda: False)())
    if _enabled:
        _enable_windows_vt()
    return _enabled


def enabled() -> bool:
    return _enabled


def paint(text: str, *styles: str) -> str:
    """Wrap ``text`` in the given styles, or return it untouched."""
    if not _enabled or not styles:
        return text
    prefix = "".join(CODES[s] for s in styles if s in CODES)
    return f"{prefix}{text}{CODES['reset']}" if prefix else text


# Shorthands, so call sites read as prose.
def bold(t: str) -> str:
    return paint(t, "bold")


def dim(t: str) -> str:
    return paint(t, "dim")


def red(t: str) -> str:
    return paint(t, "red")


def green(t: str) -> str:
    return paint(t, "green")


def yellow(t: str) -> str:
    return paint(t, "yellow")


def cyan(t: str) -> str:
    return paint(t, "cyan")


def magenta(t: str) -> str:
    return paint(t, "magenta")


def grey(t: str) -> str:
    return paint(t, "grey")


def rule(label: str, style: str = "bold", width: int = 72) -> str:
    """A labelled horizontal rule, e.g. '== ANSWER ============'."""
    head = f"== {label} "
    return paint(head + "=" * max(width - len(head), 0), style)
