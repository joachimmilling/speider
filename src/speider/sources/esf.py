"""Eliteserien Fantasy: the public JSON feed behind fantasy.eliteserien.no.

Undocumented and unofficial. It gives every Eliteserien player with club,
position, minutes, goals, assists and cards, a match log per player, and
season totals back in time. The birth date and nationality fields exist but
were empty when checked in November 2026, so age may need another source.

The functions here only turn the feed's JSON into rows for our own tables.
Fetching lives in speider.ingest, so parsing can be tested without a network.
"""

from __future__ import annotations

from datetime import date, datetime

SOURCE = "esf"
BASE_URL = "https://fantasy.eliteserien.no/api"
LEAGUE = "Eliteserien"

POSITIONS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def _id(kind_id) -> str | None:
    return None if kind_id is None else f"{SOURCE}:{kind_id}"


def _num(value) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _cost(value) -> float | None:
    """The feed stores prices in tenths (65 means 6.5)."""
    number = _num(value)
    return None if number is None else number / 10


def _time(value) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _date(value) -> date | None:
    return date.fromisoformat(value[:10]) if value else None


def season_of(bootstrap: dict) -> str:
    """The season is the year of the first round's deadline."""
    events = bootstrap.get("events") or []
    first = min((e["deadline_time"] for e in events if e.get("deadline_time")), default=None)
    return first[:4] if first else str(date.today().year)


def parse_teams(bootstrap: dict, now: datetime) -> list[dict]:
    rows = []
    for team in bootstrap.get("teams", []):
        rows.append({
            "team_id": _id(team["id"]),
            "source": SOURCE,
            "name": team["name"],
            "short_name": team.get("short_name"),
            # Clubs outside this season's game are listed but flagged unavailable.
            "league": None if team.get("unavailable") else LEAGUE,
            "updated_at": now,
        })
    return rows


def parse_players(bootstrap: dict, now: datetime) -> list[dict]:
    rows = []
    for el in bootstrap.get("elements", []):
        if el.get("removed"):
            continue
        display = el.get("known_name") or el.get("web_name") or f"{el.get('first_name', '')} {el.get('second_name', '')}".strip()
        rows.append({
            "player_id": _id(el["id"]),
            "source": SOURCE,
            "first_name": el.get("first_name"),
            "last_name": el.get("second_name"),
            "display_name": display,
            "position": POSITIONS.get(el.get("element_type")),
            "team_id": _id(el.get("team")),
            "birth_date": _date(el.get("birth_date")),
            "nationality": el.get("region"),
            "squad_number": el.get("squad_number"),
            "status": el.get("status"),
            "opta_code": el.get("opta_code"),
            "fiks_id": el.get("fiks_id"),
            "updated_at": now,
        })
    return rows


def parse_snapshots(bootstrap: dict, snapshot_date: date) -> list[dict]:
    season = season_of(bootstrap)
    rows = []
    for el in bootstrap.get("elements", []):
        if el.get("removed"):
            continue
        rows.append({
            "player_id": _id(el["id"]),
            "snapshot_date": snapshot_date,
            "season": season,
            "team_id": _id(el.get("team")),
            "minutes": el.get("minutes"),
            "goals": el.get("goals_scored"),
            "assists": el.get("assists"),
            "clean_sheets": el.get("clean_sheets"),
            "goals_conceded": el.get("goals_conceded"),
            "own_goals": el.get("own_goals"),
            "yellow_cards": el.get("yellow_cards"),
            "red_cards": el.get("red_cards"),
            "saves": el.get("saves"),
            "penalties_saved": el.get("penalties_saved"),
            "penalties_missed": el.get("penalties_missed"),
            "fantasy_points": el.get("total_points"),
            "fantasy_cost": _cost(el.get("now_cost")),
            "selected_pct": _num(el.get("selected_by_percent")),
        })
    return rows


def parse_fixtures(fixtures: list[dict], season: str) -> list[dict]:
    rows = []
    for fx in fixtures:
        rows.append({
            "fixture_id": _id(f"{season}:{fx['id']}"),
            "source": SOURCE,
            "season": season,
            "round": fx.get("event"),
            "kickoff": _time(fx.get("kickoff_time")),
            "home_team_id": _id(fx.get("team_h")),
            "away_team_id": _id(fx.get("team_a")),
            "home_score": fx.get("team_h_score"),
            "away_score": fx.get("team_a_score"),
            "finished": bool(fx.get("finished")),
        })
    return rows


def parse_player_matches(player_id: int, summary: dict, season: str) -> list[dict]:
    rows = []
    for h in summary.get("history", []):
        rows.append({
            "player_id": _id(player_id),
            "fixture_id": _id(f"{season}:{h['fixture']}"),
            "season": season,
            "round": h.get("round"),
            "kickoff": _time(h.get("kickoff_time")),
            "opponent_team_id": _id(h.get("opponent_team")),
            "was_home": h.get("was_home"),
            "minutes": h.get("minutes"),
            "goals": h.get("goals_scored"),
            "assists": h.get("assists"),
            "clean_sheets": h.get("clean_sheets"),
            "goals_conceded": h.get("goals_conceded"),
            "yellow_cards": h.get("yellow_cards"),
            "red_cards": h.get("red_cards"),
            "saves": h.get("saves"),
            "fantasy_points": h.get("total_points"),
            "fantasy_cost": _cost(h.get("value")),
        })
    return rows


def parse_player_seasons(player_id: int, summary: dict) -> list[dict]:
    rows = []
    for h in summary.get("history_past", []):
        season = h.get("season_name")
        if not season:
            continue
        rows.append({
            "player_id": _id(player_id),
            "season": str(season),
            "minutes": h.get("minutes"),
            "goals": h.get("goals_scored"),
            "assists": h.get("assists"),
            "clean_sheets": h.get("clean_sheets"),
            "goals_conceded": h.get("goals_conceded"),
            "yellow_cards": h.get("yellow_cards"),
            "red_cards": h.get("red_cards"),
            "saves": h.get("saves"),
            "fantasy_points": h.get("total_points"),
            "start_cost": _cost(h.get("start_cost")),
            "end_cost": _cost(h.get("end_cost")),
        })
    return rows
