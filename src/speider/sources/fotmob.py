"""FotMob season statistics: one JSON list per league, season and statistic.

Unofficial. The lists are static files, so no key or login is needed. Each
list holds one row per player with the value, a secondary value, minutes and
matches played, club and position codes.

Two things to know before trusting the numbers:

* Per-90 lists only include players who appeared in roughly half of the
  season's matches. Totals such as xG and xA include everyone.
* Coverage grows over time. For Eliteserien the basic, passing and defensive
  lists start in 2017, xG and xA in 2020 and line-breaking passes in 2024.

Parsing lives here; fetching lives in speider.ingest.
"""

from __future__ import annotations

SOURCE = "fotmob"
BASE_URL = "https://data.fotmob.com/stats"

ELITESERIEN = 59
# League id -> season name -> FotMob season id.
SEASONS = {
    ELITESERIEN: {
        "2026": 30202, "2025": 24542, "2024": 22600, "2023": 18510, "2022": 17324,
        "2021": 16014, "2020": 14838, "2019": 13465, "2018": 12361, "2017": 11105,
    },
}

STATS = [
    "mins_played", "rating", "goals", "goal_assist", "goals_per_90",
    "expected_goals", "expected_goals_per_90", "expected_goalsontarget",
    "expected_assists", "expected_assists_per_90",
    "total_scoring_att", "ontarget_scoring_att", "big_chance_missed",
    "accurate_pass", "accurate_long_balls", "lbp_total", "total_att_assist", "big_chance_created",
    "won_contest", "penalty_won",
    "defensive_contributions", "total_tackle", "interception", "effective_clearance",
    "outfielder_block", "ball_recovery", "poss_won_att_3rd", "penalty_conceded",
    "clean_sheet", "saves", "_save_percentage", "_goals_prevented", "goals_conceded",
    "total_high_claim", "total_keeper_sweeper", "penalty_save",
    "fouls", "yellow_card", "red_card",
]

# First position code -> role. Codes read as line (tens) and side (units).
_ROLES = {
    "GK": {11}, "CB": {33, 34, 35, 36, 37}, "FB": {32, 38, 51, 59},
    "DM": set(range(62, 69)), "CM": set(range(72, 79)), "AM": set(range(83, 88)),
    "W": {71, 79, 82, 88, 103, 107}, "ST": {104, 105, 106, 115},
}
GROUPS = {"GK": "GK", "CB": "DEF", "FB": "DEF", "DM": "MID", "CM": "MID", "AM": "MID", "W": "ATT", "ST": "ATT"}


def url(league: int, season_id: int, stat: str) -> str:
    return f"{BASE_URL}/{league}/season/{season_id}/{stat}.json"


def role_of(positions: list[int] | None) -> str | None:
    """Role from the player's first (most used) position code."""
    if not positions:
        return None
    for role, codes in _ROLES.items():
        if positions[0] in codes:
            return role
    return None


def parse_stat_list(document: dict, league: int, season: str, stat: str) -> list[dict]:
    """Rows for the player_stats table from one statistic file."""
    lists = document.get("TopLists") or []
    if not lists:
        return []
    top = lists[0]
    title = top.get("Title") or ""
    rows = []
    for item in top.get("StatList") or []:
        player = item.get("ParticiantId")   # sic: the feed misspells it
        if player is None:
            continue
        positions = item.get("Positions") or []
        rows.append({
            "player_id": f"{SOURCE}:{player}",
            "league": str(league),
            "season": season,
            "stat": stat,
            "value": item.get("StatValue"),
            "sub_value": item.get("SubStatValue"),
            "is_per_90": "per 90" in title.lower(),
            "minutes": item.get("MinutesPlayed"),
            "matches": item.get("MatchesPlayed"),
            "player_name": item.get("ParticipantName"),
            "team_id": f"{SOURCE}:{item.get('TeamId')}",
            "team_name": item.get("TeamName"),
            "nationality": item.get("ParticipantCountryCode"),
            "position_code": positions[0] if positions else None,
            "role": role_of(positions),
        })
    return rows
