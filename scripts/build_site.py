"""Build the local Speider site: static files that open without a server.

Reads data/speider.duckdb and data/frame_wide.pkl, writes data/site/ with the
page from web/ and the data as JavaScript files (loaded with script tags, so
the page works from file://). Only numbers that have passed their test are
exported; third-party market value is shown as such and never called Speider's.

Run:  SITE_LOGOS=1 PYTHONPATH=analysis python3 scripts/build_site.py   then open data/site/index.html
SITE_LOGOS=1 makes the page load club and league crests straight from the data source's image server (local,
private use only; nothing is copied into the repo or the build). Without it the page shows initials instead.
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

TYPES = {
    "ST": {"finisher": ["goals_per_90", "expected_goals_per_90", "ontarget_scoring_att"], "pressing_forward": ["poss_won_att_3rd", "total_tackle", "ball_recovery"], "link_forward": ["expected_assists_per_90", "accurate_pass", "won_contest"]},
    "W": {"dribbler": ["won_contest"], "goal_winger": ["goals_per_90", "expected_goals_per_90", "total_scoring_att"], "creator": ["expected_assists_per_90", "accurate_pass"]},
    "AM": {"creator": ["expected_assists_per_90", "accurate_pass"], "goal_threat": ["goals_per_90", "expected_goals_per_90", "total_scoring_att"], "dribbler": ["won_contest"]},
    "CM": {"playmaker": ["accurate_pass", "accurate_long_balls", "expected_assists_per_90"], "box_to_box": ["total_tackle", "ball_recovery", "total_scoring_att", "expected_goals_per_90"], "ball_winner": ["total_tackle", "interception", "ball_recovery"]},
    "DM": {"anchor": ["interception", "effective_clearance", "ball_recovery"], "deep_playmaker": ["accurate_pass", "accurate_long_balls"], "ball_winner": ["total_tackle", "poss_won_att_3rd", "ball_recovery"]},
    "CB": {"ball_playing": ["accurate_pass", "accurate_long_balls"], "stopper": ["total_tackle", "interception"], "cover": ["effective_clearance", "ball_recovery"]},
    "FB": {"attacking_back": ["expected_assists_per_90", "won_contest", "total_scoring_att"], "defensive_back": ["total_tackle", "interception", "effective_clearance"], "passing_back": ["accurate_pass", "accurate_long_balls"]},
}
NEEDP = {"ST": [0, 1, 5], "W": [2, 1, 0], "AM": [1, 0, 2], "CM": [3, 4, 1], "DM": [4, 5, 3], "CB": [6, 4, 3], "FB": [1, 4, 3]}
DIMS = [["goals_per_90", "expected_goals_per_90", "ontarget_scoring_att"], ["expected_assists_per_90"], ["won_contest"], ["accurate_pass", "accurate_long_balls"],
        ["total_tackle", "interception"], ["ball_recovery", "poss_won_att_3rd"], ["effective_clearance"]]
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
    # in the attacking-midfield line 83 and 87 are the wide players (Saka, Vinicius), 84-86 the central ones
    if c in (84, 85, 86): return "AM"
    if c in (71, 79, 82, 83, 87, 88, 103, 107): return "W"
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
    # the season shown is the latest one with 900+ minutes (a few weeks into a new season the comparison group
    # is a handful of players and every rank is 99 or 33); players without such a season keep their latest
    mins = s[s.stat == "mins_played"].assign(ok=lambda d_: d_.m >= 900).sort_values(["ok", "ey", "m"]).groupby("player_id", as_index=False).last()[["player_id", "league_id", "league", "ey", "team_id", "m", "role"]]
    # Players with a market value but no season of 270 league minutes (a 16-year-old with a few substitute appearances) are shown
    # too, without numbers on the pitch: latest senior row from this or last season.
    low = con.execute(f"""
        select s.player_id, s.league_id, l.name league, se.end_year ey, s.team_id, s.minutes m, cast(json_extract(p.positions,'$[0]') as int) pos
        from fm_stats s join fm_seasons se using (league_id, season_id) join fm_leagues l using (league_id) join fm_players p using (player_id)
        where l.gender='male' and {CUPS} and s.stat = 'mins_played' and se.end_year >= 2026
          and s.player_id in (select player_id from fm_mv where value > 0)
    """).fetchdf()
    low = low[~low.player_id.isin(mins.player_id)]
    low["role"] = low.pos.fillna(0).astype(int).map(role)
    low["youth"] = low.league.str.contains(r"Premier League 2|U\d\d|Youth|Reserve", case=False)
    low = low.sort_values(["youth", "ey", "m"], ascending=[False, True, True]).groupby("player_id", as_index=False).last()[["player_id", "league_id", "league", "ey", "team_id", "m", "role"]]
    print("players shown without a 270-minute season:", len(low))
    mins = pd.concat([mins, low], ignore_index=True)
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
    pcols = [c[0] for c in con.execute("describe fm_profiles").fetchall()]
    prof = con.execute("select player_id, name, birth, height, country, contract_end" + (", cur_team_id, injury" if "cur_team_id" in pcols else ", null::bigint cur_team_id, null::varchar injury") + " from fm_profiles where gender='male'").fetchdf()
    base = mins.merge(prof, on="player_id")
    base["age"] = (pd.Timestamp("2026-11-15") - pd.to_datetime(base.birth)).dt.days / 365.25
    # league names repeat across countries (Premier League, Serie A): add the country code where a name is not unique
    lcc = con.execute("select league_id, cc from fm_leagues").fetchdf().set_index("league_id").cc
    dup = base.groupby("league").league_id.nunique()
    base["league"] = [f"{n} ({lcc.get(i)})" if dup.get(n, 1) > 1 and lcc.get(i) else n for n, i in zip(base.league, base.league_id)]
    ls = pd.read_csv("data/result_league_ranking.csv", index_col=0)["strength"]
    base["ls"] = base.league_id.map(ls)
    # The numbers come from the latest season with 900+ minutes, but the club shown must be today's: a player who
    # moved in the summer has his numbers from the old club and league (kept as ls_stat for the common scale).
    base["ls_stat"] = base.ls
    # Today's club: the latest season row with ANY minutes (a striker with 227 minutes at his new club has moved), then the
    # latest transfer since June if it points somewhere else (signed, not yet played). The 270-minute floor is for numbers only.
    cur = con.execute(f"""
        select s.player_id, s.league_id c_lid, l.name c_league, s.team_id c_tid, se.end_year ey, s.minutes m
        from fm_stats s join fm_seasons se using (league_id, season_id) join fm_leagues l using (league_id)
        where l.gender='male' and {CUPS} and l.name not ilike '%champions league%' and l.name not ilike '%europa%' and l.name not ilike '%conference%'
          and s.stat = 'mins_played' and se.end_year >= 2025
    """).fetchdf()
    # a first-team player with a rehab match for the reserves is still a first-team player: senior rows from this or last season win
    cur["senior"] = ~(cur.c_tid.map(teams.drop_duplicates("team_id").set_index("team_id").team).fillna("").str.contains(r"U\d\d| II$| 2$| B$|NXT|Jong ") | cur.c_league.str.contains(r"Premier League 2|U\d\d|Youth|Reserve", case=False)) & (cur.ey >= 2026)
    cur = cur.sort_values(["senior", "ey", "m"]).groupby("player_id", as_index=False).last()[["player_id", "c_lid", "c_league", "c_tid"]]
    tl = cur.groupby("c_tid").agg(c_lid=("c_lid", lambda x: x.mode().iloc[0]), c_league=("c_league", lambda x: x.mode().iloc[0]))
    tr_ = con.execute("select player_id, arg_max(to_id, date) to_id from fm_transfers where date >= '2026-06-01' and to_id is not null group by 1").fetchdf()
    cur = cur.merge(tr_, on="player_id", how="left")
    mvt = cur.to_id.notna() & (cur.to_id != cur.c_tid) & cur.to_id.isin(tl.index)
    cur.loc[mvt, "c_lid"] = cur.loc[mvt, "to_id"].map(tl.c_lid).values; cur.loc[mvt, "c_league"] = cur.loc[mvt, "to_id"].map(tl.c_league).values
    cur.loc[mvt, "c_tid"] = cur.loc[mvt, "to_id"].values; cur = cur.drop(columns=["to_id"])
    print("club taken from a transfer since June:", int(mvt.sum()))
    # the provider's own "current team" on the profile (profiles downloaded from 2026-11-17) is the best source where it exists
    cur = cur.merge(prof[["player_id", "cur_team_id"]], on="player_id", how="left")
    mvp = cur.cur_team_id.notna() & (cur.cur_team_id != cur.c_tid) & cur.cur_team_id.isin(tl.index)
    cur.loc[mvp, "c_lid"] = cur.loc[mvp, "cur_team_id"].map(tl.c_lid).values; cur.loc[mvp, "c_league"] = cur.loc[mvp, "cur_team_id"].map(tl.c_league).values
    cur.loc[mvp, "c_tid"] = cur.loc[mvp, "cur_team_id"].values; cur = cur.drop(columns=["cur_team_id"])
    print("club taken from the profile:", int(mvp.sum()))
    base = base.merge(cur, on="player_id", how="left")
    mvd = (base.c_tid.notna() & (base.c_tid != base.team_id)).values
    tn_ = teams.drop_duplicates("team_id").set_index("team_id").team
    base.loc[mvd, "team"] = base.loc[mvd, "c_tid"].map(tn_).values
    base.loc[mvd, "league"] = [f"{n} ({lcc.get(i)})" if dup.get(n, 1) > 1 and lcc.get(i) else n for n, i in zip(base.loc[mvd, "c_league"], base.loc[mvd, "c_lid"])]
    base.loc[mvd, "ls"] = base.loc[mvd, "c_lid"].map(ls).values
    base.loc[mvd, "team_id"] = base.loc[mvd, "c_tid"].values; base.loc[mvd, "league_id"] = base.loc[mvd, "c_lid"].values
    print("players shown at a newer club than their numbers:", int(mvd.sum()))

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
    # form nowcast (analysis/form_nowcast.py): expected value change over the running season with and without this season's numbers,
    # what has already happened since the summer, minutes and rating so far
    formd, formlift = {}, {}
    if Path("data/form_now.pkl").exists():
        for x in pd.read_pickle("data/form_now.pkl").itertuples():
            formd[int(x.player_id)] = [round(float(x.exp), 3), round(float(x.base), 3), None if pd.isna(x.real) else round(float(x.real), 3), int(x.cur_min), None if pd.isna(x.cur_rating) else round(float(x.cur_rating), 2)]
            if x.cur_min >= 450: formlift[int(x.player_id)] = round(float(x.exp - x.base), 3)
    # Tests 27 and 32b: fees run above the model for players in form.
    fs = json.load(open("data/result_form_slope.json")) if Path("data/result_form_slope.json").exists() else {}
    # Test 32b: the lift is one-sided. Form above expectation raises the price; form below it does not lower it (no such pattern in fees).
    s_up, s_dn = fs.get("used_on_site", [0.0, 0.0])
    if s_up or s_dn:
        for pid_, f_ in formd.items():
            if pid_ in sm:
                ex_ = f_[0] - f_[1]; k_ = float(np.exp(s_up * max(ex_, 0.0) + s_dn * min(ex_, 0.0)))
                for c_ in ["sv", "sv_lo", "sv_hi"] + [f"bt{T_}" for T_ in range(1, 6) if f"bt{T_}" in sm[pid_]]: sm[pid_][c_] = sm[pid_][c_] * k_
                f_.append(round(k_, 3))
    svh = {}
    if Path("data/site_models_hist.pkl").exists():
        svh = {k: v.sort_values("y") for k, v in pd.read_pickle("data/site_models_hist.pkl").groupby("player_id")}

    # most similar players by style: distance between percentile profiles within the role
    pv = st[st.stat != "big_chance_created"].pivot_table(index="player_id", columns="stat", values="pct").fillna(50)
    info = base.set_index("player_id")
    posc = {int(k): int(v) for k, v in s.dropna(subset=["pos"]).drop_duplicates("player_id").set_index("player_id").pos.items()}   # primary position code, for the pitch
    # player type: the style group whose numbers the player ranks highest on within his role
    ptype = {}
    for pid_, row in pv.iterrows():
        role_ = info.at[pid_, "role"] if pid_ in info.index else None
        groups = TYPES.get(role_, {})
        if role_ == "GK": ptype[pid_] = "keeper"; continue
        sc = {k: float(np.mean([row.get(c, 50) for c in cols])) for k, cols in groups.items()}
        if sc: best = max(sc, key=sc.get); ptype[pid_] = best if sc[best] >= 58 else "all_round"
    sim, near = {}, {}
    for role_, grp in info.groupby("role"):
        ids_ = [i for i in grp.index if i in pv.index]
        cand = [i for i in ids_ if info.at[i, "m"] >= 600]
        if len(cand) < 6: continue
        A, B = pv.loc[ids_].values, pv.loc[cand].values
        for k0 in range(0, len(ids_), 500):
            d2 = ((A[k0:k0 + 500, None, :] - B[None, :, :]) ** 2).mean(axis=2) ** 0.5
            for j, row in enumerate(d2):
                pid_ = ids_[k0 + j]; o = np.argsort(row)[:6]
                near[pid_] = [int(cand[x]) for x in np.argsort(row)[:40] if cand[x] != pid_]
                sim[pid_] = [[int(cand[x]), info.at[cand[x], "name"], info.at[cand[x], "team"], round(float(info.at[cand[x], "age"]), 1), round(float(row[x]), 1)] for x in o if cand[x] != pid_][:5]

    car = con.execute("select player_id, season_name, end_year, league_name, team, apps, goals, assists, rating from fm_career where apps >= 1 and end_year is not null order by end_year desc").fetchdf()
    mv = con.execute("select player_id, year(date) y, arg_max(value, date) v from fm_mv where value > 0 group by 1,2 order by 2").fetchdf()
    ids = set(base.player_id)
    car = car[car.player_id.isin(ids)]; mv = mv[mv.player_id.isin(ids)]
    carg = {k: v for k, v in car.groupby("player_id")}; mvg = {k: v for k, v in mv.groupby("player_id")}; stg = {k: v for k, v in st.groupby("player_id")}

    # Buy verdicts (test 20): the fee against the third-party value on the day, relative to the same year's typical
    # ratio (the provider's level drifts against fees from year to year), in fifths within the year.
    from transfers import load as load_transfers
    tf = load_transfers(con).rename(columns={"yy": "y"}).sort_values(["player_id", "date"])
    # verdict: Speider's expected value in three years against the fee, in fifths within the year and fee size
    # (walk-forward, from analysis/buy_verdict_backtest.py); rel = expected value in three years / fee
    bv = pd.read_pickle("data/buy_verdicts.pkl")[["player_id", "date", "C2", "verdict"]].rename(columns={"C2": "rel", "verdict": "q"})
    tf = tf.merge(bv, on=["player_id", "date"], how="inner")
    nxt = tf.groupby("player_id").shift(-1); tf["next_fee"], tf["next_y"] = nxt.fee, nxt.y
    tfg = {k: v for k, v in tf.groupby("player_id")}
    bvres = json.load(open("data/result_buy_verdict.json")); verdict_stats = dict(all=bvres["verdict"], large=bvres["verdict_large"], next_fee_r2=bvres["next_fee_r2"])
    # a value on the day below a tenth of the fee is a stale provider value, not a verdict: left out of the lists
    d26 = tf[(tf.y == 2026) & (tf.fee >= 2e6) & (tf.mv >= 0.1 * tf.fee) & tf.player_id.isin(set(base.player_id))]
    deal = lambda g_: [[int(x.player_id), x["name"], x.from_name, x.to_name, int(x.fee), int(x.mv), round(float(x.rel), 2)] for _, x in g_.iterrows()]
    deals = dict(cheap=deal(d26.sort_values("rel", ascending=False).head(12)), dear=deal(d26.sort_values("rel").head(12)))
    # style dimensions per player for the team view (same groups as the radar on the player page)
    dimv = {pid_: [int(round(float(np.mean([row[c] for c in cols if c in row.index])))) for cols in DIMS] for pid_, row in pv.iterrows()}

    # One scale across leagues: rank within the own league moved by the league's strength, read as rank among
    # big-five players. ASSUMPTION, not fitted: 0.35 strength units equal one standard deviation of player quality,
    # reference level 0.30 (the big-five average). A 90 in a league at -0.14 becomes about 51.
    from scipy.special import ndtr, ndtri
    # How much one unit of league strength is worth in standard deviations of player quality, from players who
    # changed league between the two latest full seasons: change in rating rank (as a z-score) against change in strength.
    rt = full[(full.stat == "rating") & (full.m >= 900) & full.ey.isin([2025, 2026])].assign(z=lambda d_: ndtri(np.clip(d_.pct / 100, 0.01, 0.99)), lsx=lambda d_: d_.league_id.map(ls))
    mv_ = rt[rt.ey == 2025].merge(rt[rt.ey == 2026], on="player_id", suffixes=("0", "1")); mv_ = mv_[(mv_.league_id0 != mv_.league_id1) & mv_.lsx0.notna() & mv_.lsx1.notna()]
    dz, dl = (mv_.z1 - mv_.z0).values, (mv_.lsx1 - mv_.lsx0).values
    slope = float((dz * dl).sum() / (dl * dl).sum()) if len(mv_) > 50 else np.nan
    LS_PER_SD = float(np.clip(-1 / slope, 0.15, 1.0)) if np.isfinite(slope) and slope < 0 else 0.35
    print(f"scale: {len(mv_)} league movers, slope {slope:.2f} z per strength unit, {LS_PER_SD:.2f} strength units per SD")
    def adj(pct, ls_):
        return ndtr(ndtri(np.clip(np.asarray(pct, float) / 100, 0.01, 0.99)) + ((0.0 if pd.isna(ls_) else ls_) - 0.30) / LS_PER_SD) * 100
    dima = {k: [int(round(float(x))) for x in adj(v, info.at[k, "ls_stat"])] for k, v in dimv.items() if k in info.index}
    level = {k: int(round(float(np.mean([v[i] for i in NEEDP[info.at[k, "role"]]])))) for k, v in dima.items() if info.at[k, "role"] in NEEDP}
    # Similar players, redone on the common scale: style AND level. Two players are only comparable if a coach could
    # consider both, so the distance uses the league-adjusted dimensions and counts the level three times one dimension.
    sim, near = {}, {}
    wv = np.array([1.0] * 7 + [3.0])
    for role_, grp in info.groupby("role"):
        ids_ = [i for i in grp.index if i in dima]; cand = [i for i in ids_ if info.at[i, "m"] >= 600]
        if len(cand) < 6: continue
        vec = lambda i: dima[i] + [level.get(i, int(np.mean(dima[i])))]
        A, B = np.array([vec(i) for i in ids_], float), np.array([vec(i) for i in cand], float)
        for k0 in range(0, len(ids_), 500):
            d2 = np.sqrt((((A[k0:k0 + 500, None, :] - B[None, :, :]) ** 2) * wv).sum(axis=2) / wv.sum())
            for j, row in enumerate(d2):
                pid_ = ids_[k0 + j]; o = np.argsort(row)[:41]
                near[pid_] = [int(cand[x]) for x in o if cand[x] != pid_][:40]
                sim[pid_] = [[int(cand[x]), info.at[cand[x], "name"], info.at[cand[x], "team"], round(float(info.at[cand[x], "age"]), 1), round(float(row[x]), 1)] for x in o[:6] if cand[x] != pid_][:5]
    # "like him, but cheaper": among the 40 closest in style, at most a year older, at most 60 % of his value, about the same level
    alt = {}
    for k, ids_ in near.items():
        if k not in sm or sm[k]["sv"] < 2e6: continue
        c_ = [c for c in ids_ if c in sm and sm[c]["sv"] <= 0.6 * sm[k]["sv"] and info.at[c, "age"] <= info.at[k, "age"] + 1 and level.get(c, 0) >= level.get(k, 0) - 10][:5]
        if c_: alt[k] = [[c, info.at[c, "name"], info.at[c, "team"], round(float(info.at[c, "age"]), 1), int(sm[c]["sv"]), level.get(c)] for c in c_]
    # "like him, but better": the closest in style who are at least five points higher on level, whatever they cost
    better = {}
    for k, ids_ in near.items():
        if k not in level: continue
        c_ = [c for c in ids_ if c in sm and level.get(c, 0) >= level[k] + 5 and info.at[c, "m"] >= 900][:5]
        if c_: better[k] = [[c, info.at[c, "name"], info.at[c, "team"], round(float(info.at[c, "age"]), 1), int(sm[c]["sv"]), level.get(c)] for c in c_]
    # Sporting outcome of a transfer: senior matches in the two seasons after it (any club, so a loan counts).
    # Sporting outcome of a transfer: matches FOR THE BUYING CLUB in the two seasons after it (a loan elsewhere does
    # not count). Regular: 20+ in one of them (10+ in the half season after a winter move); rotation: 10+; else not.
    cc = con.execute("select player_id, end_year y, team_id, sum(apps) apps from fm_career where end_year is not null group by 1,2,3").fetchdf().set_index(["player_id", "y", "team_id"]).apps
    ml = con.execute("select player_id, end_year y, arg_max(league_id, apps) lid from fm_career where end_year is not null group by 1,2").fetchdf()
    mls = ml.assign(ls=ml.lid.map(ls)).set_index(["player_id", "y"]).ls
    tf["sy"] = np.where(tf.mo >= 6, tf.y, tf.y - 1)
    atc = lambda k_: np.nan_to_num(cc.reindex(pd.MultiIndex.from_arrays([tf.player_id, tf.sy + k_, tf.to_id])).values)
    winter = (tf.mo < 6).values
    a1 = np.where(tf.sy + 1 <= 2026, atc(1), np.nan); a2 = np.where(tf.sy + 2 <= 2026, atc(2), np.nan)
    best_ = np.fmax(np.where(winter, a1 * 2, a1), a2)
    # Matches overstate a squad player who mostly comes off the bench, so league minutes for the buying club decide
    # where they exist: regular 1,500+ in a season (half of that after a winter move), rotation 600+. Matches (25+ / 12+) only as fallback.
    cm = con.execute("""select s.player_id, se.end_year y, s.team_id, max(s.minutes) m from fm_stats s join fm_seasons se using (league_id, season_id)
                        where s.stat = 'mins_played' group by 1,2,3""").fetchdf().set_index(["player_id", "y", "team_id"]).m
    atm = lambda k_: cm.reindex(pd.MultiIndex.from_arrays([tf.player_id, tf.sy + k_, tf.to_id])).values
    m1 = np.where(tf.sy + 1 <= 2026, atm(1), np.nan); m2 = np.where(tf.sy + 2 <= 2026, atm(2), np.nan)
    bestm = np.fmax(np.where(winter, m1 * 2, m1), m2); has_m = ~np.isnan(bestm)
    by_m = np.where(bestm >= 1500, 2, np.where(bestm >= 600, 1, 0)); by_a = np.where(best_ >= 25, 2, np.where(best_ >= 12, 1, 0))
    tf["unit"] = np.where(has_m, "m", "k")
    tf["a1"] = np.where(has_m, np.nan_to_num(m1), a1); tf["a2"] = np.where(has_m, np.where(np.isnan(a2), np.nan, np.nan_to_num(m2)), a2)
    tf["sport"] = np.where(np.isnan(a1), -1, np.where(has_m, by_m, by_a)).astype(int)
    club_ls = teams.drop_duplicates("team_id").set_index("team_id").league_id.map(ls)
    tf["dls"] = tf.to_id.map(club_ls).values - mls.reindex(pd.MultiIndex.from_arrays([tf.player_id, tf.sy])).values
    tfg = {k: v for k, v in tf.groupby("player_id")}
    st_ = tf[(tf.sport >= 0) & tf.dls.notna()]
    steps = [[lo_, hi_, int(((st_.dls >= lo_) & (st_.dls < hi_)).sum()), round(float((st_[(st_.dls >= lo_) & (st_.dls < hi_)].sport == 2).mean()), 2)] for lo_, hi_ in ((-9, -0.1), (-0.1, 0.1), (0.1, 0.25), (0.25, 9))]
    sport_by_verdict = [[int(q_), int(len(g_)), round(float((g_.sport == 2).mean()), 2)] for q_, g_ in tf[tf.sport >= 0].groupby("q")]
    tname = teams.drop_duplicates("team_id").set_index("team_id").team
    ct = tf[tf.y >= 2022].assign(club=lambda d_: d_.to_id.map(tname).fillna(d_.to_name))
    js(OUT / "data/transfers.js", "transfers", [[x.club, x.from_name, int(x.player_id), x["name"], str(x.date)[:7], int(x.fee), round(float(x.rel), 2), int(x.q), int(x.sport), None if pd.isna(x.a1) else int(x.a1)] for _, x in ct.iterrows()])

    def r(x, d=2):
        return None if x is None or (isinstance(x, float) and not np.isfinite(x)) or pd.isna(x) else round(float(x), d)
    index, shards = [], {i: {} for i in range(SHARDS)}
    for b in base.itertuples():
        pid = int(b.player_id)
        index.append([pid, b.name, r(b.age, 1), b.country, b.role, b.team, b.league, int(b.m), r(b.p5, 3), r(b.ls, 2)])
        d = dict(id=pid, name=b.name, age=r(b.age, 1), country=b.country, height=r(b.height, 0), role=b.role, team=b.team, league=b.league, season=int(b.ey),
                 minutes=int(b.m), contract=str(b.contract_end)[:10] if pd.notna(b.contract_end) else None, p5=r(b.p5, 3), ls=r(b.ls, 2))
        if isinstance(getattr(b, "injury", None), str):
            ij = json.loads(b.injury); d["inj"] = [ij.get("name"), ((ij.get("expectedReturn") or {}).get("expectedReturnFallback"))]
        if pid in stg: d["stats"] = [[x.stat, r(x.shr, 2), r(x.v, 2), r(x.pct, 0), int(x.n)] for x in stg[pid].itertuples()]
        if pid in carg: d["career"] = [[x.season_name, x.league_name, x.team, r(x.apps, 0), r(x.goals, 0), r(x.assists, 0), r(x.rating, 2)] for x in carg[pid].head(40).itertuples()]
        if pid in mvg: d["mv"] = [[int(x.y), int(x.v)] for x in mvg[pid].itertuples()]
        rec = 0; peak = [None, None]
        if pid in sim: d["sim"] = sim[pid]
        if pid in ptype: d["type"] = ptype[pid]
        if pid in sm:
            v = sm[pid]
            if pid in svh: d["svh"] = [[int(x.y), int(x.sv)] for x in svh[pid].itertuples()]
            d["val"] = [int(v["sv"]), int(v["sv_lo"]), int(v["sv_hi"]), int(v["mv"])]
            # light smoothing over horizons in log space (each horizon is a separate model), anchored at 1 today
            sm3 = lambda xs: [round(float(np.exp(0.25 * a_ + 0.5 * b_ + 0.25 * c_)), 3) for a_, b_, c_ in zip(np.log([1.0] + xs[:-1]), np.log(xs), np.log(xs[1:] + xs[-1:]))]
            lo_, md_, hi_ = (sm3([float(v[f"g{h}{k}"]) for h in range(1, 6)]) for k in ("_lo", "", "_hi"))
            d["path"] = [[h, lo_[h - 1], md_[h - 1], hi_[h - 1], r(v[f"play{h}"], 2)] for h in range(1, 6)]
            d["typ"] = sm3([float(v[f"t{h}"]) for h in range(1, 6)])
            index[-1] += [int(v["sv"]), md_[2], int(v["mv"])]
            # expected peak: the highest point of the median path, today included, and the year it falls in
            pk = [1.0] + md_; peak = [int(v["sv"] * max(pk)), 2026 + int(np.argmax(pk))]
            # "Speider recommends": young regular whose Speider value is well above the market value and whose path points up
            rec = int(b.age <= 26 and b.m >= 600 and v["mv"] >= 3e5 and v["sv"] / v["mv"] >= 1.3 and md_[2] >= 1.15)
            if rec: d["rec"] = [round(float(v["sv"] / v["mv"]), 2), md_[2]]
        if len(index[-1]) == 10: index[-1] += [None, None, None]
        index[-1] += [ptype.get(pid), rec, dimv.get(pid), dima.get(pid), level.get(pid), int(b.team_id) if pd.notna(b.team_id) else None, int(b.league_id), int(str(b.contract_end)[:4]) if pd.notna(b.contract_end) else None] + peak + [posc.get(pid), formlift.get(pid)]
        if pid in formd: d["form"] = formd[pid]
        if pid in alt: d["alt"] = alt[pid]
        if pid in better: d["better"] = better[pid]
        if pid in tfg:
            d["tr"] = [[str(x.date)[:10], x.from_name, x.to_name, int(x.fee), int(x.mv), round(float(x.rel), 2), int(x.q),
                        int(x.next_fee) if pd.notna(x.next_fee) else None, int(x.next_y) if pd.notna(x.next_y) else None, int(x.sport), None if pd.isna(x.a1) else int(x.a1), None if pd.isna(x.a2) else int(x.a2), x.unit] for _, x in tfg[pid].iterrows()]
        shards[pid % SHARDS][pid] = d
    # Test 31: price per buyer tier, as a percentage of the Speider value shown, and the tier of every club from today's squads
    from buyers import TIERS, club_tiers
    for row in index:
        v = sm.get(row[0]) if row[10] else None
        row.append([int(round(100 * v[f"bt{T}"] / v["sv"])) for T in TIERS] if v and v.get("bt1") == v.get("bt1") and v.get("bt1") else None)
    tdf = pd.DataFrame([(row[18], np.log(row[12])) for row in index if row[18] is not None and row[12]], columns=["team_id", "lv"])
    tiers = {int(x.team_id): int(x.tier) for x in club_tiers(tdf, ["team_id"]).itertuples()}
    js(OUT / "data/players.js", "players", index)
    # squad model (analysis/squad_model.py): coefficients on standardised team features, and last season's standardised goal difference
    squad = None
    if Path("data/result_squad_model.json").exists():
        sq_ = json.load(open("data/result_squad_model.json")); sm_ = sq_["site_model"]
        squad = dict(features=sm_["features"], coef=sm_["coef"], intercept=sm_["intercept"], sd=sq_["sd_goal_difference_per_match"], gd_last=sq_["gd_last"], corr=sq_["out_of_time"]["xi+depth+age + last season"]["corr"],
                     test=sq_["out_of_time"]["xi+depth+age + last season"], n_test=sq_["n_test"])
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

    fo = json.load(open("data/result_fee_offset.json")) if Path("data/result_fee_offset.json").exists() else {}
    buyer_test = {"with": fo["year-centred + tiers, bagged x10"]["pooled"]["miss"], "without": fo["year-centred, bagged x10"]["pooled"]["miss"]} if fo else None
    names = con.execute("select league_id, name, cc from fm_leagues").fetchdf().set_index("league_id")
    lg = [[names.name.get(i, str(i)), names.cc.get(i, ""), r(v, 2)] for i, v in ls.sort_values(ascending=False).items() if i in names.index]
    d = np.diff(np.log(list(INDEX.values()))); drift, sd = float(d.mean()), float(d.std(ddof=1))
    proj = [[2026 + h, round(100 * np.exp(drift * h)), round(100 * np.exp(drift * h - 1.28 * sd * np.sqrt(h))), round(100 * np.exp(drift * h + 1.28 * sd * np.sqrt(h)))] for h in range(1, 9)]
    js(OUT / "data/market.js", "market", dict(index=[[k, v] for k, v in INDEX.items()], projection=proj, leagues=lg, top5_base_rate=round(base_rate, 3),
                                             built="2026-11-16", shards=SHARDS, value_test=smres.get("value"), tiers=tiers, buyer_test=buyer_test, squad=squad, verdict_stats=verdict_stats, deals=deals, steps=steps, sport_by_verdict=sport_by_verdict, ls_per_sd=round(LS_PER_SD, 2), logos=os.environ.get("SITE_LOGOS") == "1", verdict=(json.load(open("data/result_buy_verdict.json")) if Path("data/result_buy_verdict.json").exists() else {}).get("flag"), counts=dict(players=len(index), eras=len(e))))
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"players {len(index)}, era seasons {len(e)}, leagues {len(lg)}, site {size:.0f} MB in {OUT}")


if __name__ == "__main__":
    main()
