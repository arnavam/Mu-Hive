#!/usr/bin/env python3
"""
main.py
=======
Triggers the Zulip notification pipeline.
"""

import asyncio
import sys
import os

# Ensure scripts directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))

from scripts.zulip_notify import run_zulip_notifications

async def main():
    print("\n🌊 Mu-Hive Notification Agent Starting...")
    
    # JOHAN'S PART: Send vetted data from DB to Zulip
    try:
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
