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
from zoneinfo import ZoneInfo


GRAPHQL_URL = "https://api.github.com/graphql"
SUPPORTED_LOCALES = ("pt-BR", "en", "es")
PALETTE = ("#56e4c5", "#8ba6ff", "#ffca84", "#dc9bff", "#82c8e8", "#fa91ac")
LABELS = {
    "pt-BR": {
        "activity": "ATIVIDADE NO GITHUB", "since": "contribuições desde {year}",
        "year": "em {year}", "commits": "COMMITS PÚBLICOS", "all": "todo o período",
        "stars": "estrelas", "prs": "PRs", "issues": "issues", "visits": "visitas ao perfil",
        "private": "Calendário inclui contribuições privadas anônimas.",
        "public": "Calendário: commits, PRs e outras contribuições.",
        "languages": "Código em foco", "lang_sub": "Repositórios públicos próprios, sem forks nem arquivados",
        "lang_note": "Percentual de bytes de código, não de experiência com a linguagem.",
        "other": "Outras", "no_languages": "Nenhuma linguagem encontrada nos repositórios selecionados.",
        "rhythm": "Ritmo de contribuição", "current": "sequência atual", "best": "maior sequência",
        "days": "dias", "last_days": "Últimos 35 dias", "rhythm_note": "Atividade do calendário do GitHub",
    },
    "en": {
        "activity": "GITHUB ACTIVITY", "since": "contributions since {year}",
        "year": "in {year}", "commits": "PUBLIC COMMITS", "all": "all time",
        "stars": "stars", "prs": "PRs", "issues": "issues", "visits": "profile views",
        "private": "Calendar includes shared anonymous private activity.",
        "public": "Calendar: commits, PRs and other GitHub contributions.",
        "languages": "Code in focus", "lang_sub": "Owned public repositories, excluding forks and archives",
        "lang_note": "Share of code bytes, not proficiency in a language.",
        "other": "Other", "no_languages": "No languages found in the selected repositories.",
        "rhythm": "Contribution rhythm", "current": "current streak", "best": "longest streak",
        "days": "days", "last_days": "Last 35 days", "rhythm_note": "Activity from the GitHub contribution calendar",
    },
    "es": {
        "activity": "ACTIVIDAD EN GITHUB", "since": "contribuciones desde {year}",
        "year": "en {year}", "commits": "COMMITS PÚBLICOS", "all": "todo el período",
        "stars": "estrellas", "prs": "PRs", "issues": "incidencias", "visits": "visitas al perfil",
        "private": "El calendario incluye actividad privada anónima.",
        "public": "Calendario: commits, PRs y otras contribuciones de GitHub.",
        "languages": "Código destacado", "lang_sub": "Repositorios públicos propios, sin forks ni archivados",
        "lang_note": "Porcentaje de bytes de código, no dominio del lenguaje.",
        "other": "Otras", "no_languages": "No se encontraron lenguajes en los repositorios seleccionados.",
        "rhythm": "Ritmo de contribución", "current": "racha actual", "best": "racha más larga",
        "days": "días", "last_days": "Últimos 35 días", "rhythm_note": "Actividad del calendario de contribuciones de GitHub",
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


def year_bounds(year: int, now: datetime, zone: ZoneInfo) -> tuple[str, str]:
    start = datetime.combine(date(year, 1, 1), time.min, zone)
    end = min(datetime.combine(date(year + 1, 1, 1), time.min, zone) - timedelta(seconds=1), now)
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
    zone = ZoneInfo(config.get("timezone", "UTC"))
    today = now.astimezone(zone).date()
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
        start, end = year_bounds(year, now, zone)
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


def svg_shell(title: str, description: str, content: str, height: int, extra: str = "") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="{height}" viewBox="0 0 480 {height}" role="img" aria-labelledby="title desc"{extra}>
<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(description)}</desc>
<defs>
  <linearGradient id="back" x2="1" y2="1"><stop stop-color="#0b2431"/><stop offset="1" stop-color="#10182c"/></linearGradient>
  <linearGradient id="glow"><stop stop-color="#56e4c5"/><stop offset="1" stop-color="#8ba6ff"/></linearGradient>
  <clipPath id="clip"><rect width="480" height="100%" rx="22"/></clipPath>
</defs>
<rect width="480" height="{height}" rx="22" fill="url(#back)"/>
<path d="M0 58H480" stroke="#294456" opacity=".7"/>
<path d="M410 -38a106 106 0 1 0 0 212a106 106 0 1 0 0-212z" fill="none" stroke="#63e6c8" stroke-opacity=".08" stroke-width="30" clip-path="url(#clip)"/>
<g font-family="DejaVu Sans, Segoe UI, Arial, sans-serif">{content}</g>
</svg>
'''


def render_stats(stats: Stats, locale: str) -> str:
    labels = LABELS[locale]
    year = stats.year
    notes = labels["private"] if stats.restricted_all else labels["public"]
    # The larger calendar number includes all contribution types; commit numbers are a subset.
    body = f'''
<rect x="24" y="23" width="8" height="22" rx="4" fill="#56e4c5"/>
<text x="44" y="41" fill="#e4f3f2" font-size="18" font-weight="700">{labels['activity']}</text>
<text x="24" y="82" fill="#93b0ba" font-size="15">{html.escape(stats.name)}</text>
<text x="24" y="145" fill="#f4faf9" font-size="55" font-weight="700">{fmt(stats.contributions_all, locale)}</text>
<text x="24" y="170" fill="#a5c4c8" font-size="16">{labels['since'].format(year=stats.first_year)}</text>
<text x="456" y="127" text-anchor="end" fill="#56e4c5" font-size="35" font-weight="700">{fmt(stats.contributions_year, locale)}</text>
<text x="456" y="153" text-anchor="end" fill="#a5c4c8" font-size="16">{labels['year'].format(year=year)}</text>
<path d="M24 194H456" stroke="#294456" opacity=".7"/>
<text x="24" y="220" fill="#92b5c1" font-size="13" font-weight="700" letter-spacing="1.3">{labels['commits']}</text>
<rect x="24" y="238" width="209" height="81" rx="13" fill="#183243"/>
<rect x="247" y="238" width="209" height="81" rx="13" fill="#183243"/>
<text x="39" y="281" fill="#f4faf9" font-size="34" font-weight="700">{fmt(stats.commits_all, locale)}</text>
<text x="39" y="306" fill="#a5c4c8" font-size="14">{labels['all']}</text>
<text x="262" y="281" fill="#f4faf9" font-size="34" font-weight="700">{fmt(stats.commits_year, locale)}</text>
<text x="262" y="306" fill="#a5c4c8" font-size="14">{year}</text>
<text x="24" y="356" fill="#ffca84" font-size="24" font-weight="700">{fmt(stats.stars, locale)}</text>
<text x="24" y="378" fill="#a5c4c8" font-size="13">{labels['stars']}</text>
<text x="184" y="356" fill="#8ba6ff" font-size="24" font-weight="700">{fmt(stats.prs, locale)}</text>
<text x="184" y="378" fill="#a5c4c8" font-size="13">{labels['prs']}</text>
<text x="344" y="356" fill="#dc9bff" font-size="24" font-weight="700">{fmt(stats.issues, locale)}</text>
<text x="344" y="378" fill="#a5c4c8" font-size="13">{labels['issues']}</text>
<rect x="24" y="398" width="432" height="49" rx="12" fill="#164c50"/>
<circle cx="45" cy="422" r="6" fill="#56e4c5"/>
<text x="62" y="428" fill="#d4eeee" font-size="17">{labels['visits']}</text>
<text id="visits-value" x="438" y="429" text-anchor="end" fill="#f4faf9" font-size="26" font-weight="700">{fmt(stats.visits, locale)}</text>
<text x="24" y="475" fill="#95acb8" font-size="11">{html.escape(notes)}</text>'''
    return svg_shell(f"{stats.name} · {labels['activity']}", notes, body, 496,
                     f' data-visits="{stats.visits if stats.visits is not None else ""}"')


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
<rect x="24" y="23" width="8" height="22" rx="4" fill="#8ba6ff"/>
<text x="44" y="41" fill="#e4f3f2" font-size="22" font-weight="700">{labels['languages']}</text>
<text x="24" y="70" fill="#a5c4c8" font-size="13">{labels['lang_sub']}</text>
<rect x="24" y="91" width="432" height="18" rx="9" fill="#2b4151"/>'''
    if total:
        offset = 24.0
        for _, color, fraction in rows:
            width = 432 * fraction
            body += f'<rect x="{offset:.2f}" y="91" width="{width:.2f}" height="18" fill="{color}"/>'
            offset += width
        for index, (name, color, fraction) in enumerate(rows):
            y = 148 + index * 35
            body += (f'<circle cx="33" cy="{y-5}" r="5" fill="{color}"/>'
                     f'<text x="48" y="{y}" fill="#e4f3f2" font-size="18">{html.escape(name)}</text>'
                     f'<text x="448" y="{y}" text-anchor="end" fill="#f4faf9" font-size="18" font-weight="700">{fraction * 100:.1f}%</text>')
    else:
        body += f'<text x="24" y="168" fill="#c1d0d5" font-size="16">{labels["no_languages"]}</text>'
    body += f'<text x="24" y="361" fill="#95acb8" font-size="12">{labels["lang_note"]}</text>'
    return svg_shell(f"{stats.name} · {labels['languages']}", labels["lang_note"], body, 382)


def render_rhythm(stats: Stats, locale: str) -> str:
    labels = LABELS[locale]
    values = stats.recent_days
    maximum = max(values, default=0)
    bars = []
    for index, value in enumerate(values):
        height = max(3, round(52 * value / maximum)) if maximum else 3
        x = 24 + index * 12.4
        bars.append(f'<rect x="{x:.1f}" y="{231-height}" width="7.5" height="{height}" rx="3" fill="{PALETTE[0] if value else "#375363"}"/>')
    body = f'''
<rect x="24" y="23" width="8" height="22" rx="4" fill="#ffca84"/>
<text x="44" y="41" fill="#e4f3f2" font-size="21" font-weight="700">{labels['rhythm']}</text>
<rect x="24" y="65" width="209" height="87" rx="13" fill="#183243"/>
<rect x="247" y="65" width="209" height="87" rx="13" fill="#183243"/>
<text x="41" y="114" fill="#56e4c5" font-size="36" font-weight="700">{stats.current_streak}</text>
<text x="41" y="139" fill="#c4d7d9" font-size="14">{labels['current']} · {labels['days']}</text>
<text x="264" y="114" fill="#ffca84" font-size="36" font-weight="700">{stats.longest_streak}</text>
<text x="264" y="139" fill="#c4d7d9" font-size="14">{labels['best']} · {labels['days']}</text>
<text x="24" y="177" fill="#a5c4c8" font-size="15">{labels['last_days']}</text>
{''.join(bars)}
<text x="24" y="260" fill="#95acb8" font-size="12">{labels['rhythm_note']}</text>'''
    return svg_shell(f"{stats.name} · {labels['rhythm']}", labels["rhythm_note"], body, 280)


def output_name(kind: str, locale: str) -> str:
    suffix = {"pt-BR": "", "en": "-en", "es": "-es"}[locale]
    return f"{kind}{suffix}.svg"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("profile-card.json"))
    parser.add_argument("--username", help="Override username in profile-card.json")
    parser.add_argument("--output-dir", type=Path, default=Path("profile"))
    parser.add_argument("--refresh-visits", action="store_true", help="Read visitor badge once (increments it)")
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required; GitHub Actions supplies a repository-scoped token")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.username:
        config["username"] = args.username
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
