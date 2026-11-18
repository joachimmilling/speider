"""Test 30: systematic search for fee-model improvements. Protocol in docs/results.md. Writes data/result_fee_search.json."""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from availability import table as avail_table
from price_model_v4 import INDEX
from projection_v3 import KW
from site_models import AV, PF, err
from team_strength_backtest import prep
from transfers import load

G = {
    "CAL": ["cal_all", "cal_band"],
    "MVH": ["mv_d6", "mv_d12", "mv_stale", "mv_width", "mv_points"],
    "PREV": ["prev_fee", "prev_years", "prev_over_value", "prev_n"],
    "LVL": ["level"] + [f"d{i}" for i in range(7)],
    "POS": ["pos_code", "pos_n"],
    "CTX": ["sell_q", "winter"],
    "BUY": ["buy_ls", "buy_q", "step_ls", "step_q", "buy_max_fee"],
}


def build(con) -> pd.DataFrame:
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    t = load(con).drop(columns=["name"]); t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    ids = con.execute("select player_id, date, from_id from fm_transfers").fetchdf(); ids["date"] = pd.to_datetime(ids.date).astype("datetime64[ns]"); t["date"] = pd.to_datetime(t.date).astype("datetime64[ns]")
    t = t.merge(ids.drop_duplicates(["player_id", "date"]), on=["player_id", "date"], how="left")
    m = t.merge(b, on=["player_id", "y"]).sort_values("date").reset_index(drop=True)
    m["val"] = np.log(m.mv); m["r_raw"] = np.log(m.fee) - m.val; m["r_idx"] = np.log(m.fee / m.yy.map(INDEX) * 100) - m.val
    av = avail_table(con); av = av.sort_values("squad").groupby(["player_id", "ey"], as_index=False).last(); av = av[av.squad + av.inj >= 5][["player_id", "ey"] + AV].rename(columns={"ey": "y"})
    m = m.merge(av, on=["player_id", "y"], how="left")
    # CAL: median log fee over value of the transfers in the 365 days before, overall and in the value bracket (strictly earlier dates)
    d = m.date.values.astype("datetime64[D]").astype(int); r = m.r_raw.values; band = np.digitize(m.val.values, np.log([1e6, 5e6, 2e7]))
    ca, cb = np.full(len(m), np.nan), np.full(len(m), np.nan)
    for i in range(len(m)):
        k = (d < d[i]) & (d >= d[i] - 365)
        if k.sum() >= 30: ca[i] = np.median(r[k])
        kb = k & (band == band[i])
        if kb.sum() >= 20: cb[i] = np.median(r[kb])
    m["cal_all"], m["cal_band"] = ca, cb
    # MVH: the value history strictly before the transfer date
    mv = con.execute("select player_id, date, value, lo, hi from fm_mv where value > 0 order by date").fetchdf(); mv["date"] = pd.to_datetime(mv.date).astype("datetime64[ns]"); mv["lvv"] = np.log(mv.value)
    def asof(days, col="lvv", name="x"):
        q = m[["player_id", "date"]].copy(); q["date"] = q.date - pd.Timedelta(days=days); q["i"] = np.arange(len(q))
        j = pd.merge_asof(q.sort_values("date"), mv[["player_id", "date", col]].sort_values("date"), on="date", by="player_id", allow_exact_matches=False)
        return j.sort_values("i")[col].values
    l0 = asof(0); m["mv_d6"] = l0 - asof(182); m["mv_d12"] = l0 - asof(365)
    m["mv_strict"] = np.exp(l0)
    lo, hi = asof(0, "lo"), asof(0, "hi"); m["mv_width"] = (hi - lo) / np.exp(l0)
    mv["chg"] = mv.groupby("player_id").value.diff().fillna(1) != 0
    last_chg = mv[mv.chg].rename(columns={"date": "chg_date"})[["player_id", "chg_date"]]
    q = m[["player_id", "date"]].copy(); q["i"] = np.arange(len(q))
    j = pd.merge_asof(q.sort_values("date"), last_chg.sort_values("chg_date"), left_on="date", right_on="chg_date", by="player_id", allow_exact_matches=False).sort_values("i")
    m["mv_stale"] = ((m.date.values - j.chg_date.values) / np.timedelta64(30, "D")).astype(float)
    mv["k"] = mv.groupby("player_id").cumcount() + 1
    j = pd.merge_asof(q.sort_values("date"), mv[["player_id", "date", "k"]].sort_values("date"), on="date", by="player_id", allow_exact_matches=False).sort_values("i"); m["mv_points"] = j.k.values
    # PREV: earlier fees for the same player
    at = con.execute("select player_id, date, fee from fm_transfers where fee >= 50000 and not loan and not extension order by date").fetchdf(); at["date"] = pd.to_datetime(at.date).astype("datetime64[ns]")
    at["pn"] = at.groupby("player_id").cumcount() + 1; at = at.rename(columns={"date": "pdate", "fee": "pfee"})
    j = pd.merge_asof(q.sort_values("date"), at.sort_values("pdate"), left_on="date", right_on="pdate", by="player_id", allow_exact_matches=False).sort_values("i")
    m["prev_fee"] = np.log(j.pfee.values); m["prev_years"] = ((m.date.values - j.pdate.values) / np.timedelta64(365, "D")).astype(float); m["prev_over_value"] = m.prev_fee - m.val; m["prev_n"] = j.pn.fillna(0).values
    # LVL: level and attributes on the common scale from the season before
    sq, _ = prep(con); pl = sq.sort_values("m").drop_duplicates(["player_id", "ey"], keep="last")[["player_id", "ey", "level"] + [f"d{i}" for i in range(7)]]
    m = m.merge(pl.rename(columns={"ey": "y"}).assign(y=lambda x: x.y - 1), on=["player_id", "y"], how="left")   # pl.ey holds numbers from ey - 1
    # POS
    pos = con.execute("select player_id, cast(json_extract(positions,'$[0]') as int) pos_code, json_array_length(positions) pos_n from fm_players").fetchdf()
    m = m.merge(pos, on="player_id", how="left")
    # CTX and BUY: team quality = mean log value of the eleven most valuable players at the club that year; league strength = the club's players' typical
    tq = b[b.team_id.notna()].groupby(["team_id", "y"]).lv.apply(lambda x: x.nlargest(11).mean() if len(x) >= 8 else np.nan).rename("q").reset_index()
    tls = b[b.team_id.notna()].groupby(["team_id", "y"]).league_strength.median().rename("ls").reset_index()
    m = m.merge(tq.rename(columns={"team_id": "from_id", "q": "sell_q"}), on=["from_id", "y"], how="left")
    m = m.merge(tq.rename(columns={"team_id": "to_id", "q": "buy_q"}), on=["to_id", "y"], how="left").merge(tls.rename(columns={"team_id": "to_id", "ls": "buy_ls"}), on=["to_id", "y"], how="left")
    m["winter"] = m.mo.isin([12, 1, 2, 3]).astype(int); m["step_ls"] = m.buy_ls - m.league_strength; m["step_q"] = m.buy_q - m.sell_q
    from buyers import club_tiers
    ct = club_tiers(b[b.team_id.notna()], ["team_id", "y"])[["team_id", "y", "tier"]]
    m = m.merge(ct.rename(columns={"team_id": "to_id", "tier": "buy_tier"}), on=["to_id", "y"], how="left").merge(ct.rename(columns={"team_id": "from_id", "tier": "sell_tier"}), on=["from_id", "y"], how="left")
    m = m.sort_values("date").reset_index(drop=True)
    m["buy_max_fee"] = np.log(m.groupby("to_id").fee.transform(lambda x: x.shift().cummax()))
    return m


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    import os
    if os.path.exists("data/fee_search_frame.pkl") and not os.environ.get("REBUILD"): m = pd.read_pickle("data/fee_search_frame.pkl")
    else: m = build(con); m.to_pickle("data/fee_search_frame.pkl")
    if os.environ.get("BUILD_ONLY"): print(len(m), m[sum(G.values(), [])].notna().mean().round(2).to_dict()); return
    BASE = PF + AV
    def run(tr, te, feats, target="r_raw", weights=False):
        w = None
        if weights: w = 0.5 ** ((tr.date.max() - tr.date).dt.days / 730.0)
        p = HGBR(loss="absolute_error", **KW).fit(tr[feats], tr[target], sample_weight=w).predict(te[feats]) + te.val.values
        f = np.exp(p) * (te.yy.map(INDEX).values / 100 if target == "r_idx" else 1.0)
        return dict(miss=round(err(f, te.fee.values), 4), bias=round(float(np.median(f / te.fee.values)), 3), rank=round(float(pd.Series(f).corr(pd.Series(te.fee.values), method="spearman")), 3))
    res = dict(n=len(m), coverage={g: round(float(m[c].notna().all(axis=1).mean()), 3) for g, c in G.items()})
    # selection: fit to 2023, score on 2024
    tr, va = m[m.yy <= 2023], m[m.yy == 2024]
    sel = dict(n_train=len(tr), n_val=len(va), steps=[])
    sel["market value alone"] = dict(miss=round(err(va.mv.values, va.fee.values), 4), bias=round(float(np.median(va.mv.values / va.fee.values)), 3))
    sel["market value strictly before the day"] = dict(miss=round(err(va.mv_strict.values[va.mv_strict.notna()], va.fee.values[va.mv_strict.notna()]), 4))
    cur = run(tr, va, BASE, "r_idx"); sel["site model (indexed target)"] = cur
    state = dict(target="r_idx", weights=False, feats=list(BASE)); best = cur["miss"]
    def consider(name, **chg):
        nonlocal best, state
        cand = {**state, **chg}; r_ = run(tr, va, cand["feats"], cand["target"], cand["weights"]); keep = best - r_["miss"] >= 0.003
        sel["steps"].append(dict(step=name, **r_, kept=bool(keep)))
        if keep: state, best = cand, r_["miss"]
    consider("T raw ratio target", target="r_raw")
    consider("W recency weights", weights=True)
    for g in ("CAL", "MVH", "PREV", "LVL", "POS", "CTX"): consider(g, feats=state["feats"] + G[g])
    sel["chosen"] = dict(target=state["target"], weights=state["weights"], added=[f for f in state["feats"] if f not in BASE])
    res["selection"] = sel
    # final: fit to 2024, score once on 2025-26
    tr, te = m[m.yy <= 2024], m[m.yy >= 2025]
    fin = dict(n_train=len(tr), n_test=len(te))
    fin["market value alone"] = dict(miss=round(err(te.mv.values, te.fee.values), 4), bias=round(float(np.median(te.mv.values / te.fee.values)), 3), rank=round(float(te.mv.corr(te.fee, method="spearman")), 3))
    fin["site model today"] = run(tr, te, BASE, "r_idx")
    fin["selected"] = run(tr, te, state["feats"], state["target"], state["weights"])
    fin["selected plus buyer"] = run(tr, te, state["feats"] + G["BUY"], state["target"], state["weights"])
    for lab, k in (("with match data", te.absent_sh.notna()), ("value 20m+", te.mv >= 2e7), ("value under 2m", te.mv < 2e6), ("age under 23", te.age < 23)):
        sub = te[k.values]
        fin.setdefault("groups", {})[lab] = dict(n=len(sub), market=round(err(sub.mv.values, sub.fee.values), 3), site=run(tr, sub, BASE, "r_idx")["miss"], selected=run(tr, sub, state["feats"], state["target"], state["weights"])["miss"])
    res["final"] = fin; res["chosen_features"] = state["feats"]
    json.dump(res, open("data/result_fee_search.json", "w"), indent=1)
    res2 = {k: v for k, v in res.items() if k != "chosen_features"}; print(json.dumps(res2, indent=1))


if __name__ == "__main__":
    main()
