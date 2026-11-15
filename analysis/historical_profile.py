"""Historical profile v0: era- and league-adjusted output from career lines.

For seasons without detailed statistics we only have matches, goals and
assists per player, league and season (back to 2002). To compare across eras,
goal involvements per match are standardised within league, season and role
group, and shrunk for few matches. This is the simple tier; the detailed
profile for old seasons is reconstructed separately (models.md, model 11).
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

TOP5 = {47: "Premier League", 87: "LaLiga", 54: "Bundesliga", 55: "Serie A", 53: "Ligue 1"}


def group(code: int) -> str:
    if code == 11: return "GK"
    if 30 <= code <= 59: return "DEF"
    if 60 <= code <= 79: return "MID"
    return "ATT"


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    c = con.execute("""
        select c.player_id, p.name, c.end_year y, c.league_id, c.league_name, c.team, c.apps, c.goals, coalesce(c.assists,0) assists,
               c.rating, p.birth, cast(json_extract(pl.positions,'$[0]') as int) pos
        from fm_career c join fm_profiles p using (player_id) left join fm_players pl using (player_id)
        where c.apps >= 1 and c.end_year is not null and p.gender='male'
    """).fetchdf()
    c["grp"] = c.pos.fillna(0).astype(int).map(group)
    c["age"] = c.y - 0.5 - pd.to_datetime(c.birth).dt.year - (pd.to_datetime(c.birth).dt.dayofyear / 365.25)
    c["gi"] = (c.goals + c.assists) / c.apps
    cov = c.groupby("y").agg(player_seasons=("player_id", "size"), with_assists=("assists", lambda s: int((s > 0).sum())), with_rating=("rating", lambda s: int(s.notna().sum())))
    print("Coverage per season end year (loaded profiles only):")
    print(cov[cov.index >= 2003].T.to_string())
    reg = c[(c.apps >= 10) & (c.grp != "GK")].copy()
    g = reg.groupby(["league_id", "y", "grp"]).gi
    reg["n_grp"] = g.transform("size")
    reg = reg[reg.n_grp >= 8].copy()
    reg["z"] = (reg.apps / (reg.apps + 12)) * (reg.gi - g.transform("mean")) / g.transform("std").replace(0, np.nan)
    t5 = reg[reg.league_id.isin(TOP5) & (reg.grp == "ATT")]
    cols = ["name", "y", "league_name", "team", "age", "apps", "goals", "assists", "z"]
    pd.set_option("display.width", 200)
    print("\nBest attacker seasons at age 22 or younger, top five leagues, all years (z within league and season):")
    print(t5[t5.age <= 22.5].sort_values("z", ascending=False)[cols].head(15).round(2).to_string(index=False))
    for who in ["Cristiano Ronaldo", "Antonio Nusa"]:
        w = reg[reg.name == who].sort_values("y")[cols]
        print(f"\n{who}:")
        print(w.round(2).to_string(index=False) if len(w) else "  not among the loaded profiles yet")
    reg[["player_id", "y", "league_id", "grp", "age", "apps", "goals", "assists", "z"]].to_csv("data/result_historical_profile.csv", index=False)


if __name__ == "__main__":
    main()
