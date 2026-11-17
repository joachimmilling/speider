"""Test 27: one slope for running form on honest (out-of-fold) errors of the fee model. Writes data/result_form_slope.json."""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR
from sklearn.model_selection import KFold

from current_season import for_transfers, rows
from form_adjust_test import NF, seasons
from price_model_v4 import INDEX
from projection_v3 import KW
from site_models import PF, err
from transfers import load


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    cur = rows(con); S = seasons(con, cur)
    d = S[S.dv.notna() & S.age.notna() & (S.cur_min >= 450) & (S.ey <= 2024)]
    now_m, base_m = HGBR(**KW).fit(d[NF], d.dv), HGBR(**KW).fit(d[["age", "lv0"]], d.dv)
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    t = load(con).drop(columns=["name"]); t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    ids = con.execute("select player_id, date, from_id from fm_transfers").fetchdf(); ids["date"] = pd.to_datetime(ids.date)
    t = t.merge(ids.drop_duplicates(["player_id", "date"]), on=["player_id", "date"], how="left")
    cur["team_max"] = cur.groupby(["ey", "team_id"]).cur_min.transform("max")
    m = for_transfers(t.merge(b, on=["player_id", "y"]), cur)
    m["val"] = np.log(m.mv); m["ratio"] = np.log(m.fee / m.yy.map(INDEX) * 100) - m.val; m["ey_run"] = np.where(m.mo >= 7, m.yy + 1, m.yy)
    prev = S[["player_id", "ey", "cur_rating", "share"]].rename(columns={"cur_rating": "p_rating", "share": "p_share", "ey": "ey_run"}); prev["ey_run"] += 1
    m = m.merge(prev, on=["player_id", "ey_run"], how="left")
    m["share"] = (m.cur_min / m.team_max).clip(upper=1); m["lv0"] = m.val; m["d_rating"] = m.cur_rating - m.p_rating
    ok = m.cur_min >= 270; w = m.cur_min / (m.cur_min + 900)
    m["excess"] = 0.0; m.loc[ok, "excess"] = (w[ok] * (now_m.predict(m.loc[ok, NF]) - base_m.predict(m.loc[ok, ["age", "lv0"]]))).values
    tr, te = m[m.yy <= 2024].reset_index(drop=True), m[m.yy >= 2025].reset_index(drop=True)
    oof = np.zeros(len(tr))
    for a, c in KFold(5, shuffle=True, random_state=0).split(tr):
        oof[c] = HGBR(loss="absolute_error", **KW).fit(tr.loc[a, PF], tr.ratio[a]).predict(tr.loc[c, PF])
    res_tr = (tr.ratio - oof).values; k = (tr.cur_min >= 270).values
    x, y = tr.excess.values[k], res_tr[k]
    slope = float((x * y).sum() / (x * x).sum())
    rng = np.random.default_rng(0); bs = []
    for _ in range(2000):
        i = rng.integers(0, len(x), len(x)); bs.append((x[i] * y[i]).sum() / (x[i] * x[i]).sum())
    A = HGBR(loss="absolute_error", **KW).fit(tr[PF], tr.ratio); a_te = A.predict(te[PF]); has = (te.cur_min >= 270).values
    scale = te.yy.map(INDEX).values / 100; fee = te.fee.values
    f0, f1 = np.exp(a_te + te.val.values) * scale, np.exp(a_te + slope * te.excess.values + te.val.values) * scale
    e_te = (te.ratio.values - a_te)
    q = pd.qcut(pd.Series(te.excess.values[has]).rank(method="first"), 3, labels=["low", "middle", "high"])
    res = dict(n_fit=int(k.sum()), n_test_running=int(has.sum()), slope=round(slope, 3), slope_90=[round(float(np.quantile(bs, 0.05)), 3), round(float(np.quantile(bs, 0.95)), 3)],
               rank_train=round(float(pd.Series(x).corr(pd.Series(y), method="spearman")), 3), rank_test=round(float(pd.Series(te.excess.values[has]).corr(pd.Series(e_te[has]), method="spearman")), 3),
               miss=dict(site_model=dict(all=round(err(f0, fee), 3), running=round(err(f0[has], fee[has]), 3)), with_slope=dict(all=round(err(f1, fee), 3), running=round(err(f1[has], fee[has]), 3))),
               paid_over_model_by_form={g: dict(n=int((q == g).sum()), excess=round(float(np.exp(np.median(te.excess.values[has][q == g])) - 1), 3), paid_over_model=round(float(np.exp(np.median(e_te[has][q == g]))), 2)) for g in ("low", "middle", "high")})
    res["relationship"] = bool(res["slope_90"][0] > 0 and res["rank_test"] > 0)
    res["adopted"] = bool(res["relationship"] and res["miss"]["site_model"]["running"] - res["miss"]["with_slope"]["running"] >= 0.005 and res["miss"]["with_slope"]["all"] <= res["miss"]["site_model"]["all"])
    json.dump(res, open("data/result_form_slope.json", "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
