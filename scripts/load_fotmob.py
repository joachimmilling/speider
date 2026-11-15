"""Load the FotMob export (NDJSON, gzip) into DuckDB.

Run:  python3 scripts/load_fotmob.py data/raw/fotmob/export-YYYYMMDD.ndjson.gz

Tables: fm_leagues, fm_seasons, fm_teams, fm_players, fm_stats, fm_transfers.
Data stays local in data/ and is never committed.
"""
from __future__ import annotations

import csv
import gzip
import json
import re
import sys
import tempfile
from pathlib import Path

import duckdb

DB = Path("data/speider.duckdb")


def end_year(name: str) -> int:
    m = re.findall(r"\d{4}", name or "")
    return int(m[-1]) if m else 0


def main(src: str) -> None:
    tmp = Path(tempfile.mkdtemp())
    files = {n: open(tmp / f"{n}.csv", "w", newline="") for n in
             ["leagues", "seasons", "teams", "players", "stats", "transfers"]}
    w = {n: csv.writer(f) for n, f in files.items()}
    players: dict[int, tuple] = {}
    with gzip.open(src, "rt") as fh:
        for line in fh:
            o = json.loads(line)
            s, k, v = o["s"], o["k"], o["v"]
            if s == "leagues":
                w["leagues"].writerow([v["id"], v["name"], v["cc"], v.get("gender"), v.get("type"), len(v["stats"])])
                for ln in v["links"]:
                    w["seasons"].writerow([v["id"], ln["t"], ln["n"], end_year(ln["n"])])
            elif s == "meta" and str(k).startswith("teams/"):
                _, lid, sid = k.split("/")
                for tid, name in v.items():
                    w["teams"].writerow([lid, sid, tid, name])
            elif s == "players":
                for pid, (name, cc, pos) in v.items():
                    players[int(pid)] = (name, cc, json.dumps(pos))
            elif s == "transfers":
                for t in v["rows"]:
                    fee = t.get("fee") or {}
                    w["transfers"].writerow([
                        t["id"], t.get("name"), t.get("pos"), (t.get("date") or "")[:10],
                        t.get("from"), t.get("fromName"), t.get("to"), t.get("toName"),
                        fee.get("value"), fee.get("feeText"), t.get("type"),
                        bool(t.get("loan")), bool(t.get("ext")),
                        (t.get("cFrom") or "")[:10] or None, (t.get("cTo") or "")[:10] or None, t.get("mv"),
                    ])
            elif s == "lists" and "rows" in v:
                lid, sid, stat = k.split("/")
                for r in v["rows"]:
                    w["stats"].writerow([lid, sid, stat, *r])
    for pid, (name, cc, pos) in players.items():
        w["players"].writerow([pid, name, cc, pos])
    for f in files.values():
        f.close()

    DB.parent.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB))
    spec = {
        "leagues": "league_id INT, name VARCHAR, cc VARCHAR, gender VARCHAR, type VARCHAR, n_stats INT",
        "seasons": "league_id INT, season_id BIGINT, season_name VARCHAR, end_year INT",
        "teams": "league_id INT, season_id BIGINT, team_id BIGINT, name VARCHAR",
        "players": "player_id BIGINT, name VARCHAR, cc VARCHAR, positions VARCHAR",
        "stats": "league_id INT, season_id BIGINT, stat VARCHAR, player_id BIGINT, team_id BIGINT, "
                 "value DOUBLE, sub_value DOUBLE, minutes INT, matches INT",
        "transfers": "player_id BIGINT, name VARCHAR, pos VARCHAR, date DATE, from_id BIGINT, from_name VARCHAR, "
                     "to_id BIGINT, to_name VARCHAR, fee DOUBLE, fee_text VARCHAR, type VARCHAR, loan BOOLEAN, "
                     "extension BOOLEAN, contract_from DATE, contract_to DATE, market_value DOUBLE",
    }
    for n, cols in spec.items():
        con.execute(f"CREATE OR REPLACE TABLE fm_{n} ({cols})")
        con.execute(f"COPY fm_{n} FROM '{tmp / (n + '.csv')}' (HEADER false, NULLSTR '')")
        print(n, con.execute(f"SELECT count(*) FROM fm_{n}").fetchone()[0])
    con.execute("CREATE OR REPLACE TABLE fm_transfers AS SELECT DISTINCT * FROM fm_transfers")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1])
