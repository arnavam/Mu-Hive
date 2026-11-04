#!/usr/bin/env python3
"""
main.py
=======
Triggers the Zulip notification pipeline.
"""

import asyncio
import logging
import sys
import os

from src.config.console import configure_stdio

# Must happen before importing agents/loggers that emit emoji/arrows.
configure_stdio()

from scripts.zulip_notify import run_zulip_notifications
from scripts.gmailsender import run_email_agent
from src.agents.intelligence import LLMFailureThresholdExceeded
from src.orchestrator import run_pipeline
from src.config.logging_config import setup_logging

setup_logging()

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'scripts')))


logger = logging.getLogger(__name__)


async def main() -> int:
    print("\n🌊 Mu-Hive Notification Agent Starting...")
    failures: list[str] = []

    try:
        result = await run_pipeline()
        if not result.ok:
            failures.extend(result.phase_failures)
    except LLMFailureThresholdExceeded:
        raise
    except Exception as e:
        logger.exception("Pipeline stage crashed")
        print(f"❌ Pipeline failed: {e}")
        failures.append(f"pipeline: {e}")

    # Email agent — isolated so a failure doesn't block Zulip
    try:
        run_email_agent()
    except Exception as e:
        logger.exception("Email stage crashed")
        print(f"❌ Email sending failed: {e}")
        failures.append(f"email: {e}")

    # Zulip notifications — isolated so a failure doesn't mask email results
    try:
        await run_zulip_notifications()
    except Exception as e:
        logger.exception("Zulip stage crashed")
        print(f"❌ Zulip notifications failed: {e}")
        failures.append(f"zulip: {e}")

    if failures:
        stages = ", ".join(failure.split(":", 1)[0] for failure in failures)
        print(f"⚠️ Task finished with {len(failures)} failed stage(s): {stages}\n")
        return 1

    print("🏁 Task Complete.\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nStopped by user.")
        raise SystemExit(130)
    except LLMFailureThresholdExceeded as e:
        logger.exception("Pipeline aborted")
        print(f"Crashed: {e}")
        raise SystemExit(1)
    except Exception as e:
        logger.exception("Fatal error")
        print(f"Crashed: {e}")
        raise SystemExit(1)
