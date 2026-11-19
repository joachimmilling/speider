"""Test 34: is the low model error on new years caused by raw year centring on a changing mix of players? Writes data/result_fee_cause.json."""
import json
import os

import duckdb
import numpy as np
import pandas as pd

import fee_model
from fee_model import PFA, PFB
from fee_bias_test import trailing
from site_models import err
from transfers import LEVEL_EDGES

YEARS = range(2021, 2027)


def year_level(e, yy, band):
    """Median by year, halfway to the year's value bracket."""
    e = pd.Series(np.asarray(e)); return (0.5 * e.groupby(np.asarray(yy)).transform("median") + 0.5 * e.groupby([np.asarray(yy), np.asarray(band)]).transform("median")).values


def backfit(tr, feats, rounds=int(os.environ.get("ROUNDS", 3)), n=5):
    """Year levels given the inputs: fit, take each year's median error, subtract, refit."""
    fe = (tr.raw - tr.ratio).values
    for _ in range(rounds):
        g = fee_model.fit(tr.assign(t_=tr.raw.values - fe), feats=feats, n=n, target="t_")
        fe = year_level(tr.raw.values - g.predict(tr[feats]), tr.yy.values, tr.band.values)
    return fee_model.fit(tr.assign(t_=tr.raw.values - fe), feats=feats, n=10, target="t_"), fe


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    m, _, _ = fee_model.frame(con, b)
    m["day"] = m.date.values.astype("datetime64[D]").astype(int); m["band"] = np.digitize(m.val.values, LEVEL_EDGES)
    which = os.environ.get("FEATS", "PFA"); feats = PFB if which == "PFB" else PFA
    res = dict(composition={int(y): dict(n=len(g), median_age=round(float(g.age.median()), 1), share_28_plus=round(float((g.age >= 28).mean()), 3), median_value_m=round(float(np.exp(g.val.median()) / 1e6), 2), raw_level=round(float(g.raw.median()), 3)) for y, g in m.groupby("yy")})
    out = {}
    for mode in ("raw centring (today)", "levels given the inputs"):
        fwd_level, in_level, P, fees, yrs, fwd = {}, {}, [], [], [], pd.Series(np.nan, index=m.index)
        fits = {}
        for y in list(YEARS) + [YEARS[-1] + 1]:
            tr = m[m.yy < y]
            if mode.startswith("raw"): g, fe = fee_model.fit(tr, feats=feats, n=10), (tr.raw - tr.ratio).values
            else: g, fe = backfit(tr, feats)
            fits[y] = g
            # level of year y-1 once it is in the fit: the median error of that year's rows, in sample
            k = (tr.yy == y - 1).values; in_level[y - 1] = float(np.median(tr.raw.values[k] - g.predict(tr[k][feats])))
            if y <= YEARS[-1]:
                te = m[m.yy == y]; e = te.raw.values - g.predict(te[feats]); fwd[te.index] = e; fwd_level[y] = float(np.median(e))
        k0 = (m.yy == YEARS[0] - 1).values; g0 = fee_model.fit(m[m.yy < YEARS[0] - 1], feats=feats, n=5) if mode.startswith("raw") else backfit(m[m.yy < YEARS[0] - 1], feats, rounds=2)[0]
        fwd[m.index[k0]] = m.raw[k0].values - g0.predict(m[k0][feats])
        for y in YEARS:
            te = m[m.yy == y]; kn = m[(m.yy <= y) & fwd.notna()]
            off = trailing(kn.day.values, fwd[kn.index].values, kn.band.values, te.day.values, te.band.values, 180, True); off = np.where(np.isnan(off), te.lev.values, off)
            P.append(np.exp(fits[y].predict(te[feats]) + off + te.val.values)); fees.append(te.fee.values); yrs.append(np.full(len(te), y))
        f, fee, yr = np.concatenate(P), np.concatenate(fees), np.concatenate(yrs)
        out[mode] = dict(gap={y: round(fwd_level[y] - in_level[y], 3) for y in YEARS}, forward_level={y: round(fwd_level[y], 3) for y in YEARS}, level_in_fit={y: round(in_level[y], 3) for y in YEARS},
                         with_calibration=dict(miss=round(err(f, fee), 4), bias=round(float(np.median(f / fee)), 3), bias_by_year={y: round(float(np.median(f[yr == y] / fee[yr == y])), 3) for y in YEARS}))
        print(mode, json.dumps(out[mode]), flush=True)
    res[which] = out
    p = "data/result_fee_cause.json"; prev = json.load(open(p)) if os.path.exists(p) else {}; prev.update(res); json.dump(prev, open(p, "w"), indent=1)
    print(json.dumps(res["composition"]))


if __name__ == "__main__":
    main()
