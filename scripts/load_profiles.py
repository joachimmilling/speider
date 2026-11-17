"""Load player profiles (NDJSON, gzip) into DuckDB: fm_profiles, fm_mv, fm_career.

Files from 2026-11-17 on also carry the current club (team), the current injury (inj) and the status (st); older files leave them empty.
Later files win: a player downloaded again replaces his earlier profile.
"""
from __future__ import annotations

import csv, gzip, json, re, sys, tempfile
from pathlib import Path

import duckdb


def ey(name):
    m = re.findall(r"\d{4}", name or "")
    return int(m[-1]) if m else None


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main(paths):
    tmp = Path(tempfile.mkdtemp())
    f = {n: open(tmp / f"{n}.csv", "w", newline="") for n in ["profiles", "mv", "career"]}
    w = {n: csv.writer(x) for n, x in f.items()}
    seen = set()
    for p in sorted(paths, reverse=True):
        for line in gzip.open(p, "rt"):
            o = json.loads(line)
            if o["id"] in seen or "err" in o:
                continue
            seen.add(o["id"])
            info = {k: v for k, v in (o.get("info") or []) if isinstance(k, str)}
            team = o.get("team") if isinstance(o.get("team"), list) and len(o["team"]) == 2 else [None, None]   # current club, files from 2026-11-17
            h = re.findall(r"\d+", str(info.get("Height") or ""))
            w["profiles"].writerow([o["id"], o.get("name"), (o.get("b") or "")[:10] or None, (o.get("ce") or "")[:10] or None,
                                    o.get("gender"), h[0] if h else None, info.get("Preferred foot"), info.get("Country"),
                                    json.dumps(o.get("pos") or []),
                                    team[0], team[1],
                                    json.dumps(o["inj"]) if o.get("inj") else None, o.get("st")])
            for v in ((o.get("mv") or {}).get("values") or []):
                w["mv"].writerow([o["id"], v["date"][:10], v.get("value"), v.get("lowerBound"), v.get("upperBound"), v.get("teamId")])
            for s in o.get("seasons") or []:
                for t in s.get("ts") or []:
                    if t.get("isFriendly"):
                        continue
                    w["career"].writerow([o["id"], t.get("seasonName"), ey(t.get("seasonName")), t.get("leagueId"), t.get("leagueName"),
                                          s.get("teamId"), s.get("team"), num(t.get("appearances")), num(t.get("goals")),
                                          num(t.get("assists")), num(t.get("rating"))])
    for x in f.values():
        x.close()
    con = duckdb.connect("data/speider.duckdb")
    spec = {
        "profiles": "player_id BIGINT, name VARCHAR, birth DATE, contract_end DATE, gender VARCHAR, height INT, foot VARCHAR, country VARCHAR, positions VARCHAR, cur_team_id BIGINT, cur_team VARCHAR, injury VARCHAR, status VARCHAR",
        "mv": "player_id BIGINT, date DATE, value DOUBLE, lo DOUBLE, hi DOUBLE, team_id BIGINT",
        "career": "player_id BIGINT, season_name VARCHAR, end_year INT, league_id INT, league_name VARCHAR, team_id BIGINT, team VARCHAR, apps DOUBLE, goals DOUBLE, assists DOUBLE, rating DOUBLE",
    }
    for n, cols in spec.items():
        con.execute(f"CREATE OR REPLACE TABLE fm_{n} ({cols})")
        con.execute(f"COPY fm_{n} FROM '{tmp / (n + '.csv')}' (HEADER false, NULLSTR '')")
        print(n, con.execute(f"SELECT count(*) FROM fm_{n}").fetchone()[0])
    print(con.execute("select min(date), max(date), count(distinct player_id) from fm_mv").fetchone())
    print(con.execute("select min(end_year), count(*) filter(where end_year<2015), count(distinct player_id) from fm_career").fetchone())
    print(con.execute("select year(date) y, count(distinct player_id) n from fm_mv group by 1 order by 1").fetchall())


if __name__ == "__main__":
    main(sys.argv[1:])
