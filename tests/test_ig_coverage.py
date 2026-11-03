"""tests/test_ig_coverage.py
============================
Regression coverage for the 12 requested Interest Groups.

Guards the two discovery inputs that must exist for every IG:
  * curated RSS feeds in ``src.config.sources.ALL_RSS_FEEDS``
  * hackathon keyword mappings in ``src.config.constants.IG_KEYWORDS``

Also asserts user-facing names (e.g. "Game Development", "Quantum
Technologies") normalize onto the canonical registry IG. Offline only.
"""

import unittest

from src.config.constants import IG_KEYWORDS, MASTER_IGS
from src.config.interest_groups import registry
from src.config.sources import ALL_RSS_FEEDS, group_feeds_by_url
from src.utils.ig_normalizer import normalize_ig

# User-facing name -> canonical registry IG name.
REQUESTED_IGS = {
    "Devops": "Devops",
    "Game Development": "Game Dev",
    "Cyber Security": "Cyber Security",
    "UI/UX": "UI/UX",
    "Data Analytics": "Data Analytics",
    "AI": "AI",
    "Data Structures and Algorithm": "Data Structures and Algorithm",
    "Blockchain": "Blockchain",
    "Data Science": "Data Science",
    "Web Development": "Web Development",
    "Quantum Technologies": "Quantum Computing",
    "Internet Of Things (IOT) And Robotics": "Internet Of Things (IOT) And Robotics",
}

MIN_FEEDS_PER_IG = 3
MIN_KEYWORDS_PER_IG = 5


class TestRequestedIgCoverage(unittest.TestCase):
    def test_names_normalize_to_canonical_igs(self):
        for requested, canonical in REQUESTED_IGS.items():
            with self.subTest(requested=requested):
                self.assertEqual(normalize_ig(requested), canonical)

    def test_all_requested_igs_are_active_and_registered(self):
        for canonical in REQUESTED_IGS.values():
            with self.subTest(ig=canonical):
                ig = registry.get(canonical)
                self.assertIsNotNone(ig, f"{canonical} missing from registry")
                self.assertTrue(ig.is_active)
                self.assertIn(canonical, registry.all_active_names())

    def test_every_requested_ig_has_rss_feeds(self):
        for canonical in REQUESTED_IGS.values():
            with self.subTest(ig=canonical):
                feeds = ALL_RSS_FEEDS.get(canonical)
                self.assertIsNotNone(feeds, f"{canonical} has no RSS feed list")
                self.assertGreaterEqual(
                    len(feeds),
                    MIN_FEEDS_PER_IG,
                    f"{canonical} has only {len(feeds)} feed(s)",
                )

    def test_feed_urls_are_well_formed_and_unique(self):
        for ig, feeds in ALL_RSS_FEEDS.items():
            with self.subTest(ig=ig):
                self.assertEqual(
                    len(feeds), len(set(feeds)), f"{ig} has duplicate feed URLs"
                )
                for url in feeds:
                    self.assertTrue(
                        url.startswith("https://"),
                        f"{ig} feed is not HTTPS: {url}",
                    )

    def test_every_rss_key_maps_to_a_known_ig(self):
        known = set(registry.all_names())
        for ig in ALL_RSS_FEEDS:
            with self.subTest(ig=ig):
                canonical = normalize_ig(ig)
                self.assertIsNotNone(canonical, f"{ig} does not normalize")
                self.assertIn(canonical, known)

    def test_every_requested_ig_has_hackathon_keywords(self):
        for canonical in REQUESTED_IGS.values():
            with self.subTest(ig=canonical):
                self.assertIn(canonical, MASTER_IGS)
                keywords = IG_KEYWORDS.get(canonical)
                self.assertIsNotNone(keywords, f"{canonical} has no keywords")
                self.assertGreaterEqual(
                    len(keywords),
                    MIN_KEYWORDS_PER_IG,
                    f"{canonical} has only {len(keywords)} keywords",
                )

    def test_quantum_technology_variants_map_to_keywords(self):
        quantum_keywords = {kw.lower() for kw in IG_KEYWORDS["Quantum Computing"]}
        for variant in ("quantum technologies", "quantum technology", "quantum tech"):
            with self.subTest(variant=variant):
                self.assertIn(variant, quantum_keywords)

    def test_shared_feed_grouping_is_stable(self):
        grouped = group_feeds_by_url(ALL_RSS_FEEDS)
        unique_urls = {url for feeds in ALL_RSS_FEEDS.values() for url in feeds}
        self.assertEqual(len(grouped), len(unique_urls))
        for owners in grouped.values():
            self.assertGreaterEqual(len(owners), 1)
            self.assertEqual(len(owners), len(set(owners)))

    def test_shared_feed_keeps_both_ig_owners(self):
        grouped = group_feeds_by_url(ALL_RSS_FEEDS)
        owners = grouped.get("https://www.kdnuggets.com/feed", [])
        self.assertIn("Data Science", owners)
        self.assertIn("Data Analytics", owners)


if __name__ == "__main__":
    unittest.main()
