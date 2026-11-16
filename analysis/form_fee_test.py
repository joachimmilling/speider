"""Test 24: does performance leading up to a sale move the fee, beyond the market value on the day?

Ablation of the fee model (ratio target, as on the site): market value and age only; site inputs without performance;
site inputs; site inputs plus the change in form from the season before. Fit to 2024, test on 2025-26.
Writes data/result_form_fee.json.
"""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from price_model_v4 import INDEX
from projection_v3 import KW, STATS
from site_models import PF, err
from transfers import load


def main() -> None:
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    prev = b[["player_id", "y", "rating", "lmin", "goals_per_90", "expected_goals_per_90", "expected_assists_per_90", "last_rating", "last_apps"]].copy(); prev["y"] += 1
    b = b.merge(prev, on=["player_id", "y"], how="left", suffixes=("", "_p"))
    b["d_rating"] = b.rating - b.rating_p; b["d_min"] = b.lmin - b.lmin_p; b["d_goal"] = b.goals_per_90 - b.goals_per_90_p
    b["d_xg"] = b.expected_goals_per_90 - b.expected_goals_per_90_p; b["d_xa"] = b.expected_assists_per_90 - b.expected_assists_per_90_p
    b["d_last_rating"] = b.last_rating - b.last_rating_p; b["d_apps"] = b.last_apps - b.last_apps_p
    FORM = ["d_rating", "d_min", "d_goal", "d_xg", "d_xa", "d_last_rating", "d_apps"]
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    t = load(con).drop(columns=["name"]); t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    m = t.merge(b, on=["player_id", "y"]); m["val"] = np.log(m.mv); m["ratio"] = np.log(m.fee / m.yy.map(INDEX) * 100) - m.val
    PERF = [f for f in PF if f in STATS + ["lmin", "last_rating", "last_apps", "last_goals"]]
    sets = {"0 value and age": ["val", "age"], "1 site inputs without performance": [f for f in PF if f not in PERF], "2 site inputs": PF, "3 site inputs + form": PF + FORM}
    tr, te = m[m.yy <= 2024], m[m.yy >= 2025]
    scale = te.yy.map(INDEX).values / 100
    res = dict(n_train=len(tr), n_test=len(te), performance_inputs=PERF, third_party_miss=round(err(te.mv.values, te.fee.values), 3), miss={}, miss_attackers={}, miss_with_stats={})
    att = te.role_c.isin([c for c in te.role_c.unique() if str(c) in ("ST", "W", "AM", "4", "5", "6")]).values if "role_c" in te else None
    has = te.rating.notna().values
    for name, f in sets.items():
        p = np.exp(HGBR(loss="absolute_error", **KW).fit(tr[f], tr.ratio).predict(te[f]) + te.val.values) * scale
        res["miss"][name] = round(err(p, te.fee.values), 3); res["miss_with_stats"][name] = round(err(p[has], te.fee.values[has]), 3)
    res["n_test_with_stats"] = int(has.sum())
    # plain reading: fee / market value by change in form, for players with numbers in both seasons
    d = m[m.d_rating.notna()].copy(); res["form_table"] = {}
    for col, lab in (("d_rating", "rating change"), ("d_min", "minutes change"), ("d_goal", "goals per 90 change")):
        q = pd.qcut(d[col].rank(method="first"), 3, labels=["fell", "same", "rose"])
        res["form_table"][lab] = {k: dict(n=int((q == k).sum()), fee_over_value=round(float(np.exp(d.ratio[q == k].median())), 2)) for k in ("fell", "same", "rose")}
    lv = pd.qcut(d.rating.rank(method="first"), 3, labels=["low", "middle", "high"])
    res["level_table"] = {k: dict(n=int((lv == k).sum()), fee_over_value=round(float(np.exp(d.ratio[lv == k].median())), 2)) for k in ("low", "middle", "high")}
    res["corr_ratio"] = {c: round(float(d[c].corr(d.ratio, method="spearman")), 3) for c in ("rating", "d_rating", "d_min", "d_goal", "lmin")}
    json.dump(res, open("data/result_form_fee.json", "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
