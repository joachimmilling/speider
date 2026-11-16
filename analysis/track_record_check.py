"""Test 17: is the club/league/nation track record real, or an artefact of the value provider?

Test 16 measured growth with third-party values. Here the same inputs are
scored on outcomes that do not come from the provider, for players of 23 or
younger, three years ahead (train on years up to 2021, test on 2023):

  (1) plays in a big-five league (at least 10 matches in the season three years later),
      among players not there today
  (2) change in the strength of the league he plays in
  (3) the fee actually paid, for those sold within three years (price-index adjusted)

Each is predicted with and without the three track-record inputs.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as HGBC, HistGradientBoostingRegressor as HGBR
from sklearn.metrics import roc_auc_score

from projection_young import C, D

INDEX = {2015: 70, 2016: 79, 2017: 88, 2018: 93, 2019: 95, 2020: 82, 2021: 79, 2022: 81, 2023: 89, 2024: 84, 2025: 95, 2026: 100}
KW = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0)
TR = ["club_track", "nation_track", "league_track"]


def main() -> None:
    b = pd.read_pickle("data/frame_wide.pkl")
    b = b[b.age <= 23.5].copy()
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    t = con.execute("select player_id, date, fee from fm_transfers where fee >= 50000 and not loan and not extension").fetchdf()
    t["date"] = pd.to_datetime(t.date); t["real"] = np.log(t.fee / t.date.dt.year.map(INDEX).fillna(70) * 100)
    k = b[["player_id", "y"]].merge(t, on="player_id")
    cut = pd.to_datetime(k.y.astype(str) + "-06-30")
    k = k[(k.date > cut) & (k.date <= cut + pd.DateOffset(years=3))].sort_values("date").groupby(["player_id", "y"]).real.first().rename("fee_real").reset_index()
    b = b.merge(k, on=["player_id", "y"], how="left")
    b["not_top5_now"] = ~(b.last_strength >= 0.25)
    b["top5_later"] = (b.top5_f3.fillna(0) >= 10).astype(int)
    b["step"] = b.str_f3 - b.last_strength
    b["fee_vs_value"] = b.fee_real - np.log(np.exp(b.lv) / b.y.map(INDEX) * 100)
    tr, te = b[b.y <= 2021], b[b.y == 2023]
    rows = []
    a, e = tr[tr.not_top5_now], te[te.not_top5_now]
    for name, cols in (("without track record", C), ("with track record", D)):
        p = HGBC(**KW).fit(a[cols], a.top5_later).predict_proba(e[cols])[:, 1]
        top = e.top5_later[p >= np.quantile(p, .9)].mean()
        rows.append(dict(outcome="(1) big-five league in three years", inputs=name, n=len(e), base_rate=round(100 * e.top5_later.mean(), 1), auc=round(roc_auc_score(e.top5_later, p), 3), rate_in_top_tenth=round(100 * top, 1)))
    a, e = tr[tr.step.notna()], te[te.step.notna()]
    for name, cols in (("without track record", C), ("with track record", D)):
        p = HGBR(**KW).fit(a[cols], a.step).predict(e[cols])
        rows.append(dict(outcome="(2) change in league strength", inputs=name, n=len(e), r2=round(1 - ((e.step - p) ** 2).mean() / e.step.var(), 3), rank=round(pd.Series(p, index=e.index).corr(e.step, method="spearman"), 3)))
    a, e = tr[tr.fee_real.notna()], te[te.fee_real.notna()]
    for name, cols in (("without track record", C), ("with track record", D)):
        p = HGBR(**KW).fit(a[cols], a.fee_real).predict(e[cols])
        rows.append(dict(outcome="(3) fee paid within three years", inputs=name, n=len(e), r2=round(1 - ((e.fee_real - p) ** 2).mean() / e.fee_real.var(), 3),
                         rank=round(pd.Series(p, index=e.index).corr(e.fee_real, method="spearman"), 3), median_err_pct=round(100 * (np.exp(np.median(np.abs(e.fee_real - p))) - 1))))
    pd.set_option("display.width", 220)
    print(pd.DataFrame(rows).fillna("").to_string(index=False))
    e = te[te.fee_real.notna()]
    print("\nSold players in the test year: correlation of each track record with fee relative to value at the start (rank):")
    print({c: round(e[c].corr(e.fee_vs_value, method="spearman"), 3) for c in TR}, "n =", len(e))
    q = e.assign(g=pd.qcut(e.club_track.rank(method="first"), 4, labels=["lowest", "2", "3", "highest"])).groupby("g", observed=True).fee_vs_value.median()
    print("median fee / value by club track-record quarter:", {k_: round(float(np.exp(v)), 2) for k_, v in q.items()})
    pd.DataFrame(rows).to_csv("data/result_track_record_check.csv", index=False)


if __name__ == "__main__":
    main()
