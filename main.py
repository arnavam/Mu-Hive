#!/usr/bin/env python3
"""
main.py
=======
Triggers the Zulip notification pipeline.
"""

from scripts.zulip_notify import run_zulip_notifications
from scripts.gmailsender import run_email_agent
import asyncio
import sys
import os

# Ensure scripts directory is in path
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'scripts')))


async def main():
    print("\n🌊 Mu-Hive Notification Agent Starting...")

    try:
        run_email_agent()
        await run_zulip_notifications()
    except Exception as e:
        print(f"❌ Notification failed: {e}")

    print("🏁 Task Complete.\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Crashed: {e}")
