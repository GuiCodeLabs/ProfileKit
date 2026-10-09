#!/usr/bin/env python3
"""Collect GitHub activity and render original, dependency-free SVG cards."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


GRAPHQL_URL = "https://api.github.com/graphql"
SUPPORTED_LOCALES = ("pt-BR", "en", "es")
PALETTE = ("#7aa2f7", "#bb9af7", "#f7768e", "#9d7cd8", "#7dcfff", "#e0af68")
LABELS = {
    "pt-BR": {
        "activity": "Status do GitHub",
        "year": "Contribuições · {year}",
        "commits_year": "Commits · {year}", "commits_year_public": "Commits visíveis · {year}",
        "repositories_year": "Repositórios · {year}", "repositories_year_public": "Repositórios públicos · {year}",
        "stars": "Estrelas", "prs": "Pull requests", "issues": "Issues",
        "grade": "nota anual",
        "languages": "Linguagens mais usadas", "lang_sub_public": "Código de repositórios públicos próprios",
        "lang_sub_private": "Código público + privado acessível",
        "other": "Outras", "no_languages": "Nenhuma linguagem encontrada.",
        "rhythm": "Ritmo de contribuições", "current": "Sequência atual", "best": "Maior sequência",
        "days": "dias", "last_days": "Últimos 35 dias",
        "oldest": "mais antigo", "today": "hoje", "flame": "Sequência atual",
        "achievements": "Conquistas do ano", "language_count": "Linguagens", "repos_short": "Repos. {year}",
        "rhythm_note": "Ritmo recente e sequências de contribuições no GitHub",
    },
    "en": {
        "activity": "GitHub status",
        "year": "Contributions · {year}",
        "commits_year": "Commits · {year}", "commits_year_public": "Visible commits · {year}",
        "repositories_year": "Repositories · {year}", "repositories_year_public": "Public repositories · {year}",
        "stars": "Stars", "prs": "Pull requests", "issues": "Issues",
        "grade": "year grade",
        "languages": "Most used languages", "lang_sub_public": "Code in owned public repositories",
        "lang_sub_private": "Code in accessible public + private repositories",
        "other": "Other", "no_languages": "No languages found.",
        "rhythm": "Contribution rhythm", "current": "Current streak", "best": "Longest streak",
        "days": "days", "last_days": "Last 35 days",
        "oldest": "oldest", "today": "today", "flame": "Current streak",
        "achievements": "Year achievements", "language_count": "Languages", "repos_short": "Repos. {year}",
        "rhythm_note": "Recent rhythm and contribution streaks on GitHub",
    },
    "es": {
        "activity": "Estado de GitHub",
        "year": "Contribuciones · {year}",
        "commits_year": "Commits · {year}", "commits_year_public": "Commits visibles · {year}",
        "repositories_year": "Repositorios · {year}", "repositories_year_public": "Repositorios públicos · {year}",
        "stars": "Estrellas", "prs": "Pull requests", "issues": "Incidencias",
        "grade": "nota anual",
        "languages": "Lenguajes más usados", "lang_sub_public": "Código de repositorios públicos propios",
        "lang_sub_private": "Código público + privado accesible",
        "other": "Otros", "no_languages": "No se encontraron lenguajes.",
        "rhythm": "Ritmo de contribuciones", "current": "Racha actual", "best": "Racha más larga",
        "days": "días", "last_days": "Últimos 35 días",
        "oldest": "más antiguo", "today": "hoy", "flame": "Racha actual",
        "achievements": "Logros del año", "language_count": "Lenguajes", "repos_short": "Repos. {year}",
        "rhythm_note": "Ritmo reciente y rachas de contribuciones en GitHub",
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
        name stargazerCount isFork isArchived
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
    year: int
    contributions_year: int
    commits_year: int
    stars: int
    prs: int
    issues: int
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


def collect_stats(token: str, config: dict, now: datetime,
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
    private_nodes: list[dict] = []
    languages_include_private = False
    if private_repositories_token:
        try:
            private_nodes = repository_nodes(
                private_repositories_token, PRIVATE_REPOSITORIES_QUERY, username, root_field="viewer"
            )
            language_repositories.extend(private_nodes)
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
        year=today.year,
        contributions_year=yearly[today.year]["contributionCalendar"]["totalContributions"],
        commits_year=yearly[today.year]["totalCommitContributions"],
        stars=sum(repo["stargazerCount"] for repo in nodes + private_nodes),
        prs=first["pullRequests"]["totalCount"], issues=first["issues"]["totalCount"],
        languages=languages,
        current_streak=current, longest_streak=longest, recent_days=last_35,
        languages_include_private=languages_include_private,
        repositories_year=yearly[today.year]["totalRepositoriesWithContributedCommits"],
        contributions_include_private=activity_token != token,
    )


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
    "star": '<path d="m12 2.2 3.1 6.3 7 .9-5.1 4.9 1.2 7-6.2-3.3-6.2 3.3 1.2-7-5.1-4.9 7-.9L12 2.2Z"/>',
    "commit": '<circle cx="12" cy="5" r="4"/><circle cx="12" cy="19" r="4"/><path d="M10 8h4v8h-4z"/>',
    "pull": '<circle cx="6" cy="5" r="3.5"/><circle cx="18" cy="19" r="3.5"/><circle cx="18" cy="5" r="3.5"/><path d="M4.5 8h3v9h-3zM16.5 8h3v8h-3zM9 10l6 6-2.1 2.1-6-6z"/>',
    "repository": '<path d="M4 2h16v20H4z"/><path d="M8 7h8v1.8H8zm0 4.5h8v1.8H8zm0 4.5h5v1.8H8z"/>',
    "issue": '<circle cx="12" cy="12" r="10"/><path d="M10.7 6.2h2.6l-.4 7.4h-1.8zM10.8 15.2h2.4v2.6h-2.4z"/>',
    "calendar": '<path d="M4 3h3v4H4zm13 0h3v4h-3zM2 6h20v16H2z"/><path d="M5 10h3v3H5zm5 0h3v3h-3zm5 0h3v3h-3zM5 15h3v3H5zm5 0h3v3h-3z"/>',
    "code": '<path d="m7.5 4 2 2-5.9 6 5.9 6-2 2L0 12zm9 0 2-2 7.5 10-7.5 10-2-2 5.9-8zm-2.4-2h2.5l-6.2 20H8z"/>',
    "flame": '<path d="M13.3 1c.7 4.6-2.6 5.5-2.6 9.2 0 1.5.8 2.5 1.8 2.5 1.6 0 2.5-1.5 2.5-3.3 3.3 2.6 5.1 5.4 5.1 8.2a8.1 8.1 0 0 1-16.2 0c0-4.8 3-7.9 9.4-16.6Z"/><path d="M12.2 14c.4 2-1.8 2.7-1.8 4.4 0 1 .7 1.8 1.6 1.8 1.3 0 2.1-.9 2.1-2.2 0-1.2-.7-2.4-1.9-4Z" fill="#1a1b28"/>',
}


def svg_icon(name: str, x: int, y: int, color: str, size: int = 20) -> str:
    """Draw a solid pictogram on a square color block."""
    if name not in ICON_PATHS:
        raise ValueError(f"Unknown icon: {name}")
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'aria-hidden="true"><rect width="24" height="24" fill="{color}"/>'
            f'<g fill="#1a1b28">{ICON_PATHS[name]}</g></svg>')


def activity_grade(contributions: int) -> str:
    """Return a custom, non-official year grade based on contribution count."""
    for threshold, grade in ((2500, "S"), (1500, "A+"), (1000, "A"), (600, "A−"),
                             (400, "B+"), (200, "B"), (100, "B−"), (50, "C")):
        if contributions >= threshold:
            return grade
    return "D"


def render_stats(stats: Stats, locale: str) -> str:
    labels = LABELS[locale]
    rows = (
        ("star", labels["stars"], stats.stars, "#e0af68"),
        ("commit", labels["commits_year" if stats.contributions_include_private else "commits_year_public"].format(year=stats.year), stats.commits_year, "#bb9af7"),
        ("repository", labels["repositories_year" if stats.contributions_include_private else "repositories_year_public"].format(year=stats.year), stats.repositories_year, "#bb9af7"),
        ("pull", labels["prs"], stats.prs, "#bb9af7"),
        ("issue", labels["issues"], stats.issues, "#f7768e"),
        ("calendar", labels["year"].format(year=stats.year), stats.contributions_year, "#7aa2f7"),
    )
    body = (f'{svg_icon("calendar", 22, 25, "#7aa2f7", 20)}'
            f'<text x="50" y="43" fill="#7aa2f7" font-size="18" font-weight="700">{labels["activity"]}</text>'
            f'<rect x="350" y="22" width="48" height="34" fill="#7aa2f7"/>'
            f'<text x="374" y="39" text-anchor="middle" fill="#1a1b28" font-size="15" font-weight="800">{activity_grade(stats.contributions_year)}</text>'
            f'<text x="374" y="51" text-anchor="middle" fill="#1a1b28" font-size="7" font-weight="700">{labels["grade"]}</text>')
    body += f'<path d="M22 62H398" stroke="#34364c"/>'
    for index, (icon, label, value, color) in enumerate(rows):
        baseline = 86 + index * 30
        body += svg_icon(icon, 22, baseline - 19, color, 20)
        body += (f'<text x="51" y="{baseline}" fill="#9ecec5" font-size="15">{html.escape(label)}</text>'
                 f'<text x="398" y="{baseline}" text-anchor="end" '
                 f'fill="#7dcfff" font-size="18" font-weight="700">{fmt(value, locale)}</text>')
    description = (f"{stats.name} · {labels['year'].format(year=stats.year)} · "
                   f"{labels['grade']} {activity_grade(stats.contributions_year)}")
    return svg_shell(f"{stats.name} · {labels['activity']}", description, body,
                     420, 290)


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
<defs><clipPath id="bar"><rect x="22" y="98" width="376" height="14"/></clipPath></defs>
<rect x="22" y="98" width="376" height="14" fill="#34364c"/>
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
            body += (f'<rect x="{x}" y="{y-10}" width="10" height="10" fill="{color}"/>'
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
    header = (f'{svg_icon("flame", 22, 25, "#bb9af7", 20)}'
              f'<text x="50" y="43" fill="#7aa2f7" font-size="20" font-weight="700">{labels["rhythm"]}</text>')
    heatmap_values = list(stats.recent_days[-35:])
    heatmap_values = [0] * (35 - len(heatmap_values)) + heatmap_values
    maximum = max(heatmap_values, default=0)

    def heatmap(x: int, y: int, tile: int, gap: int) -> str:
        parts = []
        for index, value in enumerate(heatmap_values):
            column, row = divmod(index, 7)
            color = ("#34364c" if value <= 0 else "#465570" if value < max(2, maximum * .2)
                     else "#5775b4" if value < max(5, maximum * .45)
                     else "#6687ce" if value < max(10, maximum * .7) else "#7aa2f7")
            parts.append(f'<rect x="{x + column * (tile + gap)}" y="{y + row * (tile + gap)}" '
                         f'width="{tile}" height="{tile}" fill="{color}"/>')
        return "".join(parts)

    if mobile:
        body = f'''
{header}
<rect x="22" y="66" width="151" height="112" fill="#242234" stroke="#34364c"/>
{svg_icon("flame", 35, 78, "#f7768e", 24)}
<text x="69" y="91" fill="#f7768e" font-size="11" font-weight="700">{labels['flame']}</text>
<text x="35" y="132" fill="#f2b36b" font-size="34" font-weight="800">{stats.current_streak}</text>
<text x="84" y="132" fill="#9ecec5" font-size="13">{labels['days']}</text>
<text x="35" y="157" fill="#8994ad" font-size="11">{labels['best']}: {stats.longest_streak} {labels['days']}</text>
<text x="195" y="76" fill="#9ecec5" font-size="12">{labels['last_days']}</text>
{heatmap(195, 87, 11, 4)}
<text x="195" y="172" fill="#8994ad" font-size="10">{labels['oldest']}</text>
<text x="270" y="172" fill="#8994ad" font-size="10">{labels['today']}</text>
<path d="M22 195H398" stroke="#34364c"/>
<text x="22" y="215" fill="#bb9af7" font-size="10" font-weight="700">{labels['achievements']}</text>
<path d="M147 222V273M273 222V273" stroke="#34364c"/>
<text x="22" y="243" fill="#7aa2f7" font-size="20" font-weight="700">{len(stats.languages)}</text>
<text x="22" y="260" fill="#9ecec5" font-size="10">{labels['language_count']}</text>
<text x="160" y="243" fill="#e0af68" font-size="20" font-weight="700">{fmt(stats.stars, locale)}</text>
<text x="160" y="260" fill="#9ecec5" font-size="10">{labels['stars']}</text>
<text x="288" y="243" fill="#7dcfff" font-size="20" font-weight="700">{fmt(stats.repositories_year, locale)}</text>
<text x="288" y="260" fill="#9ecec5" font-size="10">{labels['repos_short'].format(year=stats.year)}</text>'''
        return svg_shell(f"{stats.name} · {labels['rhythm']}", labels["rhythm_note"], body, 420, 290)
    body = f'''
{header}
<rect x="22" y="69" width="223" height="107" fill="#242234" stroke="#34364c"/>
{svg_icon("flame", 39, 84, "#f7768e", 28)}
<text x="79" y="102" fill="#f7768e" font-size="13" font-weight="700">{labels['flame']}</text>
<text x="39" y="146" fill="#f2b36b" font-size="42" font-weight="800">{stats.current_streak}</text>
<text x="101" y="146" fill="#9ecec5" font-size="15">{labels['days']}</text>
<text x="39" y="164" fill="#8994ad" font-size="11">{labels['best']}: {stats.longest_streak} {labels['days']}</text>
<text x="274" y="77" fill="#9ecec5" font-size="13">{labels['last_days']}</text>
{heatmap(274, 91, 12, 5)}
<text x="274" y="208" fill="#8994ad" font-size="11">{labels['oldest']}</text>
<text x="390" y="208" fill="#8994ad" font-size="11">{labels['today']}</text>
<path d="M22 226H818" stroke="#34364c"/>
<text x="22" y="245" fill="#bb9af7" font-size="11" font-weight="700">{labels['achievements']}</text>
<path d="M286 235V270M550 235V270" stroke="#34364c"/>
<text x="370" y="250" fill="#7aa2f7" font-size="21" font-weight="700">{len(stats.languages)}</text>
<text x="370" y="265" fill="#9ecec5" font-size="10">{labels['language_count']}</text>
<text x="634" y="250" fill="#e0af68" font-size="21" font-weight="700">{fmt(stats.stars, locale)}</text>
<text x="634" y="265" fill="#9ecec5" font-size="10">{labels['stars']}</text>
<text x="714" y="250" fill="#7dcfff" font-size="21" font-weight="700">{fmt(stats.repositories_year, locale)}</text>
<text x="714" y="265" fill="#9ecec5" font-size="10">{labels['repos_short'].format(year=stats.year)}</text>'''
    return svg_shell(f"{stats.name} · {labels['rhythm']}", labels["rhythm_note"], body, 840, 290)


def output_name(kind: str, locale: str) -> str:
    suffix = {"pt-BR": "", "en": "-en", "es": "-es"}[locale]
    return f"{kind}{suffix}.svg"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("profile-card.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("profile"))
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required; GitHub Actions supplies a repository-scoped token")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if not re.fullmatch(r"[a-zA-Z0-9-]{1,39}", config["username"]):
        raise SystemExit("Invalid GitHub username")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    previous_path = args.output_dir / "data.json"
    now = datetime.now(timezone.utc)
    private_repositories_token = os.environ.get("PRIVATE_REPOSITORIES_TOKEN") or None
    private_contributions_token = os.environ.get("PRIVATE_CONTRIBUTIONS_TOKEN") or None
    stats = collect_stats(token, config, now, private_repositories_token,
                          private_contributions_token)
    for locale in SUPPORTED_LOCALES:
        for kind, renderer in (("stats", render_stats), ("languages", render_languages), ("rhythm", render_rhythm)):
            (args.output_dir / output_name(kind, locale)).write_text(renderer(stats, locale), encoding="utf-8")
        (args.output_dir / output_name("rhythm-mobile", locale)).write_text(
            render_rhythm(stats, locale, mobile=True), encoding="utf-8"
        )
    data = json.loads(json.dumps(asdict(stats)))
    previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {}
    previous.pop("generated_at", None)
    data["generated_at"] = now.isoformat(timespec="seconds")
    # Keep the snapshot stable when the actual metrics have not changed.
    if previous == data:
        data["generated_at"] = json.loads(previous_path.read_text(encoding="utf-8"))["generated_at"]
    previous_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{stats.username}: {stats.contributions_year} calendar contributions, "
          f"{stats.commits_year} commit contributions, {stats.repositories_year} repositories with commits "
          f"in {stats.year}")


if __name__ == "__main__":
    main()

