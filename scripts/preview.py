#!/usr/bin/env python3
"""Render every card from a previously generated snapshot, without API calls."""

import argparse
import json
from dataclasses import fields
from pathlib import Path

from generate_card import (SUPPORTED_LOCALES, Language, Stats, output_name,
                           render_languages, render_rhythm, render_stats)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("profile/data.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("preview"))
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    data.pop("generated_at", None)
    data["languages"] = tuple(Language(**item) for item in data["languages"])
    data["recent_days"] = tuple(data["recent_days"])
    # Older public snapshots may include visitor and all-time fields no longer rendered.
    fields_in_card = {field.name for field in fields(Stats)}
    data = {key: value for key, value in data.items() if key in fields_in_card}
    data.setdefault("languages_include_private", False)
    data.setdefault("repositories_year", 0)
    data.setdefault("contributions_include_private", False)
    stats = Stats(**data)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for locale in SUPPORTED_LOCALES:
        cards = {
            "stats": render_stats(stats, locale),
            "languages": render_languages(stats, locale),
            "rhythm": render_rhythm(stats, locale),
            "rhythm-mobile": render_rhythm(stats, locale, mobile=True),
        }
        for kind, svg in cards.items():
            (args.output_dir / output_name(kind, locale)).write_text(svg, encoding="utf-8")
    print(f"Rendered {len(SUPPORTED_LOCALES) * 4} SVGs in {args.output_dir}")


if __name__ == "__main__":
    main()
