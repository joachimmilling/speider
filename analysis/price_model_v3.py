"""Test 7: price model v3 = v2 + career path features known on the day
(levels played at, European matches, debut age, last three seasons).

Test 6: price model v2. Same setup as test 5, with a finer quality layer:

- eight roles instead of four, for normalising statistics and as an input
- league strength as a number (from test 3), so small leagues share strength
- two seasons of history, minutes-weighted, instead of one
- a goals-and-assists-only variant, to test the quality gate

Original docstring of test 5 follows.

Test 5: price model v1, trained on actual transfer fees.

Target: log(fee / price index). Inputs: age, role, selling league, and the
player's shrunk, role-relative numbers from the season before the transfer.
Third-party market value is NOT an input; it is the opponent.

Train: transfers up to 2024. Test: transfers in 2025-2026.
References: (a) market value on the transfer date, (b) age + league + position only.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGB

STATS = ["rating", "goals_per_90", "expected_goals_per_90", "expected_assists_per_90", "total_scoring_att",
         "ontarget_scoring_att", "won_contest", "big_chance_created", "accurate_pass", "accurate_long_balls",
         "total_tackle", "interception", "ball_recovery", "effective_clearance", "defensive_contributions",
         "poss_won_att_3rd", "total_att_assist"]
INDEX = {2015: 70, 2016: 79, 2017: 88, 2018: 93, 2019: 95, 2020: 82, 2021: 79, 2022: 81, 2023: 89, 2024: 84, 2025: 95, 2026: 100}
CUPS = "l.name not ilike '%cup%' and l.name not ilike '%pokal%' and l.name not ilike '%copa%' and l.name not ilike '%coppa%' and l.name not ilike '%trophy%'"


def role(code: int) -> str:
    if code == 11: return "GK"
    if code in (33, 34, 35, 36, 37): return "CB"
    if code in (32, 38, 51, 59): return "FB"
    if 62 <= code <= 68: return "DM"
    if 72 <= code <= 78: return "CM"
    if 83 <= code <= 87: return "AM"
    if code in (71, 79, 82, 88, 103, 107): return "W"
    if code in (104, 105, 106, 115): return "ST"
    return "CM"


def features(con) -> pd.DataFrame:
    s = con.execute(f"""
        select s.stat, s.league_id, se.end_year ey, s.player_id, s.value v, s.minutes m, s.matches g,
               cast(json_extract(p.positions,'$[0]') as int) pos
        from fm_stats s join fm_seasons se using (league_id, season_id)
        join fm_leagues l using (league_id) join fm_players p using (player_id)
        where l.gender='male' and {CUPS} and s.stat in (select unnest(?)) and s.minutes >= 270 and isfinite(s.value)
    """, [STATS]).fetchdf()
    s["role"] = s.pos.fillna(0).astype(int).map(role)
    s = s.groupby(["stat", "league_id", "ey", "player_id"], as_index=False).first()
    g = s.groupby(["stat", "league_id", "ey", "role"]).v
    s["z"] = (s.m / (s.m + 600)) * (s.v - g.transform("mean")) / g.transform("std").replace(0, np.nan)
    wide = s.pivot_table(index=["player_id", "league_id", "ey"], columns="stat", values="z").reset_index()
    mins = con.execute(f"""
        select s.player_id, s.league_id, se.end_year ey, max(s.minutes) as minutes, max(s.matches) as matches,
               any_value(cast(json_extract(p.positions,'$[0]') as int)) as pos
        from fm_stats s join fm_seasons se using (league_id, season_id) join fm_leagues l using (league_id)
        join fm_players p using (player_id)
        where l.gender='male' and {CUPS} and s.stat='mins_played' group by 1,2,3""").fetchdf()
    team = con.execute(f"""
        select s.player_id, s.league_id, se.end_year ey, arg_max(s.team_id, s.minutes) team_id
        from fm_stats s join fm_seasons se using (league_id, season_id)
        where s.stat='mins_played' group by 1,2,3""").fetchdf()
    tr = con.execute(f"""
        select s.league_id, se.end_year ey, s.team_id, sum(s.value*s.minutes)/sum(s.minutes) team_rating, count(*) n
        from fm_stats s join fm_seasons se using (league_id, season_id)
        where s.stat='rating' and s.minutes >= 450 group by 1,2,3 having count(*) >= 8""").fetchdf()
    g2 = tr.groupby(["league_id", "ey"]).team_rating
    tr["team_z"] = (tr.team_rating - g2.transform("mean")) / g2.transform("std").replace(0, np.nan)
    tr["team_rank"] = g2.rank(pct=True)
    out = mins.merge(wide, on=["player_id", "league_id", "ey"], how="left").merge(team, on=["player_id", "league_id", "ey"], how="left")
    return out.merge(tr[["league_id", "ey", "team_id", "team_z", "team_rank"]], on=["league_id", "ey", "team_id"], how="left")


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    f = features(con)
    t = con.execute("""
        select t.player_id, t.date, year(t.date) y, month(t.date) mo, t.fee, t.market_value mv, t.to_id,
               datediff('day', p.birth, t.date)/365.25 age, p.height
        from fm_transfers t join fm_profiles p using (player_id)
        where t.fee >= 50000 and not t.loan and not t.extension and p.birth is not null and year(t.date) >= 2017
    """).fetchdf()
    t["ey_max"] = np.where(t.mo >= 6, t.y, t.y - 1)
    m = t.merge(f[f.minutes >= 450], on="player_id")
    m = m[(m.ey <= m.ey_max) & (m.ey >= m.ey_max - 1)].sort_values(["ey", "minutes"])
    m = m.groupby(["player_id", "date"], as_index=False).last()
    prev = f[["player_id", "ey", "minutes"] + [c for c in STATS if c in f.columns]].sort_values("minutes").groupby(["player_id", "ey"], as_index=False).last()
    prev["ey"] += 1
    m = m.merge(prev, on=["player_id", "ey"], how="left", suffixes=("", "_p"))
    for c in [c for c in STATS if c in f.columns]:
        w0, w1 = m.minutes, m.minutes_p.fillna(0) * 0.6
        m[c] = np.where(m[c + "_p"].notna() & m[c].notna(), (m[c] * w0 + m[c + "_p"] * w1) / (w0 + w1), m[c].fillna(m[c + "_p"]))
    m["min_prev"] = m.minutes_p.fillna(0)
    ls = pd.read_csv("data/result_league_ranking.csv", index_col=0)["strength"]
    cr = con.execute("""select c.player_id, c.end_year, c.league_id, c.league_name, c.team_id, c.apps, coalesce(c.goals,0) goals, c.rating, p.birth
                        from fm_career c join fm_profiles p using (player_id) where c.end_year is not null and c.apps >= 1""").fetchdf()
    cr["strength"] = cr.league_id.map(ls)
    cr["top5"] = cr.league_id.isin([47, 87, 54, 55, 53])
    cr["europe"] = cr.league_name.str.contains("Champions League|Europa League|Conference League", na=False)
    cr["youth"] = cr.league_name.str.contains(r"U1[0-9]|U2[0-9]|Youth|Primavera|Reserve|II$| B$", na=False)
    cr["age"] = cr.end_year - 0.5 - pd.to_datetime(cr.birth).dt.year
    k = m[["player_id", "date", "ey_max"]].merge(cr, on="player_id")
    k = k[k.end_year <= k.ey_max]
    k["last3"] = k.end_year >= k.ey_max - 2
    k["sen"] = ~k.youth
    def agg(g):
        s10 = g[(g.apps >= 10) & g.sen]
        l3 = g[g.last3 & g.sen]
        return pd.Series(dict(
            apps_top5=g.apps[g.top5].sum(), apps_europe=g.apps[g.europe].sum(), apps_youth=g.apps[g.youth].sum(),
            best_strength=s10.strength.max(), debut_age=g.age[g.sen & (g.apps >= 5)].min(),
            apps_last3=l3.apps.sum(), goals_last3=l3.goals.sum(),
            rating_last3=(l3.rating * l3.apps).sum() / l3.apps[l3.rating.notna()].sum() if l3.rating.notna().any() else np.nan,
            strength_last3=(l3.strength * l3.apps).sum() / l3.apps[l3.strength.notna()].sum() if l3.strength.notna().any() else np.nan,
            n_clubs=g.team_id.nunique()))
    kk = k.groupby(["player_id", "date"]).apply(agg).reset_index()
    m = m.merge(kk, on=["player_id", "date"], how="left")
    PATH = ["apps_top5", "apps_europe", "apps_youth", "best_strength", "debut_age", "apps_last3", "goals_last3", "rating_last3", "strength_last3", "n_clubs"]
    m["league_strength"] = m.league_id.map(ls)
    m["y_log"] = np.log(m.fee / m.y.map(INDEX) * 100)
    m["role_name"] = m.pos.fillna(0).astype(int).map(role)
    m["role"] = m.role_name.astype("category").cat.codes
    lg = {l: i for i, l in enumerate(sorted(m.league_id.unique()))}
    m["league"] = m.league_id.map(lg)
    m["lmin"] = np.log(m.minutes)
    m["age2"] = (m.age - 25) ** 2
    m["recency"] = m.ey_max - m.ey
    # history known on the day: earlier fees paid for the player, and senior career so far
    allf = con.execute("select player_id, date, fee, year(date) y from fm_transfers where fee > 0 and not loan").fetchdf()
    allf["real"] = np.log(allf.fee / allf.y.map(INDEX).fillna(70) * 100)
    h = m[["player_id", "date"]].merge(allf, on="player_id", suffixes=("", "_p"))
    h = h[h.date_p < h.date].sort_values("date_p").groupby(["player_id", "date"]).agg(prev_fee=("real", "last"), max_fee=("real", "max"), n_prev=("real", "size"), prev_date=("date_p", "last")).reset_index()
    m = m.merge(h, on=["player_id", "date"], how="left")
    m["yrs_since_prev"] = (pd.to_datetime(m.date) - pd.to_datetime(m.prev_date)).dt.days / 365.25
    m["n_prev"] = m.n_prev.fillna(0)
    car = con.execute("select player_id, end_year, sum(apps) apps, sum(goals) goals, max(rating) best from fm_career where end_year is not null group by 1,2").fetchdf()
    c = m[["player_id", "date", "ey_max"]].merge(car, on="player_id")
    c = c[c.end_year <= c.ey_max].groupby(["player_id", "date"]).agg(car_apps=("apps", "sum"), car_goals=("goals", "sum"), car_seasons=("end_year", "nunique")).reset_index()
    m = m.merge(c, on=["player_id", "date"], how="left")
    stats = [c for c in STATS if c in m.columns]
    base = ["age", "age2", "league", "role"]
    v1 = base + ["lmin", "matches", "height", "pos", "recency"] + stats
    full = v1 + ["team_z", "team_rank", "prev_fee", "max_fee", "n_prev", "yrs_since_prev", "car_apps", "car_goals", "car_seasons", "league_strength", "min_prev"]
    v2 = list(full); full = full + PATH
    ga = base + ["lmin", "goals_per_90", "total_att_assist", "league_strength"]
    noperf = [c for c in full if c not in stats]
    tr, te = m[m.y <= 2024], m[m.y >= 2025]
    print(f"train {len(tr)}  test {len(te)}  leagues {len(lg)}  features {len(full)}")

    def fit(cols, loss="squared_error", q=None):
        kw = dict(max_iter=400, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=25, l2_regularization=1.0,
                  categorical_features=[cols.index("league"), cols.index("role")], random_state=0)
        mdl = HGB(loss=loss, quantile=q, **kw) if q else HGB(**kw)
        return mdl.fit(tr[cols], tr.y_log)

    pred = {"B: age+league+role": fit(base).predict(te[base]), "Goals+assists only": fit(ga).predict(te[ga]), "Speider v2": fit(v2).predict(te[v2]), "Speider v3": fit(full).predict(te[full])}
    lo, hi = fit(full, "quantile", 0.1).predict(te[full]), fit(full, "quantile", 0.9).predict(te[full])
    y = te.y_log.values
    has_mv = (te.mv > 0).values
    pred["A: market value"] = np.where(has_mv, np.log(te.mv.clip(lower=1) / te.y.map(INDEX) * 100), np.nan)
    pred["Blend 50/50 (reference only)"] = (pred["Speider v3"] + pred["A: market value"]) / 2

    def row(name, p, mask):
        ok = mask & ~np.isnan(p)
        e = np.abs(p[ok] - y[ok])
        return dict(model=name, n=int(ok.sum()), median_err_pct=round(100 * (np.exp(np.median(e)) - 1)),
                    within_2x_pct=round(100 * np.mean(e < np.log(2))),
                    rank_corr=round(float(pd.Series(p[ok]).corr(pd.Series(y[ok]), method="spearman")), 2))
    groups = {"all": np.ones(len(te), bool), "under 23": (te.age < 23).values, "fee under 1m": (te.fee < 1e6).values,
              "fee over 10m": (te.fee > 1e7).values,
              "defenders+DM": te.role_name.isin(["CB", "FB", "DM"]).values, "small leagues": (te.league_strength < 0).values}
    out = []
    for gname, mask in groups.items():
        for name, p in pred.items():
            out.append(dict(group=gname, **row(name, p, mask & has_mv)))
    res = pd.DataFrame(out)
    pd.set_option("display.width", 200)
    print(res.to_string(index=False))
    print(f"\n80% interval coverage (Speider v3): {100*np.mean((y>=lo)&(y<=hi)):.0f} %   median width: x{np.exp(np.median(hi-lo)):.1f}")
    res.to_csv("data/result_price_model_v3.csv", index=False)

    # calibrated interval (conformalised quantile regression): fit on <= 2023, calibrate on 2024
    fit_, cal = tr[tr.y <= 2023], tr[tr.y == 2024]
    kw = dict(max_iter=400, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=25, l2_regularization=1.0,
              categorical_features=[full.index("league"), full.index("role")], random_state=0)
    ql = HGB(loss="quantile", quantile=0.1, **kw).fit(fit_[full], fit_.y_log)
    qh = HGB(loss="quantile", quantile=0.9, **kw).fit(fit_[full], fit_.y_log)
    sc = np.maximum(ql.predict(cal[full]) - cal.y_log.values, cal.y_log.values - qh.predict(cal[full]))
    q = np.quantile(sc, min(1.0, 0.8 * (1 + 1 / len(sc))))
    clo, chi = ql.predict(te[full]) - q, qh.predict(te[full]) + q
    print(f"calibrated 80% interval: coverage {100*np.mean((y>=clo)&(y<=chi)):.0f} %  median width x{np.exp(np.median(chi-clo)):.1f}  (widened by x{np.exp(q):.2f} each side, n_cal={len(cal)})")
    for gname, mask in groups.items():
        print(f"   {gname}: coverage {100*np.mean(((y>=clo)&(y<=chi))[mask]):.0f} %")

    # which inputs matter: drop-one-group permutation on the test set
    mdl = fit(full); basee = np.median(np.abs(mdl.predict(te[full]) - y)); rng = np.random.default_rng(0); imp = {}
    for name, cols in {"age": ["age", "age2"], "league": ["league"], "playing time": ["lmin", "matches", "recency"],
                       "role/position": ["role", "pos", "height"], "team strength": ["team_z", "team_rank"], "earlier fees": ["prev_fee", "max_fee", "n_prev", "yrs_since_prev"], "career so far": ["car_apps", "car_goals", "car_seasons"], "career path": PATH, "attacking stats": [c for c in stats if c in ("goals_per_90","expected_goals_per_90","expected_assists_per_90","total_scoring_att","ontarget_scoring_att","won_contest","big_chance_created","total_att_assist")],
                       "passing/defending stats": [c for c in stats if c in ("accurate_pass","accurate_long_balls","total_tackle","interception","ball_recovery","effective_clearance","defensive_contributions","poss_won_att_3rd")],
                       "rating": ["rating"]}.items():
        X = te[full].copy(); idx = rng.permutation(len(X))
        for c in cols: X[c] = X[c].values[idx]
        imp[name] = round(100 * (np.exp(np.median(np.abs(mdl.predict(X) - y))) - np.exp(basee)))
    print("error added when shuffled (pct points):", dict(sorted(imp.items(), key=lambda kv: -kv[1])))

    te = te.assign(pred=pred["Speider v3"], lo=lo, hi=hi)
    te["ratio"] = np.exp(te.pred - te.y_log)
    names = con.execute("select player_id, name from fm_profiles").fetchdf()
    show = te.merge(names, on="player_id")[["name", "date", "age", "fee", "mv", "ratio"]]
    show["speider"] = (show.fee * show.ratio).round(-4)
    print("\nPaid far below Speider's estimate (test set):")
    print(show.sort_values("ratio", ascending=False).head(8).round(2).to_string(index=False))
    print("\nPaid far above Speider's estimate (test set):")
    print(show.sort_values("ratio").head(8).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
