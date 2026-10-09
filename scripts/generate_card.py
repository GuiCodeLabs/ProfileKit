#!/usr/bin/env python3
"""Collect GitHub activity and render original, dependency-free SVG cards."""

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
        "activity": "Status do GitHub", "total": "Contribuições · todo o período",
        "year": "Contribuições · {year}",
        "commits_year": "Commits · {year}", "commits_year_public": "Commits visíveis · {year}",
        "repositories_year": "Repositórios · {year}", "repositories_year_public": "Repositórios públicos · {year}",
        "stars": "Estrelas", "prs": "Pull requests", "issues": "Issues", "visits": "Visitas do perfil",
        "since": "desde {year}",
        "languages": "Linguagens mais usadas", "lang_sub_public": "Código de repositórios públicos próprios",
        "lang_sub_private": "Código público + privado acessível",
        "other": "Outras", "no_languages": "Nenhuma linguagem encontrada.",
        "rhythm": "Ritmo de contribuições", "current": "Sequência atual", "best": "Maior sequência",
        "days": "dias", "last_days": "Últimos 35 dias · atividade diária",
        "oldest": "35 dias atrás", "today": "hoje",
        "rhythm_note": "Dados do calendário do GitHub",
    },
    "en": {
        "activity": "GitHub statistics", "total": "Contributions · all time",
        "year": "Contributions · {year}",
        "commits_year": "Commits · {year}", "commits_year_public": "Visible commits · {year}",
        "repositories_year": "Repositories · {year}", "repositories_year_public": "Public repositories · {year}",
        "stars": "Stars", "prs": "Pull requests", "issues": "Issues", "visits": "Profile views",
        "since": "since {year}",
        "languages": "Most used languages", "lang_sub_public": "Code in owned public repositories",
        "lang_sub_private": "Code in accessible public + private repositories",
        "other": "Other", "no_languages": "No languages found.",
        "rhythm": "Contribution rhythm", "current": "Current streak", "best": "Longest streak",
        "days": "days", "last_days": "Last 35 days · daily activity",
        "oldest": "35 days ago", "today": "today",
        "rhythm_note": "GitHub contribution calendar data",
    },
    "es": {
        "activity": "Estadísticas de GitHub", "total": "Contribuciones · todo el período",
        "year": "Contribuciones · {year}",
        "commits_year": "Commits · {year}", "commits_year_public": "Commits visibles · {year}",
        "repositories_year": "Repositorios · {year}", "repositories_year_public": "Repositorios públicos · {year}",
        "stars": "Estrellas", "prs": "Pull requests", "issues": "Incidencias", "visits": "Visitas del perfil",
        "since": "desde {year}",
        "languages": "Lenguajes más usados", "lang_sub_public": "Código de repositorios públicos propios",
        "lang_sub_private": "Código público + privado accesible",
        "other": "Otros", "no_languages": "No se encontraron lenguajes.",
        "rhythm": "Ritmo de contribuciones", "current": "Racha actual", "best": "Racha más larga",
        "days": "días", "last_days": "Últimos 35 días · actividad diaria",
        "oldest": "hace 35 días", "today": "hoy",
        "rhythm_note": "Datos del calendario de GitHub",
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

PRIVATE_REPOSITORIES_QUERY = """
query($cursor: String) {
  viewer {
    repositories(first: 100, after: $cursor, privacy: PRIVATE) {
      nodes {
        name isFork isArchived
        languages(first: 100) { edges { size node { name color } } }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""

YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalRepositoriesWithContributedCommits
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
    stars: int
    prs: int
    issues: int
    visits: int | None
    languages: tuple[Language, ...]
    current_streak: int
    longest_streak: int
    recent_days: tuple[int, ...]
    languages_include_private: bool = False
    repositories_year: int = 0
    contributions_include_private: bool = False


def graphql(token: str, query: str, variables: dict, root_field: str = "user") -> dict:
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
    owner = result.get("data", {}).get(root_field)
    if not owner:
        raise RuntimeError(f"{root_field} not found in GitHub GraphQL response")
    return owner


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


def repository_nodes(token: str, query: str, username: str,
                     connection: dict | None = None, root_field: str = "user") -> list[dict]:
    if connection is None:
        variables = {"login": username, "cursor": None} if "$login" in query else {"cursor": None}
        connection = graphql(token, query, variables, root_field=root_field)["repositories"]
    nodes = list(connection["nodes"])
    while connection["pageInfo"]["hasNextPage"]:
        cursor = connection["pageInfo"]["endCursor"]
        if not cursor:
            raise RuntimeError("GitHub repositories pagination has no cursor")
        variables = {"login": username, "cursor": cursor} if "$login" in query else {"cursor": cursor}
        connection = graphql(token, query, variables, root_field=root_field)["repositories"]
        nodes.extend(connection["nodes"])
    return nodes


def collect_stats(token: str, config: dict, now: datetime, visits: int | None,
                  private_repositories_token: str | None = None,
                  private_contributions_token: str | None = None) -> Stats:
    username = config["username"]
    today = now.astimezone(timezone.utc).date()

    def collect_activity(activity_token: str) -> tuple[dict, dict[int, dict], dict[date, int]]:
        first = graphql(activity_token, PROFILE_QUERY, {"login": username, "cursor": None})
        years = sorted(set(first["contributionsCollection"]["contributionYears"]) | {today.year})
        if any(year < 2008 or year > today.year for year in years):
            raise RuntimeError(f"Unexpected contribution years: {years}")
        yearly: dict[int, dict] = {}
        daily: dict[date, int] = {}
        for year in years:
            start, end = year_bounds(year, now)
            collection = graphql(activity_token, YEAR_QUERY, {"login": username, "from": start, "to": end})[
                "contributionsCollection"
            ]
            yearly[year] = collection
            for week in collection["contributionCalendar"]["weeks"]:
                for entry in week["contributionDays"]:
                    day = date.fromisoformat(entry["date"])
                    if day.year == year and day <= today:
                        daily[day] = entry["contributionCount"]
        return first, yearly, daily

    activity_token = private_contributions_token or token
    try:
        first, yearly, daily = collect_activity(activity_token)
    except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        if not private_contributions_token:
            raise
        print(f"Private contribution token unavailable ({exc.__class__.__name__}); using public scope")
        activity_token = token
        first, yearly, daily = collect_activity(token)

    nodes = repository_nodes(token, PROFILE_QUERY, username, first["repositories"])
    language_repositories = list(nodes)
    languages_include_private = False
    if private_repositories_token:
        try:
            language_repositories.extend(repository_nodes(
                private_repositories_token, PRIVATE_REPOSITORIES_QUERY, username, root_field="viewer"
            ))
            languages_include_private = True
        except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
            print(f"Private repository token unavailable ({exc.__class__.__name__}); using public languages")

    excluded = set(config.get("exclude_repositories", []))
    sizes = Counter()
    colors = {}
    for repo in language_repositories:
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

    current, longest = streak_lengths(daily, today)
    last_35 = tuple(daily.get(today - timedelta(days=offset), 0) for offset in range(34, -1, -1))
    return Stats(
        username=username,
        name=config.get("display_name") or first["name"] or username,
        first_year=min(yearly), year=today.year,
        contributions_all=sum(item["contributionCalendar"]["totalContributions"] for item in yearly.values()),
        contributions_year=yearly[today.year]["contributionCalendar"]["totalContributions"],
        commits_all=sum(item["totalCommitContributions"] for item in yearly.values()),
        commits_year=yearly[today.year]["totalCommitContributions"],
        stars=sum(repo["stargazerCount"] for repo in nodes),
        prs=first["pullRequests"]["totalCount"], issues=first["issues"]["totalCount"],
        visits=visits, languages=languages,
        current_streak=current, longest_streak=longest, recent_days=last_35,
        languages_include_private=languages_include_private,
        repositories_year=yearly[today.year]["totalRepositoriesWithContributedCommits"],
        contributions_include_private=activity_token != token,
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
        request = urllib.request.Request(url, headers={
            "User-Agent": "github-profile-card",
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
        })
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
    """Render an original, compact card with a familiar dark statistics-card palette."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"{extra}>
<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(description)}</desc>
<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="11" fill="#1a1b28" stroke="#34364c"/>
<rect x="22" y="16" width="24" height="3" rx="1.5" fill="#7aa2f7"/>
<rect x="50" y="16" width="11" height="3" rx="1.5" fill="#bb9af7"/>
<path d="M22 60H{width-22}" stroke="#34364c"/>
<g font-family="DejaVu Sans, Segoe UI, Arial, sans-serif">{content}</g>
</svg>
'''


ICON_PATHS = {
    "star": '<path d="m12 2.3 2.9 6 6.6.8-4.8 4.6 1.2 6.6-5.9-3.2-5.9 3.2 1.2-6.6-4.8-4.6 6.6-.8 2.9-6Z"/>',
    "commit": '<circle cx="12" cy="5" r="2.6"/><circle cx="12" cy="19" r="2.6"/><path d="M12 7.6v8.8"/>',
    "pull": '<circle cx="7" cy="5" r="2.5"/><circle cx="17" cy="19" r="2.5"/><circle cx="17" cy="5" r="2.5"/><path d="M7 7.5v9m10-9v9m-7-7 4 4"/>',
    "repository": '<path d="M4 3h16v18H4zM8 7h8M8 11h8M8 15h5"/>',
    "issue": '<path d="m12 2 10 10-10 10L2 12 12 2Z"/><path d="M12 7v6m0 4v.01"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16"/><path d="M7 2v6m10-6v6M3 10h18m-13 4h2m4 0h2m-8 4h2"/>',
    "lock": '<path d="M4 10h16v11H4zM8 10V7a4 4 0 0 1 8 0v3m-4 4v3"/>',
    "eye": '<path d="m2 12 5-6h10l5 6-5 6H7l-5-6Z"/><path d="m12 9 3 3-3 3-3-3 3-3Z"/>',
    "code": '<path d="m8 6-6 6 6 6m8-12 6 6-6 6m-2-14-4 16"/>',
    "flame": '<path d="m12 2 4 7-2 2 5 4-3 7H8l-4-6 4-5 1 4 3-5-2-3 2-5Z"/><path d="m12 14 3 3-2 3H9l-1-3 3-3 1 2 1-2Z"/>',
}


def svg_icon(name: str, x: int, y: int, color: str, size: int = 18) -> str:
    """Draw a small original line icon from simple SVG primitives."""
    if name not in ICON_PATHS:
        raise ValueError(f"Unknown icon: {name}")
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="square" '
            f'stroke-linejoin="miter" aria-hidden="true">{ICON_PATHS[name]}</svg>')


def render_stats(stats: Stats, locale: str) -> str:
    labels = LABELS[locale]
    rows = (
        ("star", labels["stars"], stats.stars, "#e0af68"),
        ("commit", labels["commits_year" if stats.contributions_include_private else "commits_year_public"].format(year=stats.year), stats.commits_year, "#bb9af7"),
        ("repository", labels["repositories_year" if stats.contributions_include_private else "repositories_year_public"].format(year=stats.year), stats.repositories_year, "#bb9af7"),
        ("pull", labels["prs"], stats.prs, "#bb9af7"),
        ("issue", labels["issues"], stats.issues, "#f7768e"),
        ("calendar", labels["year"].format(year=stats.year), stats.contributions_year, "#7aa2f7"),
        ("eye", labels["visits"], stats.visits, "#7dcfff"),
    )
    body = (f'{svg_icon("calendar", 22, 27, "#7aa2f7", 18)}'
            f'<text x="50" y="43" fill="#7aa2f7" font-size="19" font-weight="700">{labels["activity"]}</text>')
    body += f'<path d="M22 57H398" stroke="#34364c"/>'
    for index, (icon, label, value, color) in enumerate(rows):
        baseline = 82 + index * 28
        body += svg_icon(icon, 22, baseline - 15, color, 18)
        value_id = ' id="visits-value"' if icon == "eye" else ""
        body += (f'<text x="51" y="{baseline}" fill="#9ecec5" font-size="15">{html.escape(label)}</text>'
                 f'<text{value_id} x="398" y="{baseline}" text-anchor="end" '
                 f'fill="#7dcfff" font-size="18" font-weight="700">{fmt(value, locale)}</text>')
    description = f"{stats.name} · {labels['year'].format(year=stats.year)}"
    return svg_shell(f"{stats.name} · {labels['activity']}", description, body,
                     420, 290, f' data-visits="{stats.visits if stats.visits is not None else ""}"')


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
    language_scope = labels["lang_sub_private"] if stats.languages_include_private else labels["lang_sub_public"]
    body = f'''
{svg_icon("code", 22, 27, "#7aa2f7", 18)}
<text x="50" y="45" fill="#7aa2f7" font-size="20" font-weight="700">{labels['languages']}</text>
<text x="22" y="82" fill="#9ecec5" font-size="13">{language_scope}</text>
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
            row, column = divmod(index, 2)
            x = 22 + column * 186
            y = 157 + row * 49
            short_name = name if len(name) <= 13 else name[:12] + "…"
            body += (f'<circle cx="{x+5}" cy="{y-5}" r="5" fill="{color}"/>'
                     f'<text x="{x+18}" y="{y}" fill="#e3e6f2" font-size="14">{html.escape(short_name)}</text>'
                     f'<text x="{x+178}" y="{y}" text-anchor="end" fill="#9ecec5" font-size="13">{fraction * 100:.1f}%</text>')
    else:
        body += f'</g><text x="22" y="173" fill="#e3e6f2" font-size="15">{labels["no_languages"]}</text>'
    return svg_shell(f"{stats.name} · {labels['languages']}", language_scope, body, 420, 290)


def recent_bars(stats: Stats, x: float, bottom: int, width: float, height: int) -> str:
    maximum = max(stats.recent_days, default=0)
    parts = []
    slot = width / len(stats.recent_days) if stats.recent_days else width
    for index, value in enumerate(stats.recent_days):
        if value and maximum:
            size = max(5, round(height * (value / maximum) ** 0.5))
            color = ("#7aa2f7" if value >= 40 else "#6687ce" if value >= 15
                     else "#5775b4" if value >= 5 else "#465570")
        else:
            size, color = 3, "#34364c"
        parts.append(f'<rect x="{x + index * slot:.1f}" y="{bottom-size}" width="{slot*.58:.1f}" height="{size}" fill="{color}"/>')
    return "".join(parts)


def render_rhythm(stats: Stats, locale: str, mobile: bool = False) -> str:
    labels = LABELS[locale]
    header = (f'{svg_icon("flame", 22, 27, "#bb9af7", 18)}'
              f'<text x="50" y="45" fill="#7aa2f7" font-size="20" font-weight="700">{labels["rhythm"]}</text>')
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
<text x="22" y="232" fill="#8994ad" font-size="12">{labels['last_days']}</text>
<path d="M22 247H398" stroke="#34364c"/>
{recent_bars(stats, 22, 264, 376, 20)}'''
        return svg_shell(f"{stats.name} · {labels['rhythm']}", labels["rhythm_note"], body, 420, 270)
    body = f'''
{header}
<path d="M280 75V166M560 75V166" stroke="#34364c"/>
<text x="140" y="113" text-anchor="middle" fill="#7aa2f7" font-size="45" font-weight="700">{fmt(stats.contributions_all, locale)}</text>
<text x="140" y="138" text-anchor="middle" fill="#9ecec5" font-size="15">{labels['total']}</text>
<text x="140" y="157" text-anchor="middle" fill="#8994ad" font-size="12">{labels['since'].format(year=stats.first_year)}</text>
<text x="420" y="113" text-anchor="middle" fill="#bb9af7" font-size="45" font-weight="700">{stats.current_streak}</text>
<text x="420" y="138" text-anchor="middle" fill="#9ecec5" font-size="15">{labels['current']} · {labels['days']}</text>
<text x="700" y="113" text-anchor="middle" fill="#7aa2f7" font-size="45" font-weight="700">{stats.longest_streak}</text>
<text x="700" y="138" text-anchor="middle" fill="#9ecec5" font-size="15">{labels['best']} · {labels['days']}</text>
<text x="22" y="190" fill="#8994ad" font-size="12">{labels['last_days']}</text>
<path d="M197 237H817" stroke="#34364c"/>
{recent_bars(stats, 197, 237, 620, 38)}
<text x="197" y="252" fill="#8994ad" font-size="11">{labels['oldest']}</text>
<text x="817" y="252" text-anchor="end" fill="#8994ad" font-size="11">{labels['today']}</text>'''
    return svg_shell(f"{stats.name} · {labels['rhythm']}", labels["rhythm_note"], body, 840, 256)


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
    private_repositories_token = os.environ.get("PRIVATE_REPOSITORIES_TOKEN") or None
    private_contributions_token = os.environ.get("PRIVATE_CONTRIBUTIONS_TOKEN") or None
    stats = collect_stats(token, config, now, visits, private_repositories_token,
                          private_contributions_token)
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
          f"{stats.commits_all} commit contributions, {stats.repositories_year} repositories with commits "
          f"in {stats.year}")


if __name__ == "__main__":
    main()

