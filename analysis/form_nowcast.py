"""Form nowcast for today: where a player's third-party value is heading by the summer, given the season in progress.

The model is the one tested in test 26 (how a value moves during a season given what the player does in it; out of time R2 0.27
against 0.15 for age and value alone). Here it is fitted on every finished season and applied to the running one. The excess over
what age and value alone would say is shrunk by minutes played (900 minutes count half). Writes data/form_now.pkl.
It does not change the Speider price: tests 25 and 26 found no gain on fees.
"""
import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from current_season import rows
from form_adjust_test import NF, seasons
from projection_v3 import KW

RUN = 2027


def main() -> None:
    con = duckdb.connect("data/speider.duckdb", read_only=True)
    S = seasons(con, rows(con))
    d = S[S.dv.notna() & S.age.notna() & (S.cur_min >= 450) & (S.ey < RUN)]
    full, base = HGBR(**KW).fit(d[NF], d.dv), HGBR(**KW).fit(d[["age", "lv0"]], d.dv)
    n = S[(S.ey == RUN) & S.lv0.notna() & S.age.notna() & (S.cur_min >= 180)].copy()
    n["base"] = base.predict(n[["age", "lv0"]]); w = n.cur_min / (n.cur_min + 900)
    n["exp"] = n.base + w * (full.predict(n[NF]) - n.base)                       # expected change over the season, against the market
    latest = con.execute("select player_id, ln(arg_max(value, date)) lv_now from fm_mv where value > 0 group by 1").fetchdf()
    n = n.merge(latest, on="player_id", how="left"); n["real"] = n.lv_now - n.lv0; n["real"] -= n.real.median()   # already moved since the summer, against the market
    n[["player_id", "exp", "base", "real", "cur_min", "cur_rating", "share"]].to_pickle("data/form_now.pkl")
    nm = con.execute("select player_id, name from fm_players").fetchdf(); n = n.merge(nm, on="player_id")
    print(len(n), "players with a running season")
    print(n.sort_values("exp", ascending=False).head(12)[["name", "age", "cur_min", "cur_rating", "exp", "base", "real"]].round(2).to_string())
    print(n[n.name.isin(["Martin Ødegaard", "Erling Haaland", "Antonio Nusa", "Bukayo Saka", "Lamine Yamal", "Gabriel Jesus"])][["name", "age", "cur_min", "cur_rating", "p_rating", "exp", "base", "real"]].round(2).to_string())


if __name__ == "__main__":
    main()
