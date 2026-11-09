# src/config/console.py
"""Console encoding safety for Windows.

Windows consoles and redirected files default to the legacy ANSI code page
(cp1252), where emoji and box-drawing characters raise UnicodeEncodeError.
The pipeline prints/ logs such characters, so stdio is forced to UTF-8 with
a replacement fallback at startup. This never changes file IO encoding.
"""

import sys


def configure_stdio() -> None:
    """Best-effort UTF-8 for stdout/stderr; safe to call more than once."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            # Older/custom streams may not support reconfiguration; ignore.
            pass
