"""Test 19: still playing by age and horizon, from career lines.

Career lines exist for players who have stopped as well as for those active
today (about four in five players in each season have a profile), unlike value
histories, which exist almost only for players active today. A regular
(15+ matches in a season) counts as still playing h years later if he has 5+
matches in that season. Writes data/result_dropout_career.json.
Run: python3 analysis/dropout_career.py
"""
import duckdb
import numpy as np
import pandas as pd

con = duckdb.connect("data/speider.duckdb", read_only=True)
c = con.execute("select player_id, end_year y, sum(apps) apps from fm_career where end_year is not null group by 1,2").fetchdf()
p = con.execute("select player_id, birth from fm_profiles where birth is not null and gender='male'").fetchdf()
b = c[(c.apps >= 15) & c.y.between(2015, 2025)].merge(p, on="player_id")
b["a"] = np.floor(b.y - 0.5 - pd.to_datetime(b.birth).dt.year - pd.to_datetime(b.birth).dt.dayofyear / 365.25)
rows = []
for h in range(1, 6):
    b = b.merge(c.rename(columns={"apps": f"f{h}"}).assign(y=lambda x: x.y - h), on=["player_id", "y"], how="left")
    g = b[b.y <= 2026 - h]
    rows.append((g[f"f{h}"].fillna(0) >= 5).groupby(g.a).mean().rename(h))
t = pd.concat(rows, axis=1).loc[16:42]
t = t.rolling(3, center=True, min_periods=1).mean()          # smooth across neighbouring ages
print(t.loc[[18, 21, 24, 27, 30, 32, 34, 36, 38, 40]].round(2).T.to_string())
t.round(4).to_json("data/result_dropout_career.json")
