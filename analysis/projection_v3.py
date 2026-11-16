"""Test 18: one merged projection for all ages, calibrated.

Combines test 14 (per-player, per-horizon), test 15 (calibration per age band
on a held-out year) and test 16 (wide sample and career lines). The club,
league and nation track record is left out: test 17 showed it mostly reflects
the value provider, not outcomes.

Usage: python3 analysis/projection_v3.py H [player name ...]
For horizon H: fit on years up to T-2, calibrate on T-1, test on T = 2026 - H.
Then refit on everything and print the calibrated projection for the names.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as HGBC, HistGradientBoostingRegressor as HGBR

from growth_model import STATS
from projection_young import C

KW = dict(max_iter=160, learning_rate=0.08, max_leaf_nodes=20, min_samples_leaf=40, l2_regularization=1.0, random_state=0)
FEATS = C + ["role_c", "league_strength", "team_q", "lmin"] + STATS
BANDS = [(16, 19.999, "17-19"), (20, 21.999, "20-21"), (22, 24.999, "22-24"), (25, 28.999, "25-28"), (29, 40, "29+")]


def band(a: float) -> str:
    for lo, hi, n in BANDS:
        if lo <= a <= hi: return n
    return "29+"


def fit_q(tr):
    w = np.where(tr.age <= 21, 2.0, 1.0)
    return {a: HGBR(loss="quantile", quantile=a, **KW).fit(tr[FEATS], tr.growth, sample_weight=w) for a in (0.1, 0.5, 0.9)}


def offsets(m, cal):
    p = {a: mm.predict(cal[FEATS]) for a, mm in m.items()}
    off = {}
    for _, _, b in BANDS:
        i = (cal.band == b).values
        if i.sum() < 80: off[b] = (0.0, 0.0, 0.0); continue
        y = cal.growth.values[i]
        off[b] = (float(np.quantile(y - p[0.1][i], 0.10)), float(np.median(y - p[0.5][i])), float(np.quantile(y - p[0.9][i], 0.90)))
    return off


def apply(m, df, off):
    p = {a: mm.predict(df[FEATS]) for a, mm in m.items()}
    o = np.array([off[b] for b in df.band])
    return p[0.1] + o[:, 0], p[0.5] + o[:, 1], p[0.9] + o[:, 2]


def main() -> None:
    h = int(sys.argv[1]); names = sys.argv[2:]
    b = pd.read_pickle("data/frame_wide.pkl")
    b["growth_abs"] = b[f"lv_f{h}"] - b.lv
    # Player growth relative to the market: subtract the median value change of all players that year.
    # The market-wide move is a separate question (the price index); short horizons are dominated by it.
    b["market"] = b.groupby("y").growth_abs.transform("median")
    b["growth"] = b.growth_abs - b.market
    b["playing"] = (b[f"apps_f{h}"].fillna(0) >= 5).astype(int)
    b["band"] = b.age.map(band)
    T = 2026 - h
    g = b[b.growth.notna()]
    tr, cal, te = g[g.y <= T - 2], g[g.y == T - 1], g[g.y == T].copy()
    m = fit_q(tr); off = offsets(m, cal)
    raw = {a: mm.predict(te[FEATS]) for a, mm in m.items()}
    lo, md, hi = apply(m, te, off)
    y = te.growth.values
    rows = []
    for bname in ["17-19", "20-21", "22-24", "25-28", "29+", "all"]:
        i = np.ones(len(te), bool) if bname == "all" else (te.band == bname).values
        rows.append(dict(h=h, band=bname, n=int(i.sum()), actual_x=round(float(np.exp(np.median(y[i]))), 2),
                         bias_raw_pct=round(100 * (np.exp(np.median(raw[0.5][i] - y[i])) - 1)), bias_pct=round(100 * (np.exp(np.median(md[i] - y[i])) - 1)),
                         inside_raw=round(100 * float(np.mean((y[i] >= raw[0.1][i]) & (y[i] <= raw[0.9][i]))), 0), inside_80=round(100 * float(np.mean((y[i] >= lo[i]) & (y[i] <= hi[i]))), 0),
                         r2=round(1 - float(((y[i] - md[i]) ** 2).mean() / y[i].var()), 2), rank=round(float(pd.Series(md[i]).corr(pd.Series(y[i]), method="spearman")), 2)))
    a_tr, a_te = b[b.y <= T - 1], b[b.y == T]
    c = HGBC(**KW).fit(a_tr[a_tr.y <= T - 1 - 0][FEATS], a_tr.playing)
    ps = c.predict_proba(a_te[FEATS])[:, 1]
    from sklearn.metrics import roc_auc_score
    pd.set_option("display.width", 220)
    print(pd.DataFrame(rows).to_string(index=False))
    print("market move by start year (median value change of all players, x):", {int(k): round(float(np.exp(v)), 2) for k, v in b[b.growth_abs.notna()].groupby("y").market.first().items()})
    print(f"still playing after {h} years: actual {100*a_te.playing.mean():.0f} %, predicted {100*ps.mean():.0f} %, AUC {roc_auc_score(a_te.playing, ps):.3f}")
    pd.DataFrame(rows).to_csv(f"data/result_projection_v3_h{h}.csv", index=False)
    if names:
        allg = g[g.y <= 2026 - h]
        mf = fit_q(allg[allg.y <= T - 1]); offf = offsets(mf, allg[allg.y == T])     # calibrate on the latest year with an outcome
        mf = fit_q(allg)
        cf = HGBC(**KW).fit(b[b.y <= 2026 - h][FEATS], b[b.y <= 2026 - h].playing)
        now = b[b.y == 2026]
        out = []
        for n in names:
            r = now[now.name == n]
            if r.empty: out.append(dict(name=n, h=h, missing=True)); continue
            r = r.tail(1); lo_, md_, hi_ = apply(mf, r, offf); v0 = float(np.exp(r.lv.iloc[0]))
            out.append(dict(name=n, h=h, age_now=round(float(r.age.iloc[0]), 1), value_now_m=round(v0 / 1e6, 1), low_m=round(v0 * float(np.exp(lo_[0])) / 1e6, 1),
                            likely_m=round(v0 * float(np.exp(md_[0])) / 1e6, 1), high_m=round(v0 * float(np.exp(hi_[0])) / 1e6, 1), still_playing=round(float(cf.predict_proba(r[FEATS])[0, 1]), 2)))
        print("PROJ " + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
