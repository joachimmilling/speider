"""Fetch from the sources and load into the local database."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Callable

from .db import upsert
from .sources import esf
from .sources.http import Fetcher


def load_esf_bootstrap(con, bootstrap: dict, fixtures: list[dict] | None = None,
                       today: date | None = None) -> dict[str, int]:
    """Load one bootstrap document (and optionally the fixture list). No network."""
    today = today or date.today()
    now = datetime.now().replace(microsecond=0)
    season = esf.season_of(bootstrap)
    counts = {
        "teams": upsert(con, "teams", esf.parse_teams(bootstrap, now)),
        "players": upsert(con, "players", esf.parse_players(bootstrap, now)),
        "player_snapshots": upsert(con, "player_snapshots", esf.parse_snapshots(bootstrap, today)),
    }
    if fixtures is not None:
        counts["fixtures"] = upsert(con, "fixtures", esf.parse_fixtures(fixtures, season))
    for what, rows in counts.items():
        con.execute("INSERT INTO fetch_log VALUES (?, ?, ?, ?)", [now, esf.SOURCE, what, rows])
    return counts


def load_esf_summary(con, player_id: int, summary: dict, season: str) -> dict[str, int]:
    return {
        "player_matches": upsert(con, "player_matches", esf.parse_player_matches(player_id, summary, season)),
        "player_seasons": upsert(con, "player_seasons", esf.parse_player_seasons(player_id, summary)),
    }


def fetch_esf(con, raw_dir: str | Path = "data/raw", with_matches: bool = False,
              fetcher: Fetcher | None = None,
              progress: Callable[[str], None] = lambda message: None) -> dict[str, int]:
    """Fetch Eliteserien Fantasy. with_matches adds one request per player (a few minutes)."""
    today = date.today()
    fetcher = fetcher or Fetcher(raw_dir=Path(raw_dir) / esf.SOURCE / today.isoformat())
    progress("Henter spillere og lag")
    bootstrap = fetcher.get_json(f"{esf.BASE_URL}/bootstrap-static/", "bootstrap-static.json")
    progress("Henter kamper")
    fixtures = fetcher.get_json(f"{esf.BASE_URL}/fixtures/", "fixtures.json")
    counts = load_esf_bootstrap(con, bootstrap, fixtures, today)

    if with_matches:
        season = esf.season_of(bootstrap)
        players = [el["id"] for el in bootstrap.get("elements", []) if not el.get("removed")]
        counts["player_matches"] = counts["player_seasons"] = 0
        for number, player_id in enumerate(players, start=1):
            if number % 50 == 1:
                progress(f"Henter kamplogg {number} av {len(players)}")
            summary = fetcher.get_json(f"{esf.BASE_URL}/element-summary/{player_id}/",
                                       f"element-summary/{player_id}.json")
            for what, rows in load_esf_summary(con, player_id, summary, season).items():
                counts[what] += rows
    return counts
