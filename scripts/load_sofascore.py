"""Load a SofaScore export (NDJSON, gzip) into DuckDB: ss_tournaments, ss_stats.

ss_stats has one row per player, tournament and season, with one column per
statistic. Run:  python3 scripts/load_sofascore.py data/raw/sofascore/export-*.ndjson.gz
"""
from __future__ import annotations

import gzip, json, re, sys

import duckdb
import pandas as pd


def end_year(y: str) -> int | None:
    m = re.findall(r"\d{2,4}", str(y))
    if not m: return None
    v = int(m[-1])
    return v if v > 100 else 2000 + v


def main(paths) -> None:
    tours, rows = {}, {}
    for p in paths:
        for line in gzip.open(p, "rt"):
            o = json.loads(line)
            if o["s"] == "tournaments":
                v = o["v"]
                t = tours.setdefault(v["id"], dict(tournament_id=v["id"], name=None, category=None, cc=None, gender=None, deep=False, history=False))
                t["name"] = v.get("name") or t["name"]; t["category"] = v.get("cat") or t["category"]; t["cc"] = v.get("cc") or t["cc"]
                t["gender"] = v.get("gender") or t["gender"]; t["deep"] = t["deep"] or bool(v.get("deep")); t["history"] = t["history"] or bool(v.get("hist"))
            else:
                ut, sid, _ = str(o["k"]).split("/")
                for r in o["v"]["rows"]:
                    key = (int(ut), int(sid), r["p"])
                    d = rows.setdefault(key, dict(tournament_id=int(ut), season_id=int(sid), season=o["v"].get("year"), end_year=end_year(o["v"].get("year")),
                                                  player_id=r["p"], player=r["n"], team_id=r["t"], team=r["tn"]))
                    d.update({k: v for k, v in r.items() if k not in ("p", "n", "t", "tn")})
    T, S = pd.DataFrame(tours.values()), pd.DataFrame(rows.values())
    con = duckdb.connect("data/speider.duckdb")
    con.execute("CREATE OR REPLACE TABLE ss_tournaments AS SELECT * FROM T")
    con.execute("CREATE OR REPLACE TABLE ss_stats AS SELECT * FROM S")
    print("tournaments", len(T), "deep", int(T.deep.sum()), "history", int(T.history.sum()))
    print("player-seasons", len(S), "players", S.player_id.nunique(), "seasons", S.end_year.min(), "-", S.end_year.max())
    print(con.execute("""select count(distinct tournament_id) from ss_stats s where tournament_id in (select tournament_id from ss_tournaments where deep)""").fetchone())


if __name__ == "__main__":
    main(sys.argv[1:])
