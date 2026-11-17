"""Availability per player, team and season from match line-ups: started, came on, on the bench unused, out of the matchday squad
(listed injured, listed suspended, not listed). Big five leagues from 2022/23."""
import numpy as np
import pandas as pd


def table(con) -> pd.DataFrame:
    m = con.execute("select match_id, end_year ey, home_id, away_id from fm_matches").fetchdf()
    tm = pd.concat([m[["match_id", "ey", "home_id"]].rename(columns={"home_id": "team_id"}), m[["match_id", "ey", "away_id"]].rename(columns={"away_id": "team_id"})])
    n = tm.groupby(["team_id", "ey"]).size().rename("n").reset_index()
    l = con.execute("select l.*, m.end_year ey from fm_lineups l join fm_matches m using (match_id)").fetchdf()
    g = l.groupby(["player_id", "team_id", "ey"]).agg(squad=("match_id", "size"), starts=("started", "sum"), played=("played", "sum"), minutes=("minutes", "sum"), rating=("rating", "mean")).reset_index()
    u = con.execute("select u.player_id, u.team_id, m.end_year ey, sum((u.type = 'injury')::int) inj, sum((u.type = 'suspension')::int) susp from fm_unavailable u join fm_matches m using (match_id) group by all").fetchdf()
    g = g.merge(u, on=["player_id", "team_id", "ey"], how="outer").merge(n, on=["team_id", "ey"])
    for c in ("squad", "starts", "played", "minutes", "inj", "susp"): g[c] = g[c].fillna(0)
    g["sub_in"] = g.played - g.starts; g["bench"] = g.squad - g.played; g["absent"] = (g.n - g.squad).clip(lower=0)
    for c in ("starts", "sub_in", "bench", "absent", "inj"): g[c + "_sh"] = g[c] / g.n
    g["min_sh"] = g.minutes / (g.n * 90)
    return g
