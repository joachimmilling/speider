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

# Momentum is left out everywhere (test 20): it adds nothing out of time, it punished top players for a
# fall that does not predict anything, and the mid-year value can postdate a summer transfer and leak the fee.
import projection_v3 as _pv
FEATS = [f for f in FEATS if f not in ("mom1", "mom2")]; _pv.FEATS = FEATS
PF = [f for f in dict.fromkeys(FEATS + ["age"]) if f != "lv"] + ["val"]


def err(pred, fee):
    return float(np.median(np.abs(pred - fee) / fee))


def main() -> None:
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    b["band"] = b.age.map(band)
    # momentum relative to the market: the provider's values swing market-wide from year to year,
    # and a player should not be marked as falling because every value fell that year
    for k in ("mom1", "mom2"): b[k] = b[k] - b.groupby("y")[k].transform("median")
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
    from transfers import load as load_transfers
    t = load_transfers(con).drop(columns=["name"])          # value on the day from the value history, not the crawl-time field
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
                            sv_lo=np.exp(q[0.1].predict(now[PF]) + lo_off), sv_hi=np.exp(q[0.9].predict(now[PF]) + hi_off), band=now.band.values, age_i=np.clip(np.round(now.age.values), 16, 38).astype(int)))
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
        # What actually happened to comparable players: the 60 past player-years closest in age and value
        # (one year of age counts like a 40 % difference in value), with their realised growth against the market.
        # The model is good where there are many alike and guesses where there are few (a 100m teenager), so the
        # shown path is half model, half realised outcomes of the closest comparables. No ceiling: records can fall.
        from sklearn.neighbors import NearestNeighbors
        nn = NearestNeighbors(n_neighbors=60).fit(np.column_stack([g.age.values, g.lv.values / 0.35]))
        ix = nn.kneighbors(np.column_stack([now.age.values, now.lv.values / 0.35]), return_distance=False)
        e_lo, e_md, e_hi = (np.quantile(g.growth.values[ix], q_, axis=1) for q_ in (0.1, 0.5, 0.9))
        lo, md, hi = (lo + e_lo) / 2, (md + e_md) / 2, (hi + e_hi) / 2
        out[f"e{h}_lo"], out[f"e{h}"], out[f"e{h}_hi"] = np.exp(e_lo), np.exp(e_md), np.exp(e_hi)
        # older players are never more likely to still be playing than younger ones with the same record
        cf = HGBC(**KW, monotonic_cst=[-1 if f == "age" else 0 for f in FEATS]).fit(b[b.y <= T][FEATS], b[b.y <= T].playing)
        out[f"g{h}_lo"], out[f"g{h}"], out[f"g{h}_hi"] = np.exp(lo), np.exp(md), np.exp(hi)
        out[f"play{h}"] = cf.predict_proba(now[FEATS])[:, 1]
        # typical path by exact age, not by band: a 39-year-old is not a typical 30-year-old
        res["path"][h] = dict(n=len(g), typical={int(a): round(float(np.exp(np.median(md[out.age_i.values == a]))), 3) for a in sorted(set(out.age_i))})
        print("h", h, json.dumps(res["path"][h]), flush=True)
    # 3. Survivorship correction. Value histories exist almost only for players who are active today, so the
    # frame is a sample of survivors: its still-playing rates are too high and its growth is growth given that
    # the player is still around. Career lines do not have that problem (analysis/dropout_career.py), so:
    #  - the base rate of still playing comes from career lines by age and horizon, and the survivor-trained
    #    model only tilts it up or down for the individual (odds ratio against the average for his age);
    #  - the value path becomes a mixture: with probability 1 - p the player has left and is worth nothing,
    #    otherwise the survivor path applies. Quantiles of the mixture replace the conditional ones.
    from scipy.special import ndtri
    base = pd.DataFrame(json.load(open("data/result_dropout_career.json"))); base.index = base.index.astype(float).astype(int); base.columns = base.columns.astype(int)
    a_floor = np.clip(np.floor(now.age.values), 16, 42).astype(int)
    # still-playing model on career lines (no survivorship): age, matches in the last three seasons, rating
    cl = con.execute("select player_id, end_year y, sum(apps) apps, avg(rating) rating from fm_career where end_year is not null group by 1,2").fetchdf()
    pb = con.execute("select player_id, birth from fm_profiles where birth is not null and gender='male'").fetchdf()
    cl = cl.merge(pb, on="player_id"); cl["age"] = cl.y - 0.5 - pd.to_datetime(cl.birth).dt.year - pd.to_datetime(cl.birth).dt.dayofyear / 365.25
    for k in (1, 2): cl = cl.merge(cl[["player_id", "y", "apps"]].rename(columns={"apps": f"apps_m{k}"}).assign(y=lambda x: x.y + k), on=["player_id", "y"], how="left")
    CF = ["age", "apps", "apps_m1", "apps_m2", "rating"]
    cur = cl[cl.y == 2026].drop_duplicates("player_id").set_index("player_id")
    for h in range(1, 6):
        d = cl.merge(cl[["player_id", "y", "apps"]].rename(columns={"apps": "fut"}).assign(y=lambda x: x.y - h), on=["player_id", "y"], how="left")
        d = d[(d.y <= 2026 - h) & (d.y >= 2015) & (d.apps >= 5)]
        m_ = HGBC(**KW, monotonic_cst=[-1, 0, 0, 0, 0]).fit(d[CF], (d.fut.fillna(0) >= 5).astype(int))
        pc = pd.Series(m_.predict_proba(cur[CF])[:, 1], index=cur.index)
        p_ = pc.reindex(out.player_id.values).values
        p_ = np.where(np.isnan(p_), base[h].reindex(a_floor).values, p_)
        if h > 1: p_ = np.minimum(p_, out[f"play{h-1}"].values)
        out[f"play{h}"] = p_
        lo_, md_, hi_ = np.log(out[f"g{h}_lo"].values), np.log(out[f"g{h}"].values), np.log(out[f"g{h}_hi"].values)
        for q_, col in ((0.1, f"g{h}_lo"), (0.5, f"g{h}"), (0.9, f"g{h}_hi")):
            qc = (q_ - (1 - p_)) / p_                      # the quantile to read off the survivor distribution
            z = ndtri(np.clip(qc, 1e-4, 1 - 1e-4)) / 1.2816
            v = np.exp(np.where(z < 0, md_ + z * (md_ - lo_), md_ + z * (hi_ - md_)))
            out[col] = np.where(qc <= 0.01, 0.02, np.maximum(v, 0.02))
        res["path"][h]["typical"] = {int(a): round(float(np.median(out[f"g{h}"].values[out.age_i.values == a])), 3) for a in sorted(set(out.age_i))}
        # typical path for the player's own peer group: same age and about the same value today
        # (expensive players lose more in relative terms than cheap ones, so age alone is the wrong yardstick)
        # peers: realised median of the comparables, through the same stopped-or-not mixture
        el, em, eh = np.log(out[f"e{h}_lo"].values), np.log(out[f"e{h}"].values), np.log(out[f"e{h}_hi"].values)
        qc = (0.5 - (1 - p_)) / p_; z = ndtri(np.clip(qc, 1e-4, 1 - 1e-4)) / 1.2816
        out[f"t{h}"] = np.where(qc <= 0.01, 0.02, np.maximum(np.exp(np.where(z < 0, em + z * (em - el), em + z * (eh - em))), 0.02))
    out.to_pickle("data/site_models.pkl")
    json.dump(res, open("data/result_site_models.json", "w"), indent=1)
    print("done", len(out))


if __name__ == "__main__":
    main()
