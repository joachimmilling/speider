"""Models behind the player page: Speider value now and the value path ahead.

1. Speider value: what a transfer would cost today. Trained on actual fees
   (deflated by the price index) with the third-party value on the day as one
   input among the player's age, career, level and numbers. Tested out of time
   against the third-party value alone.
2. Value path: growth relative to the market for 1 to 5 years (test 18 set-up:
   quantile models, calibrated per age band on the latest year with an outcome),
   plus the chance of still playing.

Writes data/site_models.pkl (one row per player) and data/result_site_models.json.
Run: PYTHONPATH=analysis python3 analysis/site_models.py   (SITE_STAGE=value refits only the fee model and updates the value columns)
"""
from __future__ import annotations

import json
import os

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as HGBC, HistGradientBoostingRegressor as HGBR

from projection_v3 import BANDS, FEATS, KW, apply, band, fit_q, offsets

# Momentum is left out everywhere (test 20): it adds nothing out of time, it punished top players for a
# fall that does not predict anything, and the mid-year value can postdate a summer transfer and leak the fee.
import projection_v3 as _pv
FEATS = [f for f in FEATS if f not in ("mom1", "mom2")]; _pv.FEATS = FEATS
PF = [f for f in dict.fromkeys(FEATS + ["age"]) if f != "lv"] + ["val"]
AV = ["starts_sh", "min_sh", "absent_sh", "bench_sh"]
PFA = PF + AV


# Above about 40m the data thins out (145 fees at 40-70m, 24 above), and trees fill the gap with patterns learned
# from cheaper players: teenagers sell above their value and grow fast, so a 220m teenager was priced at 320m and
# projected to 600m. Outside the support a straight line in age and value takes over gradually: it is fitted on the
# expensive end only and carries the mean reversion seen there (teenagers at 60m+ lost value against the market).
TAIL_LO, TAIL_HI = np.log(40e6), np.log(100e6)


def tail_w(lv):
    return np.clip((np.asarray(lv, float) - TAIL_LO) / (TAIL_HI - TAIL_LO), 0, 1)


def tail_fit(age, lv, y, floor):
    from sklearn.linear_model import HuberRegressor
    k = np.asarray(lv) >= np.log(floor)
    X = lambda a, l: np.column_stack([a, np.asarray(a) ** 2 / 100, l])
    m = HuberRegressor(alpha=1.0, max_iter=500).fit(X(np.asarray(age)[k], np.asarray(lv)[k]), np.asarray(y)[k])
    return lambda a, l: m.predict(X(np.asarray(a, float), np.asarray(l, float)))


class Bag:
    """Mean of n tree models, each fitted on a bootstrap sample of the rows (test 31b): steadier than one model."""

    def __init__(self, n=25, **kw): self.n, self.kw = n, kw

    def fit(self, X, y):
        X, y, rs = pd.DataFrame(X).astype(float).values, np.asarray(y, float), np.random.RandomState(0); self.models = []
        for i in range(self.n):
            ix = rs.randint(0, len(y), len(y)); self.models.append(HGBR(**{**self.kw, "random_state": i}).fit(X[ix], y[ix]))
        return self

    def predict(self, X):
        X = pd.DataFrame(X).astype(float).values; return np.mean([m_.predict(X) for m_ in self.models], axis=0)


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
    # Test 28: availability from match line-ups (big five leagues from 2022/23): share of the team's matches started, minutes share,
    # share out of the matchday squad and share on the bench unused, in the season before. Missing elsewhere.
    from availability import table as _avail
    av = _avail(con); av = av.sort_values("squad").groupby(["player_id", "ey"], as_index=False).last(); av = av[av.squad + av.inj >= 5][["player_id", "ey"] + AV].rename(columns={"ey": "y"})
    m = m.merge(av, on=["player_id", "y"], how="left"); now = now.merge(av[av.y == 2026].drop(columns=["y"]), on="player_id", how="left")
    m["val"] = np.log(m.mv); m["target"] = np.log(m.fee)
    # Test 31: buyer and seller tier (clubs ranked by the value of their best eleven that year), for the price per type of buyer
    from buyers import TIERS, club_tiers
    ct = club_tiers(b[b.team_id.notna()], ["team_id", "y"])[["team_id", "y", "tier"]]
    fid = con.execute("select player_id, date, any_value(from_id) from_id from fm_transfers group by 1,2").fetchdf(); fid["date"] = pd.to_datetime(fid.date).astype(m.date.dtype)
    m = m.merge(fid, on=["player_id", "date"], how="left")
    m = m.merge(ct.rename(columns={"team_id": "to_id", "tier": "buy_tier"}), on=["to_id", "y"], how="left").merge(ct.rename(columns={"team_id": "from_id", "tier": "sell_tier"}), on=["from_id", "y"], how="left")
    now = now.merge(ct[ct.y == 2026].rename(columns={"team_id": "team_id", "tier": "sell_tier"})[["team_id", "sell_tier"]], on="team_id", how="left")
    PFB = PFA + ["buy_tier", "sell_tier"]
    m = m.sort_values(["date", "player_id", "fee"], kind="stable").reset_index(drop=True)   # query order varies between runs; the fit must not
    # The models learn the fee relative to the third-party value (log ratio), not the fee itself. Trees cannot
    # extrapolate, so a model of the fee itself caps out near the largest fees seen and marks every
    # 100m+ player as overpriced. A ratio carries over to values above anything in the training data.
    # Test 30b: the ratio is measured against the going rate (median log fee over value in the previous 365 days,
    # by value bracket), which is added back at prediction time. That replaces the yearly price index and keeps the
    # model from carrying the fee-over-value level of old years into today.
    from transfers import price_level
    raw = (m.target - m.val).values
    m["lev"] = price_level(m.date, raw, m.val, m.date, m.val)[1]
    lev_at = lambda dates, vals: price_level(m.date, raw, m.val, dates, vals)[1]
    # Test 30c: each training fee is measured against the level of its own calendar year, so no year-level signal is left
    # for the trees to pick up through inputs that only exist in some seasons; predictions add the trailing level.
    _b = np.digitize(m.val.values, np.log([1e6, 5e6, 2e7])); _ya = pd.Series(raw).groupby(m.yy.values).transform("median").values
    m["ratio"] = raw - (0.5 * _ya + 0.5 * pd.Series(raw).groupby([m.yy.values, _b]).transform("median").values)
    pv0 = lambda mm, X: mm.predict(X[PFA]) + X.val.values + X.lev.values
    TL = {}
    def pv(mm, X):
        # the tail line moves the median; the 10 % and 90 % models move by the same amount
        d = tail_w(X.val.values) * (TL["f"](X.age.values, X.val.values) + X.val.values + X.lev.values - pv0(TL["med"], X))
        return pv0(mm, X) + d
    tr, te = m[m.yy <= 2024], m[m.yy >= 2025]
    q = {a: Bag(loss="quantile", quantile=a, **KW).fit(tr[PFA], tr.ratio) for a in (0.1, 0.5, 0.9)}
    TL["f"], TL["med"] = tail_fit(tr.age.values, tr.val.values, tr.ratio.values, 20e6), q[0.5]
    big = (te.mv >= 40e6).values
    res["tail_value"] = dict(n_test_40m=int(big.sum()), err_trees=round(err(np.exp(pv0(q[0.5], te))[big], te.fee.values[big]), 3))
    p = {a: np.exp(pv(mm, te)) for a, mm in q.items()}
    res["tail_value"]["err_with_tail"] = round(err(p[0.5][big], te.fee.values[big]), 3)
    young = (te.age < 23).values
    res["value"] = dict(n_train=len(tr), n_test=len(te), speider_err=round(err(p[0.5], te.fee.values), 3), third_party_err=round(err(te.mv.values, te.fee.values), 3),
                        speider_err_u23=round(err(p[0.5][young], te.fee.values[young]), 3), third_party_err_u23=round(err(te.mv.values[young], te.fee.values[young]), 3),
                        speider_bias=round(float(np.median(p[0.5] / te.fee.values)), 3), third_party_bias=round(float(np.median(te.mv.values / te.fee.values)), 3),
                        inside_80=round(float(np.mean((te.fee.values >= p[0.1]) & (te.fee.values <= p[0.9]))), 3),
                        rank=round(float(pd.Series(p[0.5]).corr(pd.Series(te.fee.values), method="spearman")), 3),
                        rank_third_party=round(float(te.mv.corr(te.fee, method="spearman")), 3))
    # widen the interval so 80 % of held-out fees fall inside, then refit on everything
    r = np.log(te.fee.values)
    lo_off = float(np.quantile(r - pv(q[0.1], te), 0.10)); hi_off = float(np.quantile(r - pv(q[0.9], te), 0.90))
    res["value"]["interval_offsets"] = [round(lo_off, 3), round(hi_off, 3)]
    q = {a: Bag(loss="quantile", quantile=a, **KW).fit(m[PFA], m.ratio) for a in (0.1, 0.5, 0.9)}
    TL["f"], TL["med"] = tail_fit(m.age.values, m.val.values, m.ratio.values, 20e6), q[0.5]
    now["val"] = now.lv; today = m.date.max() + pd.Timedelta(days=1)
    now["lev"] = lev_at(np.full(len(now), today.to_datetime64()), now.val)
    res["value"]["level_today"] = {k: round(float(v), 3) for k, v in zip(("under 1m", "1-5m", "5-20m", "20m+"), lev_at(np.full(4, today.to_datetime64()), np.log([5e5, 2e6, 1e7, 5e7])))}
    # price per buyer tier: the price never falls with the buyer's tier; the tail line moves it by the same amount as the main model
    qb = Bag(loss="quantile", quantile=0.5, **KW, monotonic_cst=[1 if f == "buy_tier" else 0 for f in PFB]).fit(m[PFB], m.ratio)
    tail_d = pv(q[0.5], now) - pv0(q[0.5], now)
    bt = {T: np.exp(qb.predict(now.assign(buy_tier=T)[PFB]) + now.val.values + now.lev.values + tail_d) for T in TIERS}
    out = pd.DataFrame(dict(player_id=now.player_id.values, mv=np.exp(now.lv.values), sv=np.exp(pv(q[0.5], now)),
                            sv_lo=np.exp(pv(q[0.1], now) + lo_off), sv_hi=np.exp(pv(q[0.9], now) + hi_off), band=now.band.values, age_i=np.clip(np.round(now.age.values), 16, 38).astype(int)))
    for T in TIERS: out[f"bt{T}"] = bt[T]
    # Speider value back in time: the same model applied to each earlier mid-year, with the going rate of that summer (in-sample for the training years)
    hist = b[b.y < 2026].merge(av, on=["player_id", "y"], how="left"); hist["val"] = hist.lv
    hist["lev"] = lev_at(pd.to_datetime(hist.y.astype(int).astype(str) + "-07-01").values, hist.val)
    pd.DataFrame(dict(player_id=hist.player_id.values, y=hist.y.values, sv=np.exp(pv(q[0.5], hist)))).to_pickle("data/site_models_hist.pkl")
    print("value", json.dumps(res["value"]), flush=True)
    if os.environ.get("SITE_STAGE") == "value":
        # Refit only the fee model: the path models below do not depend on it, so the value columns of the existing file are replaced.
        prev = pd.read_pickle("data/site_models.pkl"); assert (prev.player_id.values == out.player_id.values).all()
        for c in ["mv", "sv", "sv_lo", "sv_hi"] + [f"bt{T}" for T in TIERS]: prev[c] = out[c].values
        prev.to_pickle("data/site_models.pkl")
        old = json.load(open("data/result_site_models.json")); old.update(value=res["value"], tail_value=res["tail_value"])
        json.dump(old, open("data/result_site_models.json", "w"), indent=1); print("done (value only)", len(prev)); return

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
        # same tail treatment for the growth model; checked on the held-out year first
        hold = g[g.y == T]; hb = (hold.lv >= TAIL_LO).values
        if hb.sum() >= 5:
            _, md1, _ = apply(m1, hold, off); tr_ = g[g.y <= T - 1]
            tf1 = tail_fit(tr_.age.values, tr_.lv.values, tr_.growth.values, 15e6)
            md1t = md1 + tail_w(hold.lv.values) * (tf1(hold.age.values, hold.lv.values) - md1)
            res.setdefault("tail_growth", {})[h] = dict(n=int(hb.sum()), abs_err_trees=round(float(np.median(np.abs(md1[hb] - hold.growth.values[hb]))), 3), abs_err_with_tail=round(float(np.median(np.abs(md1t[hb] - hold.growth.values[hb]))), 3))
        tf = tail_fit(g.age.values, g.lv.values, g.growth.values, 15e6)
        d_ = tail_w(now.lv.values) * (tf(now.age.values, now.lv.values) - md)
        lo, md, hi = lo + d_, md + d_, hi + d_
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
