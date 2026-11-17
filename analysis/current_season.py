"""The season in progress: what a player has done so far this season, per club.

Only leagues with split-year seasons (2026/2027). In calendar-year leagues the running season is already the latest season in the frame.
"""
import numpy as np
import pandas as pd

CUR = ["cur_min", "cur_rating", "cur_g90", "cur_xg90", "cur_xa90", "cur_d_rating"]
STATS = {"mins_played": "cur_min", "rating": "cur_rating", "goals_per_90": "cur_g90", "expected_goals_per_90": "cur_xg90", "expected_assists_per_90": "cur_xa90"}


def rows(con) -> pd.DataFrame:
    """One row per player, season and club: minutes and minute-weighted numbers over the leagues he played in for that club (cups left out)."""
    s = con.execute("""
        select s.player_id, se.end_year ey, s.team_id, s.stat, s.value v, s.minutes m
        from fm_stats s join fm_seasons se using (league_id, season_id) join fm_leagues l using (league_id)
        where l.gender = 'male' and se.season_name like '%/%' and s.stat in (select unnest(?)) and isfinite(s.value) and s.minutes > 0
          and l.name not ilike '%cup%' and l.name not ilike '%pokal%' and l.name not ilike '%copa%' and l.name not ilike '%coppa%' and l.name not ilike '%trophy%'
    """, [list(STATS)]).fetchdf()
    s["w"] = s.v * s.m
    g = s.groupby(["player_id", "ey", "team_id", "stat"]).agg(w=("w", "sum"), m=("m", "sum")).reset_index()
    g["x"] = np.where(g.stat == "mins_played", g.m, g.w / g.m)
    return g.pivot_table(index=["player_id", "ey", "team_id"], columns="stat", values="x").rename(columns=STATS).reset_index()


def finish(d: pd.DataFrame) -> pd.DataFrame:
    """Change in rating against the last finished season, shrunk by minutes (900 minutes count half)."""
    d["cur_d_rating"] = (d.cur_rating - d.rating) * d.cur_min / (d.cur_min + 900)
    for c in CUR:
        if c not in d: d[c] = np.nan
    return d


def for_transfers(m: pd.DataFrame, cur: pd.DataFrame) -> pd.DataFrame:
    """Attach the selling club's row for the season running on the transfer date (July-May). m needs yy, mo, from_id."""
    m = m.copy(); m["ey"] = np.where(m.mo >= 7, m.yy + 1, np.where(m.mo <= 5, m.yy, -1))
    m = m.merge(cur, left_on=["player_id", "ey", "from_id"], right_on=["player_id", "ey", "team_id"], how="left", suffixes=("", "_cur")).drop(columns=["ey"])
    return finish(m)


def for_now(now: pd.DataFrame, cur: pd.DataFrame, ey: int = 2027) -> pd.DataFrame:
    """Attach the season in progress today, over all clubs he has played for in it."""
    c = cur[cur.ey == ey].copy()
    for k in ("cur_rating", "cur_g90", "cur_xg90", "cur_xa90"): c[k] = c[k] * c.cur_min
    c = c.groupby("player_id").sum(numeric_only=True).reset_index()
    for k in ("cur_rating", "cur_g90", "cur_xg90", "cur_xa90"): c[k] = c[k] / c.cur_min
    return finish(now.merge(c[["player_id"] + [k for k in CUR if k in c]], on="player_id", how="left"))
