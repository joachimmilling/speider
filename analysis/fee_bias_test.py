"""Test 33: where the fee model's low bias comes from, and calibration on the model's own recent errors. Writes data/result_fee_bias.json."""
import json

import duckdb
import numpy as np
import pandas as pd

import fee_model
from fee_model import PFA, PFB
from site_models import err
from transfers import LEVEL_EDGES

YEARS = range(2021, 2027)


def trailing(h_day, h_val, h_band, q_day, q_band, window, by_band):
    """Median of h_val over the `window` days strictly before each query day; with by_band, halfway to the same value bracket."""
    out = np.full(len(q_day), np.nan)
    for i in range(len(q_day)):
        k = (h_day < q_day[i]) & (h_day >= q_day[i] - window)
        if k.sum() < 30: continue
        a = np.median(h_val[k]); out[i] = a
        if by_band:
            kb = k & (h_band == q_band[i])
            if kb.sum() >= 20: out[i] = 0.5 * a + 0.5 * np.median(h_val[kb])
    return out


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    m, _, _ = fee_model.frame(con, b)
    m["day"] = m.date.values.astype("datetime64[D]").astype(int); m["band"] = np.digitize(m.val.values, LEVEL_EDGES)
    m["own"] = m.raw - m.ratio                       # the level of the fee's own year, as used in training
    V = {"today (trailing raw level, bracket, 365 d)": None, "own errors, overall, 365 d": (365, False), "own errors, bracket, 365 d": (365, True), "own errors, overall, 180 d": (180, False), "own errors, bracket, 180 d": (180, True),
         "forward errors, bracket, 180 d": (180, True, "fwd"), "forward errors, bracket, 365 d": (365, True, "fwd"), "forward errors, overall, 365 d": (365, False, "fwd")}
    res = {}
    for name, feats in (("no buyer", PFA), ("buyer and seller tier", PFB)):
        P = {k: [] for k in V}; fees, years, diag = [], [], {}
        fwd = pd.Series(np.nan, index=m.index)          # forward error of every transfer: from the model fitted on earlier years only
        g0 = fee_model.fit(m[m.yy < YEARS[0] - 1], feats=feats, n=10); k0 = m.yy == YEARS[0] - 1; fwd[k0] = m.raw[k0].values - g0.predict(m[k0][feats])
        for y in YEARS:
            tr, te = m[m.yy < y], m[m.yy == y]
            g = fee_model.fit(tr, feats=feats, n=10); fwd[te.index] = te.raw.values - g.predict(te[feats])
            g_te = g.predict(te[feats]); known = m[m.yy <= y]; e_known = known.raw.values - g.predict(known[feats])     # log fee minus (model + value)
            diag[y] = dict(level_lag=round(float(np.median(te.lev - te.own)), 3), model_error=round(float(np.median(g_te - te.ratio)), 3), total=round(float(np.median(g_te + te.lev - te.raw)), 3), n=len(te))
            for k, v in V.items():
                if v is None: off = te.lev.values
                elif len(v) == 3:
                    kf = known[fwd[known.index].notna().values]
                    off = trailing(kf.day.values, fwd[kf.index].values, kf.band.values, te.day.values, te.band.values, v[0], v[1]); off = np.where(np.isnan(off), te.lev.values, off)
                else:
                    off = trailing(known.day.values, e_known, known.band.values, te.day.values, te.band.values, v[0], v[1]); off = np.where(np.isnan(off), te.lev.values, off)
                P[k].append(np.exp(g_te + off + te.val.values))
            fees.append(te.fee.values); years.append(np.full(len(te), y))
        fee, yr = np.concatenate(fees), np.concatenate(years); r = dict(diagnosis=diag, variants={})
        base_b = {y: float(np.median(np.concatenate(P[list(V)[0]])[yr == y] / fee[yr == y])) for y in YEARS}
        for k in V:
            f = np.concatenate(P[k]); by = {y: round(float(np.median(f[yr == y] / fee[yr == y])), 3) for y in YEARS}
            r["variants"][k] = dict(miss=round(err(f, fee), 4), bias=round(float(np.median(f / fee)), 3), bias_by_year=by, closer_years=int(sum(abs(np.log(by[y])) < abs(np.log(base_b[y])) for y in YEARS)),
                                    miss_by_year={y: round(err(f[yr == y], fee[yr == y]), 3) for y in YEARS})
        res[name] = r
        print(name); print(" diagnosis", json.dumps(diag))
        for k, v in r["variants"].items(): print(f"  {k:46s} miss {v['miss']:.3f} bias {v['bias']:.3f} closer {v['closer_years']} | " + " ".join(f"{v['bias_by_year'][y]:.2f}" for y in YEARS))
    json.dump(res, open("data/result_fee_bias.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
