import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "generate_card", Path(__file__).resolve().parents[1] / "scripts" / "generate_card.py"
)
card = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = card
spec.loader.exec_module(card)


class CardTests(unittest.TestCase):
    def test_visit_count_uses_last_numeric_text_in_badge(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><text>Visitas ao perfil</text><text>1,234</text><text>1,234</text></svg>'
        self.assertEqual(card.parse_visit_badge(svg), 1234)

    def test_svg_distinguishes_all_time_and_calendar_year(self):
        now = datetime(2026, 10, 9, 2, 20, tzinfo=timezone.utc)
        stats = card.Stats("Guilherme Beserra", 40, 131, 103, 2, 0, 7)
        svg = card.render_card(stats, now)
        self.assertIn("Commits · todo o período", svg)
        self.assertIn("Commits · 2026", svg)
        self.assertIn('data-visits="7"', svg)
        self.assertIn("08/10/2026 23:20 BRT", svg)
        self.assertNotIn("token", svg.lower())


if __name__ == "__main__":
    unittest.main()
