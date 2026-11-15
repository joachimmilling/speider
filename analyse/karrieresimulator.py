"""Test 4: kan korte vinduer lenkes sammen til en hel karriere?

Idé: lær ettårs-overganger i verdi (alder a -> a+1) bare fra 2022-2026.
Lenk dem til en simulering over mange år. Test mot ekte lange forløp:
start i juni 2016, simuler ti år, sammenlign med faktisk verdi i juni 2026.

Varianter (antagelser som testes mot hverandre):
  A  bare alder
  B  alder + nivå (verdi-kvintil for alderen)
  C  alder + nivå + retning siste år (opp/ned)
Referanse: verdien står stille.
Tilstand: log markedsverdi (SciSports via FotMob). Verdien er IKKE inndata i
prismodellen; her brukes den som mål på karriereforløp.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)
N_SIM = 300


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    df = con.execute("""
      with g as (select unnest(range(2015, 2027)) y),
      s as (select m.player_id, g.y, arg_min(m.value, abs(datediff('day', m.date, make_date(g.y,6,30)))) v,
                   min(abs(datediff('day', m.date, make_date(g.y,6,30)))) d
            from fm_mv m, g where m.value > 0 and abs(datediff('day', m.date, make_date(g.y,6,30))) <= 100 group by 1,2)
      select s.player_id, s.y, ln(s.v) lv, datediff('day', p.birth, make_date(s.y,6,30))/365.25 age
      from s join fm_profiles p using (player_id) where p.birth is not null and p.gender='male'
    """).fetchdf()
    df["a"] = np.floor(df.age).astype(int)
    df = df[(df.a >= 16) & (df.a <= 38)]
    nx = df[["player_id", "y", "lv"]].copy(); nx["y"] -= 1
    pv = df[["player_id", "y", "lv"]].copy(); pv["y"] += 1
    t = df.merge(nx, on=["player_id", "y"], suffixes=("", "1")).merge(pv, on=["player_id", "y"], how="left", suffixes=("", "p"))
    t["d"] = t.lv1 - t.lv
    t["up"] = np.where(t.lvp.isna(), -1, (t.lv > t.lvp).astype(int))
    train = t[t.y >= 2022].copy()                       # overganger 2022->23 ... 2025->26
    qs = train.groupby("a").lv.quantile([.2, .4, .6, .8]).unstack()

    def lvl(a, lv):
        a = min(max(a, qs.index.min()), qs.index.max())
        return int(np.searchsorted(qs.loc[a].values, lv))
    train["q"] = [lvl(a, v) for a, v in zip(train.a, train.lv)]
    bank = {"A": {k: g.d.values for k, g in train.groupby("a")},
            "B": {k: g.d.values for k, g in train.groupby(["a", "q"])},
            "C": {k: g.d.values for k, g in train[train.up >= 0].groupby(["a", "q", "up"])}}
    print(f"Treningsoverganger: {len(train)}  (2022-2026)")

    QA = qs.index.values; QV = qs.values

    def levels(a, lv):
        ai = np.clip(a, QA.min(), QA.max()) - QA.min()
        return (lv[:, None] > QV[ai]).sum(axis=1)

    def step(model, a, lv, up):
        a = np.clip(a, 16, 37); q = levels(a, lv); d = np.zeros(len(lv))
        if model == "A": keys = a
        elif model == "B": keys = a * 10 + q
        else: keys = a * 100 + q * 10 + (up + 1)
        for k in np.unique(keys):
            m = keys == k; ak = int(a[m][0]); qk = int(q[m][0])
            if model == "A": pool = bank["A"].get(ak)
            elif model == "B": pool = bank["B"].get((ak, qk))
            else:
                pool = bank["C"].get((ak, qk, int(up[m][0])))
                if pool is None or len(pool) < 25: pool = bank["B"].get((ak, qk))
            if pool is None or len(pool) < 25: pool = bank["A"].get(ak, np.array([0.0]))
            d[m] = pool[RNG.integers(len(pool), size=m.sum())]
        return d

    res = []
    for start, end in [(2016, 2026), (2018, 2026), (2021, 2026)]:
        s0 = df[df.y == start].merge(df[df.y == end][["player_id", "lv"]], on="player_id", suffixes=("", "_end"))
        s0 = s0[(s0.a >= 18) & (s0.a <= 26)]
        prev = df[df.y == start - 1].set_index("player_id").lv
        s0["up"] = [(-1 if pid not in prev.index else int(lv > prev[pid])) for pid, lv in zip(s0.player_id, s0.lv)]
        if len(s0) > 2000: s0 = s0.sample(2000, random_state=1)
        H = end - start; n = len(s0); y = s0.lv_end.values
        for model in ["A", "B", "C"]:
            a = np.repeat(s0.a.values, N_SIM); x = np.repeat(s0.lv.values, N_SIM); u = np.repeat(s0.up.values, N_SIM)
            for h in range(H):
                d = step(model, a + h, x, u); x = x + d; u = (d > 0).astype(int)
            X = x.reshape(n, N_SIM); med = np.median(X, axis=1); lo = np.quantile(X, .1, axis=1); hi = np.quantile(X, .9, axis=1)
            res.append(dict(start=start, aar=H, n=n, modell=model,
                            median_feil_pst=round(100 * (np.exp(np.median(np.abs(med - y))) - 1)),
                            dekning_80=round(100 * np.mean((y >= lo) & (y <= hi))),
                            rang_korr=round(float(pd.Series(med).corr(pd.Series(y), method="spearman")), 2),
                            skjevhet_pst=round(100 * (np.exp(np.median(med - y)) - 1))))
        res.append(dict(start=start, aar=H, n=n, modell="stille", median_feil_pst=round(100 * (np.exp(np.median(np.abs(s0.lv.values - y))) - 1)),
                        dekning_80=None, rang_korr=round(float(s0.lv.corr(s0.lv_end, method="spearman")), 2),
                        skjevhet_pst=round(100 * (np.exp(np.median(s0.lv.values - y)) - 1))))
    out = pd.DataFrame(res)
    print(out.to_string(index=False))
    out.to_csv("data/resultat_karrieresimulator.csv", index=False)
    curve = train.groupby("a").d.agg(["median", "count"])
    c = curve["median"].cumsum().shift(1).fillna(0)
    curve["verdi_rel_21"] = np.exp(c - c.loc[21])
    print("\nLenket alderskurve (verdi relativt til 21 år):")
    print(curve[(curve.index >= 17) & (curve.index <= 35)].round(2).T.to_string())


if __name__ == "__main__":
    main()
