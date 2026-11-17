"""Test 25: does the season in progress improve the fee model? Writes data/result_current_season.json."""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from current_season import CUR, for_transfers, rows
from price_model_v4 import INDEX
from projection_v3 import KW
from site_models import PF, err
from transfers import load


def main() -> None:
    b = pd.read_pickle("data/frame_wide.pkl").drop_duplicates(["player_id", "y"], keep="last")
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    t = load(con).drop(columns=["name"]); t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    ids = con.execute("select player_id, date, from_id from fm_transfers").fetchdf(); ids["date"] = pd.to_datetime(ids.date)
    t = t.merge(ids.drop_duplicates(["player_id", "date"]), on=["player_id", "date"], how="left")
    m = for_transfers(t.merge(b, on=["player_id", "y"]), rows(con))
    m["val"] = np.log(m.mv); m["ratio"] = np.log(m.fee / m.yy.map(INDEX) * 100) - m.val
    tr, te = m[m.yy <= 2024], m[m.yy >= 2025]; scale = te.yy.map(INDEX).values / 100
    has = (te.cur_min >= 270).values; win = has & te.mo.isin([12, 1, 2, 3]).values
    res = dict(n_train=len(tr), n_test=len(te), train_with_running_season=int((tr.cur_min >= 270).sum()), test_with_running_season=int(has.sum()), test_winter=int(win.sum()), miss={})
    P = {}
    for name, f in (("A site inputs", PF), ("B plus season in progress", PF + CUR)):
        P[name] = np.exp(HGBR(loss="absolute_error", **KW).fit(tr[f], tr.ratio).predict(te[f]) + te.val.values) * scale
        res["miss"][name] = dict(all=round(err(P[name], te.fee.values), 3), running_season=round(err(P[name][has], te.fee.values[has]), 3), winter=round(err(P[name][win], te.fee.values[win]), 3))
    res["miss"]["third-party value"] = dict(all=round(err(te.mv.values, te.fee.values), 3), running_season=round(err(te.mv.values[has], te.fee.values[has]), 3), winter=round(err(te.mv.values[win], te.fee.values[win]), 3))
    # plain reading: fee / market value by how the running season compares with the last one
    d = m[(m.cur_min >= 450) & m.cur_d_rating.notna()]
    q = pd.qcut(d.cur_d_rating.rank(method="first"), 3, labels=["worse", "same", "better"])
    res["fee_over_value_by_running_form"] = {k: dict(n=int((q == k).sum()), ratio=round(float(np.exp(d.ratio[q == k].median())), 2)) for k in ("worse", "same", "better")}
    lv = pd.qcut(d.cur_rating.rank(method="first"), 3, labels=["low", "middle", "high"])
    res["fee_over_value_by_running_rating"] = {k: dict(n=int((lv == k).sum()), ratio=round(float(np.exp(d.ratio[lv == k].median())), 2)) for k in ("low", "middle", "high")}
    json.dump(res, open("data/result_current_season.json", "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
