"""Test 2b: prisindeks med alder holdt fast (alder, alder^2, ung/gammel-knekk)."""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from prisindeks import fit


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    con.execute("""
      create temp table tl as
      select team_id, arg_max(league_id, end_year) league_id from fm_teams t
      join fm_seasons using (league_id, season_id) join fm_leagues l using (league_id)
      where l.gender='male' and l.name not ilike '%cup%' and l.name not ilike '%pokal%' and l.name not ilike '%copa%'
        and l.name not ilike '%coppa%' and l.name not ilike '%trophy%' group by 1""")
    b = con.execute("""
      select t.player_id, year(t.date) y, t.fee, coalesce(t.pos,'?') pos,
             coalesce(cast(f.league_id as varchar),'ukjent') fra, coalesce(cast(k.league_id as varchar),'ukjent') til,
             datediff('day', p.birth, t.date)/365.25 age,
             datediff('day', t.date, t.contract_to)/365.25 kontrakt
      from fm_transfers t left join tl f on f.team_id=t.from_id left join tl k on k.team_id=t.to_id
      left join fm_profiles p using (player_id)
      where t.fee >= 50000 and not t.loan and not t.extension
    """).fetchdf()
    print("overganger:", len(b), " med alder:", int(b.age.notna().sum()))
    print("medianalder per år:", b.dropna(subset=["age"]).groupby("y").age.median().round(1).to_dict())
    m = b.dropna(subset=["age"]).copy()
    m["age2"] = (m.age - 25) ** 2
    m["ung"] = np.clip(22 - m.age, 0, None)
    A = fit(m, ["fra", "til", "pos"], [])
    B = fit(m, ["fra", "til", "pos"], ["age", "age2", "ung"])
    for navn, idx in [("Uten alder (samme utvalg)", A), ("Med alder", B)]:
        lvl = np.exp(idx - idx.iloc[-1]) * 100
        d = np.diff(idx.values); drift, sd = d.mean(), d.std(ddof=1)
        print(f"\n{navn} (n={idx.attrs['n']}, R2={idx.attrs['r2']:.2f})")
        print("  indeks:", {int(k): round(float(v)) for k, v in lvl.items()})
        print(f"  vekst per år {100*(np.exp(drift)-1):.1f} %, sd {100*sd:.0f}")
        for h in [3, 8]:
            print(f"  {2026+h}: {100*np.exp(drift*h):.0f} ({100*np.exp(drift*h-1.28*sd*np.sqrt(h)):.0f}–{100*np.exp(drift*h+1.28*sd*np.sqrt(h)):.0f})")


if __name__ == "__main__":
    main()
