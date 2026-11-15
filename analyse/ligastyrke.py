"""Test 3: hjelper ligastyrke når vi spår en spiller som bytter liga?

Mål: spillerens tall i ny liga, relativt til rollesnittet der.
  B0  samme relative nivå som før (ingen ligastyrke, ingen demping)
  B1  dempet relativt nivå (lært helning, ingen ligastyrke)
  M   B1 + ligastyrke per statistikk (ridge, lært på bytter til og med 2025)
Test: bytter der ny sesong ender 2026 eller senere.
"""
from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

STATS = ["accurate_pass", "ball_recovery", "defensive_contributions", "effective_clearance",
         "total_tackle", "total_scoring_att", "accurate_long_balls", "interception", "won_contest",
         "ontarget_scoring_att", "poss_won_att_3rd", "expected_goals_per_90", "expected_assists_per_90",
         "goals_per_90", "rating"]
K = {"accurate_pass": 300, "goals_per_90": 1800, "poss_won_att_3rd": 2700, "interception": 1200, "rating": 1200}


def role(code: int) -> str:
    if code == 11: return "K"
    if 30 <= code <= 59: return "F"
    if 60 <= code <= 89: return "M"
    return "A"


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    df = con.execute("""
        select s.stat, s.league_id, l.name league, l.cc, se.end_year y, s.player_id, s.value v, s.minutes m,
               cast(json_extract(p.positions,'$[0]') as int) pos
        from fm_stats s join fm_seasons se using (league_id, season_id)
        join fm_leagues l using (league_id) join fm_players p using (player_id)
        where l.gender='male' and s.stat in (select unnest(?)) and s.minutes >= 900 and isfinite(s.value)
    """, [STATS]).fetchdf()
    df["role"] = df.pos.fillna(0).astype(int).map(role)
    df = df[df.role != "K"].groupby(["stat", "league_id", "y", "player_id"], as_index=False).first()
    g = df.groupby(["stat", "league_id", "y", "role"]).v
    df["mu"], df["sd"] = g.transform("mean"), g.transform("std")
    k = df.stat.map(K).fillna(600)
    df["z"] = (df.m / (df.m + k)) * (df.v - df.mu) / df.sd.replace(0, np.nan)
    df = df.dropna(subset=["z"])
    names = df.drop_duplicates("league_id").set_index("league_id")[["league", "cc"]]

    a = df[["stat", "player_id", "y", "league_id", "z"]]
    res, strengths = [], {}
    for stat, s in a.groupby("stat"):
        s = s.sort_values("y")
        b = s.copy(); b["y"] -= 1
        p = s.merge(b, on=["stat", "player_id", "y"], suffixes=("_old", "_new"))
        p = p[p.league_id_old != p.league_id_new]
        tr, te = p[p.y + 1 <= 2025], p[p.y + 1 >= 2026]
        if len(tr) < 400 or len(te) < 150:
            continue
        leagues = sorted(set(tr.league_id_old) | set(tr.league_id_new))
        ix = {l: i for i, l in enumerate(leagues)}

        def X(d):
            M = np.zeros((len(d), len(leagues) + 1))
            M[:, 0] = d.z_old.values
            for r, (lo, ln) in enumerate(zip(d.league_id_old, d.league_id_new)):
                if lo in ix: M[r, 1 + ix[lo]] += 1
                if ln in ix: M[r, 1 + ix[ln]] -= 1
            return M
        Xtr, ytr, Xte, yte = X(tr), tr.z_new.values, X(te), te.z_new.values
        slope = float((Xtr[:, 0] @ ytr) / (Xtr[:, 0] @ Xtr[:, 0]))
        best = None
        cut = tr.y + 1 <= 2024
        for lam in [1, 3, 10, 30, 100]:
            P = np.eye(Xtr.shape[1]) * lam; P[0, 0] = 0
            A, yA = Xtr[cut.values], ytr[cut.values]
            beta = np.linalg.solve(A.T @ A + P, A.T @ yA)
            e = np.sqrt(np.mean((Xtr[~cut.values] @ beta - ytr[~cut.values]) ** 2))
            if best is None or e < best[1]: best = (lam, e)
        P = np.eye(Xtr.shape[1]) * best[0]; P[0, 0] = 0
        beta = np.linalg.solve(Xtr.T @ Xtr + P, Xtr.T @ ytr)
        rm = lambda pred: float(np.sqrt(np.mean((pred - yte) ** 2)))
        r0, r1, rM = rm(Xte[:, 0]), rm(slope * Xte[:, 0]), rm(Xte @ beta)
        res.append(dict(stat=stat, n_tren=len(tr), n_test=len(te), helning=round(slope, 2),
                        rmse_B0=r0, rmse_B1=r1, rmse_M=rM, M_mot_B1_pst=round(100 * (1 - rM / r1), 1),
                        M_mot_B0_pst=round(100 * (1 - rM / r0), 1)))
        strengths[stat] = pd.Series(beta[1:], index=leagues)
    out = pd.DataFrame(res).sort_values("M_mot_B1_pst", ascending=False)
    pd.set_option("display.width", 250)
    print(out.round(3).to_string(index=False))
    out.to_csv("data/resultat_ligastyrke.csv", index=False)
    S = pd.DataFrame(strengths)
    att = S[[c for c in ["goals_per_90", "expected_goals_per_90", "total_scoring_att", "won_contest", "expected_assists_per_90", "rating"] if c in S]].mean(axis=1)
    rank = pd.concat([names, att.rename("styrke")], axis=1).dropna().sort_values("styrke", ascending=False)
    print("\nSterkest (offensive tall + rating, snitt z-forskyvning):")
    print(rank.head(15).round(2).to_string())
    print("\nSvakest:")
    print(rank.tail(10).round(2).to_string())
    rank.to_csv("data/resultat_ligarangering.csv")


if __name__ == "__main__":
    main()
