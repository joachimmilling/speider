"""Load match details (NDJSON, gzip) into DuckDB: fm_matches, fm_lineups, fm_unavailable.

One line per match as written by the browser crawl: date, teams, score, formation, starters and substitutes
(player, position id, line, rating, substitution events) and the players listed as unavailable with the reason.
Run:  python3 scripts/load_matches.py data/raw/fotmob/matches-*.ndjson.gz
"""
from __future__ import annotations

import csv, gzip, json, sys, tempfile
from pathlib import Path

import duckdb


def main(paths):
    tmp = Path(tempfile.mkdtemp())
    f = {n: open(tmp / f"{n}.csv", "w", newline="") for n in ["matches", "lineups", "unavailable"]}
    w = {n: csv.writer(x) for n, x in f.items()}
    seen = set()
    for p in sorted(paths, reverse=True):
        for line in gzip.open(p, "rt"):
            o = json.loads(line)
            if o["id"] in seen or not o.get("home") or not o.get("away"):
                continue
            seen.add(o["id"])
            ey = int(o["season"][-4:])
            w["matches"].writerow([o["id"], o["lid"], o["season"], ey, o.get("round"), (o.get("t") or "")[:19].replace("T", " ") or None, o["h"], o["a"], o.get("hs"), o.get("as"),
                                   o["home"].get("f"), o["away"].get("f"), o["home"].get("r"), o["away"].get("r")])
            for side, team in (("home", o["h"]), ("away", o["a"])):
                t = o[side]
                for started, lst in ((1, t.get("st") or []), (0, t.get("su") or [])):
                    for pid, pos, line_, rating, ev in lst:
                        on = 0 if started else next((m for k, m in ev if k == "subIn"), None)
                        off = next((m for k, m in ev if k == "subOut"), None)
                        played = started or on is not None
                        mins = (min(off if off is not None else 90, 90) - min(on or 0, 90)) if played else 0
                        w["lineups"].writerow([o["id"], team, pid, started, pos or None, line_, rating, on, off, int(played), max(mins, 0)])
                for pid, typ, inj, ret in t.get("un") or []:
                    w["unavailable"].writerow([o["id"], team, pid, typ, inj, json.dumps(ret) if ret else None])
    for x in f.values():
        x.close()
    con = duckdb.connect("data/speider.duckdb")
    spec = {
        "matches": "match_id BIGINT, league_id INT, season VARCHAR, end_year INT, round VARCHAR, played_at TIMESTAMP, home_id BIGINT, away_id BIGINT, home_goals INT, away_goals INT, home_formation VARCHAR, away_formation VARCHAR, home_rating DOUBLE, away_rating DOUBLE",
        "lineups": "match_id BIGINT, team_id BIGINT, player_id BIGINT, started INT, position_id INT, line INT, rating DOUBLE, minute_on INT, minute_off INT, played INT, minutes INT",
        "unavailable": "match_id BIGINT, team_id BIGINT, player_id BIGINT, type VARCHAR, injury_id INT, expected_return VARCHAR",
    }
    for n, cols in spec.items():
        con.execute(f"CREATE OR REPLACE TABLE fm_{n} ({cols})")
        con.execute(f"COPY fm_{n} FROM '{tmp / (n + '.csv')}' (HEADER false, NULLSTR '')")
        print(n, con.execute(f"SELECT count(*) FROM fm_{n}").fetchone()[0])
    print(con.execute("select end_year, count(*), sum((select count(*) from fm_unavailable u where u.match_id = m.match_id)) from fm_matches m group by 1 order by 1").fetchall())
    print(con.execute("select type, count(*) from fm_unavailable group by 1 order by 2 desc").fetchall())


if __name__ == "__main__":
    main(sys.argv[1:])
