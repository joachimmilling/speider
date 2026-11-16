"""Test 14: a projection per player, several horizons, with profile shape.

For each horizon h (1 to 5 years) two models are fitted on the player's
profile today: the value change if still playing (10th, 50th, 90th
percentile) and the probability of still playing. This replaces the fixed
age curve. Profile-shape inputs are added: best skill, second-best skill,
number of standout skills (above the 90th percentile for the role), number
of weak skills, and spread.

Out-of-time check per horizon: fit on seasons before the test season, test on
the latest season whose outcome is known (2026 - h).
"""
from __future__ import annotations

import sys

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier as HGBC, HistGradientBoostingRegressor as HGBR

from growth_model import SHAPE, STATS, build

KW = dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0)


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    d, val, mins = build(con)
    d = d[d.age.between(16, 34)].copy()
    base = ["age", "lv"]
    prof = base + ["role_c", "height", "league_strength", "team_q", "lmin", "car_apps"] + STATS
    full = prof + SHAPE
    cat = lambda cols: [cols.index("role_c")] if "role_c" in cols else None
    latest = d[d.ey == 2026].copy()
    rows, models = [], {}
    for h in (1, 2, 3, 4, 5):
        fut = val.rename(columns={"lv": "lv_f"}).assign(ey=lambda x: x.y - h)[["player_id", "ey", "lv_f"]]
        alive = mins[mins.m >= 270][["player_id", "ey"]].assign(ey=lambda x: x.ey - h, playing=1).drop_duplicates()
        x = d.merge(fut, on=["player_id", "ey"], how="left").merge(alive, on=["player_id", "ey"], how="left").fillna({"playing": 0})
        x["growth"] = x.lv_f - x.lv
        test_ey = 2026 - h
        tr, te = x[(x.ey < test_ey) & (x.ey >= 2018)], x[x.ey == test_ey]
        trg, teg = tr[tr.growth.notna()], te[te.growth.notna()].copy()
        out = dict(h=h, n_train=len(trg), n_test=len(teg))
        for name, cols in (("age_level", base), ("profile", prof), ("profile_shape", full)):
            m = HGBR(categorical_features=cat(cols), **KW).fit(trg[cols], trg.growth)
            p = m.predict(teg[cols]); y = teg.growth
            out["r2_" + name] = round(1 - ((y - p) ** 2).mean() / y.var(), 2)
            yy = teg.age <= 21
            out["r2_u21_" + name] = round(1 - ((y[yy] - p[yy]) ** 2).mean() / y[yy].var(), 2)
        q = {a: HGBR(loss="quantile", quantile=a, categorical_features=cat(full), **KW).fit(trg[full], trg.growth) for a in (0.1, 0.5, 0.9)}
        lo, hi = q[0.1].predict(teg[full]), q[0.9].predict(teg[full])
        out["coverage_80"] = round(100 * float(np.mean((teg.growth >= lo) & (teg.growth <= hi))))
        c = HGBC(categorical_features=cat(full), **KW).fit(tr[full], tr.playing)
        ps = c.predict_proba(te[full])[:, 1]
        out["playing_actual"] = round(100 * te.playing.mean()); out["playing_pred"] = round(100 * ps.mean())
        rows.append(out)
        # final models for today's players: all seasons with a known outcome
        allg = x[(x.ey >= 2018) & x.growth.notna()]; alla = x[(x.ey >= 2018) & (x.ey <= 2026 - h)]
        models[h] = ({a: HGBR(loss="quantile", quantile=a, categorical_features=cat(full), **KW).fit(allg[full], allg.growth) for a in (0.1, 0.5, 0.9)},
                     HGBC(categorical_features=cat(full), **KW).fit(alla[full], alla.playing))
    pd.set_option("display.width", 240)
    print(pd.DataFrame(rows).to_string(index=False))

    def project(name: str) -> None:
        r = latest[latest.name == name]
        if r.empty:
            print(f"\n{name}: no 2025/26 season with a value in the data"); return
        r = r.sort_values("m").tail(1)
        v0 = float(np.exp(r.lv.iloc[0]))
        print(f"\n{name}: age {r.age.iloc[0]:.1f}, role {r.role.iloc[0]}, {int(r.m.iloc[0])} min, value now {v0/1e6:.1f}m, "
              f"best skill z {r.best_skill.iloc[0]:.2f}, standout skills {int(r.n_standout.iloc[0])}")
        t = []
        for h, (q, c) in models.items():
            g = {a: float(m.predict(r[full])[0]) for a, m in q.items()}
            p = float(c.predict_proba(r[full])[0, 1])
            t.append(dict(years=h, age=round(r.age.iloc[0] + h), low=v0 * np.exp(g[0.1]) / 1e6, likely=v0 * np.exp(g[0.5]) / 1e6,
                          high=v0 * np.exp(g[0.9]) / 1e6, still_playing=p, expected=v0 * np.exp(g[0.5]) * p / 1e6))
        print(pd.DataFrame(t).round(2).to_string(index=False))

    for n in sys.argv[1:] or ["Antonio Nusa", "Oscar Bobb", "Sverre Nypan"]:
        project(n)
    # two players, same age band and value, different projections
    y = latest[(latest.age <= 20) & latest.lv.between(np.log(1.5e6), np.log(3e6)) & (latest.m >= 900)].copy()
    q3, c3 = models[3]
    y["x3"] = np.exp(q3[0.5].predict(y[full])); y["p3"] = c3.predict_proba(y[full])[:, 1]; y["value_m"] = np.exp(y.lv) / 1e6
    y = y.sort_values("x3")
    print(f"\nToday, aged 20 or younger, valued 1.5-3m, at least 900 min (n={len(y)}): three-year projection, extremes")
    print(pd.concat([y.tail(5).iloc[::-1], y.head(5)])[["name", "age", "role", "m", "value_m", "x3", "p3", "best_skill", "n_standout", "league_strength"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
