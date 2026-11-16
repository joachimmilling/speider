"""Models behind the player page: Speider value now and the value path ahead.

1. Speider value: what a transfer would cost today. Trained on actual fees
   (deflated by the price index) with the third-party value on the day as one
   input among the player's age, career, level and numbers. Tested out of time
   against the third-party value alone.
2. Value path: growth relative to the market for 1 to 5 years (test 18 set-up:
   quantile models, calibrated per age band on the latest year with an outcome),
   plus the chance of still playing.

Writes data/site_models.pkl (one row per player) and data/result_site_models.json.
Run: PYTHONPATH=analysis python3 analysis/site_models.py
"""
from __future__ import annotations

import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as HGBC, HistGradientBoostingRegressor as HGBR

from price_model_v4 import INDEX
from projection_v3 import BANDS, FEATS, KW, apply, band, fit_q, offsets

PF = [f for f in dict.fromkeys(FEATS + ["age"]) if f != "lv"] + ["val"]


def err(pred, fee):
    return float(np.median(np.abs(pred - fee) / fee))


def main() -> None:
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    b["band"] = b.age.map(band)
    now = b[b.y == 2026].copy()
    res: dict = {}

    # 1. Speider value from fees
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    # The frame holds mid-year values. Start today's numbers from the latest third-party value instead,
    # so the page agrees with the value history and a jump since the summer is not ignored.
    latest = con.execute("select player_id, ln(arg_max(value, date)) lv_latest from fm_mv where value > 0 group by 1").fetchdf()
    now = now.merge(latest, on="player_id", how="left")
    shift = (now.lv_latest - now.lv).fillna(0.0)
    now["lv"] += shift; now["mom1"] += shift; now["mom2"] += shift
    t = con.execute("""select player_id, year(date) yy, month(date) mo, fee, market_value mv from fm_transfers
                       where fee >= 50000 and not loan and not extension and market_value > 0 and year(date) >= 2016""").fetchdf()
    t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    m = t.merge(b, on=["player_id", "y"])
    m["val"] = np.log(m.mv); m["target"] = np.log(m.fee / m.yy.map(INDEX) * 100)
    tr, te = m[m.yy <= 2024], m[m.yy >= 2025]
    q = {a: HGBR(loss="quantile", quantile=a, **KW).fit(tr[PF], tr.target) for a in (0.1, 0.5, 0.9)}
    scale = te.yy.map(INDEX).values / 100
    p = {a: np.exp(mm.predict(te[PF])) * scale for a, mm in q.items()}
    young = (te.age < 23).values
    res["value"] = dict(n_train=len(tr), n_test=len(te), speider_err=round(err(p[0.5], te.fee.values), 3), third_party_err=round(err(te.mv.values, te.fee.values), 3),
                        speider_err_u23=round(err(p[0.5][young], te.fee.values[young]), 3), third_party_err_u23=round(err(te.mv.values[young], te.fee.values[young]), 3),
                        inside_80=round(float(np.mean((te.fee.values >= p[0.1]) & (te.fee.values <= p[0.9]))), 3),
                        rank=round(float(pd.Series(p[0.5]).corr(pd.Series(te.fee.values), method="spearman")), 3),
                        rank_third_party=round(float(te.mv.corr(te.fee, method="spearman")), 3))
    # widen the interval so 80 % of held-out fees fall inside, then refit on everything
    r = np.log(te.fee.values / scale)
    lo_off = float(np.quantile(r - q[0.1].predict(te[PF]), 0.10)); hi_off = float(np.quantile(r - q[0.9].predict(te[PF]), 0.90))
    res["value"]["interval_offsets"] = [round(lo_off, 3), round(hi_off, 3)]
    q = {a: HGBR(loss="quantile", quantile=a, **KW).fit(m[PF], m.target) for a in (0.1, 0.5, 0.9)}
    now["val"] = now.lv
    out = pd.DataFrame(dict(player_id=now.player_id.values, mv=np.exp(now.lv.values), sv=np.exp(q[0.5].predict(now[PF])),
                            sv_lo=np.exp(q[0.1].predict(now[PF]) + lo_off), sv_hi=np.exp(q[0.9].predict(now[PF]) + hi_off), band=now.band.values))
    # Speider value back in time: the same model applied to each earlier mid-year (in-sample for the training years)
    hist = b[b.y < 2026].copy(); hist["val"] = hist.lv
    pd.DataFrame(dict(player_id=hist.player_id.values, y=hist.y.values, sv=np.exp(q[0.5].predict(hist[PF])) * hist.y.map(INDEX).fillna(70).values / 100)).to_pickle("data/site_models_hist.pkl")
    print("value", json.dumps(res["value"]), flush=True)

    # 2. Value path, relative to the market, in today's prices
    res["path"] = {}
    for h in range(1, 6):
        b["growth_abs"] = b[f"lv_f{h}"] - b.lv
        b["growth"] = b.growth_abs - b.groupby("y").growth_abs.transform("median")
        b["playing"] = (b[f"apps_f{h}"].fillna(0) >= 5).astype(int)
        T = 2026 - h
        g = b[b.growth.notna() & (b.y <= T)]
        m1 = fit_q(g[g.y <= T - 1]); off = offsets(m1, g[g.y == T])
        mf = fit_q(g)
        lo, md, hi = apply(mf, now, off)
        cf = HGBC(**KW).fit(b[b.y <= T][FEATS], b[b.y <= T].playing)
        out[f"g{h}_lo"], out[f"g{h}"], out[f"g{h}_hi"] = np.exp(lo), np.exp(md), np.exp(hi)
        out[f"play{h}"] = cf.predict_proba(now[FEATS])[:, 1]
        res["path"][h] = dict(n=len(g), typical={bn: round(float(np.exp(np.median(md[(now.band == bn).values]))), 3) for _, _, bn in BANDS})
        print("h", h, json.dumps(res["path"][h]), flush=True)
    out.to_pickle("data/site_models.pkl")
    json.dump(res, open("data/result_site_models.json", "w"), indent=1)
    print("done", len(out))


if __name__ == "__main__":
    main()
