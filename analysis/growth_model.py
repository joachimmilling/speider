"""Test 13: growth conditioned on the player, not a fixed age curve.

Two players of the same age and value can have very different futures. This
tests whether a player's characteristics today (role, statistic profile,
league and team level, playing time, height, career path) predict
  (a) the change in value three years ahead, given he is still playing, and
  (b) whether he is still playing three years ahead,
better than age and current level alone (what the simulator used so far).

Train: seasons ending 2018-2021 (outcomes to 2024). Test: seasons ending
2022-2023 (outcomes 2025-2026). Value = third-party market value, used here as
the measure of a career path, never as an input to the price model.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as HGBC, HistGradientBoostingRegressor as HGBR
from sklearn.metrics import roc_auc_score

STATS = ["rating", "goals_per_90", "expected_goals_per_90", "expected_assists_per_90", "total_scoring_att", "won_contest",
         "big_chance_created", "accurate_pass", "accurate_long_balls", "total_tackle", "interception", "ball_recovery",
         "effective_clearance", "poss_won_att_3rd"]
NICE = {"rating": "rating", "goals_per_90": "goals", "expected_goals_per_90": "xG", "expected_assists_per_90": "xA",
        "total_scoring_att": "shots", "won_contest": "dribbles", "big_chance_created": "big chances created",
        "accurate_pass": "passes", "accurate_long_balls": "long passes", "total_tackle": "tackles",
        "interception": "interceptions", "ball_recovery": "recoveries", "effective_clearance": "clearances",
        "poss_won_att_3rd": "high ball wins"}
CUPS = "l.name not ilike '%cup%' and l.name not ilike '%pokal%' and l.name not ilike '%copa%' and l.name not ilike '%coppa%' and l.name not ilike '%trophy%'"
H = 3


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


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    s = con.execute(f"""
        select s.stat, s.league_id, se.end_year ey, s.player_id, s.team_id, s.value v, s.minutes m,
               cast(json_extract(p.positions,'$[0]') as int) pos
        from fm_stats s join fm_seasons se using (league_id, season_id) join fm_leagues l using (league_id)
        join fm_players p using (player_id)
        where l.gender='male' and {CUPS} and s.stat in (select unnest(?)) and s.minutes >= 270 and isfinite(s.value)
    """, [STATS + ["mins_played"]]).fetchdf()
    s["role"] = s.pos.fillna(0).astype(int).map(role)
    mins = s[s.stat == "mins_played"].sort_values("m").groupby(["player_id", "ey"], as_index=False).last()[["player_id", "ey", "league_id", "team_id", "m", "role", "pos"]]
    best = s[["player_id", "ey"]].drop_duplicates().assign(ok=True)
    st = s[s.stat != "mins_played"].groupby(["stat", "league_id", "ey", "player_id"], as_index=False).first()
    g = st.groupby(["stat", "league_id", "ey", "role"]).v
    st["z"] = (st.m / (st.m + 600)) * (st.v - g.transform("mean")) / g.transform("std").replace(0, np.nan)
    wide = st.pivot_table(index=["player_id", "league_id", "ey"], columns="stat", values="z").reset_index()
    d = mins[mins.m >= 450].merge(wide, on=["player_id", "league_id", "ey"], how="left")
    tm = d.groupby(["league_id", "ey", "team_id"]).rating.mean().rename("team_q").reset_index()
    d = d.merge(tm, on=["league_id", "ey", "team_id"], how="left")
    val = con.execute("""
      with g as (select unnest(range(2017, 2027)) y),
      s as (select m.player_id, g.y, arg_min(m.value, abs(datediff('day', m.date, make_date(g.y,6,30)))) v
            from fm_mv m, g where m.value > 0 and abs(datediff('day', m.date, make_date(g.y,6,30))) <= 100 group by 1,2)
      select player_id, y, ln(v) lv from s""").fetchdf()
    prof = con.execute("select player_id, name, birth, height from fm_profiles where birth is not null and gender='male'").fetchdf()
    d = d.merge(prof, on="player_id").merge(val.rename(columns={"y": "ey"}), on=["player_id", "ey"])
    d["age"] = d.ey + 0.5 - pd.to_datetime(d.birth).dt.year - pd.to_datetime(d.birth).dt.dayofyear / 365.25
    fut = val.rename(columns={"lv": "lv_f"}).assign(ey=lambda x: x.y - H)[["player_id", "ey", "lv_f"]]
    d = d.merge(fut, on=["player_id", "ey"], how="left")
    alive = mins[mins.m >= 270][["player_id", "ey"]].assign(ey=lambda x: x.ey - H, playing=1).drop_duplicates()
    d = d.merge(alive, on=["player_id", "ey"], how="left").fillna({"playing": 0})
    ls = pd.read_csv("data/result_league_ranking.csv", index_col=0)["strength"]
    d["league_strength"] = d.league_id.map(ls)
    car = con.execute("select player_id, end_year, sum(apps) apps from fm_career where end_year is not null group by 1,2").fetchdf()
    c = d[["player_id", "ey"]].merge(car, on="player_id"); c = c[c.end_year <= c.ey].groupby(["player_id", "ey"]).apps.sum().rename("car_apps").reset_index()
    d = d.merge(c, on=["player_id", "ey"], how="left")
    d["lmin"] = np.log(d.m); d["role_c"] = d.role.astype("category").cat.codes
    d = d[d.ey.between(2018, 2023) & d.age.between(16, 33)].copy()
    d["growth"] = d.lv_f - d.lv
    base = ["age", "lv"]
    full = base + ["role_c", "height", "league_strength", "team_q", "lmin", "car_apps"] + STATS
    tr, te = d[d.ey <= 2021], d[d.ey >= 2022]
    print(f"player-seasons: train {len(tr)}, test {len(te)}; still playing after {H} years: {100*te.playing.mean():.0f} %")
    kw = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0)

    def reg(cols):
        a = tr[tr.growth.notna()]
        return HGBR(categorical_features=[cols.index("role_c")] if "role_c" in cols else None, **kw).fit(a[cols], a.growth)
    rb, rf = reg(base), reg(full)
    tg = te[te.growth.notna()].copy()
    tg["p_base"], tg["p_full"] = rb.predict(tg[base]), rf.predict(tg[full])
    rows = []
    for name, mask in {"all": tg.age > 0, "21 or younger": tg.age <= 21, "22-25": tg.age.between(21.001, 25), "26 or older": tg.age > 25}.items():
        t = tg[mask]; v = t.growth.var()
        rows.append(dict(group=name, n=len(t), growth_sd=round(float(np.sqrt(v)), 2),
                         r2_age_level=round(1 - ((t.growth - t.p_base) ** 2).mean() / v, 2),
                         r2_with_player=round(1 - ((t.growth - t.p_full) ** 2).mean() / v, 2),
                         rank_age_level=round(t.p_base.corr(t.growth, method="spearman"), 2),
                         rank_with_player=round(t.p_full.corr(t.growth, method="spearman"), 2)))
    pd.set_option("display.width", 220)
    print("\n(a) Value change three years ahead, players still valued:")
    print(pd.DataFrame(rows).to_string(index=False))
    cb = HGBC(**kw).fit(tr[base], tr.playing); cf = HGBC(categorical_features=[full.index("role_c")], **kw).fit(tr[full], tr.playing)
    te = te.copy(); te["s_base"], te["s_full"] = cb.predict_proba(te[base])[:, 1], cf.predict_proba(te[full])[:, 1]
    print(f"\n(b) Still playing after {H} years, AUC: age+level {roc_auc_score(te.playing, te.s_base):.3f}, with player {roc_auc_score(te.playing, te.s_full):.3f}")
    y = te[te.age <= 21]; print(f"    21 or younger: {roc_auc_score(y.playing, y.s_base):.3f} -> {roc_auc_score(y.playing, y.s_full):.3f}")

    # what moves predicted growth for young players: set one input to its 80th vs 20th percentile
    yg = tg[tg.age <= 21]
    eff = {}
    for c in ["league_strength", "team_q", "lmin", "height", "car_apps"] + STATS:
        lo, hi = yg[c].quantile(.2), yg[c].quantile(.8)
        a, b = yg[full].copy(), yg[full].copy(); a[c] = lo; b[c] = hi
        eff[NICE.get(c, c)] = round(100 * (np.exp(np.mean(rf.predict(b) - rf.predict(a))) - 1))
    print("\nEffect on predicted three-year growth, 21 or younger, strong (80th pct) vs weak (20th pct) on one input, in %:")
    print(dict(sorted(eff.items(), key=lambda kv: -abs(kv[1]))))
    for r_ in ["W", "ST", "CM", "CB"]:
        yr = yg[yg.role == r_]; e = {}
        for c in STATS:
            lo, hi = yr[c].quantile(.2), yr[c].quantile(.8); a, b = yr[full].copy(), yr[full].copy(); a[c] = lo; b[c] = hi
            e[NICE[c]] = round(100 * (np.exp(np.mean(rf.predict(b) - rf.predict(a))) - 1))
        top = sorted(e.items(), key=lambda kv: -kv[1])
        print(f"  {r_} (n={len(yr)}): most positive {top[:4]}, least {top[-2:]}")

    # same age and value, different expected paths
    yt = te[(te.age <= 20) & te.lv.between(np.log(8e5), np.log(1.5e6))].copy()
    yt["pred_growth"] = rf.predict(yt[full]); yt["exp_factor"] = np.exp(yt.pred_growth) * yt.s_full
    cols = ["name", "ey", "age", "role", "m", "value_now", "pred_x_if_playing", "p_playing", "actual_x"]
    yt["value_now"] = np.exp(yt.lv).round(-4); yt["pred_x_if_playing"] = np.exp(yt.pred_growth); yt["p_playing"] = yt.s_full; yt["actual_x"] = np.exp(yt.growth)
    yt = yt.sort_values("exp_factor")
    print(f"\nPlayers aged 20 or younger valued 0.8-1.5m in the test seasons (n={len(yt)}): highest and lowest expected growth")
    print(pd.concat([yt.tail(6).iloc[::-1], yt.head(6)])[cols].round(2).to_string(index=False))
    q = yt.assign(grp=pd.qcut(yt.exp_factor, 4, labels=["lowest quarter", "2", "3", "highest quarter"])).groupby("grp", observed=True).agg(
        n=("name", "size"), predicted_x=("pred_x_if_playing", "median"), actual_x=("actual_x", "median"), still_playing=("playing", "mean"))
    print("\nSame group split by predicted growth: what actually happened")
    print(q.round(2).to_string())
    tg[["player_id", "ey", "age", "role", "growth", "p_base", "p_full"]].to_csv("data/result_growth_model.csv", index=False)


if __name__ == "__main__":
    main()
