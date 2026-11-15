"""Test 8: dropout. How often does a regular stop being a regular?

Cohort without look-ahead: every player with >= 900 minutes in a men's league
season ending in year y. Outcome the next year, in any covered league:
regular (>= 900 min), fringe (270-899), out (< 270 or absent from the data).
"Out" mixes retirement, long injury and moves to leagues we do not cover.

Age needs a profile. Profiles are still downloading and the loaded ones lean
towards players with long careers, so the age table is scaled to match the
overall rate, which uses all players.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    s = con.execute("""
        select s.player_id, se.end_year y, max(s.minutes) m
        from fm_stats s join fm_seasons se using (league_id, season_id) join fm_leagues l using (league_id)
        where s.stat='mins_played' and l.gender='male' and l.name not ilike '%cup%' and l.name not ilike '%pokal%'
          and l.name not ilike '%copa%' and l.name not ilike '%coppa%' and l.name not ilike '%trophy%'
        group by 1,2""").fetchdf()
    # a league must be covered in both years, otherwise "out" is just missing coverage
    cov = con.execute("""select league_id, end_year y from fm_stats s join fm_seasons se using (league_id, season_id)
                         where s.stat='mins_played' group by 1,2""").fetchdf()
    lg = con.execute("""select s.player_id, se.end_year y, arg_max(s.league_id, s.minutes) league_id
                        from fm_stats s join fm_seasons se using (league_id, season_id) where s.stat='mins_played' group by 1,2""").fetchdf()
    covset = set(zip(cov.league_id, cov.y))
    birth = con.execute("select player_id, year(birth) + dayofyear(birth)/365.25 as byear from fm_profiles where birth is not null").fetchdf()
    base = s[(s.m >= 900) & s.y.between(2022, 2025)].merge(lg, on=["player_id", "y"])
    base = base[[(l, y + 1) in covset for l, y in zip(base.league_id, base.y)]]
    nxt = s.rename(columns={"m": "m1"}).assign(y=lambda d: d.y - 1)
    nx2 = s.rename(columns={"m": "m2"}).assign(y=lambda d: d.y - 2)
    d = base.merge(nxt, on=["player_id", "y"], how="left").merge(nx2, on=["player_id", "y"], how="left").fillna({"m1": 0, "m2": 0})
    d["out1"] = d.m1 < 270
    d["fringe1"] = (d.m1 >= 270) & (d.m1 < 900)
    d["gone2"] = (d.m1 < 270) & (d.m2 < 270) & (d.y <= 2024)
    print(f"cohort: {len(d)} regular player-seasons 2022-2025")
    print(f"next year: regular {100*(d.m1>=900).mean():.0f} %, fringe {100*d.fringe1.mean():.0f} %, out {100*d.out1.mean():.0f} %")
    d2 = d[d.y <= 2024]
    print(f"out two years running: {100*d2.gone2.mean():.0f} % (of {len(d2)})")
    print(f"of those out one year, back as regular the year after: {100*(d2[d2.out1].m2>=900).mean():.0f} %")
    a = d.merge(birth, on="player_id")
    a["age"] = np.floor(a.y - 0.5 - a.byear).astype(int)
    print(f"with age: {len(a)} ({100*len(a)/len(d):.0f} %)  out-rate with age {100*a.out1.mean():.1f} % vs all {100*d.out1.mean():.1f} %")
    scale = d.out1.mean() / a.out1.mean()
    t = a[a.age.between(17, 37)].groupby("age").agg(n=("out1", "size"), out=("out1", "mean"), fringe=("fringe1", "mean"))
    t["out_scaled"] = (t.out * scale).clip(upper=1)
    t["regular"] = 1 - t.out_scaled - t.fringe
    print((t * [1, 100, 100, 100, 100]).round(0).astype(int).T.to_string())
    haz = t.out_scaled
    haz.to_csv("data/result_dropout_hazard.csv")
    # two-year "gone" hazard is the better proxy for leaving the game; scale the one-year rate
    k = d2.gone2.mean() / d2.out1.mean()
    for start in [19, 21, 23, 25]:
        surv = 1.0; out = []
        for age in range(start, 35):
            if age in (start + 4, start + 8) : out.append(f"{age}: {100*surv:.0f} %")
            surv *= 1 - k * haz.get(age, haz.iloc[-1])
        print(f"regular at {start} -> still in the data at", ", ".join(out))


if __name__ == "__main__":
    main()
