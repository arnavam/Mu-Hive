"""
Verify that the Mu-Hive environment is correctly configured before running the pipeline.
Checks: Database connectivity, Groq API key presence.
"""
import sqlite3
import sys
import os
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))


def test_db():
    """Verify the SQLite database exists and is readable."""
    try:
        db_path = os.path.join(ROOT_DIR, "mu_hive.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the opportunities table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='opportunities'")
        if not cursor.fetchone():
            print("[WARN] DATABASE: 'opportunities' table does not exist yet. Run 'python main.py' to initialize.")
            conn.close()
            return True  # Not a failure — table gets created on first run

        count = cursor.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
        unprocessed = cursor.execute("SELECT COUNT(*) FROM opportunities WHERE quality_score IS NULL").fetchone()[0]
        conn.close()
        print(f"[OK]   DATABASE: {count} total opportunities, {unprocessed} awaiting evaluation.")
        return True
    except Exception as e:
        print(f"[FAIL] DATABASE ERROR: {e}")
        return False


def test_groq():
    """Verify the Groq API key is set in environment."""
    if os.getenv("GROQ_API_KEY"):
        print("[OK]   GROQ: API key is configured.")
        return True
    else:
        print("[FAIL] GROQ: GROQ_API_KEY is not set! Add it to your .env file.")
        return False


if __name__ == '__main__':
    print("=" * 45)
    print("  Mu-Hive Environment Verification")
    print("=" * 45)

    db_ok = test_db()
    groq_ok = test_groq()

    print("-" * 45)
    if db_ok and groq_ok:
        print(">>> ALL CHECKS PASSED. Ready to run: python main.py")
        sys.exit(0)
    else:
        print(">>> SOME CHECKS FAILED. Fix the issues above before running.")
        sys.exit(1)
