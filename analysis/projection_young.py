"""Test 16: telling young players apart.

Test 15 left one problem: for players of 21 or younger the three-year
projection explained little of who grows. This test attacks it with data on
the player before and around his breakthrough, on a much larger sample:

- every player-year with a value at age 16-23 from 2015 (not only regulars in
  leagues with statistics), outcome three years later
- career lines to date: senior, reserve and youth matches, goals, level of the
  leagues played in, debut age, last season's matches, goals and rating
- national teams to date: senior call-up, age at first call-up, age groups
- track record of the club, league and nationality: how young players there
  developed in earlier years, relative to their age and value (out-of-time)
- season statistics where they exist

Train on years up to 2021, test on 2023 (outcome 2026). 2022 is kept apart.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from growth_model import STATS, build

KW = dict(max_iter=500, learning_rate=0.04, max_leaf_nodes=24, min_samples_leaf=30, l2_regularization=1.0, random_state=0)
H = 3


def track_record(df, key, name):
    """Mean residual growth of young players per key in earlier years whose outcome was known, shrunk."""
    out = []
    for y in sorted(df.y.unique()):
        past = df[(df.y <= y - H) & df.resid.notna()]
        g = past.groupby(key).resid.agg(["sum", "count"])
        enc = (g["sum"] / (g["count"] + 15)).rename(name)
        cur = df.loc[df.y == y, ["player_id", "y", key]].merge(enc, left_on=key, right_index=True, how="left")
        out.append(cur[["player_id", "y", name]])
    return pd.concat(out)


def frame(con, amin: float = 16, amax: float = 23.5) -> pd.DataFrame:
    val = con.execute("""
      with g as (select unnest(range(2013, 2027)) y),
      s as (select m.player_id, g.y, arg_min(m.value, abs(datediff('day', m.date, make_date(g.y,6,30)))) v,
                   arg_min(m.team_id, abs(datediff('day', m.date, make_date(g.y,6,30)))) team_id
            from fm_mv m, g where m.value > 0 and abs(datediff('day', m.date, make_date(g.y,6,30))) <= 100 group by 1,2)
      select player_id, y, ln(v) lv, team_id from s""").fetchdf()
    prof = con.execute("select player_id, name, birth, height, country from fm_profiles where birth is not null and gender='male'").fetchdf()
    b = val.merge(prof, on="player_id")
    b["age"] = b.y + 0.5 - pd.to_datetime(b.birth).dt.year - pd.to_datetime(b.birth).dt.dayofyear / 365.25
    b = b[b.age.between(amin, amax)].copy()
    for k in (1, 2):
        p = val.rename(columns={"lv": f"lv_m{k}"}).assign(y=lambda x: x.y + k)[["player_id", "y", f"lv_m{k}"]]
        b = b.merge(p, on=["player_id", "y"], how="left"); b[f"mom{k}"] = b.lv - b[f"lv_m{k}"]
    fut = val.rename(columns={"lv": "lv_f"}).assign(y=lambda x: x.y - H)[["player_id", "y", "lv_f"]]
    b = b.merge(fut, on=["player_id", "y"], how="left"); b["growth"] = b.lv_f - b.lv

    ls = pd.read_csv("data/result_league_ranking.csv", index_col=0)["strength"]
    car = con.execute("select player_id, end_year, league_id, league_name, apps, coalesce(goals,0) goals, rating from fm_career where end_year is not null and apps >= 1").fetchdf()
    car["youth"] = car.league_name.str.contains(r"U1[0-9]|U2[0-9]|Youth|Primavera|Reserve|II$| B$|Premier League 2", na=False)
    car["strength"] = car.league_id.map(ls)
    k = b[["player_id", "y", "birth"]].merge(car, on="player_id"); k = k[k.end_year <= k.y]
    k["sen"] = ~k.youth; k["is_last"] = k.end_year >= k.y; k["a"] = k.end_year - 0.5 - pd.to_datetime(k.birth).dt.year
    k["sa"] = k.apps.where(k.sen, 0); k["ya"] = k.apps.where(k.youth, 0); k["sg"] = k.goals.where(k.sen, 0)
    k["la"] = k.apps.where(k.sen & k.is_last, 0); k["lg"] = k.goals.where(k.sen & k.is_last, 0)
    k["sw"] = k.strength * k.sa; k["swn"] = k.sa.where(k.strength.notna(), 0)
    k["deb"] = k.a.where(k.sen & (k.apps >= 3)); k["lr"] = k.rating.where(k.sen & k.is_last); k["ls_"] = k.strength.where(k.sen & k.is_last & (k.apps >= 5))
    k["s_u19"] = k.sa.where(k.a < 19, 0); k["beststr"] = k.strength.where(k.sen & (k.apps >= 8))
    c = k.groupby(["player_id", "y"]).agg(sen_apps=("sa", "sum"), youth_apps=("ya", "sum"), sen_goals=("sg", "sum"), last_apps=("la", "sum"), last_goals=("lg", "sum"),
                                         sw=("sw", "sum"), swn=("swn", "sum"), debut_age=("deb", "min"), last_rating=("lr", "max"), last_strength=("ls_", "max"),
                                         sen_apps_u19=("s_u19", "sum"), best_strength=("beststr", "max"), n_leagues=("league_id", "nunique")).reset_index()
    c["avg_strength"] = c.sw / c.swn.replace(0, np.nan); c = c.drop(columns=["sw", "swn"])
    b = b.merge(c, on=["player_id", "y"], how="left")
    b["apps_per_age"] = b.sen_apps / (b.age - 15)
    # outcome flags from career lines: senior matches h years later, and the level played at
    sen = car[~car.youth].groupby(["player_id", "end_year"]).agg(apps_f=("apps", "sum"), str_f=("strength", "max")).reset_index()
    top5 = car[car.league_id.isin([47, 87, 54, 55, 53])].groupby(["player_id", "end_year"]).apps.sum().rename("top5_f").reset_index()
    for h in (1, 2, 3, 4, 5):
        f_ = sen.assign(y=sen.end_year - h).rename(columns={"apps_f": f"apps_f{h}", "str_f": f"str_f{h}"})[["player_id", "y", f"apps_f{h}", f"str_f{h}"]]
        b = b.merge(f_, on=["player_id", "y"], how="left")
        t_ = top5.assign(y=top5.end_year - h).rename(columns={"top5_f": f"top5_f{h}"})[["player_id", "y", f"top5_f{h}"]]
        b = b.merge(t_, on=["player_id", "y"], how="left")
        vf = val.rename(columns={"lv": f"lv_f{h}"}).assign(y=lambda x: x.y - h)[["player_id", "y", f"lv_f{h}"]]
        b = b.merge(vf, on=["player_id", "y"], how="left")

    nat = con.execute("select player_id, level, start_date as st, end_date, apps from fm_national where start_date is not null").fetchdf()
    n = b[["player_id", "y", "birth"]].merge(nat, on="player_id"); n["cut"] = pd.to_datetime(n.y.astype(str) + "-06-30")
    n = n[pd.to_datetime(n.st) <= n.cut]
    n["age_start"] = (pd.to_datetime(n.st) - pd.to_datetime(n.birth)).dt.days / 365.25
    n["senior"] = (n.level == 99).astype(int); n["youth_level"] = n.level.where(n.level < 99)
    na = n.groupby(["player_id", "y"]).agg(nat_levels=("level", "nunique"), nat_senior=("senior", "max"), nat_top_youth=("youth_level", "max"),
                                          nat_first_age=("age_start", "min")).reset_index()
    b = b.merge(na, on=["player_id", "y"], how="left").fillna({"nat_levels": 0, "nat_senior": 0})

    d, _, _ = build(con)
    d = d.sort_values("m").groupby(["player_id", "ey"], as_index=False).last()[["player_id", "ey", "role_c", "league_strength", "team_q", "lmin", "league_id"] + STATS].rename(columns={"ey": "y"})
    b = b.merge(d, on=["player_id", "y"], how="left")
    b["ab"] = np.floor(b.age).astype(int); b["vb"] = pd.qcut(b.lv, 5, labels=False)
    b["resid"] = b.growth - b.groupby(["y", "ab", "vb"]).growth.transform("mean")
    b["league_key"] = b.league_id.fillna(-1)
    for key, name in (("team_id", "club_track"), ("country", "nation_track"), ("league_key", "league_track")):
        b = b.merge(track_record(b, key, name), on=["player_id", "y"], how="left")
    return b


A = ["age", "lv"]
B_ = A + ["mom1", "mom2", "height", "sen_apps", "youth_apps", "sen_goals", "last_apps", "last_goals", "debut_age", "last_rating", "last_strength",
          "avg_strength", "best_strength", "sen_apps_u19", "n_leagues", "apps_per_age"]
C = B_ + ["nat_levels", "nat_senior", "nat_top_youth", "nat_first_age"]
D = C + ["club_track", "nation_track", "league_track"]
E = D + ["role_c", "league_strength", "team_q", "lmin"] + STATS


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    b = frame(con)
    x = b[b.growth.notna() & (b.y >= 2015)].copy()
    tr, te = x[x.y <= 2021], x[x.y == 2023].copy()
    print(f"train {len(tr)} player-years (2015-2021), test {len(te)}; share of test with season statistics {100*te.lmin.notna().mean():.0f} %")
    rows = []
    for name, cols in (("age + level", A), ("+ career lines", B_), ("+ national teams", C), ("+ club/nation/league track record", D), ("+ season statistics", E)):
        m = HGBR(**KW).fit(tr[cols], tr.growth)
        te["p"] = m.predict(te[cols])
        for grp, mask in (("17-19", te.age < 20), ("20-21", te.age.between(20, 21.999)), ("22-23", te.age >= 22)):
            t = te[mask]; top = t[t.p >= t.p.quantile(.9)]; bot = t[t.p <= t.p.quantile(.1)]
            rows.append(dict(inputs=name, age=grp, n=len(t), r2=round(1 - ((t.growth - t.p) ** 2).mean() / t.growth.var(), 2),
                             rank=round(t.p.corr(t.growth, method="spearman"), 2), top10_actual_x=round(float(np.exp(top.growth.median())), 1),
                             bottom10_actual_x=round(float(np.exp(bot.growth.median())), 2), all_actual_x=round(float(np.exp(t.growth.median())), 2)))
    pd.set_option("display.width", 220)
    r = pd.DataFrame(rows)
    for grp in ("17-19", "20-21", "22-23"):
        print(r[r.age == grp].to_string(index=False)); print()
    r.to_csv("data/result_projection_young.csv", index=False)
    rng = np.random.default_rng(0); yg = te[te.age < 22]; base = ((yg.growth - m.predict(yg[E])) ** 2).mean(); imp = {}
    groups = {"level and momentum": ["lv", "mom1", "mom2"], "age": ["age"], "career lines": [c for c in B_ if c not in ("age", "lv", "mom1", "mom2", "height")],
              "national teams": [c for c in C if c.startswith("nat_")], "track record": ["club_track", "nation_track", "league_track"],
              "season statistics": ["role_c", "league_strength", "team_q", "lmin"] + STATS, "height": ["height"]}
    for g, cs in groups.items():
        X = yg[E].copy(); idx = rng.permutation(len(X))
        for c_ in cs: X[c_] = X[c_].values[idx]
        imp[g] = round(100 * (((yg.growth - m.predict(X)) ** 2).mean() / base - 1))
    print("21 or younger, error added when the input group is shuffled (%):", dict(sorted(imp.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
