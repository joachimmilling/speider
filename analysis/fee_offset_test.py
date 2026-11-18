"""Test 30b: price-level offset and recency weights for the fee model, scored on a rolling origin. Writes data/result_fee_offset.json."""
import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from fee_feature_search import G
from price_model_v4 import INDEX
from projection_v3 import KW
from site_models import AV, PF, err

YEARS = range(2021, 2027)


def main() -> None:
    m = pd.read_pickle("data/fee_search_frame.pkl"); BASE = PF + AV
    for c in ("cal_all", "cal_band"): m[c] = m[c].fillna(m.cal_all).fillna(0.0)
    m["cal_band"] = 0.5 * m.cal_band + 0.5 * m.cal_all   # bracket level shrunk halfway to the overall level
    V = {
        "site model today": dict(t="idx"),
        "recency weights": dict(t="idx", hl=730),
        "raw target": dict(t="raw"),
        "offset overall": dict(t="raw", off="cal_all"),
        "offset bracket": dict(t="raw", off="cal_band"),
        "offset overall + weights": dict(t="raw", off="cal_all", hl=730),
        "offset bracket + weights": dict(t="raw", off="cal_band", hl=730),
        "offset overall + weights 1y": dict(t="raw", off="cal_all", hl=365),
        "year-centred, bracket level": dict(t="raw", off="cal_band", centre=True),
        "year-centred, overall level": dict(t="raw", off="cal_all", centre=True),
        "year-centred, no availability": dict(t="raw", off="cal_band", centre=True, noav=True),
    }
    band = np.digitize(m.val.values, np.log([1e6, 5e6, 2e7])); ya = m.groupby("yy").r_raw.transform("median"); yb = m.r_raw.groupby([m.yy, band]).transform("median")
    m["own_cal_all"], m["own_cal_band"] = ya, 0.5 * ya + 0.5 * yb
    V["year-centred + buyer tier"] = dict(t="raw", off="cal_band", centre=True, extra=["buy_tier"])
    V["year-centred + buyer and seller tier"] = dict(t="raw", off="cal_band", centre=True, extra=["buy_tier", "sell_tier"])
    V["year-centred + buyer and seller tier (price never falls with buyer tier)"] = dict(t="raw", off="cal_band", centre=True, extra=["buy_tier", "sell_tier"], mono=True)
    V["year-centred, bagged x10"] = dict(t="raw", off="cal_band", centre=True, bag=10)
    V["year-centred + tiers, bagged x10"] = dict(t="raw", off="cal_band", centre=True, extra=["buy_tier", "sell_tier"], mono=True, bag=10)
    V.update({k + " + buyer": dict(v, buy=True) for k, v in list(V.items()) if k in ("site model today", "offset overall", "year-centred, bracket level")})
    only = os.environ.get("ONLY")          # variant names separated by ;: run those (plus the reference) and merge into the existing result file
    if only: V = {k: v for k, v in V.items() if k in only.split(";") or k == "site model today"}
    out = {k: {} for k in V}; out["market value alone"] = {}; preds = {k: [] for k in V}; fees = []
    for y in YEARS:
        tr, te = m[m.yy < y], m[m.yy == y]; fees.append(te.fee.values)
        out["market value alone"][y] = dict(miss=round(err(te.mv.values, te.fee.values), 4), bias=round(float(np.median(te.mv.values / te.fee.values)), 3))
        for k, v in V.items():
            feats = (PF if v.get("noav") else BASE) + (G["BUY"] if v.get("buy") else []) + v.get("extra", [])
            off_tr = tr[("own_" if v.get("centre") else "") + v["off"]].values if v.get("off") else 0.0; off_te = te[v["off"]].values if v.get("off") else 0.0
            yv = (tr.r_idx if v["t"] == "idx" else tr.r_raw).values - off_tr
            w = 0.5 ** ((tr.date.max() - tr.date).dt.days / v["hl"]) if v.get("hl") else None
            mk = lambda seed: HGBR(loss="absolute_error", **{**KW, "random_state": seed}, monotonic_cst=[1 if f == "buy_tier" else 0 for f in feats] if v.get("mono") else None)
            if v.get("bag"):
                rs = np.random.RandomState(0); X, Xt, pr = tr[feats].astype(float).values, te[feats].astype(float).values, []
                for s_ in range(v["bag"]):
                    ix = rs.randint(0, len(tr), len(tr)); pr.append(mk(s_).fit(X[ix], yv[ix]).predict(Xt))
                p = np.mean(pr, axis=0) + off_te + te.val.values
            else: p = mk(0).fit(tr[feats], yv, sample_weight=w).predict(te[feats]) + off_te + te.val.values
            f = np.exp(p) * (te.yy.map(INDEX).values / 100 if v["t"] == "idx" else 1.0); preds[k].append(f)
            out[k][y] = dict(miss=round(err(f, te.fee.values), 4), bias=round(float(np.median(f / te.fee.values)), 3))
    fee = np.concatenate(fees); mvall = np.concatenate([m[m.yy == y].mv.values for y in YEARS])
    out["market value alone"]["pooled"] = dict(miss=round(err(mvall, fee), 4), bias=round(float(np.median(mvall / fee)), 3), rank=round(float(pd.Series(mvall).corr(pd.Series(fee), method="spearman")), 3))
    for k in V:
        f = np.concatenate(preds[k]); out[k]["pooled"] = dict(miss=round(err(f, fee), 4), bias=round(float(np.median(f / fee)), 3), rank=round(float(pd.Series(f).corr(pd.Series(fee), method="spearman")), 3))
        out[k]["worse_years"] = int(sum(out[k][y]["miss"] > out["site model today"][y]["miss"] for y in YEARS))
    out["n"] = {y: int((m.yy == y).sum()) for y in YEARS}
    if only: prev = json.load(open("data/result_fee_offset.json")); prev.update({k: v for k, v in out.items() if k != "n"}); json.dump(prev, open("data/result_fee_offset.json", "w"), indent=1, default=str)
    else: json.dump(out, open("data/result_fee_offset.json", "w"), indent=1, default=str)
    for k, v in out.items():
        if k == "n": continue
        print(f"{k:38s} pooled {v['pooled']['miss']:.3f} bias {v['pooled']['bias']:.3f} rank {v['pooled'].get('rank')}  worse {v.get('worse_years','')}  | " + " ".join(f"{v[y]['miss']:.3f}/{v[y]['bias']:.2f}" for y in YEARS))


if __name__ == "__main__":
    main()
