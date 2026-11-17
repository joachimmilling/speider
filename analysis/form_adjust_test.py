"""Test 26: a few-parameter form adjustment on top of the fee model. Writes data/result_form_adjust.json."""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR
from sklearn.linear_model import RidgeCV

from current_season import for_transfers, rows
from price_model_v4 import INDEX
from projection_v3 import KW
from site_models import PF, err
from transfers import load

NF = ["age", "lv0", "share", "cur_rating", "cur_g90", "cur_xg90", "cur_xa90", "p_rating", "p_share", "d_rating"]


def seasons(con, cur: pd.DataFrame) -> pd.DataFrame:
    """One row per player and split-year season: what he did in it (over all clubs), his share of the busiest team-mate's minutes,
    the season before, and his third-party value before (1 August) and after (1 August the year after)."""
    c = cur.copy(); c["team_max"] = c.groupby(["ey", "team_id"]).cur_min.transform("max"); c["share"] = c.cur_min / c.team_max
    for k in ("cur_rating", "cur_g90", "cur_xg90", "cur_xa90"): c[k] = c[k] * c.cur_min
    g = c.groupby(["player_id", "ey"]).agg(cur_min=("cur_min", "sum"), share=("share", "sum"), **{k: (k, "sum") for k in ("cur_rating", "cur_g90", "cur_xg90", "cur_xa90")}).reset_index()
    for k in ("cur_rating", "cur_g90", "cur_xg90", "cur_xa90"): g[k] = (g[k] / g.cur_min).where(g[k] > 0)
    g["share"] = g.share.clip(upper=1)
    p = g[["player_id", "ey", "cur_rating", "share"]].rename(columns={"cur_rating": "p_rating", "share": "p_share"}); p["ey"] += 1
    g = g.merge(p, on=["player_id", "ey"], how="left"); g["d_rating"] = g.cur_rating - g.p_rating
    mv = con.execute("select player_id, year(date) + (month(date) >= 8)::int ey, ln(arg_max(value, date)) lv from fm_mv where value > 0 group by 1, 2").fetchdf()
    # mv.ey is the season a value falls in (August to July): the latest value of season ey - 1 goes into season ey, the latest of ey comes out of it
    g = g.merge(mv.assign(ey=mv.ey + 1).rename(columns={"lv": "lv0"}), on=["player_id", "ey"], how="left")
    g = g.merge(mv.rename(columns={"lv": "lv1"}), on=["player_id", "ey"], how="left")
    b = con.execute("select player_id, birth from fm_profiles where birth is not null").fetchdf()
    g = g.merge(b, on="player_id", how="left"); bd = pd.to_datetime(g.birth, errors="coerce"); g["age"] = g.ey - 0.5 - bd.dt.year - (bd.dt.month - 1) / 12
    g["dv"] = g.lv1 - g.lv0; g["dv"] -= g.groupby("ey").dv.transform("median")
    return g


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    cur = rows(con); S = seasons(con, cur)
    d = S[S.dv.notna() & S.age.notna() & (S.cur_min >= 450)]
    tr_s, te_s = d[d.ey <= 2024], d[d.ey.isin([2025, 2026])]
    res = dict(nowcast=dict(n_train=len(tr_s), n_test=len(te_s)))
    for name, f in (("age and value", ["age", "lv0"]), ("plus the season", NF)):
        p = HGBR(**KW).fit(tr_s[f], tr_s.dv).predict(te_s[f])
        res["nowcast"][name] = dict(r2=round(float(1 - ((te_s.dv - p) ** 2).sum() / ((te_s.dv - te_s.dv.mean()) ** 2).sum()), 3), rank=round(float(pd.Series(p).corr(pd.Series(te_s.dv.values), method="spearman")), 3))
    now_m = HGBR(**KW).fit(tr_s[NF], tr_s.dv); base_m = HGBR(**KW).fit(tr_s[["age", "lv0"]], tr_s.dv)

    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    t = load(con).drop(columns=["name"]); t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    ids = con.execute("select player_id, date, from_id from fm_transfers").fetchdf(); ids["date"] = pd.to_datetime(ids.date)
    t = t.merge(ids.drop_duplicates(["player_id", "date"]), on=["player_id", "date"], how="left")
    cur["team_max"] = cur.groupby(["ey", "team_id"]).cur_min.transform("max")
    m = for_transfers(t.merge(b, on=["player_id", "y"]), cur)
    m["val"] = np.log(m.mv); m["ratio"] = np.log(m.fee / m.yy.map(INDEX) * 100) - m.val
    m["ey_run"] = np.where(m.mo >= 7, m.yy + 1, m.yy)
    prev = S[["player_id", "ey", "cur_rating", "share", "cur_g90", "cur_xa90"]].rename(columns={"cur_rating": "p_rating", "share": "p_share", "cur_g90": "p_g90", "cur_xa90": "p_xa90", "ey": "ey_run"}); prev["ey_run"] += 1
    m = m.merge(prev, on=["player_id", "ey_run"], how="left")
    m["share"] = (m.cur_min / m.team_max).clip(upper=1); m["lv0"] = m.val; m["d_rating"] = m.cur_rating - m.p_rating
    w = m.cur_min / (m.cur_min + 900)
    m["f_rating"] = (w * (m.cur_rating - m.p_rating)).fillna(0); m["f_threat"] = (w * ((m.cur_g90 + m.cur_xa90) - (m.p_g90 + m.p_xa90))).fillna(0)
    # nowcast: expected revaluation given the season so far, minus what age and value alone would say; zero without a running season
    ok = (m.cur_min >= 270)
    m["nowcast"] = 0.0; m.loc[ok, "nowcast"] = now_m.predict(m.loc[ok, NF]) - base_m.predict(m.loc[ok, ["age", "lv0"]])
    tr, te = m[m.yy <= 2024].copy(), m[m.yy >= 2025].copy(); scale = te.yy.map(INDEX).values / 100
    A = HGBR(loss="absolute_error", **KW).fit(tr[PF], tr.ratio)
    tr["res"] = tr.ratio - A.predict(tr[PF]); a_te = A.predict(te[PF])            # in-sample residuals understate; the slope is still usable
    trr = tr[tr.cur_min >= 270]; has = (te.cur_min >= 270).values
    c1 = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(trr[["f_rating", "f_threat"]], trr.res)
    c2 = RidgeCV(alphas=np.logspace(-2, 3, 20), fit_intercept=True).fit(trr[["nowcast"]], trr.res)
    preds = {"A site model": a_te, "C1 two-input line": a_te + np.where(has, c1.predict(te[["f_rating", "f_threat"]]), 0), "C2 scaled nowcast": a_te + np.where(has, c2.predict(te[["nowcast"]]), 0)}
    res["fees"] = dict(n_fit=len(trr), n_test_running=int(has.sum()), c1_coef=[round(float(x), 3) for x in c1.coef_], c1_intercept=round(float(c1.intercept_), 3), c2_coef=round(float(c2.coef_[0]), 3), c2_intercept=round(float(c2.intercept_), 3), miss={})
    for k, p in preds.items():
        f = np.exp(p + te.val.values) * scale
        res["fees"]["miss"][k] = dict(all=round(err(f, te.fee.values), 3), running_season=round(err(f[has], te.fee.values[has]), 3))
    res["fees"]["rank_resid_running"] = {k: round(float(pd.Series(v[has]).corr(pd.Series((te.ratio.values - a_te)[has]), method="spearman")), 3) for k, v in (("f_rating", te.f_rating.values), ("nowcast", te.nowcast.values))}
    json.dump(res, open("data/result_form_adjust.json", "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
