import importlib.util
import sys
import unittest
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "generate_card", Path(__file__).resolve().parents[1] / "scripts" / "generate_card.py"
)
card = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = card
spec.loader.exec_module(card)


class CardTests(unittest.TestCase):
    def test_calendar_and_public_commits_remain_distinct(self):
        now = datetime(2026, 10, 9, 2, 20, tzinfo=timezone.utc)
        config = {"username": "GuiCodeLabs", "display_name": "Gui & Code",
                  "exclude_repositories": ["profile"]}
        first = {
            "name": "Gui", "contributionsCollection": {"contributionYears": [2024, 2025, 2026]},
            "pullRequests": {"totalCount": 2}, "issues": {"totalCount": 0},
            "repositories": {"nodes": [
                {"name": "project", "stargazerCount": 40, "isFork": False, "isArchived": False,
                 "languages": {"edges": [
                     {"size": 800, "node": {"name": "Python", "color": "#3572A5"}},
                     {"size": 200, "node": {"name": "HTML", "color": "#e34c26"}}]}},
                {"name": "profile", "stargazerCount": 0, "isFork": False, "isArchived": False,
                 "languages": {"edges": [{"size": 2000, "node": {"name": "Markdown", "color": "#000000"}}]}},
            ], "pageInfo": {"hasNextPage": False, "endCursor": None}},
        }
        contributions = {2024: (100, 30, 0), 2025: (200, 50, 50), 2026: (113, 61, 80)}

        def graphql(_token, query, variables):
            if query == card.PROFILE_QUERY:
                return first
            year = int(variables["from"][:4])
            total, commits, private = contributions[year]
            days = []
            if year == 2026:
                days = [{"date": "2026-10-07", "contributionCount": 2},
                        {"date": "2026-10-08", "contributionCount": 1}]
            return {"contributionsCollection": {
                "totalCommitContributions": commits, "restrictedContributionsCount": private,
                "contributionCalendar": {"totalContributions": total,
                                         "weeks": [{"contributionDays": days}]},
            }}

        with patch.object(card, "graphql", side_effect=graphql):
            stats = card.collect_stats("test-token", config, now, 7)
        self.assertEqual((stats.contributions_all, stats.contributions_year), (413, 113))
        self.assertEqual((stats.commits_all, stats.commits_year), (141, 61))
        self.assertEqual((stats.restricted_all, stats.restricted_year), (130, 80))
        self.assertEqual((stats.current_streak, stats.longest_streak), (2, 2))
        self.assertEqual([lang.name for lang in stats.languages], ["Python", "HTML"])
        self.assertEqual(stats.stars, 40)
        svg = card.render_stats(stats, "pt-BR")
        ET.fromstring(svg)
        self.assertIn('data-visits="7"', svg)
        self.assertIn('id="visits-value"', svg)
        self.assertIn("Gui &amp; Code", svg)
        self.assertIn("413", svg)
        self.assertIn("141", svg)
        self.assertIn('viewBox="0 0 420 344"', svg)
        self.assertIn("Privadas anônimas", svg)
        self.assertIn("Commits visíveis", svg)

        for locale, expected in (("en", "GitHub statistics"), ("es", "Estadísticas de GitHub")):
            self.assertIn(expected, card.render_stats(stats, locale))
            ET.fromstring(card.render_languages(stats, locale))
            ET.fromstring(card.render_rhythm(stats, locale))
            ET.fromstring(card.render_rhythm(stats, locale, mobile=True))
        rows, total = card.language_rows(stats, "pt-BR")
        self.assertEqual(total, 1000)
        self.assertAlmostEqual(sum(row[2] for row in rows), 1)

    def test_year_boundaries_match_github_utc_calendar(self):
        from_, to = card.year_bounds(2025, datetime(2026, 10, 9, tzinfo=timezone.utc))
        self.assertEqual(from_, "2025-01-01T00:00:00+00:00")
        self.assertEqual(to, "2025-12-31T23:59:59+00:00")

    def test_streak_uses_yesterday_when_today_has_no_activity(self):
        today = date(2026, 10, 8)
        self.assertEqual(card.streak_lengths({today.replace(day=6): 1,
                                              today.replace(day=7): 1,
                                              today: 0}, today), (2, 2))

    def test_visit_count_uses_last_numeric_text_in_badge(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><text>views</text><text>1,234</text><text>1,234</text></svg>'
        self.assertEqual(card.parse_visit_badge(svg), 1234)


if __name__ == "__main__":
    unittest.main()
