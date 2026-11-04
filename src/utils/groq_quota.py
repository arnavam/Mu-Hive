# src/utils/groq_quota.py
"""Groq free-tier budget tracking.

The free tier is limited per model per UTC day. The pipeline runs daily, so
usage must survive process restarts: the authoritative counter is the
``llm_usage`` table (falling back to an in-process counter if the DB is
unreachable).

Observed free-tier TPD (Nov 2026):
  * ``llama-3.1-8b-instant``   500,000 tokens/day
  * ``openai/gpt-oss-120b``    200,000 tokens/day
All values can be overridden with ``GROQ_TPD_LIMIT`` or
``GROQ_TPD_LIMIT_<MODEL>`` (model name upper-cased, non-alphanumerics -> _).
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Defaults per model family. Keep the cheaper/high-quota model the default.
_MODEL_TPD = {
    "llama-3.1-8b-instant": 500_000,
    "meta-llama/llama-4-scout-17b-16e-instruct": 500_000,
    "openai/gpt-oss-120b": 200_000,
    "openai/gpt-oss-20b": 200_000,
    "llama-3.3-70b-versatile": 100_000,
}
_DEFAULT_TPD = int(os.getenv("GROQ_TPD_LIMIT", "200000"))
# Reserve headroom so we route/stop before a hard 429.
SAFETY_BUFFER = int(os.getenv("GROQ_SAFETY_BUFFER", "15000"))

_DEFAULT_MODEL = os.getenv("GROQ_BULK_MODEL", "openai/gpt-oss-20b")

_groq_tokens_used: int = 0          # in-process high-water mark
_daily_cache: dict[tuple[str, str], int] = {}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _env_suffix(model_name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", (model_name or "").upper()).strip("_")


def model_tpd_limit(model_name: str | None = None) -> int:
    """Return the daily token limit for a Groq model."""
    model_name = model_name or _DEFAULT_MODEL
    override = os.getenv(f"GROQ_TPD_LIMIT_{_env_suffix(model_name)}")
    if override:
        try:
            return int(override)
        except ValueError:
            logger.warning("Invalid GROQ_TPD_LIMIT_%s=%r", _env_suffix(model_name), override)
    return _MODEL_TPD.get(model_name, _DEFAULT_TPD)


def _db_is_open() -> bool:
    """True when the shared DB connection is already usable.

    The quota counter must never open a connection by itself (import-time or
    unit tests would hit the network); during a real run the pipeline has
    already connected before any LLM call.
    """
    try:
        from src.db.connection import db_conn

        conn = getattr(db_conn, "_conn", None)
        return conn is not None and not getattr(conn, "closed", 1)
    except Exception:
        return False


def _read_daily_tokens(model_name: str) -> int:
    cache_key = (_today(), model_name)
    if cache_key in _daily_cache:
        return _daily_cache[cache_key]
    if not _db_is_open():
        return _groq_tokens_used
    try:
        from src.db.connection import db_conn

        with db_conn.get_cursor() as cur:
            cur.execute(
                "SELECT input_tokens + output_tokens FROM llm_usage "
                "WHERE usage_date = %s AND model = %s",
                (_today(), model_name),
            )
            row = cur.fetchone()
        used = int(row[0]) if row and row[0] is not None else 0
    except Exception as exc:  # DB unavailable: degrade to in-process count
        logger.debug("Could not read persistent LLM usage: %s", exc)
        used = _groq_tokens_used
    _daily_cache[cache_key] = used
    return used


def _write_daily_tokens(model_name: str, total_tokens: int) -> None:
    if total_tokens < 0:
        return
    cache_key = (_today(), model_name)
    _daily_cache[cache_key] = total_tokens
    if not _db_is_open():
        return
    try:
        from src.db.connection import db_conn

        with db_conn.get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO llm_usage (usage_date, model, input_tokens, output_tokens, requests)
                VALUES (%s, %s, 0, %s, 0)
                ON CONFLICT (usage_date, model) DO UPDATE SET
                    output_tokens = GREATEST(llm_usage.output_tokens, EXCLUDED.output_tokens),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (_today(), model_name, total_tokens),
            )
    except Exception as exc:
        logger.debug("Could not persist LLM usage: %s", exc)


def record_llm_usage(model_name: str, input_tokens: int = 0, output_tokens: int = 0,
                     requests: int = 1) -> None:
    """Persist a completed request's token usage (best effort)."""
    global _groq_tokens_used
    model_name = model_name or _DEFAULT_MODEL
    input_tokens = max(0, int(input_tokens or 0))
    output_tokens = max(0, int(output_tokens or 0))
    requests = max(0, int(requests or 0))
    if _db_is_open():
        try:
            from src.db.connection import db_conn

            with db_conn.get_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO llm_usage (usage_date, model, input_tokens, output_tokens, requests)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (usage_date, model) DO UPDATE SET
                        input_tokens = llm_usage.input_tokens + EXCLUDED.input_tokens,
                        output_tokens = llm_usage.output_tokens + EXCLUDED.output_tokens,
                        requests = llm_usage.requests + EXCLUDED.requests,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING input_tokens + output_tokens
                    """,
                    (_today(), model_name, input_tokens, output_tokens, requests),
                )
                row = cur.fetchone()
            if row and row[0] is not None:
                _daily_cache[(_today(), model_name)] = int(row[0])
        except Exception as exc:
            logger.debug("Could not record LLM usage: %s", exc)

    if model_name == _DEFAULT_MODEL:
        _groq_tokens_used = max(
            _groq_tokens_used,
            input_tokens + output_tokens,
            _read_daily_tokens(model_name),
        )
    logger.info(
        "LLM usage: %s +%d in / +%d out (today: %d / %d TPD)",
        model_name,
        input_tokens,
        output_tokens,
        _read_daily_tokens(model_name),
        model_tpd_limit(model_name),
    )


def record_groq_usage(tokens_used: int):
    """Backward-compatible hook for usage parsed out of a 429 body."""
    global _groq_tokens_used
    _groq_tokens_used = max(_groq_tokens_used, int(tokens_used or 0))
    _write_daily_tokens(_DEFAULT_MODEL, _groq_tokens_used)
    logger.info(
        "Groq TPD updated: %d used, %d remaining.",
        _groq_tokens_used,
        max(0, model_tpd_limit(_DEFAULT_MODEL) - _groq_tokens_used),
    )


def get_daily_tokens(model_name: str | None = None) -> int:
    return _read_daily_tokens(model_name or _DEFAULT_MODEL)


def groq_quota_available(model_name: str | None = None) -> bool:
    """True while the model has more than the safety buffer left today."""
    model_name = model_name or _DEFAULT_MODEL
    remaining = model_tpd_limit(model_name) - _read_daily_tokens(model_name)
    return remaining > SAFETY_BUFFER


def get_groq_tokens_used() -> int:
    """Current high-water mark (observability only)."""
    return max(_groq_tokens_used, get_daily_tokens())


def parse_and_record_groq_usage(error_message: str):
    """Parse ``Used 12345`` out of a 429 body and persist it."""
    match = re.search(r"used\s+(\d+)", error_message or "", re.IGNORECASE)
    if match:
        record_groq_usage(int(match.group(1)))


def default_model_name() -> str:
    return _DEFAULT_MODEL
