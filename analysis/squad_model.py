"""Test 22: a model of what makes a good squad.

Target: the team's goal difference per match, standardised within the league season.
Inputs, all known before the season and standardised the same way: the starting eleven picked by market value per role slot
(one keeper, two centre-backs, two full-backs, one each of DM, CM, AM, two wide, one striker) from the players who played
450+ minutes for the team; per line (keeper, defence, midfield, attack) the mean log value and the mean level from the season
before; depth; age; the weakest line; the seven collective attributes; and last season's goal difference.
Nested ridge models are compared out of time (fit to 2024, test 2025-26) and the smallest one within reach of the best
is refitted on everything and written for the site.

Writes data/result_squad_model.json.
"""
import json

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

from team_strength_backtest import SLOTS, prep

LINE = {"CB": "def", "FB": "def", "DM": "mid", "CM": "mid", "AM": "att", "W": "att", "ST": "att"}


def features(grp: pd.DataFrame) -> dict | None:
    g = grp[grp.mv.notna()].assign(lmv=lambda d: np.log(d.mv))
    role = g.role.fillna(g.pos_role)
    g = g.assign(role=role)
    first = pd.concat([g[g.role == r].nlargest(k, "lmv") for r, k in SLOTS.items()])
    if len(first) < 8: return None
    gk = g[g.role == "GK"].nlargest(1, "lmv")
    rest = g.drop(first.index.union(gk.index)).nlargest(7, "lmv")
    f = dict(n=len(first), top11=np.log(g.mv.nlargest(11).sum()), v_gk=gk.lmv.mean() if len(gk) else np.nan, depth=rest.lmv.mean() if len(rest) >= 3 else np.nan,
             age=first.age.mean(), v_all=first.lmv.mean(), l_all=first.level.mean())
    for ln in ("def", "mid", "att"):
        x = first[first.role.map(LINE) == ln]
        f[f"v_{ln}"] = x.lmv.mean() if len(x) else np.nan; f[f"l_{ln}"] = x.level.mean() if len(x) else np.nan
    for i in range(7): f[f"a{i}"] = first[f"d{i}"].mean()
    return f


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    sq, out = prep(con)
    rows = []
    for (lid, ey, tid), grp in sq.groupby(["league_id", "ey", "team_id"]):
        f = features(grp)
        if f: rows.append(dict(league_id=lid, ey=ey, team_id=tid, **f))
    t = pd.DataFrame(rows).merge(out[["league_id", "ey", "team_id", "gd"]], on=["league_id", "ey", "team_id"])
    t = t.merge(out.assign(ey=out.ey + 1)[["league_id", "ey", "team_id", "gd"]].rename(columns={"gd": "gd_prev"}), on=["league_id", "ey", "team_id"], how="left")
    t = t[t.groupby(["league_id", "ey"]).team_id.transform("size") >= 10].copy()
    sd_gd = float(t.groupby(["league_id", "ey"]).gd.std().median())
    t["age2"] = (t.age - 26.5) ** 2
    raw = ["top11", "v_gk", "v_def", "v_mid", "v_att", "v_all", "l_def", "l_mid", "l_att", "l_all", "depth", "age", "age2", "gd_prev", "gd"] + [f"a{i}" for i in range(7)]
    z = t.copy()
    for c in raw:
        gz = t.groupby(["league_id", "ey"])[c]
        z[c] = ((t[c] - gz.transform("mean")) / gz.transform("std").replace(0, 1)).fillna(0.0)      # missing = league average
    z["weak"] = z[["v_def", "v_mid", "v_att"]].min(axis=1)
    z["promoted"] = t.gd_prev.isna().astype(float).values                                             # no last season in this league
    A = [f"a{i}" for i in range(7)]
    sets = {"top11": ["top11"], "lines_value": ["v_gk", "v_def", "v_mid", "v_att"], "lines_value+level": ["v_gk", "v_def", "v_mid", "v_att", "l_def", "l_mid", "l_att"],
            "xi_value+level": ["v_all", "l_all"], "xi+depth+age": ["v_all", "l_all", "depth", "age", "age2"], "xi+depth+age+weak": ["v_all", "l_all", "depth", "age", "age2", "weak"],
            "xi+depth+age+attributes": ["v_all", "l_all", "depth", "age", "age2"] + A}
    tr, te = z[z.ey <= 2024], z[z.ey >= 2025]
    res = dict(team_seasons=len(z), n_train=len(tr), n_test=len(te), sd_goal_difference_per_match=round(sd_gd, 3), out_of_time={})
    def fit(f, d): return RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(d[f], d.gd)
    def score(f):
        p = fit(f, tr).predict(te[f]); return dict(r2=round(float(1 - ((te.gd - p) ** 2).sum() / (te.gd ** 2).sum()), 3), corr=round(float(np.corrcoef(p, te.gd)[0, 1]), 3))
    for name, f in sets.items():
        res["out_of_time"][name] = score(f); res["out_of_time"][name + " + last season"] = score(f + ["gd_prev", "promoted"])
    res["out_of_time"]["last season only"] = score(["gd_prev", "promoted"])
    # the site model: eleven value and level, depth, age, last season
    F = ["v_all", "l_all", "depth", "age", "age2", "gd_prev", "promoted"]
    m = fit(F, z)
    res["site_model"] = dict(features=F, coef=[round(float(c), 4) for c in m.coef_], intercept=round(float(m.intercept_), 4), alpha=float(m.alpha_))
    F0 = ["v_all", "l_all", "depth", "age", "age2"]; m0 = fit(F0, z)
    res["site_model_no_history"] = dict(features=F0, coef=[round(float(c), 4) for c in m0.coef_], intercept=round(float(m0.intercept_), 4))
    # last full season's standardised goal difference per team, for the site
    last = z[z.ey == z.ey.max()]
    res["gd_last"] = {str(int(a)): round(float(b), 2) for a, b in zip(last.team_id, last.gd)}
    res["age_sd"] = round(float(t.groupby(["league_id", "ey"]).age.std().median()), 2)
    json.dump(res, open("data/result_squad_model.json", "w"), indent=1)
    res.pop("gd_last"); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
