"""Test 2: prisindeks for overgangsmarkedet, og fremskriving.

Indeksen er årseffekten i en regresjon på log(sum), der vi holder fast
hvem som selger, hvem som kjøper, posisjon og (versjon B) spillerens tall
sesongen før. Alder mangler foreløpig og legges inn når profilene er hentet.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd


def fit(df: pd.DataFrame, cats: list[str], nums: list[str]) -> pd.Series:
    X = [pd.get_dummies(df["y"], prefix="y", drop_first=True, dtype=float)]
    for c in cats:
        top = df[c].value_counts()
        keep = top[top >= 15].index
        X.append(pd.get_dummies(df[c].where(df[c].isin(keep), "annet"), prefix=c, drop_first=True, dtype=float))
    for n in nums:
        X.append(((df[n] - df[n].mean()) / df[n].std()).rename(n))
    X = pd.concat(X, axis=1)
    X.insert(0, "c", 1.0)
    beta, *_ = np.linalg.lstsq(X.values, np.log(df.fee.values), rcond=None)
    b = pd.Series(beta, index=X.columns)
    resid = np.log(df.fee.values) - X.values @ beta
    yrs = sorted(df.y.unique())
    idx = pd.Series({yrs[0]: 0.0, **{y: b[f"y_{y}"] for y in yrs[1:]}})
    idx.attrs["r2"] = 1 - resid.var() / np.log(df.fee).var()
    idx.attrs["n"] = len(df)
    return idx


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    con.execute("""
      create temp table tl as
      select team_id, arg_max(league_id, end_year) league_id from fm_teams t
      join fm_seasons using (league_id, season_id) join fm_leagues l using (league_id)
      where l.gender='male' and l.name not ilike '%cup%' and l.name not ilike '%pokal%' and l.name not ilike '%copa%'
        and l.name not ilike '%coppa%' and l.name not ilike '%trophy%' and l.name not ilike '%super%cup%'
      group by 1""")
    base = con.execute("""
      select t.player_id, t.date, year(t.date) y, month(t.date) mo, t.fee, coalesce(t.pos,'?') pos,
             coalesce(cast(f.league_id as varchar),'ukjent') fra, coalesce(cast(k.league_id as varchar),'ukjent') til
      from fm_transfers t left join tl f on f.team_id=t.from_id left join tl k on k.team_id=t.to_id
      where t.fee >= 50000 and not t.loan and not t.extension
    """).fetchdf()
    A = fit(base, ["fra", "til", "pos"], [])

    perf = con.execute("""
      with s as (
        select s.player_id, se.end_year ey, s.stat, max(s.value) v, max(s.minutes) m
        from fm_stats s join fm_seasons se using (league_id, season_id)
        where s.stat in ('rating','mins_played','_goals_and_goal_assist') group by 1,2,3)
      select player_id, ey, max(v) filter(where stat='rating') as rating,
             max(m) as minutes, coalesce(max(v) filter(where stat='_goals_and_goal_assist'),0) as ga
      from s group by 1,2 having max(m) >= 450 and max(v) filter(where stat='rating') is not null
    """).fetchdf()
    b2 = base.copy()
    b2["ey_max"] = np.where(b2.mo >= 6, b2.y, b2.y - 1)
    m = b2.merge(perf, on="player_id")
    m = m[m.ey <= m.ey_max].sort_values("ey").groupby(["player_id", "date"], as_index=False).last()
    m = m[m.ey >= m.ey_max - 1]
    m["lmin"] = np.log(m.minutes)
    m["ga90"] = m.ga / m.minutes * 90
    B = fit(m, ["fra", "til", "pos"], ["rating", "lmin", "ga90"])

    for navn, idx in [("A: uten prestasjon", A), ("B: med prestasjon sesongen før", B)]:
        lvl = np.exp(idx - idx.iloc[-1]) * 100
        d = np.diff(idx.values)
        drift, sd = d.mean(), d.std(ddof=1)
        print(f"\n{navn}  (n={idx.attrs['n']}, R2={idx.attrs['r2']:.2f})")
        print("  indeks (2026=100):", {int(k): round(float(v)) for k, v in lvl.items()})
        print(f"  snitt endring per år: {100*(np.exp(drift)-1):.1f} %, standardavvik {100*sd:.0f} %-poeng (log)")
        for h in [3, 5, 8]:
            mid = 100 * np.exp(drift * h)
            lo, hi = 100 * np.exp(drift * h - 1.28 * sd * np.sqrt(h)), 100 * np.exp(drift * h + 1.28 * sd * np.sqrt(h))
            print(f"  {2026+h}: {mid:.0f}  (80 %: {lo:.0f}–{hi:.0f})")
    raw = base.groupby("y").fee.median()
    print("\nRå median (mill.):", {int(k): round(v / 1e6, 2) for k, v in raw.items()})
    print("Antall per år:", base.groupby("y").size().to_dict())


if __name__ == "__main__":
    main()
