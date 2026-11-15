"""Test 1: do shrunk numbers beat raw numbers when predicting next season?

Train (find shrinkage strength k per statistic) on season pairs ending <= 2024.
Test on pairs where the next season ends >= 2025. Same league both years.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

PER90 = ["accurate_pass", "ball_recovery", "defensive_contributions", "effective_clearance", "fouls",
         "total_tackle", "total_scoring_att", "accurate_long_balls", "interception", "won_contest",
         "ontarget_scoring_att", "poss_won_att_3rd", "outfielder_block", "expected_goals_per_90",
         "expected_assists_per_90", "goals_per_90", "rating"]


def role(code: int) -> str:
    if code == 11: return "K"
    if 30 <= code <= 59: return "F"
    if 60 <= code <= 89: return "M"
    return "A"


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    df = con.execute("""
        select s.stat, s.league_id, se.end_year y, s.player_id, s.value v, s.minutes m,
               cast(json_extract(p.positions,'$[0]') as int) pos
        from fm_stats s join fm_seasons se using (league_id, season_id)
        join fm_leagues l using (league_id) join fm_players p using (player_id)
        where l.gender='male' and s.stat in (select unnest(?)) and s.minutes >= 270 and isfinite(s.value)
    """, [PER90]).fetchdf()
    df["role"] = df.pos.fillna(0).astype(int).map(role)
    df = df.groupby(["stat", "league_id", "y", "player_id"], as_index=False).first()
    grp = df.groupby(["stat", "league_id", "y", "role"]).v
    df["mu"] = grp.transform("mean")
    nxt = df[["stat", "league_id", "y", "player_id", "v", "m", "mu"]].copy()
    nxt["y"] -= 1
    pairs = df.merge(nxt, on=["stat", "league_id", "y", "player_id"], suffixes=("", "2"))
    pairs = pairs[pairs.m2 >= 900]
    rows = []
    for stat, g in pairs.groupby("stat"):
        tr, te = g[g.y + 1 <= 2024], g[g.y + 1 >= 2025]
        if len(tr) < 500 or len(te) < 300:
            continue
        best = None
        for k in [0, 150, 300, 500, 800, 1200, 1800, 2700, 4000, 6000]:
            w = tr.m / (tr.m + k)
            e = np.sqrt(np.mean((tr.mu + w * (tr.v - tr.mu) - tr.v2) ** 2))
            if best is None or e < best[1]:
                best = (k, e)
        k = best[0]
        w = te.m / (te.m + k)
        pred = te.mu + w * (te.v - te.mu)
        rmse = lambda a: float(np.sqrt(np.mean((a - te.v2) ** 2)))
        lo = te.m < 900
        rows.append(dict(stat=stat, n_test=len(te), k=k,
                         rmse_raw=rmse(te.v), rmse_shrunk=rmse(pred), rmse_mean=rmse(te.mu),
                         improvement_pct=round(100 * (1 - rmse(pred) / rmse(te.v)), 1),
                         improvement_under900=round(100 * (1 - np.sqrt(np.mean((pred[lo] - te.v2[lo]) ** 2)) /
                                                         np.sqrt(np.mean((te.v[lo] - te.v2[lo]) ** 2))), 1) if lo.sum() > 50 else None,
                         n_under900=int(lo.sum()),
                         r_raw=round(float(np.corrcoef(te.v, te.v2)[0, 1]), 3),
                         r_shrunk=round(float(np.corrcoef(pred, te.v2)[0, 1]), 3)))
    out = pd.DataFrame(rows).sort_values("improvement_pct", ascending=False)
    pd.set_option("display.width", 250)
    print(out.round(3).to_string(index=False))
    out.to_csv("data/result_shrinkage.csv", index=False)


if __name__ == "__main__":
    main()
