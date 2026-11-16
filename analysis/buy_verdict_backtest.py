"""Test 20: can a signal known on the day tell good buys from bad ones?

Matching the fee is the wrong goal: a model that predicts fees perfectly calls
every buy fair. The outcome is what the player was worth three years after the
transfer (third-party value then; nothing if he had stopped playing), divided
by the fee paid. A signal is useful if buys it calls cheap end up with a higher
outcome per euro than buys it calls expensive.

Walk-forward for transfers in 2020-2023; every model only sees what was known:
  A  third-party value on the day / fee
  B  Speider fee model (trained on earlier fees) / fee
  C  Speider outcome model: expected value in three years (trained on player-years
     whose three-year outcome was already known) / fee
  C2 as C without the momentum inputs
  D  C2 blended half and half with the realised outcome of the 60 closest comparables
Writes data/result_buy_verdict.json.  Run: PYTHONPATH=analysis python3 analysis/buy_verdict_backtest.py
"""
from __future__ import annotations

import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR
from sklearn.neighbors import NearestNeighbors

from price_model_v4 import INDEX
from projection_v3 import FEATS, KW

NOMOM = [f for f in FEATS if f not in ("mom1", "mom2")]
# no momentum in the fee model: the mid-year value can postdate a summer transfer and leak the fee
PF = [f for f in dict.fromkeys(FEATS + ["age"]) if f not in ("lv", "mom1", "mom2")] + ["val"]


def main() -> None:
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    b["g3"] = b.lv_f3 - b.lv
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    from transfers import load as load_transfers
    t = load_transfers(con).drop(columns=["name"])
    t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    # money outcome that does not come from the value provider: the next fee paid for the same player, in the same price level
    t = t.sort_values(["player_id", "date"]); nxt = t.groupby("player_id").shift(-1)
    t["resale"] = (nxt.fee / nxt.yy.map(INDEX)) / (t.fee / t.yy.map(INDEX)); t["held_years"] = (nxt.date - t.date).dt.days / 365.25
    m = t.merge(b, on=["player_id", "y"]); m["val"] = np.log(m.mv); m["target"] = np.log(m.fee / m.yy.map(INDEX) * 100)
    rows = []
    for Y in range(2018, 2027):
        te = m[m.yy == Y].copy()
        te["ret"] = np.where(te.lv_f3.notna(), np.exp(te.lv_f3) / te.fee, np.nan)
        fee_m = HGBR(loss="absolute_error", **KW).fit(m[m.yy < Y][PF], m[m.yy < Y].target)
        te["A"] = te.mv / te.fee
        te["B"] = np.exp(fee_m.predict(te[PF])) * INDEX[Y] / 100 / te.fee
        tr = b[(b.y <= Y - 3) & b.g3.notna()]
        tex = te.assign(lv=te.val)                                   # start from the value on the day
        for name, F in (("C", FEATS), ("C2", NOMOM)):
            om = HGBR(loss="absolute_error", **KW).fit(tr[F], tr.g3)
            te[name] = np.exp(tex.lv + om.predict(tex[F])) / te.fee
        nn = NearestNeighbors(n_neighbors=60).fit(np.column_stack([tr.age.values, tr.lv.values / 0.35]))
        ix = nn.kneighbors(np.column_stack([tex.age.values, tex.lv.values / 0.35]), return_distance=False)
        te["D"] = np.sqrt(te.C2 * np.exp(tex.lv + np.median(tr.g3.values[ix], axis=1)) / te.fee)
        rows.append(te[["player_id", "name", "date", "yy", "age", "fee", "mv", "ret", "resale", "held_years", "A", "B", "C", "C2", "D"]])
    allr = pd.concat(rows)
    # verdict used on the site: expected value in three years / fee (C2), in fifths within the year and fee size
    allr["size"] = allr.groupby("yy").fee.transform(lambda x: pd.qcut(x.rank(method="first"), 3, labels=False))
    allr["verdict"] = allr.groupby(["yy", "size"]).C2.transform(lambda x: pd.qcut(x.rank(method="first"), 5, labels=False)).astype(int)
    allr.to_pickle("data/buy_verdicts.pkl")
    vs = allr[allr.resale.notna() & (allr.held_years >= 0.9) & (allr.yy <= 2023)]
    r = allr[allr.ret.notna() & (allr.yy <= 2023)]
    y_, lf_ = np.log(vs.resale * vs.fee), np.log(vs.fee)
    def r2(cols):
        X = np.column_stack([np.ones(len(y_))] + cols); return round(float(1 - (y_ - X @ np.linalg.lstsq(X, y_, rcond=None)[0]).var() / y_.var()), 3)
    extra = dict(next_fee_r2=dict(fee_only=r2([lf_]), **{k: r2([lf_, np.log(vs[k] * vs.fee)]) for k in ("A", "B", "C2", "D")}),
                 next_fee_rank=dict(fee=round(float(vs.fee.corr(vs.resale * vs.fee, method="spearman")), 3), **{k: round(float((vs[k] * vs.fee).corr(vs.resale * vs.fee, method="spearman")), 3) for k in ("A", "B", "C2", "D")}),
                 verdict=[[int(q), int(len(g)), round(float(g.resale.median()), 2), round(float((g.resale > 1).mean()), 2)] for q, g in vs.groupby("verdict")],
                 verdict_large=[[int(q), int(len(g)), round(float(g.resale.median()), 2), round(float((g.resale > 1).mean()), 2)] for q, g in vs[vs["size"] == 2].groupby("verdict")])
    res = dict(extra, n=len(r), median_return=round(float(r.ret.median()), 2), signals={})
    for s in ("A", "B", "C", "C2", "D"):
        q = r.groupby("yy")[s].transform(lambda x: pd.qcut(x.rank(method="first"), 5, labels=False))
        top, bot = r[q == 4], r[q == 0]
        res["signals"][s] = dict(rank_corr=round(float(r.groupby("yy").apply(lambda g: g[s].corr(g.ret, method="spearman")).mean()), 3),
                                 cheap_median_return=round(float(top.ret.median()), 2), dear_median_return=round(float(bot.ret.median()), 2),
                                 cheap_share_held_value=round(float((top.ret >= 1).mean()), 2), dear_share_held_value=round(float((bot.ret >= 1).mean()), 2))
    rs = r[r.resale.notna() & (r.held_years >= 0.9)]
    res["resale"] = dict(n=len(rs), median_resale=round(float(rs.resale.median()), 2), signals={})
    for s in ("A", "B", "C", "C2", "D"):
        q = pd.qcut(rs[s].rank(method="first"), 5, labels=False)
        res["resale"]["signals"][s] = dict(rank_corr=round(float(rs[s].corr(rs.resale, method="spearman")), 3), cheap_median=round(float(rs[q == 4].resale.median()), 2), dear_median=round(float(rs[q == 0].resale.median()), 2),
                                           cheap_profit_share=round(float((rs[q == 4].resale > 1).mean()), 2), dear_profit_share=round(float((rs[q == 0].resale > 1).mean()), 2))
    res["resale"]["under23"] = {s: round(float(rs[rs.age < 23][s].corr(rs[rs.age < 23].resale, method="spearman")), 3) for s in ("A", "B", "C", "C2", "D")}
    res["resale"]["n_under23"] = int((rs.age < 23).sum())
    for u23, lab in ((True, "under23"), (False, "23plus")):
        g = r[(r.age < 23) == u23]
        res[lab] = {s: round(float(g.groupby("yy").apply(lambda x: x[s].corr(x.ret, method="spearman")).mean()), 3) for s in ("A", "B", "C", "C2", "D")}
    # The "Speider above market value" flag: fee-model value / third-party value on the day, for players of 26 or younger.
    # Outcome: the next fee paid for the player / third-party value on the day, against the same year's typical.
    f = r[(r.age <= 26) & r.resale.notna() & (r.held_years >= 0.9)].copy(); f["flag"] = f.B / f.A; f["nx"] = f.resale * f.fee / f.mv
    f["q"] = f.groupby("yy").flag.transform(lambda x: pd.qcut(x.rank(method="first"), 5, labels=False)); f["nxr"] = f.nx / f.groupby("yy").nx.transform("median")
    f["q2"] = f.groupby("yy").A.transform(lambda x: pd.qcut((1 / x).rank(method="first"), 5, labels=False)); near = f[(f.q2 > 0) & (f.q2 < 4)]
    res["flag"] = dict(n=len(f), top=round(float(f[f.q == 4].nxr.median()), 2), middle=round(float(f[(f.q > 0) & (f.q < 4)].nxr.median()), 2), bottom=round(float(f[f.q == 0].nxr.median()), 2),
                       top_beat=round(float((f[f.q == 4].nxr > 1).mean()), 2), bottom_beat=round(float((f[f.q == 0].nxr > 1).mean()), 2),
                       near_value_top=round(float(near[near.q == 4].nxr.median()), 2), near_value_bottom=round(float(near[near.q == 0].nxr.median()), 2))
    print(json.dumps(res, indent=1))
    json.dump(res, open("data/result_buy_verdict.json", "w"), indent=1)
    r.to_pickle("data/buy_verdict_backtest.pkl")


if __name__ == "__main__":
    main()
