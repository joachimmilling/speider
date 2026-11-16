"""Test 15: fixing the three-year projection where the calibration plot showed it failing.

Failures seen: the youngest are under-predicted (17: 2.3x predicted, 5.4x
actual), the oldest over-predicted, and the upside of the interval is too
narrow for young players.

Variants, all scored on season 2022/23 (outcome 2026):
  V0  model from test 14
  V1  + momentum (value change over the last one and two years) and career
      path (debut age, senior matches, top-five and European matches)
  V2  V1 + young players weighted three times in training
  V3  V2 + calibration on a held-out year (2021/22): median shift and interval
      widening per age band (conformal)
V3 trains on seasons up to 2020/21 so the calibration year stays unseen.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from growth_model import STATS, build

KW = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0)
H = 3
BANDS = [(16, 19.999, "17-19"), (20, 21.999, "20-21"), (22, 24.999, "22-24"), (25, 28.999, "25-28"), (29, 40, "29+")]


def band(a):
    for lo, hi, n in BANDS:
        if lo <= a <= hi: return n
    return "29+"


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    d, val, mins = build(con)
    d = d[d.age.between(16, 34)].copy()
    v = val.copy()
    for k in (1, 2):
        p = v.rename(columns={"lv": f"lv_m{k}"}).assign(ey=lambda x: x.y + k)[["player_id", "ey", f"lv_m{k}"]]
        d = d.merge(p, on=["player_id", "ey"], how="left"); d[f"mom{k}"] = d.lv - d[f"lv_m{k}"]
    car = con.execute("""select c.player_id, c.end_year, c.league_id, c.league_name, c.apps, year(p.birth) by_
                         from fm_career c join fm_profiles p using (player_id) where c.end_year is not null and c.apps >= 1""").fetchdf()
    car["top5"] = car.league_id.isin([47, 87, 54, 55, 53]); car["europe"] = car.league_name.str.contains("Champions League|Europa League|Conference League", na=False)
    car["youth"] = car.league_name.str.contains(r"U1[0-9]|U2[0-9]|Youth|Primavera|Reserve|II$| B$", na=False)
    k = d[["player_id", "ey"]].merge(car, on="player_id"); k = k[k.end_year <= k.ey]
    k["sen_age"] = np.where(~k.youth & (k.apps >= 5), k.end_year - 0.5 - k.by_, np.nan)
    agg = k.groupby(["player_id", "ey"]).agg(debut_age=("sen_age", "min"), apps_top5=("apps", lambda s: s[k.loc[s.index, "top5"]].sum()),
                                             apps_europe=("apps", lambda s: s[k.loc[s.index, "europe"]].sum()),
                                             apps_youth=("apps", lambda s: s[k.loc[s.index, "youth"]].sum())).reset_index()
    d = d.merge(agg, on=["player_id", "ey"], how="left")
    fut = val.rename(columns={"lv": "lv_f"}).assign(ey=lambda x: x.y - H)[["player_id", "ey", "lv_f"]]
    x = d.merge(fut, on=["player_id", "ey"], how="left"); x["growth"] = x.lv_f - x.lv
    x = x[x.growth.notna() & (x.ey >= 2018)].copy(); x["band"] = x.age.map(band)
    f0 = ["age", "lv", "role_c", "height", "league_strength", "team_q", "lmin", "car_apps"] + STATS
    f1 = f0 + ["mom1", "mom2", "debut_age", "apps_top5", "apps_europe", "apps_youth"]
    te = x[x.ey == 2023].copy()

    def fit(tr, cols, w=None):
        return {a: HGBR(loss="quantile", quantile=a, categorical_features=[cols.index("role_c")], **KW).fit(tr[cols], tr.growth, sample_weight=w) for a in (0.1, 0.5, 0.9)}

    def pred(m, df, cols):
        return {a: mm.predict(df[cols]) for a, mm in m.items()}
    out = {}
    tr = x[x.ey <= 2022]
    out["V0"] = pred(fit(tr, f0), te, f0)
    out["V1"] = pred(fit(tr, f1), te, f1)
    out["V2"] = pred(fit(tr, f1, np.where(tr.age <= 21, 3.0, 1.0)), te, f1)
    tr3, cal = x[x.ey <= 2021], x[x.ey == 2022].copy()
    m3 = fit(tr3, f1, np.where(tr3.age <= 21, 3.0, 1.0))
    pc, pt = pred(m3, cal, f1), pred(m3, te, f1)
    v3 = {a: pt[a].copy() for a in pt}
    for _, _, b in BANDS:
        ci, ti = (cal.band == b).values, (te.band == b).values
        shift = float(np.median(cal.growth.values[ci] - pc[0.5][ci]))
        lo_gap = float(np.quantile(pc[0.1][ci] + shift - cal.growth.values[ci], 0.8))   # widen so 10 % fall below
        hi_gap = float(np.quantile(cal.growth.values[ci] - pc[0.9][ci] - shift, 0.8))
        # one-sided conformal: choose offsets so 10 % of the calibration year falls outside each side
        lo_off = float(np.quantile(cal.growth.values[ci] - (pc[0.1][ci]), 0.10))
        hi_off = float(np.quantile(cal.growth.values[ci] - (pc[0.9][ci]), 0.90))
        v3[0.5][ti] = pt[0.5][ti] + shift; v3[0.1][ti] = pt[0.1][ti] + lo_off; v3[0.9][ti] = pt[0.9][ti] + hi_off
    out["V3"] = v3
    y = te.growth.values
    rows = []
    for name, p in out.items():
        for b in ["17-19", "20-21", "22-24", "25-28", "29+", "all"]:
            i = np.ones(len(te), bool) if b == "all" else (te.band == b).values
            rows.append(dict(model=name, band=b, n=int(i.sum()), pred_x=round(float(np.exp(np.median(p[0.5][i]))), 2), actual_x=round(float(np.exp(np.median(y[i]))), 2),
                             bias_pct=round(100 * (np.exp(np.median(p[0.5][i] - y[i])) - 1)), inside_80=round(100 * float(np.mean((y[i] >= p[0.1][i]) & (y[i] <= p[0.9][i])))),
                             below=round(100 * float(np.mean(y[i] < p[0.1][i]))), above=round(100 * float(np.mean(y[i] > p[0.9][i]))),
                             r2=round(1 - float(((y[i] - p[0.5][i]) ** 2).mean() / y[i].var()), 2), med_err_pct=round(100 * (np.exp(np.median(np.abs(y[i] - p[0.5][i]))) - 1))))
    r = pd.DataFrame(rows); pd.set_option("display.width", 220)
    for b in ["17-19", "20-21", "22-24", "25-28", "29+", "all"]:
        print(r[r.band == b].to_string(index=False)); print()
    r.to_csv("data/result_projection_v2.csv", index=False)
    te = te.assign(a=np.floor(te.age).astype(int), q10=out["V3"][0.1], q50=out["V3"][0.5], q90=out["V3"][0.9])
    e = lambda s: float(np.exp(s))
    by = te[te.a.between(17, 33)].groupby("a").apply(lambda g: pd.Series(dict(n=len(g), pred_low=e(g.q10.median()), pred=e(g.q50.median()), pred_high=e(g.q90.median()),
        act_low=e(g.growth.quantile(.1)), act=e(g.growth.median()), act_high=e(g.growth.quantile(.9))))).round(2)
    by.to_csv("data/result_projection_v2_by_age.csv"); print(by.T.to_string())


if __name__ == "__main__":
    main()
