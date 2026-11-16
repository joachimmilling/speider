"""Load national-team spells from the profile exports into DuckDB: fm_national.

One row per player and national team (senior or age-group) with start and end
date, matches and goals. Run after load_profiles.py with the same files.
"""
from __future__ import annotations

import gzip, json, re, sys

import duckdb
import pandas as pd


def num(x):
    m = re.search(r"\d+", str(x or ""))
    return float(m.group()) if m else None


def main(paths) -> None:
    rows, seen = [], set()
    for p in paths:
        for line in gzip.open(p, "rt"):
            o = json.loads(line)
            if o["id"] in seen: continue
            seen.add(o["id"])
            for t in o.get("nat") or []:
                m = re.search(r"U(\d{2})", t.get("team") or "")
                rows.append(dict(player_id=o["id"], team=t.get("team"), level=int(m.group(1)) if m else 99,
                                 start_date=(t.get("startDate") or "")[:10] or None, end_=(t.get("endDate") or "")[:10] or None,
                                 apps=num(t.get("appearances")),
                                 goals=num(t.get("goals"))))
    df = pd.DataFrame(rows)
    con = duckdb.connect("data/speider.duckdb")
    con.execute("CREATE OR REPLACE TABLE fm_national AS SELECT player_id, team, level, cast(start_date as date) as start_date, cast(end_ as date) as end_date, apps, goals FROM df")
    print("national spells", len(df), "players", df.player_id.nunique(), "senior", int((df.level == 99).sum()))


if __name__ == "__main__":
    main(sys.argv[1:])
