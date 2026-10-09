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
    def test_current_year_contributions_and_public_commits_remain_distinct(self):
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
        # Calendar totals already include anonymous private activity when enabled.
        contributions = {2024: (100, 30, 4), 2025: (200, 50, 6), 2026: (113, 61, 8)}

        def graphql(_token, query, variables, root_field="user"):
            if query == card.PROFILE_QUERY:
                return first
            year = int(variables["from"][:4])
            total, commits, repositories = contributions[year]
            days = []
            if year == 2026:
                days = [{"date": "2026-10-07", "contributionCount": 2},
                        {"date": "2026-10-08", "contributionCount": 1}]
            return {"contributionsCollection": {
                "totalCommitContributions": commits,
                "totalRepositoriesWithContributedCommits": repositories,
                "contributionCalendar": {"totalContributions": total,
                                         "weeks": [{"contributionDays": days}]},
            }}

        with patch.object(card, "graphql", side_effect=graphql):
            stats = card.collect_stats("test-token", config, now)
        self.assertEqual(stats.contributions_year, 113)
        self.assertEqual(stats.commits_year, 61)
        self.assertEqual(stats.repositories_year, 8)
        self.assertFalse(stats.contributions_include_private)
        self.assertFalse(stats.languages_include_private)
        self.assertEqual((stats.current_streak, stats.longest_streak), (2, 2))
        self.assertEqual([lang.name for lang in stats.languages], ["Python", "HTML"])
        self.assertEqual(stats.stars, 40)
        svg = card.render_stats(stats, "pt-BR")
        ET.fromstring(svg)
        self.assertIn("Gui &amp; Code", svg)
        self.assertIn(">113</text>", svg)
        self.assertNotIn(">413</text>", svg)
        self.assertNotIn(">141</text>", svg)
        self.assertIn(">8</text>", svg)
        self.assertIn('viewBox="0 0 420 290"', svg)
        self.assertNotIn("Contribuições privadas anônimas", svg)
        self.assertNotIn("todo o período", svg)
        self.assertNotIn("Atividade privada aparece", svg)
        self.assertIn("Commits visíveis · 2026", svg)
        self.assertIn("Repositórios públicos · 2026", svg)
        self.assertIn("Contribuições · 2026", svg)
        self.assertIn('width="48" height="34"', svg)
        self.assertIn("B−", svg)
        self.assertEqual(svg.count('<svg x="'), 7)

        for locale, expected, year_commits in (
            ("en", "GitHub status", "Visible commits · 2026"),
            ("es", "Estado de GitHub", "Commits visibles · 2026"),
        ):
            localized_stats = card.render_stats(stats, locale)
            self.assertIn(expected, localized_stats)
            self.assertIn(year_commits, localized_stats)
            ET.fromstring(localized_stats)
            languages_svg = card.render_languages(stats, locale)
            ET.fromstring(languages_svg)
            self.assertNotIn("Proporção de bytes", languages_svg)
            self.assertNotIn("Share of code bytes", languages_svg)
            ET.fromstring(card.render_rhythm(stats, locale))
            ET.fromstring(card.render_rhythm(stats, locale, mobile=True))
        rows, total = card.language_rows(stats, "pt-BR")
        self.assertEqual(total, 1000)
        self.assertAlmostEqual(sum(row[2] for row in rows), 1)

    def test_private_language_token_adds_only_language_aggregates(self):
        now = datetime(2026, 10, 9, 2, 20, tzinfo=timezone.utc)
        first = {
            "name": "Gui", "contributionsCollection": {"contributionYears": [2026]},
            "pullRequests": {"totalCount": 0}, "issues": {"totalCount": 0},
            "repositories": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}},
        }
        private = {
            "repositories": {"nodes": [
                {"name": "secret-project", "stargazerCount": 0, "isFork": False, "isArchived": False,
                 "languages": {"edges": [
                     {"size": 300, "node": {"name": "Python", "color": "#3572A5"}},
                     {"size": 700, "node": {"name": "Rust", "color": "#dea584"}},
                 ]}},
            ], "pageInfo": {"hasNextPage": False, "endCursor": None}},
        }

        def graphql(token, query, variables, root_field="user"):
            if query == card.PROFILE_QUERY:
                return first
            if query == card.PRIVATE_REPOSITORIES_QUERY:
                self.assertEqual(token, "private-read-token")
                self.assertEqual(root_field, "viewer")
                return private
            return {"contributionsCollection": {
                "totalCommitContributions": 0,
                "totalRepositoriesWithContributedCommits": 0,
                "contributionCalendar": {"totalContributions": 25, "weeks": []},
            }}

        with patch.object(card, "graphql", side_effect=graphql):
            stats = card.collect_stats("public-token", {"username": "GuiCodeLabs"}, now,
                                       private_repositories_token="private-read-token")

        self.assertTrue(stats.languages_include_private)
        self.assertEqual([(item.name, item.size) for item in stats.languages],
                         [("Rust", 700), ("Python", 300)])
        self.assertNotIn("secret-project", str(card.asdict(stats)))
        svg = card.render_languages(stats, "pt-BR")
        self.assertIn("Código público + privado acessível", svg)
        self.assertNotIn("secret-project", svg)

    def test_read_user_token_includes_private_repository_commit_count(self):
        now = datetime(2026, 10, 9, 2, 20, tzinfo=timezone.utc)
        first = {
            "name": "Gui", "contributionsCollection": {"contributionYears": [2026]},
            "pullRequests": {"totalCount": 0}, "issues": {"totalCount": 0},
            "repositories": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}},
        }

        def graphql(token, query, variables, root_field="user"):
            if query == card.PROFILE_QUERY:
                return first
            if token == "read-user-token":
                return {"contributionsCollection": {
                    "totalCommitContributions": 12,
                    "totalRepositoriesWithContributedCommits": 5,
                    "contributionCalendar": {"totalContributions": 24, "weeks": []},
                }}
            raise AssertionError("Expected the private read:user token for contribution data")

        with patch.object(card, "graphql", side_effect=graphql):
            stats = card.collect_stats(
                "public-token", {"username": "GuiCodeLabs"}, now,
                private_contributions_token="read-user-token",
            )

        self.assertTrue(stats.contributions_include_private)
        self.assertEqual(stats.repositories_year, 5)
        self.assertIn("Repositórios · 2026", card.render_stats(stats, "pt-BR"))

    def test_language_grid_reads_left_to_right_by_size(self):
        stats = card.Stats(
            username="GuiCodeLabs", name="Gui", year=2026,
            contributions_year=4, commits_year=1,
            stars=0, prs=0, issues=0,
            languages=(card.Language("Python", "#3572A5", 600),
                       card.Language("PHP", "#4F5D95", 250),
                       card.Language("HTML", "#e34c26", 100),
                       card.Language("CSS", "#663399", 50)),
            current_streak=0, longest_streak=0, recent_days=(),
        )
        svg = card.render_languages(stats, "pt-BR")
        self.assertLess(svg.index(">Python</text>"), svg.index(">PHP</text>"))
        self.assertLess(svg.index(">PHP</text>"), svg.index(">HTML</text>"))
        self.assertIn('viewBox="0 0 420 290"', svg)
        self.assertIn('viewBox="0 0 420 290"', card.render_stats(stats, "pt-BR"))

    def test_year_boundaries_match_github_utc_calendar(self):
        from_, to = card.year_bounds(2025, datetime(2026, 10, 9, tzinfo=timezone.utc))
        self.assertEqual(from_, "2025-01-01T00:00:00+00:00")
        self.assertEqual(to, "2025-12-31T23:59:59+00:00")

    def test_streak_uses_yesterday_when_today_has_no_activity(self):
        today = date(2026, 10, 8)
        self.assertEqual(card.streak_lengths({today.replace(day=6): 1,
                                              today.replace(day=7): 1,
                                              today: 0}, today), (2, 2))

    def test_rhythm_card_has_more_space_for_a_clear_recent_activity_axis(self):
        stats = card.Stats(
            username="GuiCodeLabs", name="Gui", year=2026,
            contributions_year=4, commits_year=1,
            stars=0, prs=0, issues=0, languages=(),
            current_streak=2, longest_streak=4, recent_days=(0,) * 34 + (4,),
        )
        desktop = card.render_rhythm(stats, "pt-BR")
        mobile = card.render_rhythm(stats, "pt-BR", mobile=True)
        ET.fromstring(desktop)
        ET.fromstring(mobile)
        self.assertIn('viewBox="0 0 840 290"', desktop)
        self.assertIn('viewBox="0 0 420 290"', mobile)
        self.assertIn("Últimos 35 dias", desktop)
        self.assertIn("Conquistas do ano", desktop)
        self.assertIn("Sequência atual", desktop)
        self.assertNotIn("todo o período", desktop)
        self.assertEqual(desktop.count('width="12" height="12" fill='), 35)

    def test_recent_activity_uses_square_heatmap_and_localized_labels(self):
        stats = card.Stats(
            username="GuiCodeLabs", name="Gui", year=2026,
            contributions_year=4, commits_year=1,
            stars=0, prs=0, issues=0, languages=(),
            current_streak=2, longest_streak=4, recent_days=(0, 1, 5, 15, 40, 100),
        )
        portuguese = card.render_rhythm(stats, "pt-BR")
        english = card.render_rhythm(stats, "en")
        spanish = card.render_rhythm(stats, "es")
        for svg in (portuguese, english, spanish):
            ET.fromstring(svg)
        self.assertIn("mais antigo", portuguese)
        self.assertIn("hoje", portuguese)
        self.assertIn("oldest", english)
        self.assertIn("today", english)
        self.assertIn("más antiguo", spanish)
        self.assertIn("hoy", spanish)

    def test_activity_grade_is_custom_and_uses_annual_contribution_thresholds(self):
        self.assertEqual(card.activity_grade(0), "D")
        self.assertEqual(card.activity_grade(100), "B−")
        self.assertEqual(card.activity_grade(400), "B+")
        self.assertEqual(card.activity_grade(1500), "A+")
        self.assertEqual(card.activity_grade(2500), "S")

if __name__ == "__main__":
    unittest.main()

