#!/usr/bin/env python3
"""Generate one public GitHub profile card without a personal access token."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


USERNAME = "GuiCodeLabs"
GRAPHQL_URL = "https://api.github.com/graphql"
CARD_PATH = Path("profile/stats.svg")
VISITS_URL = "https://komarev.com/ghpvc/?" + urllib.parse.urlencode(
    {"username": USERNAME, "label": "Visitas ao perfil", "color": "70a5fd", "style": "flat-square"}
)

PROFILE_QUERY = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    name
    contributionsCollection { contributionYears }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, privacy: PUBLIC) {
      nodes { stargazerCount }
      pageInfo { hasNextPage endCursor }
    }
    pullRequests(first: 1) { totalCount }
    issues(first: 1) { totalCount }
  }
}
"""

COMMITS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
    }
  }
}
"""


@dataclass(frozen=True)
class Stats:
    name: str
    stars: int
    commits_all: int
    commits_year: int
    prs: int
    issues: int
    visits: int | None


def graphql(token: str, query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "GuiCodeLabs-profile-card",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(f"GitHub GraphQL: {result['errors']}")
    if not result.get("data", {}).get("user"):
        raise RuntimeError("Usuário não encontrado na resposta do GitHub")
    return result["data"]["user"]


def public_github_stats(token: str, now: datetime) -> tuple[dict, int, int, int]:
    first_page = graphql(token, PROFILE_QUERY, {"login": USERNAME, "cursor": None})
    repositories = first_page["repositories"]
    stars = sum(node["stargazerCount"] for node in repositories["nodes"])
    while repositories["pageInfo"]["hasNextPage"]:
        cursor = repositories["pageInfo"]["endCursor"]
        if not cursor:
            raise RuntimeError("Paginação de repositórios sem cursor")
        repositories = graphql(token, PROFILE_QUERY, {"login": USERNAME, "cursor": cursor})["repositories"]
        stars += sum(node["stargazerCount"] for node in repositories["nodes"])

    year = now.astimezone(ZoneInfo("America/Fortaleza")).year
    years = sorted(set(first_page["contributionsCollection"]["contributionYears"]) | {year})
    if not years or any(y < 2008 or y > year for y in years):
        raise RuntimeError(f"Anos de contribuição inesperados: {years}")

    yearly: dict[int, int] = {}
    for y in years:
        start = f"{y}-01-01T00:00:00Z"
        end = min(datetime(y + 1, 1, 1, tzinfo=timezone.utc), now.astimezone(timezone.utc))
        # GraphQL includes the upper bound. The next year's start is excluded.
        end = end.replace(microsecond=0)
        if end.year != y:
            end = datetime(y, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        data = graphql(
            token,
            COMMITS_QUERY,
            {"login": USERNAME, "from": start, "to": end.isoformat().replace("+00:00", "Z")},
        )
        yearly[y] = data["contributionsCollection"]["totalCommitContributions"]

    return first_page, stars, yearly[year], sum(yearly.values())


def parse_visit_badge(svg: bytes) -> int:
    root = ET.fromstring(svg)
    texts = [node.text.strip() for node in root.iter() if node.tag.endswith("}text") and node.text]
    candidates = [text for text in texts if re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)", text)]
    if not candidates:
        raise ValueError("Contagem não encontrada no SVG do contador")
    return int(candidates[-1].replace(",", ""))


def visits_count(previous_card: Path = CARD_PATH) -> int | None:
    try:
        request = urllib.request.Request(VISITS_URL, headers={"User-Agent": "GuiCodeLabs-profile-card"})
        with urllib.request.urlopen(request, timeout=15) as response:
            return parse_visit_badge(response.read())
    except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError) as exc:
        print(f"Contador indisponível: {exc.__class__.__name__}; conservando valor anterior")
        if previous_card.exists():
            match = re.search(r'data-visits="(\d+)"', previous_card.read_text(encoding="utf-8"))
            if match:
                return int(match.group(1))
        return None


def pt_number(number: int | None) -> str:
    return "—" if number is None else f"{number:,}".replace(",", ".")


def render_card(stats: Stats, now: datetime) -> str:
    local = now.astimezone(ZoneInfo("America/Fortaleza"))
    year = local.year
    stamp = local.strftime("%d/%m/%Y %H:%M BRT")
    rows = [
        ("★", "Estrelas recebidas", stats.stars),
        ("↻", "Commits · todo o período", stats.commits_all),
        ("↻", f"Commits · {year}", stats.commits_year),
        ("⑂", "Pull requests", stats.prs),
        ("!", "Issues", stats.issues),
        ("◉", "Visitas ao perfil", stats.visits),
    ]
    lines = []
    for i, (icon, label, value) in enumerate(rows):
        y = 82 + i * 32
        lines.append(
            f'<text x="28" y="{y}" fill="#bb9af7" font-size="20">{icon}</text>'
            f'<text x="60" y="{y}" fill="#38bdae" font-size="16">{label}</text>'
            f'<text x="504" y="{y}" fill="#38bdae" font-size="17" font-weight="bold" '
            f'text-anchor="end">{pt_number(value)}</text>'
        )
    visits_attribute = "" if stats.visits is None else f' data-visits="{stats.visits}"'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="290" viewBox="0 0 520 290" role="img" aria-labelledby="title desc"{visits_attribute}>
  <title id="title">Estatísticas do GitHub de {stats.name}</title>
  <desc id="desc">Estrelas, commits públicos de todo o período e de {year}, pull requests, issues e visitas ao perfil.</desc>
  <rect x="0" y="0" width="520" height="290" rx="8" fill="#1a1b27" />
  <g font-family="Segoe UI, DejaVu Sans, sans-serif">
    <text x="28" y="37" fill="#70a5fd" font-size="20" font-weight="bold">GitHub de {stats.name}</text>
    <path d="M28 51 H492" stroke="#34364e" stroke-width="1" />
    {''.join(lines)}
    <text x="28" y="281" fill="#9aa5ce" font-size="11">Commits públicos · Atualizado em {stamp}</text>
  </g>
</svg>
'''


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN ausente: use apenas o token automático do GitHub Actions")
    now = datetime.now(timezone.utc)
    profile, stars, this_year, all_time = public_github_stats(token, now)
    stats = Stats(
        name="Guilherme Beserra",
        stars=stars,
        commits_all=all_time,
        commits_year=this_year,
        prs=profile["pullRequests"]["totalCount"],
        issues=profile["issues"]["totalCount"],
        visits=visits_count(),
    )
    CARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    CARD_PATH.write_text(render_card(stats, now), encoding="utf-8")
    print(f"Cartão atualizado: {all_time} commits públicos, {this_year} em {now.year}")


if __name__ == "__main__":
    main()
