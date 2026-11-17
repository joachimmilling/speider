"""Test 29: does the balance of a line-up matter for the result, beyond how good the players are? Writes data/result_lineup_balance.json.

Unit: one team in one match. Quality of the starters: market value before the season and level from the season before.
Balance: the eleven's mean on each of the seven attributes, the lowest of them and their spread, and, per attribute,
the best starter on it interacted with how weak the rest of the eleven is on it.
"""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR
from sklearn.linear_model import RidgeCV

from projection_v3 import KW
from team_strength_backtest import prep

D = [f"d{i}" for i in range(7)]


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    sq, _ = prep(con)
    pl = sq.sort_values("m").drop_duplicates(["player_id", "ey"], keep="last")[["player_id", "ey", "level", "mv"] + D]
    pl["lmv"] = np.log(pl.mv)
    mt = con.execute("select match_id, end_year ey, home_id, away_id, home_goals, away_goals from fm_matches where home_goals is not null").fetchdf()
    st = con.execute("select l.match_id, l.team_id, l.player_id, m.end_year ey from fm_lineups l join fm_matches m using (match_id) where l.started = 1 and l.position_id <> 11").fetchdf()
    st = st.merge(pl, on=["player_id", "ey"], how="left")
    rows = []
    for (mid, tid), g in st.groupby(["match_id", "team_id"]):
        k = g[g.level.notna()]
        if len(k) < 7 or g.lmv.notna().sum() < 7: continue
        A = k[D].values; mean = A.mean(axis=0); best = A.max(axis=0); rest = (A.sum(axis=0) - best) / (len(k) - 1)
        r = dict(match_id=mid, team_id=tid, q_v=g.lmv.mean(), q_l=k.level.mean(), low=mean.min(), spread=mean.std(), known=len(k))
        for i in range(7): r[f"a{i}"] = mean[i]; r[f"b{i}"] = best[i]; r[f"x{i}"] = best[i] * (50 - rest[i]) / 50
        rows.append(r)
    t = pd.DataFrame(rows)
    h = mt.rename(columns={"home_id": "team_id", "away_id": "opp_id"}).assign(home=1, gd=mt.home_goals - mt.away_goals)
    a = mt.rename(columns={"away_id": "team_id", "home_id": "opp_id"}).assign(home=0, gd=mt.away_goals - mt.home_goals)
    u = pd.concat([h, a])[["match_id", "ey", "team_id", "opp_id", "home", "gd"]].merge(t, on=["match_id", "team_id"])
    u = u.merge(t[["match_id", "team_id", "q_v", "q_l"]].rename(columns={"team_id": "opp_id", "q_v": "o_v", "q_l": "o_l"}), on=["match_id", "opp_id"])
    Q = ["home", "q_v", "q_l", "o_v", "o_l"]; A7 = [f"a{i}" for i in range(7)]; X = [f"b{i}" for i in range(7)] + [f"x{i}" for i in range(7)]
    sets = {"1 quality of both elevens": Q, "2 plus seven attribute means": Q + A7, "3 plus lowest attribute and spread": Q + A7 + ["low", "spread"], "4 plus specialist interactions": Q + A7 + ["low", "spread"] + X}
    tr, te = u[u.ey <= 2025], u[u.ey >= 2026]
    mu, sd = tr[Q + A7 + ["low", "spread"] + X].mean(), tr[Q + A7 + ["low", "spread"] + X].std()
    z = lambda d, f: (d[f] - mu[f]) / sd[f]
    res = dict(team_matches=len(u), n_train=len(tr), n_test=len(te), ridge={}, trees={})
    for name, f in sets.items():
        m = RidgeCV(alphas=np.logspace(-1, 4, 20)).fit(z(tr, f), tr.gd); p = m.predict(z(te, f))
        res["ridge"][name] = dict(r2=round(float(1 - ((te.gd - p) ** 2).sum() / ((te.gd - te.gd.mean()) ** 2).sum()), 4), rank=round(float(pd.Series(p).corr(pd.Series(te.gd.values), method="spearman")), 3))
        if name.startswith("3"): res["coef_low_spread"] = dict(low=round(float(m.coef_[f.index("low")]), 3), spread=round(float(m.coef_[f.index("spread")]), 3))
        if name.startswith("2"): res["coef_attributes"] = [round(float(c), 3) for c in m.coef_[len(Q):]]
        p = HGBR(**KW).fit(tr[f], tr.gd).predict(te[f])
        res["trees"][name] = dict(r2=round(float(1 - ((te.gd - p) ** 2).sum() / ((te.gd - te.gd.mean()) ** 2).sum()), 4), rank=round(float(pd.Series(p).corr(pd.Series(te.gd.values), method="spearman")), 3))
    json.dump(res, open("data/result_lineup_balance.json", "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
