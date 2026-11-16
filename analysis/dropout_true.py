"""Test 19: dropout by age without survivorship.

The profile table only holds players in today's squads, so every historical
row is a survivor. The SofaScore season lists hold full squads back in time
(retired players included) but no birth dates. The age mix of league regulars
is stable from year to year, so for a past season y:

    regulars of age a in y        = N_y * f(a)        (f from the latest full season, where nearly all match a profile)
    of those found in today's data = m_y(a)           (matched by name to a profile with a career line that season)
    S(a, h = 2026 - y)             = m_y(a) / (N_y * f(a) * r0)

r0 is the name-match rate in the latest season. A smooth logistic surface in
age and horizon is fitted to the cells and written to data/result_dropout_true.json.
Run: python3 analysis/dropout_true.py
"""
from __future__ import annotations

import json
import unicodedata

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


def norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if not unicodedata.combining(c)).replace("ø", "o").replace("æ", "ae").replace("đ", "d").strip()


def feats(a, h):
    a = np.asarray(a, float); h = np.asarray(h, float); o = np.clip(a - 27, 0, None); yg = np.clip(22 - a, 0, None)
    return np.column_stack([h, o, o * o, o * h, o * o * h, yg, yg * h])


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    ss = con.execute("select tournament_id t, end_year y, player, sum(minutesPlayed) m from ss_stats where end_year between 2014 and 2026 group by 1,2,3 having sum(minutesPlayed) >= 900").fetchdf()
    stable = ss.groupby("t").y.nunique(); stable = stable[stable == 13].index
    ss = ss[ss.t.isin(stable)].copy(); ss["k"] = ss.player.map(norm)
    prof = con.execute("select player_id, name, birth from fm_profiles where gender='male' and birth is not null").fetchdf(); prof["k"] = prof.name.map(norm)
    car = con.execute("select distinct player_id, end_year y from fm_career where apps >= 5 and end_year is not null").fetchdf()
    pc = prof.merge(car, on="player_id"); pc["age"] = pc.y - 0.5 - pd.to_datetime(pc.birth).dt.year - pd.to_datetime(pc.birth).dt.dayofyear / 365.25
    pc = pc[pc.age.between(15, 45)].sort_values("age").drop_duplicates(["k", "y"])
    m = ss.merge(pc[["k", "y", "age"]], on=["k", "y"], how="left"); m["a"] = np.floor(m.age)
    N = m.groupby("y").size(); last = m[m.y == 2026]; r0 = float(last.age.notna().mean()); f = last.a.value_counts(normalize=True)
    rows = []
    for y in range(2014, 2026):
        g = m[m.y == y]; cnt = g.a.value_counts()
        for a in range(17, 41):
            exp = N[y] * f.get(a, 0) * r0
            if exp >= 15: rows.append(dict(y=y, h=2026 - y, a=a, expected=exp, found=float(cnt.get(a, 0)), s=min(1.0, cnt.get(a, 0) / exp)))
    c = pd.DataFrame(rows)
    X = np.vstack([feats(c.a, c.h), feats(c.a, c.h)]); yv = np.r_[np.ones(len(c)), np.zeros(len(c))]; w = np.r_[c.expected * c.s, c.expected * (1 - c.s)]
    lr = LogisticRegression(C=1e3, max_iter=2000).fit(X, yv, sample_weight=w)
    S = lambda a, h: lr.predict_proba(feats(a, h))[:, 1]
    pd.set_option("display.width", 200)
    print("leagues", len(stable), "regulars per season", int(N.mean()), "match rate latest season", round(r0, 3))
    print("raw cells, share found today:"); print(c[c.a.isin([20, 24, 28, 30, 32, 34, 36, 38])].pivot(index="a", columns="h", values="s").round(2).to_string())
    tab = pd.DataFrame({h: S(np.arange(17, 43), np.full(26, h)) for h in range(1, 6)}, index=range(17, 43)).round(3)
    print("fitted chance of still being in professional squads after h years:"); print(tab.loc[[18, 21, 24, 27, 30, 32, 34, 36, 38, 40]].to_string())
    json.dump(dict(r0=r0, leagues=int(len(stable)), table={int(a): [float(x) for x in tab.loc[a]] for a in tab.index}), open("data/result_dropout_true.json", "w"))


if __name__ == "__main__":
    main()
