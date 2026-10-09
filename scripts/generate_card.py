#!/usr/bin/env python3
"""Collect public GitHub activity and render original, dependency-free SVG cards."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


GRAPHQL_URL = "https://api.github.com/graphql"
SUPPORTED_LOCALES = ("pt-BR", "en", "es")
PALETTE = ("#7aa2f7", "#bb9af7", "#f7768e", "#9d7cd8", "#7dcfff", "#e0af68")
LABELS = {
    "pt-BR": {
        "activity": "Estatísticas do GitHub", "total": "Total de contribuições", "year": "Em {year}",
        "private": "Privadas anônimas", "commits": "Commits visíveis", "stars": "Estrelas",
        "prs": "PRs", "issues": "Issues", "visits": "Visitas", "since": "desde {year}",
        "scope": "Calendário: atividade pública + privada anônima",
        "languages": "Linguagens mais usadas", "lang_sub": "Código de repositórios públicos próprios",
        "lang_note": "Proporção de bytes de código · não mede experiência",
        "other": "Outras", "no_languages": "Nenhuma linguagem encontrada.",
        "rhythm": "Ritmo de contribuições", "current": "Sequência atual", "best": "Maior sequência",
        "days": "dias", "last_days": "Últimos 35 dias", "rhythm_note": "Dados do calendário do GitHub",
    },
    "en": {
        "activity": "GitHub statistics", "total": "All contributions", "year": "In {year}",
        "private": "Anonymous private", "commits": "Visible commits", "stars": "Stars",
        "prs": "PRs", "issues": "Issues", "visits": "Views", "since": "since {year}",
        "scope": "Calendar: public + anonymous private activity",
        "languages": "Most used languages", "lang_sub": "Code in owned public repositories",
        "lang_note": "Share of code bytes · not a measure of skill",
        "other": "Other", "no_languages": "No languages found.",
        "rhythm": "Contribution rhythm", "current": "Current streak", "best": "Longest streak",
        "days": "days", "last_days": "Last 35 days", "rhythm_note": "GitHub contribution calendar data",
    },
    "es": {
        "activity": "Estadísticas de GitHub", "total": "Contribuciones totales", "year": "En {year}",
        "private": "Privadas anónimas", "commits": "Commits visibles", "stars": "Estrellas",
        "prs": "PRs", "issues": "Incidencias", "visits": "Visitas", "since": "desde {year}",
        "scope": "Calendario: actividad pública + privada anónima",
        "languages": "Lenguajes más usados", "lang_sub": "Código de repositorios públicos propios",
        "lang_note": "Proporción de bytes · no mide experiencia",
        "other": "Otros", "no_languages": "No se encontraron lenguajes.",
        "rhythm": "Ritmo de contribuciones", "current": "Racha actual", "best": "Racha más larga",
        "days": "días", "last_days": "Últimos 35 días", "rhythm_note": "Datos del calendario de GitHub",
    },
}

PROFILE_QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    name
    contributionsCollection { contributionYears }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, privacy: PUBLIC) {
      nodes {
        name stargazerCount isFork isArchived
        languages(first: 100) { edges { size node { name color } } }
      }
      pageInfo { hasNextPage endCursor }
    }
    pullRequests(first: 1) { totalCount }
    issues(first: 1) { totalCount }
  }
}
"""

YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class Language:
    name: str
    color: str
    size: int


@dataclass(frozen=True)
class Stats:
    username: str
    name: str
    first_year: int
    year: int
    contributions_all: int
    contributions_year: int
    commits_all: int
    commits_year: int
    restricted_all: int
    restricted_year: int
    stars: int
    prs: int
    issues: int
    visits: int | None
    languages: tuple[Language, ...]
    current_streak: int
    longest_streak: int
    recent_days: tuple[int, ...]


def graphql(token: str, query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "User-Agent": "github-profile-card"},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(f"GitHub GraphQL: {result['errors']}")
    user = result.get("data", {}).get("user")
    if not user:
        raise RuntimeError("User not found in GitHub GraphQL response")
    return user


def year_bounds(year: int, now: datetime) -> tuple[str, str]:
    # GitHub contribution dates are in UTC, even when the account lives elsewhere.
    start = datetime.combine(date(year, 1, 1), time.min, timezone.utc)
    end = min(datetime.combine(date(year + 1, 1, 1), time.min, timezone.utc) - timedelta(seconds=1),
              now.astimezone(timezone.utc))
    return (start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds"))


def streak_lengths(days: dict[date, int], today: date) -> tuple[int, int]:
    if not days:
        return 0, 0
    ordered = sorted(day for day in days if day <= today)
    best = running = 0
    previous = None
    for day in ordered:
        if days[day] > 0:
            running = running + 1 if previous == day - timedelta(days=1) else 1
            best = max(best, running)
            previous = day
        else:
            running = 0
            previous = None
    cursor = today if days.get(today, 0) else today - timedelta(days=1)
    current = 0
    while days.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    return current, best


def collect_stats(token: str, config: dict, now: datetime, visits: int | None) -> Stats:
    username = config["username"]
    today = now.astimezone(timezone.utc).date()
    first = graphql(token, PROFILE_QUERY, {"login": username, "cursor": None})
    repos = first["repositories"]
    nodes = list(repos["nodes"])
    while repos["pageInfo"]["hasNextPage"]:
        cursor = repos["pageInfo"]["endCursor"]
        if not cursor:
            raise RuntimeError("GitHub repositories pagination has no cursor")
        repos = graphql(token, PROFILE_QUERY, {"login": username, "cursor": cursor})["repositories"]
        nodes.extend(repos["nodes"])

    excluded = set(config.get("exclude_repositories", []))
    sizes = Counter()
    colors = {}
    for repo in nodes:
        if repo["name"] in excluded or repo["isFork"] or repo["isArchived"]:
            continue
        for edge in repo["languages"]["edges"]:
            language = edge["node"]["name"]
            sizes[language] += edge["size"]
            colors[language] = edge["node"]["color"]
    languages = tuple(
        Language(name, colors.get(name) or "", size)
        for name, size in sorted(sizes.items(), key=lambda entry: (-entry[1], entry[0]))
        if size > 0
    )

    years = sorted(set(first["contributionsCollection"]["contributionYears"]) | {today.year})
    if any(year < 2008 or year > today.year for year in years):
        raise RuntimeError(f"Unexpected contribution years: {years}")
    yearly: dict[int, dict] = {}
    daily: dict[date, int] = {}
    for year in years:
        start, end = year_bounds(year, now)
        collection = graphql(token, YEAR_QUERY, {"login": username, "from": start, "to": end})[
            "contributionsCollection"
        ]
        yearly[year] = collection
        for week in collection["contributionCalendar"]["weeks"]:
            for entry in week["contributionDays"]:
                day = date.fromisoformat(entry["date"])
                if day.year == year and day <= today:
                    daily[day] = entry["contributionCount"]

    current, longest = streak_lengths(daily, today)
    last_35 = tuple(daily.get(today - timedelta(days=offset), 0) for offset in range(34, -1, -1))
    return Stats(
        username=username,
        name=config.get("display_name") or first["name"] or username,
        first_year=min(years), year=today.year,
        contributions_all=sum(item["contributionCalendar"]["totalContributions"] for item in yearly.values()),
        contributions_year=yearly[today.year]["contributionCalendar"]["totalContributions"],
        commits_all=sum(item["totalCommitContributions"] for item in yearly.values()),
        commits_year=yearly[today.year]["totalCommitContributions"],
        restricted_all=sum(item["restrictedContributionsCount"] for item in yearly.values()),
        restricted_year=yearly[today.year]["restrictedContributionsCount"],
        stars=sum(repo["stargazerCount"] for repo in nodes),
        prs=first["pullRequests"]["totalCount"], issues=first["issues"]["totalCount"],
        visits=visits, languages=languages,
        current_streak=current, longest_streak=longest, recent_days=last_35,
    )


def parse_visit_badge(svg: bytes) -> int:
    root = ET.fromstring(svg)
    texts = [node.text.strip() for node in root.iter()
             if node.tag.rsplit("}", 1)[-1] == "text" and node.text]
    numbers = [value for value in texts if re.fullmatch(r"\d{1,3}(?:,\d{3})+|\d+", value)]
    if not numbers:
        raise ValueError("No numeric visit count in SVG")
    return int(numbers[-1].replace(",", ""))


def visits_count(username: str, previous: int | None, refresh: bool) -> int | None:
    if not refresh:
        return previous
    url = "https://komarev.com/ghpvc/?" + urllib.parse.urlencode({"username": username, "style": "flat-square"})
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "github-profile-card"})
        with urllib.request.urlopen(request, timeout=15) as response:
            return parse_visit_badge(response.read())
    except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError) as exc:
        print(f"Visitor badge unavailable ({exc.__class__.__name__}); preserving previous count")
        return previous


def fmt(value: int | None, locale: str) -> str:
    if value is None:
        return "—"
    return f"{value:,}".replace(",", ".") if locale == "pt-BR" else f"{value:,}"


def svg_shell(title: str, description: str, content: str, width: int, height: int,
              extra: str = "") -> str:
    """Compact cards inspired by the familiar dark palette, with our own layout and SVG."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"{extra}>
<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(description)}</desc>
<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="11" fill="#1a1b28" stroke="#34364c"/>
<rect x="22" y="16" width="24" height="3" rx="1.5" fill="#7aa2f7"/>
<rect x="50" y="16" width="11" height="3" rx="1.5" fill="#bb9af7"/>
<path d="M22 60H{width-22}" stroke="#34364c"/>
<g font-family="DejaVu Sans, Segoe UI, Arial, sans-serif">{content}</g>
</svg>
'''


def render_stats(stats: Stats, locale: str) -> str:
    labels = LABELS[locale]
    body = f'''
<text x="22" y="45" fill="#7aa2f7" font-size="20" font-weight="700">{labels['activity']}</text>
<text x="22" y="113" fill="#e3e6f2" font-size="40" font-weight="700">{fmt(stats.contributions_all, locale)}</text>
<text x="22" y="136" fill="#9ecec5" font-size="14">{labels['total']}</text>
<text x="22" y="154" fill="#8994ad" font-size="12">{labels['since'].format(year=stats.first_year)}</text>
<path d="M208 78V157" stroke="#34364c"/>
<text x="230" y="113" fill="#7aa2f7" font-size="37" font-weight="700">{fmt(stats.contributions_year, locale)}</text>
<text x="230" y="138" fill="#9ecec5" font-size="14">{labels['year'].format(year=stats.year)}</text>
<path d="M22 170H398" stroke="#34364c"/>
<text x="22" y="196" fill="#9ecec5" font-size="14">{labels['private']}</text>
<text x="22" y="225" fill="#bb9af7" font-size="26" font-weight="700">{fmt(stats.restricted_all, locale)}</text>
<text x="230" y="196" fill="#9ecec5" font-size="14">{labels['commits']}</text>
<text x="230" y="225" fill="#bb9af7" font-size="26" font-weight="700">{fmt(stats.commits_all, locale)}</text>
<path d="M22 240H398" stroke="#34364c"/>
<text x="22" y="273" fill="#e3e6f2" font-size="23" font-weight="700">{fmt(stats.stars, locale)}</text>
<text x="22" y="291" fill="#9ecec5" font-size="12">{labels['stars']}</text>
<text x="130" y="273" fill="#e3e6f2" font-size="23" font-weight="700">{fmt(stats.prs, locale)}</text>
<text x="130" y="291" fill="#9ecec5" font-size="12">{labels['prs']}</text>
<text x="216" y="273" fill="#e3e6f2" font-size="23" font-weight="700">{fmt(stats.issues, locale)}</text>
<text x="216" y="291" fill="#9ecec5" font-size="12">{labels['issues']}</text>
<text id="visits-value" x="310" y="273" fill="#e3e6f2" font-size="23" font-weight="700">{fmt(stats.visits, locale)}</text>
<text x="310" y="291" fill="#9ecec5" font-size="12">{labels['visits']}</text>
<text x="22" y="326" fill="#8994ad" font-size="11">{labels['scope']}</text>'''
    return svg_shell(f"{stats.name} · {labels['activity']}", labels["scope"], body,
                     420, 344, f' data-visits="{stats.visits if stats.visits is not None else ""}"')


def language_rows(stats: Stats, locale: str) -> tuple[list[tuple[str, str, float]], int]:
    total = sum(language.size for language in stats.languages)
    top = list(stats.languages[:5])
    rows = [(item.name, item.color if re.fullmatch(r"#[0-9a-fA-F]{6}", item.color) else PALETTE[i],
             item.size / total) for i, item in enumerate(top)] if total else []
    remaining = total - sum(item.size for item in top)
    if remaining:
        rows.append((LABELS[locale]["other"], PALETTE[5], remaining / total))
    return rows, total


def render_languages(stats: Stats, locale: str) -> str:
    labels = LABELS[locale]
    rows, total = language_rows(stats, locale)
    body = f'''
<text x="22" y="45" fill="#7aa2f7" font-size="20" font-weight="700">{labels['languages']}</text>
<text x="22" y="82" fill="#9ecec5" font-size="13">{labels['lang_sub']}</text>
<defs><clipPath id="bar"><rect x="22" y="98" width="376" height="14" rx="7"/></clipPath></defs>
<rect x="22" y="98" width="376" height="14" rx="7" fill="#34364c"/>
<g clip-path="url(#bar)">'''
    if total:
        offset = 22.0
        for _, color, fraction in rows:
            width = 376 * fraction
            body += f'<rect x="{offset:.2f}" y="98" width="{width:.2f}" height="14" fill="{color}"/>'
            offset += width
        body += '</g>'
        for index, (name, color, fraction) in enumerate(rows):
            column, row = divmod(index, 3)
            x = 22 + column * 206
            y = 157 + row * 49
            short_name = name if len(name) <= 13 else name[:12] + "…"
            body += (f'<circle cx="{x+5}" cy="{y-5}" r="5" fill="{color}"/>'
                     f'<text x="{x+18}" y="{y}" fill="#e3e6f2" font-size="14">{html.escape(short_name)}</text>'
                     f'<text x="{x+184}" y="{y}" text-anchor="end" fill="#9ecec5" font-size="13">{fraction * 100:.1f}%</text>')
    else:
        body += f'</g><text x="22" y="173" fill="#e3e6f2" font-size="15">{labels["no_languages"]}</text>'
    body += f'<path d="M22 302H398" stroke="#34364c"/><text x="22" y="326" fill="#8994ad" font-size="11">{labels["lang_note"]}</text>'
    return svg_shell(f"{stats.name} · {labels['languages']}", labels["lang_note"], body, 420, 344)


def recent_bars(stats: Stats, x: float, bottom: int, width: float, height: int) -> str:
    maximum = max(stats.recent_days, default=0)
    parts = []
    slot = width / len(stats.recent_days) if stats.recent_days else width
    for index, value in enumerate(stats.recent_days):
        size = max(3, round(height * value / maximum)) if maximum else 3
        parts.append(f'<rect x="{x + index * slot:.1f}" y="{bottom-size}" width="{slot*.55:.1f}" height="{size}" rx="1.5" fill="{"#7aa2f7" if value else "#34364c"}"/>')
    return "".join(parts)


def render_rhythm(stats: Stats, locale: str, mobile: bool = False) -> str:
    labels = LABELS[locale]
    header = f'<text x="22" y="45" fill="#7aa2f7" font-size="20" font-weight="700">{labels["rhythm"]}</text>'
    if mobile:
        body = f'''
{header}
<text x="22" y="101" fill="#7aa2f7" font-size="32" font-weight="700">{fmt(stats.contributions_all, locale)}</text>
<text x="138" y="88" fill="#9ecec5" font-size="14">{labels['total']}</text>
<text x="138" y="105" fill="#8994ad" font-size="12">{labels['since'].format(year=stats.first_year)}</text>
<path d="M22 119H398" stroke="#34364c"/>
<text x="22" y="158" fill="#bb9af7" font-size="32" font-weight="700">{stats.current_streak}</text>
<text x="138" y="151" fill="#9ecec5" font-size="14">{labels['current']} · {labels['days']}</text>
<path d="M22 170H398" stroke="#34364c"/>
<text x="22" y="207" fill="#7aa2f7" font-size="32" font-weight="700">{stats.longest_streak}</text>
<text x="138" y="201" fill="#9ecec5" font-size="14">{labels['best']} · {labels['days']}</text>
{recent_bars(stats, 22, 242, 376, 23)}'''
        return svg_shell(f"{stats.name} · {labels['rhythm']}", labels["rhythm_note"], body, 420, 255)
    body = f'''
{header}
<path d="M280 75V157M560 75V157" stroke="#34364c"/>
<text x="140" y="113" text-anchor="middle" fill="#7aa2f7" font-size="45" font-weight="700">{fmt(stats.contributions_all, locale)}</text>
<text x="140" y="138" text-anchor="middle" fill="#9ecec5" font-size="15">{labels['total']}</text>
<text x="140" y="157" text-anchor="middle" fill="#8994ad" font-size="12">{labels['since'].format(year=stats.first_year)}</text>
<text x="420" y="113" text-anchor="middle" fill="#bb9af7" font-size="45" font-weight="700">{stats.current_streak}</text>
<text x="420" y="138" text-anchor="middle" fill="#9ecec5" font-size="15">{labels['current']} · {labels['days']}</text>
<text x="700" y="113" text-anchor="middle" fill="#7aa2f7" font-size="45" font-weight="700">{stats.longest_streak}</text>
<text x="700" y="138" text-anchor="middle" fill="#9ecec5" font-size="15">{labels['best']} · {labels['days']}</text>
<text x="22" y="189" fill="#8994ad" font-size="12">{labels['last_days']}</text>
{recent_bars(stats, 197, 198, 620, 22)}'''
    return svg_shell(f"{stats.name} · {labels['rhythm']}", labels["rhythm_note"], body, 840, 212)


def output_name(kind: str, locale: str) -> str:
    suffix = {"pt-BR": "", "en": "-en", "es": "-es"}[locale]
    return f"{kind}{suffix}.svg"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("profile-card.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("profile"))
    parser.add_argument("--refresh-visits", action="store_true", help="Read visitor badge once (increments it)")
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required; GitHub Actions supplies a repository-scoped token")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if not re.fullmatch(r"[a-zA-Z0-9-]{1,39}", config["username"]):
        raise SystemExit("Invalid GitHub username")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    previous_path = args.output_dir / "data.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
    visits = visits_count(config.get("visits_username", config["username"]), previous.get("visits"), args.refresh_visits)
    now = datetime.now(timezone.utc)
    stats = collect_stats(token, config, now, visits)
    for locale in SUPPORTED_LOCALES:
        for kind, renderer in (("stats", render_stats), ("languages", render_languages), ("rhythm", render_rhythm)):
            (args.output_dir / output_name(kind, locale)).write_text(renderer(stats, locale), encoding="utf-8")
        (args.output_dir / output_name("rhythm-mobile", locale)).write_text(
            render_rhythm(stats, locale, mobile=True), encoding="utf-8"
        )
    data = json.loads(json.dumps(asdict(stats)))
    previous.pop("generated_at", None)
    data["generated_at"] = now.isoformat(timespec="seconds")
    # Keep the snapshot stable when the actual metrics have not changed.
    if previous == data:
        data["generated_at"] = json.loads(previous_path.read_text(encoding="utf-8"))["generated_at"]
    previous_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{stats.username}: {stats.contributions_all} calendar contributions, "
          f"{stats.commits_all} public commit contributions, {stats.contributions_year} in {stats.year}")


if __name__ == "__main__":
    main()
