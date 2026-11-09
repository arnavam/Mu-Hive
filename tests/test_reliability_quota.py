"""Reliability, quota, and enrichment tests (offline).

Covers the Phase E fixes:
  * PipelineResult / main() exit codes
  * summary-only RSS persistence support (needs_enrichment)
  * batched (url, ig) existence checks
  * persistent Groq budget + per-model limits
  * prompt truncation for free-tier tokens-per-minute limits
"""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class TestPipelineResult(unittest.TestCase):
    def test_default_result_is_ok(self):
        from src.orchestrator import PipelineResult

        result = PipelineResult()
        self.assertTrue(result.ok)
        self.assertEqual(result.phase_failures, [])

    def test_failures_mark_not_ok(self):
        from src.orchestrator import PipelineResult

        result = PipelineResult(ok=False, phase_failures=["scout: boom"])
        self.assertFalse(result.ok)
        self.assertEqual(result.phase_failures, ["scout: boom"])


class TestMainExitCodes(unittest.TestCase):
    def _main(self, result):
        import main

        with patch.object(main, "run_pipeline", new=AsyncMock(return_value=result)), \
             patch.object(main, "run_email_agent", return_value=None), \
             patch.object(main, "run_zulip_notifications", new=AsyncMock(return_value=None)):
            return _run(main.main())

    def test_ok_pipeline_returns_zero(self):
        from src.orchestrator import PipelineResult

        self.assertEqual(self._main(PipelineResult(ok=True)), 0)

    def test_degraded_pipeline_returns_one(self):
        from src.orchestrator import PipelineResult

        code = self._main(
            PipelineResult(ok=False, phase_failures=["intelligence: quota"])
        )
        self.assertEqual(code, 1)

    def test_email_failure_returns_one(self):
        import main
        from src.orchestrator import PipelineResult

        with patch.object(main, "run_pipeline", new=AsyncMock(return_value=PipelineResult())), \
             patch.object(main, "run_email_agent", side_effect=RuntimeError("smtp down")), \
             patch.object(main, "run_zulip_notifications", new=AsyncMock(return_value=None)):
            self.assertEqual(_run(main.main()), 1)


class TestQuotaBudget(unittest.TestCase):
    def setUp(self):
        from src.utils import groq_quota

        groq_quota._groq_tokens_used = 0
        groq_quota._daily_cache.clear()

    def tearDown(self):
        from src.utils import groq_quota

        groq_quota._groq_tokens_used = 0
        groq_quota._daily_cache.clear()

    def test_model_specific_limits(self):
        from src.utils import groq_quota

        self.assertEqual(groq_quota.model_tpd_limit("llama-3.1-8b-instant"), 500_000)
        self.assertEqual(groq_quota.model_tpd_limit("openai/gpt-oss-120b"), 200_000)

    def test_in_memory_usage_tracks_default_model(self):
        from src.utils import groq_quota

        groq_quota._groq_tokens_used = 0
        groq_quota._daily_cache.clear()
        with patch.object(groq_quota, "_db_is_open", return_value=False):
            groq_quota.record_llm_usage(
                groq_quota.default_model_name(), input_tokens=1000, output_tokens=500
            )
            self.assertGreaterEqual(groq_quota.get_groq_tokens_used(), 1500)
            self.assertTrue(groq_quota.groq_quota_available())

    def test_budget_guard_blocks_near_limit(self):
        from src.utils import groq_quota

        groq_quota._daily_cache.clear()
        model = groq_quota.default_model_name()
        groq_quota._daily_cache[(groq_quota._today(), model)] = (
            groq_quota.model_tpd_limit(model) - groq_quota.SAFETY_BUFFER + 1
        )
        try:
            self.assertFalse(groq_quota.groq_quota_available(model))
        finally:
            groq_quota._daily_cache.clear()

    def test_parse_429_body(self):
        from src.utils import groq_quota

        groq_quota._groq_tokens_used = 0
        with patch.object(groq_quota, "_db_is_open", return_value=False):
            groq_quota.parse_and_record_groq_usage("Used 123456, Requested 700")
        self.assertEqual(groq_quota.get_groq_tokens_used(), 123456)


class TestPromptTruncation(unittest.TestCase):
    def test_content_is_truncated(self):
        from src.agents import intelligence as intel

        doc = {
            "_id": 1,
            "title": "T" * 5000,
            "scraped_full_text": "C" * 5000,
            "category": "News",
            "ig_tags": ["AI"],
        }
        prompt = intel.build_batch_prompt([doc])
        self.assertIn("C" * intel.INTELLIGENCE_MAX_CONTENT_CHARS, prompt)
        self.assertNotIn("C" * (intel.INTELLIGENCE_MAX_CONTENT_CHARS + 1), prompt)
        self.assertIn("T" * intel.INTELLIGENCE_MAX_TITLE_CHARS, prompt)
        self.assertNotIn("T" * (intel.INTELLIGENCE_MAX_TITLE_CHARS + 1), prompt)


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.rows = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestScrapeRepository(unittest.TestCase):
    def test_existing_url_igs_uses_one_query(self):
        from src.db.repositories import scrape_repository as repo

        cursor = FakeCursor()
        cursor.rows = [
            ("https://a.example/x", "AI"),
            ("https://b.example/y", "Web Development"),
        ]
        conn = MagicMock()
        conn.get_cursor.return_value = cursor

        pairs = [
            ("https://a.example/x", "AI"),
            ("https://a.example/x", "Space"),
            ("https://c.example/z", "AI"),
        ]
        with patch.object(repo, "db_conn", conn):
            found = repo.ScrapeRepository.existing_url_igs(pairs)

        self.assertEqual(len(cursor.executed), 1)
        self.assertEqual(found, {("https://a.example/x", "AI")})

    def test_insert_queue_persists_enrichment_flag(self):
        from src.db.repositories import scrape_repository as repo

        cursor = FakeCursor()
        cursor.rows = [(42,)]
        conn = MagicMock()
        conn.get_cursor.return_value = cursor

        with patch.object(repo, "db_conn", conn):
            row_id = repo.ScrapeRepository.insert_queue(
                "Title", "https://a.example/x", "AI", "RSS", "scraped",
                data={"summary": "short"}, needs_enrichment=True,
            )

        self.assertEqual(row_id, 42)
        self.assertIn("needs_enrichment", cursor.executed[0][0])
        self.assertEqual(cursor.executed[0][1][-1], True)


class TestEnrichmentQueue(unittest.TestCase):
    def test_find_pending_includes_summary_only_rows(self):
        from src.db.repositories import scrape_repository as repo

        cursor = FakeCursor()
        conn = MagicMock()
        conn.get_cursor.return_value = cursor

        with patch.object(repo, "db_conn", conn):
            repo.ScrapeRepository.find_pending(10)

        sql = cursor.executed[0][0]
        self.assertIn("needs_enrichment IS TRUE", sql)
        self.assertIn("retry_count", sql)


class TestEvaluationCache(unittest.TestCase):
    def test_cached_evaluation_skips_llm(self):
        from src.agents import intelligence as intel

        docs = [{
            "_id": 1,
            "title": "Cached article",
            "summary": "text",
            "scraped_full_text": None,
            "category": "News",
            "ig_tags": ["AI"],
            "url": "https://example.com/1",
            "link": "https://example.com/1",
            "source": "RSS",
            "data": {},
        }]
        cached_eval = intel.OpportunityIntelligence(
            is_relevant=True,
            quality_score=8,
            ig_tags=["AI"],
            category="News",
            summary="cached summary",
            reasoning="cached",
            structured_metadata=None,
        ).model_dump()

        fake_db = MagicMock()
        fake_db.get_unprocessed_for_intelligence.return_value = docs
        fake_db.get_cached_evaluations.return_value = {"https://example.com/1": cached_eval}

        with patch.object(intel, "Database", return_value=fake_db), \
             patch.object(intel.batch_intelligence_agent, "run", new_callable=AsyncMock) as run:
            stats = _run(intel.run_intelligence(batch_limit=1))

        run.assert_not_called()
        self.assertEqual(stats["cache_hits"], 1)
        self.assertEqual(stats["total_evaluated"], 1)


if __name__ == "__main__":
    unittest.main()
