"""Build the local Speider site: static files that open without a server.

Reads data/speider.duckdb and data/frame_wide.pkl, writes data/site/ with the
page from web/ and the data as JavaScript files (loaded with script tags, so
the page works from file://). Only numbers that have passed their test are
exported; third-party market value is shown as such and never called Speider's.

Run:  PYTHONPATH=analysis python3 scripts/build_site.py   then open data/site/index.html
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as HGBC

from projection_young import C

OUT = Path(os.environ.get("SITE_OUT", "data/site"))
SHARDS = int(os.environ.get("SITE_SHARDS", 256))
STATS = ["rating", "goals_per_90", "expected_goals_per_90", "expected_assists_per_90", "total_scoring_att", "ontarget_scoring_att",
         "won_contest", "big_chance_created", "accurate_pass", "accurate_long_balls", "total_tackle", "interception",
         "ball_recovery", "effective_clearance", "poss_won_att_3rd"]
K = {"accurate_pass": 300, "goals_per_90": 1800, "poss_won_att_3rd": 2700, "interception": 1200, "rating": 1200, "total_tackle": 800, "ball_recovery": 800}
CUPS = "l.name not ilike '%cup%' and l.name not ilike '%pokal%' and l.name not ilike '%copa%' and l.name not ilike '%coppa%' and l.name not ilike '%trophy%'"
INDEX = {2015: 70, 2016: 79, 2017: 88, 2018: 93, 2019: 95, 2020: 82, 2021: 79, 2022: 81, 2023: 89, 2024: 84, 2025: 95, 2026: 100}


def role(c: int) -> str:
    if c == 11: return "GK"
    if c in (33, 34, 35, 36, 37): return "CB"
    if c in (32, 38, 51, 59): return "FB"
    if 62 <= c <= 68: return "DM"
    if 72 <= c <= 78: return "CM"
    if 83 <= c <= 87: return "AM"
    if c in (71, 79, 82, 88, 103, 107): return "W"
    if c in (104, 105, 106, 115): return "ST"
    return "CM"


def js(path: Path, name: str, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"window.SP=window.SP||{{}};window.SP[{json.dumps(name)}]=" + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + ";")


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for f in Path("web").iterdir(): shutil.copy(f, OUT / f.name)

    # season statistics: shrunk value and percentile within league, season and role
    s = con.execute(f"""
        select s.stat, s.league_id, l.name league, se.end_year ey, s.player_id, s.team_id, s.value v, s.minutes m,
               cast(json_extract(p.positions,'$[0]') as int) pos
        from fm_stats s join fm_seasons se using (league_id, season_id) join fm_leagues l using (league_id)
        join fm_players p using (player_id)
        where l.gender='male' and {CUPS} and s.stat in (select unnest(?)) and s.minutes >= 270 and isfinite(s.value) and se.end_year >= 2025
    """, [STATS + ["mins_played"]]).fetchdf()
    s["role"] = s.pos.fillna(0).astype(int).map(role)
    mins = s[s.stat == "mins_played"].sort_values(["ey", "m"]).groupby("player_id", as_index=False).last()[["player_id", "league_id", "league", "ey", "team_id", "m", "role"]]
    st = s[s.stat != "mins_played"].merge(mins[["player_id", "league_id", "ey"]], on=["player_id", "league_id", "ey"])
    full = s[s.stat != "mins_played"]
    g = full.groupby(["stat", "league_id", "ey", "role"]).v
    full = full.assign(mu=g.transform("mean"))
    full["shr"] = full.mu + (full.m / (full.m + full.stat.map(K).fillna(600))) * (full.v - full.mu)
    full["pct"] = full.groupby(["stat", "league_id", "ey", "role"]).shr.rank(pct=True) * 100
    full["n"] = full.groupby(["stat", "league_id", "ey", "role"]).shr.transform("size")
    st = full.merge(mins[["player_id", "league_id", "ey"]], on=["player_id", "league_id", "ey"])
    teams = con.execute("select league_id, team_id, any_value(name) team from fm_teams group by 1,2").fetchdf()
    mins = mins.merge(teams, on=["league_id", "team_id"], how="left")
    prof = con.execute("select player_id, name, birth, height, country, contract_end from fm_profiles where gender='male'").fetchdf()
    base = mins.merge(prof, on="player_id")
    base["age"] = (pd.Timestamp("2026-11-15") - pd.to_datetime(base.birth)).dt.days / 365.25
    ls = pd.read_csv("data/result_league_ranking.csv", index_col=0)["strength"]
    base["ls"] = base.league_id.map(ls)

    # chance of a big-five league within three years (test 17, without track record)
    w = pd.read_pickle("data/frame_wide.pkl")
    w["not_top5_now"] = ~(w.last_strength >= 0.25); w["top5_later"] = (w.top5_f3.fillna(0) >= 10).astype(int)
    tr = w[(w.age <= 23.5) & (w.y <= 2023) & w.not_top5_now]
    clf = HGBC(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0).fit(tr[C], tr.top5_later)
    now = w[(w.y == 2026) & (w.age <= 23.5) & w.not_top5_now].copy()
    now["p5"] = clf.predict_proba(now[C])[:, 1]
    base = base.merge(now[["player_id", "p5"]], on="player_id", how="left")
    base_rate = float(tr.top5_later.mean())

    # Speider value and value path (analysis/site_models.py), if built
    sm, smres = {}, {}
    if Path("data/site_models.pkl").exists():
        sm = pd.read_pickle("data/site_models.pkl").set_index("player_id").to_dict("index")
        smres = json.load(open("data/result_site_models.json"))
    svh = {}
    if Path("data/site_models_hist.pkl").exists():
        svh = {k: v.sort_values("y") for k, v in pd.read_pickle("data/site_models_hist.pkl").groupby("player_id")}

    # most similar players by style: distance between percentile profiles within the role
    pv = st[st.stat != "big_chance_created"].pivot_table(index="player_id", columns="stat", values="pct").fillna(50)
    info = base.set_index("player_id")
    sim = {}
    for role_, grp in info.groupby("role"):
        ids_ = [i for i in grp.index if i in pv.index]
        cand = [i for i in ids_ if info.at[i, "m"] >= 600]
        if len(cand) < 6: continue
        A, B = pv.loc[ids_].values, pv.loc[cand].values
        for k0 in range(0, len(ids_), 500):
            d2 = ((A[k0:k0 + 500, None, :] - B[None, :, :]) ** 2).mean(axis=2) ** 0.5
            for j, row in enumerate(d2):
                pid_ = ids_[k0 + j]; o = np.argsort(row)[:6]
                sim[pid_] = [[int(cand[x]), info.at[cand[x], "name"], info.at[cand[x], "team"], round(float(info.at[cand[x], "age"]), 1), round(float(row[x]), 1)] for x in o if cand[x] != pid_][:5]

    car = con.execute("select player_id, season_name, end_year, league_name, team, apps, goals, assists, rating from fm_career where apps >= 1 and end_year is not null order by end_year desc").fetchdf()
    mv = con.execute("select player_id, year(date) y, arg_max(value, date) v from fm_mv where value > 0 group by 1,2 order by 2").fetchdf()
    ids = set(base.player_id)
    car = car[car.player_id.isin(ids)]; mv = mv[mv.player_id.isin(ids)]
    carg = {k: v for k, v in car.groupby("player_id")}; mvg = {k: v for k, v in mv.groupby("player_id")}; stg = {k: v for k, v in st.groupby("player_id")}

    def r(x, d=2):
        return None if x is None or (isinstance(x, float) and not np.isfinite(x)) or pd.isna(x) else round(float(x), d)
    index, shards = [], {i: {} for i in range(SHARDS)}
    for b in base.itertuples():
        pid = int(b.player_id)
        index.append([pid, b.name, r(b.age, 1), b.country, b.role, b.team, b.league, int(b.m), r(b.p5, 3), r(b.ls, 2)])
        d = dict(id=pid, name=b.name, age=r(b.age, 1), country=b.country, height=r(b.height, 0), role=b.role, team=b.team, league=b.league, season=int(b.ey),
                 minutes=int(b.m), contract=str(b.contract_end)[:10] if pd.notna(b.contract_end) else None, p5=r(b.p5, 3), ls=r(b.ls, 2))
        if pid in stg: d["stats"] = [[x.stat, r(x.shr, 2), r(x.v, 2), r(x.pct, 0), int(x.n)] for x in stg[pid].itertuples()]
        if pid in carg: d["career"] = [[x.season_name, x.league_name, x.team, r(x.apps, 0), r(x.goals, 0), r(x.assists, 0), r(x.rating, 2)] for x in carg[pid].head(40).itertuples()]
        if pid in mvg: d["mv"] = [[int(x.y), int(x.v)] for x in mvg[pid].itertuples()]
        if pid in sim: d["sim"] = sim[pid]
        if pid in sm:
            v = sm[pid]
            if pid in svh: d["svh"] = [[int(x.y), int(x.sv)] for x in svh[pid].itertuples()]
            d["val"] = [int(v["sv"]), int(v["sv_lo"]), int(v["sv_hi"]), int(v["mv"])]
            # light smoothing over horizons in log space (each horizon is a separate model), anchored at 1 today
            sm3 = lambda xs: [round(float(np.exp(0.25 * a_ + 0.5 * b_ + 0.25 * c_)), 3) for a_, b_, c_ in zip(np.log([1.0] + xs[:-1]), np.log(xs), np.log(xs[1:] + xs[-1:]))]
            lo_, md_, hi_ = (sm3([float(v[f"g{h}{k}"]) for h in range(1, 6)]) for k in ("_lo", "", "_hi"))
            d["path"] = [[h, lo_[h - 1], md_[h - 1], hi_[h - 1], r(v[f"play{h}"], 2)] for h in range(1, 6)]
            d["typ"] = sm3([float(smres["path"][str(h)]["typical"][v["band"]]) for h in range(1, 6)])
            index[-1] += [int(v["sv"]), md_[2], int(v["mv"])]
        shards[pid % SHARDS][pid] = d
    js(OUT / "data/players.js", "players", index)
    for i, d in shards.items(): js(OUT / f"data/shard/{i}.js", f"shard{i}", d)

    # across eras: non-penalty goals per 90 against the full squads of the league season
    e = con.execute("""
        select s.tournament_id t, coalesce(tt.name, h.name) league, s.end_year y, s.player_id, s.player, s.team, s.minutesPlayed m,
               coalesce(s.goals,0) goals, coalesce(s.penaltyGoals,0) pens, coalesce(s.assists,0) assists
        from ss_stats s left join (select tournament_id, name from ss_tournaments where name is not null) tt using (tournament_id)
        left join (select tournament_id, name from ss_tournaments where history) h using (tournament_id)
        where s.minutesPlayed >= 900 and coalesce(s.saves,0) < 20
    """).fetchdf().drop_duplicates(["t", "y", "player_id"])
    e["npg90"] = (e.goals - e.pens) / e.m * 90
    gg = e.groupby(["t", "y"])
    e["n"] = gg.npg90.transform("size"); e = e[e.n >= 100].copy(); gg = e.groupby(["t", "y"])
    e["z"] = (e.npg90 - gg.npg90.transform("mean")) / gg.npg90.transform("std"); e["pct"] = gg.npg90.rank(pct=True) * 100
    js(OUT / "data/eras.js", "eras", [[x.player, int(x.y), x.league, x.team, int(x.m), int(x.goals), int(x.pens), int(x.assists), r(x.npg90, 2), r(x.z, 2), r(x.pct, 1)] for x in e.itertuples()])

    names = con.execute("select league_id, name, cc from fm_leagues").fetchdf().set_index("league_id")
    lg = [[names.name.get(i, str(i)), names.cc.get(i, ""), r(v, 2)] for i, v in ls.sort_values(ascending=False).items() if i in names.index]
    d = np.diff(np.log(list(INDEX.values()))); drift, sd = float(d.mean()), float(d.std(ddof=1))
    proj = [[2026 + h, round(100 * np.exp(drift * h)), round(100 * np.exp(drift * h - 1.28 * sd * np.sqrt(h))), round(100 * np.exp(drift * h + 1.28 * sd * np.sqrt(h)))] for h in range(1, 9)]
    js(OUT / "data/market.js", "market", dict(index=[[k, v] for k, v in INDEX.items()], projection=proj, leagues=lg, top5_base_rate=round(base_rate, 3),
                                             built="2026-11-16", shards=SHARDS, value_test=smres.get("value"), counts=dict(players=len(index), eras=len(e))))
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"players {len(index)}, era seasons {len(e)}, leagues {len(lg)}, site {size:.0f} MB in {OUT}")


if __name__ == "__main__":
    main()
