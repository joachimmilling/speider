"""Calibration data for the three-year projection: predicted against actual.

Fits the test-14 models for h = 3 on seasons before 2023 and scores the
2022/23 season (outcome 2026). Writes two tables: by age and by predicted
growth decile.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from growth_model import SHAPE, STATS, build

KW = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0)
H = 3


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    d, val, mins = build(con)
    d = d[d.age.between(16, 34)].copy()
    full = ["age", "lv", "role_c", "height", "league_strength", "team_q", "lmin", "car_apps"] + STATS
    fut = val.rename(columns={"lv": "lv_f"}).assign(ey=lambda x: x.y - H)[["player_id", "ey", "lv_f"]]
    x = d.merge(fut, on=["player_id", "ey"], how="left"); x["growth"] = x.lv_f - x.lv
    tr, te = x[(x.ey < 2023) & (x.ey >= 2018) & x.growth.notna()], x[(x.ey == 2023) & x.growth.notna()].copy()
    for a in (0.1, 0.5, 0.9):
        te[f"q{int(a*100)}"] = HGBR(loss="quantile", quantile=a, categorical_features=[full.index("role_c")], **KW).fit(tr[full], tr.growth).predict(te[full])
    te["a"] = np.floor(te.age).astype(int)
    e = lambda s: float(np.exp(s))
    by_age = te[te.a.between(17, 33)].groupby("a").apply(lambda g: pd.Series(dict(
        n=len(g), pred_low=e(g.q10.median()), pred=e(g.q50.median()), pred_high=e(g.q90.median()),
        act_low=e(g.growth.quantile(.1)), act=e(g.growth.median()), act_high=e(g.growth.quantile(.9)),
        inside=float(((g.growth >= g.q10) & (g.growth <= g.q90)).mean())))).round(3)
    te["dec"] = pd.qcut(te.q50, 10, labels=False) + 1
    by_dec = te.groupby("dec").apply(lambda g: pd.Series(dict(n=len(g), pred=e(g.q50.median()), act=e(g.growth.median()),
        act_low=e(g.growth.quantile(.1)), act_high=e(g.growth.quantile(.9)), pred_low=e(g.q10.median()), pred_high=e(g.q90.median())))).round(3)
    by_age.to_csv("data/result_projection_by_age.csv"); by_dec.to_csv("data/result_projection_by_decile.csv")
    pd.set_option("display.width", 200)
    print(by_age.to_string()); print(by_dec.to_string())
    print("n test", len(te), "overall inside", round(float(((te.growth >= te.q10) & (te.growth <= te.q90)).mean()), 3))


if __name__ == "__main__":
    main()
