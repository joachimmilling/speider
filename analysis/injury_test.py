"""Test 28: does injury history say something the minutes do not? Writes data/result_injury.json."""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from availability import table
from price_model_v4 import INDEX
from projection_v3 import KW
from site_models import PF, err
from transfers import load


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    a = table(con)
    # one row per player and season: the team where he was in the squad most
    a = a.sort_values("squad").groupby(["player_id", "ey"], as_index=False).last()
    a = a[a.squad + a.inj >= 5]
    birth = con.execute("select player_id, birth from fm_profiles where birth is not null").fetchdf()
    a = a.merge(birth, on="player_id", how="left"); bd = pd.to_datetime(a.birth, errors="coerce"); a["age"] = a.ey - 0.5 - bd.dt.year - (bd.dt.month - 1) / 12
    res = dict(player_seasons=len(a), listed_injured_share_mean=round(float(a.inj_sh.mean()), 3), absent_share_mean=round(float(a.absent_sh.mean()), 3), bench_share_mean=round(float(a.bench_sh.mean()), 3),
               note="the provider's unavailable lists are incomplete (Odegaard's seven missed matches in autumn 2024 are not listed), so 'out of the matchday squad' is used next to 'listed injured'")
    # (a) next season
    nx = a[["player_id", "ey", "absent_sh", "inj_sh", "min_sh"]].rename(columns={"absent_sh": "absent_next", "inj_sh": "inj_next", "min_sh": "min_next"}); nx["ey"] -= 1
    d = a.merge(nx, on=["player_id", "ey"]).dropna(subset=["age"])
    d = d[d.ey <= 2025]                                           # next season complete
    tr, te = d[d.ey <= 2024], d[d.ey == 2025]
    res["a"] = dict(n_train=len(tr), n_test=len(te))
    sets = {"minutes and age": ["min_sh", "age"], "plus out of squad, bench, listed injured": ["min_sh", "age", "absent_sh", "bench_sh", "inj_sh", "starts_sh"]}
    for tgt in ("absent_next", "inj_next", "min_next"):
        res["a"][tgt] = {}
        for name, f in sets.items():
            p = HGBR(**KW).fit(tr[f], tr[tgt]).predict(te[f])
            res["a"][tgt][name] = round(float(pd.Series(p).corr(pd.Series(te[tgt].values), method="spearman")), 3)
    lowm = d[(d.min_sh < 0.5)]
    grp = np.where(lowm.absent_sh >= lowm.bench_sh + 0.15, "mostly out of squad", np.where(lowm.bench_sh >= lowm.absent_sh + 0.15, "mostly on the bench", "mixed"))
    res["a"]["low_minutes_then_next_season"] = {k: dict(n=int((grp == k).sum()), minutes_share_next=round(float(lowm.min_next[grp == k].mean()), 3), out_of_squad_next=round(float(lowm.absent_next[grp == k].mean()), 3)) for k in ("mostly out of squad", "mostly on the bench", "mixed")}
    # (b) fees: transfers with a covered season before them
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    t = load(con).drop(columns=["name"]); t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    m = t.merge(b, on=["player_id", "y"]); m["val"] = np.log(m.mv); m["ratio"] = np.log(m.fee / m.yy.map(INDEX) * 100) - m.val
    A = ["absent_sh", "bench_sh", "inj_sh", "starts_sh", "min_sh"]
    m = m.merge(a[["player_id", "ey"] + A].rename(columns={"ey": "y"}), on=["player_id", "y"], how="left")
    cov = m[m.absent_sh.notna()]
    tr, te = m[m.yy <= 2024], m[m.yy >= 2025]; has = te.absent_sh.notna().values; scale = te.yy.map(INDEX).values / 100
    res["b"] = dict(transfers_with_data=len(cov), n_test_with_data=int(has.sum()), miss={})
    for name, f in (("site inputs", PF), ("plus availability", PF + A)):
        p = np.exp(HGBR(loss="absolute_error", **KW).fit(tr[f], tr.ratio).predict(te[f]) + te.val.values) * scale
        res["b"]["miss"][name] = dict(all=round(err(p, te.fee.values), 3), with_data=round(err(p[has], te.fee.values[has]), 3))
    lowc = cov[cov.min_sh < 0.5]
    g2 = np.where(lowc.absent_sh >= lowc.bench_sh + 0.15, "mostly out of squad", np.where(lowc.bench_sh >= lowc.absent_sh + 0.15, "mostly on the bench", "mixed"))
    res["b"]["fee_over_value_low_minutes"] = {k: dict(n=int((g2 == k).sum()), ratio=round(float(np.exp(lowc.ratio[g2 == k].median())), 2)) for k in ("mostly out of squad", "mostly on the bench", "mixed")}
    res["b"]["fee_over_value_regulars"] = dict(n=int((cov.min_sh >= 0.5).sum()), ratio=round(float(np.exp(cov.ratio[cov.min_sh >= 0.5].median())), 2))
    q = pd.qcut(cov.absent_sh.rank(method="first"), 3, labels=["low", "middle", "high"])
    res["b"]["fee_over_value_by_out_of_squad"] = {k: dict(n=int((q == k).sum()), ratio=round(float(np.exp(cov.ratio[q == k].median())), 2)) for k in ("low", "middle", "high")}
    # (c) made it at the new club? next season's minutes share (any covered club) for transferred players with under half the minutes before
    c = lowc.merge(nx.rename(columns={"ey": "y"}), on=["player_id", "y"])
    g3 = np.where(c.absent_sh >= c.bench_sh + 0.15, "mostly out of squad", np.where(c.bench_sh >= c.absent_sh + 0.15, "mostly on the bench", "mixed"))
    res["c"] = {k: dict(n=int((g3 == k).sum()), regular_next=round(float((c.min_next[g3 == k] >= 0.5).mean()), 2) if (g3 == k).sum() else None) for k in ("mostly out of squad", "mostly on the bench", "mixed")}
    json.dump(res, open("data/result_injury.json", "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
