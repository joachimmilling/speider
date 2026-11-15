"""Test 11: the career curve with dropout built in.

Test 4 gives the value path of players who stay in the data (survivors).
Test 8 gives the yearly probability of dropping out by age. Combined:
expected value at age a = value if still playing x probability of still playing.

Reruns the chained age curve on all loaded profiles and multiplies in survival.
Dropout hazard: one-year "out" rate by age, scaled to the two-year "gone" rate
(a player out one year often returns).
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

GONE_SHARE = 0.66   # share of one-year "out" that is still out the year after (test 8: 12 % / 18 %)


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    df = con.execute("""
      with g as (select unnest(range(2021, 2027)) y),
      s as (select m.player_id, g.y, arg_min(m.value, abs(datediff('day', m.date, make_date(g.y,6,30)))) v
            from fm_mv m, g where m.value > 0 and abs(datediff('day', m.date, make_date(g.y,6,30))) <= 100 group by 1,2)
      select s.player_id, s.y, ln(s.v) lv, floor(datediff('day', p.birth, make_date(s.y,6,30))/365.25)::int a
      from s join fm_profiles p using (player_id) where p.birth is not null and p.gender='male'
    """).fetchdf()
    nx = df[["player_id", "y", "lv"]].copy(); nx["y"] -= 1
    t = df.merge(nx, on=["player_id", "y"], suffixes=("", "1"))
    t["d"] = t.lv1 - t.lv
    step = t[t.a.between(16, 37)].groupby("a").d.agg(["median", lambda s: s.quantile(.1), lambda s: s.quantile(.9), "size"])
    step.columns = ["med", "p10", "p90", "n"]
    haz = pd.read_csv("data/result_dropout_hazard.csv", index_col=0).iloc[:, 0] * GONE_SHARE
    rows = []
    for start in (19, 21, 24):
        lv, surv = 0.0, 1.0
        for a in range(start, 36):
            rows.append(dict(start=start, age=a, value_if_playing=np.exp(lv), still_playing=surv, expected=np.exp(lv) * surv))
            lv += step.med.get(a, step.med.iloc[-1]); surv *= 1 - haz.get(a, haz.iloc[-1])
    out = pd.DataFrame(rows)
    out.to_csv("data/result_career_curve_dropout.csv", index=False)
    pd.set_option("display.width", 200)
    for start, g in out.groupby("start"):
        g = g[g.age.isin([start, start + 2, start + 4, start + 6, start + 8, start + 10, start + 12])]
        print(f"\nStart age {start} (value = 1.00 at start):")
        print(g.set_index("age")[["value_if_playing", "still_playing", "expected"]].round(2).T.to_string())
    peak = out.loc[out.groupby("start").expected.idxmax()][["start", "age", "expected"]]
    peak2 = out.loc[out.groupby("start").value_if_playing.idxmax()][["start", "age", "value_if_playing"]]
    print("\nPeak age, survivors only:", dict(zip(peak2.start, peak2.age)), " with dropout:", dict(zip(peak.start, peak.age)))
    print(f"transitions used: {int(step.n.sum())}")


if __name__ == "__main__":
    main()
