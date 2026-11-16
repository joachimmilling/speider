"""Test 21: does the best eleven by level say anything about how teams actually do?

For every team season, the eleven is picked the way the site picks it (best by level per role slot) from the
players who played for the team that season, using only their numbers from the season BEFORE (in whatever league
they played then, on the common scale). The outcome is the team's goal difference per match that season.
Compared with two baselines known before the season: the market value of the eleven most valuable players,
and last season's goal difference. Also asks whether the seven collective attributes add anything beyond the level.

Writes data/result_team_strength.json.
"""
import json
import sys

import duckdb
import numpy as np
import pandas as pd
from scipy.special import ndtr, ndtri
from sklearn.linear_model import RidgeCV

sys.path.insert(0, "scripts")
from build_site import CUPS, DIMS, K, NEEDP, STATS, role  # noqa: E402

LS_PER_SD = 0.23
SLOTS = {"CB": 2, "FB": 2, "DM": 1, "CM": 1, "AM": 1, "W": 2, "ST": 1}


def prep(con):
    """Squads (players with 450+ minutes, with level and attributes from the season before, value before the season, age) and team outcomes."""
    s = con.execute(f"""
        select s.stat, s.league_id, se.end_year ey, s.player_id, s.team_id, s.value v, s.sub_value sv, s.minutes m,
               cast(json_extract(p.positions,'$[0]') as int) pos
        from fm_stats s join fm_seasons se using (league_id, season_id) join fm_leagues l using (league_id)
        join fm_players p using (player_id)
        where l.gender='male' and {CUPS} and s.stat in (select unnest(?)) and isfinite(s.value) and se.end_year between 2017 and 2026
    """, [STATS + ["mins_played", "goals", "goals_conceded"]]).fetchdf()
    s["role"] = s.pos.fillna(0).astype(int).map(role)
    ls = pd.read_csv("data/result_league_ranking.csv", index_col=0)["strength"]

    # player level per season, exactly as on the site
    full = s[s.stat.isin(STATS) & (s.stat != "big_chance_created") & (s.m >= 270)].copy()
    g = full.groupby(["stat", "league_id", "ey", "role"]).v
    full["mu"] = g.transform("mean")
    full["shr"] = full.mu + (full.m / (full.m + full.stat.map(K).fillna(600))) * (full.v - full.mu)
    full["pct"] = full.groupby(["stat", "league_id", "ey", "role"]).shr.rank(pct=True) * 100
    mins = s[(s.stat == "mins_played") & (s.m >= 900)].sort_values("m").groupby(["player_id", "ey"], as_index=False).last()[["player_id", "ey", "league_id", "role"]]
    pv = full.merge(mins[["player_id", "ey", "league_id"]], on=["player_id", "ey", "league_id"]).pivot_table(index=["player_id", "ey"], columns="stat", values="pct").fillna(50)
    dims = np.column_stack([pv[[c for c in cols if c in pv.columns]].mean(axis=1).values if any(c in pv.columns for c in cols) else np.full(len(pv), 50.0) for cols in DIMS])
    meta = pv.index.to_frame(index=False).merge(mins, on=["player_id", "ey"], how="left")
    shift = ((meta.league_id.map(ls).fillna(0.0) - 0.30) / LS_PER_SD).values[:, None]
    adj = ndtr(ndtri(np.clip(dims / 100, 0.01, 0.99)) + shift) * 100
    meta[[f"d{i}" for i in range(7)]] = adj
    meta["level"] = [np.mean(adj[i, NEEDP[r]]) if r in NEEDP else np.nan for i, r in enumerate(meta.role)]
    prior = meta.assign(ey=meta.ey + 1).drop(columns=["league_id"])      # numbers from the season before

    # team outcome: goals scored (players' goals) minus goals conceded (keepers' totals), per 90 keeper minutes
    gf = s[s.stat == "goals"].groupby(["league_id", "ey", "team_id"]).v.sum().rename("gf")
    gk = s[s.stat == "goals_conceded"].groupby(["league_id", "ey", "team_id"]).agg(ga=("sv", "sum"), gm=("m", "sum"))
    out = pd.concat([gf, gk], axis=1).dropna().reset_index()
    out = out[out.gm >= 1800]
    out["gd"] = (out.gf - out.ga) / (out.gm / 90)

    # squads: players with 450+ minutes for the team that season
    sq = s[(s.stat == "mins_played") & (s.m >= 450)][["league_id", "ey", "team_id", "player_id", "m"]].merge(prior, on=["player_id", "ey"], how="left")
    mv = con.execute("select player_id, year(date) + (month(date) >= 8)::int ey, arg_max(value, date) mv from fm_mv where value > 0 group by 1, 2").fetchdf()   # latest value before 1 August
    sq = sq.merge(mv, on=["player_id", "ey"], how="left")
    age = con.execute("select player_id, birth from fm_profiles where birth is not null").fetchdf()
    sq = sq.merge(age, on="player_id", how="left"); bd = pd.to_datetime(sq.birth, errors="coerce")
    sq["age"] = sq.ey - 0.5 - bd.dt.year - (bd.dt.month - 1) / 12       # age around the turn of the year in the season
    pos = s[["player_id", "role", "pos"]].drop_duplicates("player_id").rename(columns={"role": "pos_role"})
    u = pos.pos.fillna(5).astype(int) % 10                               # last digit of the position code: low = right, high = left
    pos["left"] = np.where(u >= 6, 1, np.where(u <= 4, 0, pos.player_id % 2 == 0)).astype(int); pos = pos.drop(columns=["pos"])
    sq = sq.merge(pos, on="player_id", how="left")
    return sq, out


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    sq, out = prep(con)
    rows = []
    for (lid, ey, tid), grp in sq.groupby(["league_id", "ey", "team_id"]):
        lv = grp[grp.level.notna()]
        first = pd.concat([lv[lv.role == r].nlargest(k, "level") for r, k in SLOTS.items()])
        if len(first) < 8: continue
        act = lv.nlargest(10, "m")                                     # the ten who actually played most, for comparison
        rows.append(dict(league_id=lid, ey=ey, team_id=tid, n=len(first), level=first.level.mean(), level_played=act.level.mean(),
                         value=np.log(grp.mv.nlargest(11).sum()) if grp.mv.notna().sum() >= 8 else np.nan,
                         **{f"a{i}": first[f"d{i}"].mean() for i in range(7)}))
    t = pd.DataFrame(rows).merge(out[["league_id", "ey", "team_id", "gd"]], on=["league_id", "ey", "team_id"])
    t = t.merge(out.assign(ey=out.ey + 1)[["league_id", "ey", "team_id", "gd"]].rename(columns={"gd": "gd_prev"}), on=["league_id", "ey", "team_id"], how="left")
    t["nteams"] = t.groupby(["league_id", "ey"]).team_id.transform("size")
    t = t[t.nteams >= 10].copy()
    cols = ["level", "level_played", "value", "gd_prev", "gd"] + [f"a{i}" for i in range(7)]
    z = t.copy()
    for c in cols: z[c] = t.groupby(["league_id", "ey"])[c].transform(lambda x: (x - x.mean()) / (x.std() or 1))   # within league season
    res = dict(team_seasons=len(t), league_seasons=int(t.groupby(["league_id", "ey"]).ngroups), years=[int(t.ey.min()), int(t.ey.max())])
    both = z.dropna(subset=["level", "value", "gd_prev", "gd"])
    res["n_all_three"] = len(both)
    res["corr_with_goal_difference"] = {c: round(float(both[c].corr(both.gd)), 3) for c in ("level", "level_played", "value", "gd_prev")}
    res["corr_level_any"] = round(float(z.level.corr(z.gd)), 3)
    top5 = both[both.league_id.isin([47, 87, 54, 55, 53])]
    res["big_five"] = dict(n=len(top5), **{c: round(float(top5[c].corr(top5.gd)), 3) for c in ("level", "value", "gd_prev")})
    # out of time: fit on seasons to 2024, test on 2025-26
    tr, te = both[both.ey <= 2024], both[both.ey >= 2025]
    A = [f"a{i}" for i in range(7)]
    def r2(f):
        m = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(tr[f], tr.gd); p = m.predict(te[f])
        return round(float(1 - ((te.gd - p) ** 2).sum() / ((te.gd - te.gd.mean()) ** 2).sum()), 3), m
    res["out_of_time_r2"] = dict(n_train=len(tr), n_test=len(te))
    for name, f in (("level", ["level"]), ("attributes", A), ("value", ["value"]), ("gd_prev", ["gd_prev"]), ("value+gd_prev", ["value", "gd_prev"]),
                    ("value+gd_prev+level", ["value", "gd_prev", "level"]), ("value+gd_prev+attributes", ["value", "gd_prev"] + A)):
        res["out_of_time_r2"][name], m = r2(f)
        if name == "attributes": res["attribute_weights"] = [round(float(c), 3) for c in m.coef_]
    json.dump(res, open("data/result_team_strength.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
