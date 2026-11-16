"""Historical profile v1: output standardised against full squads of the time.

v0 compared old seasons with the survivors we had profiles for. v1 uses
SofaScore season lists, which hold every squad member of each league season
(big five and Eredivisie back to 2001/02, 15 more leagues from 2013/14).

Measure: non-penalty goals per 90 (assists are unreliable before ~2010), plus
goals + assists per 90 where assists exist. Standardised among outfield
regulars (>= 900 min) in the same league and season. No position is available
in this source, so the comparison group is all outfield regulars.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

BIG5 = (17, 8, 35, 23, 34)


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    s = con.execute("""
        select s.tournament_id, coalesce(t.name, h.name) league, s.end_year y, s.player_id, s.player, s.team,
               s.minutesPlayed m, s.appearances apps, coalesce(s.goals,0) goals, coalesce(s.penaltyGoals,0) pens,
               coalesce(s.assists,0) assists, s.totalShots shots, s.rating
        from ss_stats s left join (select tournament_id, name from ss_tournaments where name is not null) t using (tournament_id)
        left join (select tournament_id, name from ss_tournaments where history) h using (tournament_id)
        where s.minutesPlayed >= 900 and coalesce(s.saves,0) < 20
    """).fetchdf().drop_duplicates(["tournament_id", "y", "player_id"])
    s["npg90"] = (s.goals - s.pens) / s.m * 90
    s["ga90"] = (s.goals - s.pens + s.assists) / s.m * 90
    g = s.groupby(["tournament_id", "y"])
    s["n"] = g.npg90.transform("size")
    s = s[s.n >= 100].copy()
    g = s.groupby(["tournament_id", "y"])
    for c in ("npg90", "ga90"):
        s[c + "_z"] = (s[c] - g[c].transform("mean")) / g[c].transform("std")
        s[c + "_pct"] = g[c].rank(pct=True) * 100
    assists_ok = g.assists.transform(lambda x: (x > 0).mean()) > 0.25
    s.loc[~assists_ok, ["ga90_z", "ga90_pct"]] = np.nan
    cov = s.groupby("y").agg(leagues=("tournament_id", "nunique"), regulars=("player_id", "size"), with_assists=("ga90_z", lambda x: int(x.notna().sum())))
    print("Coverage, outfield regulars per season end year:")
    print(cov.T.to_string())
    pd.set_option("display.width", 220)
    cols = ["player", "y", "league", "team", "m", "goals", "pens", "assists", "npg90", "npg90_z", "npg90_pct", "ga90_z"]
    b5 = s[s.tournament_id.isin(BIG5)]
    print("\nBest non-penalty scoring seasons in the big five since 2001/02 (z within league and season):")
    print(b5.sort_values("npg90_z", ascending=False)[cols].head(12).round(2).to_string(index=False))
    for who, yrs in [("Cristiano Ronaldo", (2007, 2008, 2009)), ("Antonio Nusa", (2025, 2026))]:
        w = s[(s.player == who) & s.y.isin(yrs)].sort_values("y")
        print(f"\n{who}:")
        print(w[cols].round(2).to_string(index=False) if len(w) else "  not found by exact name")
    print("\nSame scale, different eras: mean league scoring rate (non-penalty goals per 90, outfield regulars), big five")
    print(b5.groupby("y").npg90.mean().round(3).iloc[::3].to_dict())
    s[["tournament_id", "y", "player_id", "player", "m", "npg90", "npg90_z", "npg90_pct", "ga90_z"]].to_csv("data/result_historical_profile_v1.csv", index=False)


if __name__ == "__main__":
    main()
