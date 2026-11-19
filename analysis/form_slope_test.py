"""Test 27: one slope for running form on honest (out-of-fold) errors of the fee model. Writes data/result_form_slope.json."""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR
from sklearn.model_selection import KFold

from current_season import for_transfers, rows
from form_adjust_test import NF, seasons
from projection_v3 import KW
import fee_model
from fee_model import PFA
from site_models import err


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    cur = rows(con); S = seasons(con, cur)
    d = S[S.dv.notna() & S.age.notna() & (S.cur_min >= 450) & (S.ey <= 2024)]
    now_m, base_m = HGBR(**KW).fit(d[NF], d.dv), HGBR(**KW).fit(d[["age", "lv0"]], d.dv)
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    t, _, _ = fee_model.frame(con, b)              # the site's fee model (analysis/fee_model.py), not a copy
    cur["team_max"] = cur.groupby(["ey", "team_id"]).cur_min.transform("max")
    m = for_transfers(t, cur).sort_values(["date", "player_id", "fee"], kind="stable").reset_index(drop=True)
    m["ey_run"] = np.where(m.mo >= 7, m.yy + 1, m.yy)
    prev = S[["player_id", "ey", "cur_rating", "share"]].rename(columns={"cur_rating": "p_rating", "share": "p_share", "ey": "ey_run"}); prev["ey_run"] += 1
    m = m.merge(prev, on=["player_id", "ey_run"], how="left")
    m["share"] = (m.cur_min / m.team_max).clip(upper=1); m["lv0"] = m.val; m["d_rating"] = m.cur_rating - m.p_rating
    ok = m.cur_min >= 270; w = m.cur_min / (m.cur_min + 900)
    m["excess"] = 0.0; m.loc[ok, "excess"] = (w[ok] * (now_m.predict(m.loc[ok, NF]) - base_m.predict(m.loc[ok, ["age", "lv0"]]))).values
    tr, te = m[m.yy <= 2024].reset_index(drop=True), m[m.yy >= 2025].reset_index(drop=True)
    oof = np.zeros(len(tr))
    for a, c in KFold(5, shuffle=True, random_state=0).split(tr):
        oof[c] = fee_model.fit(tr.loc[a], n=10).predict(tr.loc[c, PFA])
    res_tr = (tr.ratio - oof).values; k = (tr.cur_min >= 270).values
    x, y = tr.excess.values[k], res_tr[k]
    slope = float((x * y).sum() / (x * x).sum())
    rng = np.random.default_rng(0); bs = []
    for _ in range(2000):
        i = rng.integers(0, len(x), len(x)); bs.append((x[i] * y[i]).sum() / (x[i] * x[i]).sum())
    a_te = fee_model.predict(fee_model.fit(tr), te); has = (te.cur_min >= 270).values; fee = te.fee.values
    f0, f1 = np.exp(a_te), np.exp(a_te + slope * te.excess.values)
    e_te = np.log(fee) - a_te
    q = pd.qcut(pd.Series(te.excess.values[has]).rank(method="first"), 3, labels=["low", "middle", "high"])
    res = dict(n_fit=int(k.sum()), n_test_running=int(has.sum()), slope=round(slope, 3), slope_90=[round(float(np.quantile(bs, 0.05)), 3), round(float(np.quantile(bs, 0.95)), 3)],
               rank_train=round(float(pd.Series(x).corr(pd.Series(y), method="spearman")), 3), rank_test=round(float(pd.Series(te.excess.values[has]).corr(pd.Series(e_te[has]), method="spearman")), 3),
               miss=dict(site_model=dict(all=round(err(f0, fee), 3), running=round(err(f0[has], fee[has]), 3)), with_slope=dict(all=round(err(f1, fee), 3), running=round(err(f1[has], fee[has]), 3))),
               paid_over_model_by_form={g: dict(n=int((q == g).sum()), excess=round(float(np.exp(np.median(te.excess.values[has][q == g])) - 1), 3), paid_over_model=round(float(np.exp(np.median(e_te[has][q == g]))), 2)) for g in ("low", "middle", "high")})
    # one-sided: separate slopes for form above and below expectation, both from the training errors
    def side(k_):
        xs, ys = x[k_], y[k_]; sl = float((xs * ys).sum() / (xs * xs).sum()); bb = []
        for _ in range(2000):
            i = rng.integers(0, len(xs), len(xs)); bb.append((xs[i] * ys[i]).sum() / (xs[i] * xs[i]).sum())
        return dict(n=int(k_.sum()), slope=round(sl, 3), slope_90=[round(float(np.quantile(bb, 0.05)), 3), round(float(np.quantile(bb, 0.95)), 3)])
    up, down = side(x > 0), side(x < 0)
    s_up = up["slope"] if up["slope_90"][0] > 0 else 0.0; s_dn = down["slope"] if down["slope_90"][0] > 0 else 0.0
    ex = te.excess.values; f2 = np.exp(a_te + np.where(ex > 0, s_up * ex, s_dn * ex))
    res["one_sided"] = dict(above=up, below=down, used=[s_up, s_dn], miss=dict(all=round(err(f2, fee), 3), running=round(err(f2[has], fee[has]), 3)))
    res["one_sided"]["adopted"] = bool(s_up > 0 and res["miss"]["site_model"]["running"] - res["one_sided"]["miss"]["running"] >= 0.005 and res["one_sided"]["miss"]["all"] <= res["miss"]["site_model"]["all"])
    # Decision 49: the one-sided lift is used on the site when the slope above expectation is established on the training errors
    # and the miss on all transfers does not rise, also when the gain on the miss is below the 0.5-point bar.
    res["used_on_site"] = [s_up, s_dn] if s_up > 0 and res["one_sided"]["miss"]["all"] <= res["miss"]["site_model"]["all"] else [0.0, 0.0]
    res["relationship"] = bool(res["slope_90"][0] > 0 and res["rank_test"] > 0)
    res["adopted"] = bool(res["relationship"] and res["miss"]["site_model"]["running"] - res["miss"]["with_slope"]["running"] >= 0.005 and res["miss"]["with_slope"]["all"] <= res["miss"]["site_model"]["all"])
    json.dump(res, open("data/result_form_slope.json", "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
