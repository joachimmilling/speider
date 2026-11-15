"""Command line: speider fetch | status | player | top."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .db import DEFAULT_PATH, connect
from .ingest import fetch_esf, fetch_fotmob

METRICS = {
    "goals": "goals", "assists": "assists", "minutes": "minutes",
    "goals_per_90": "goals_per_90", "assists_per_90": "assists_per_90",
    "goal_involvements_per_90": "goal_involvements_per_90", "minutes_share": "minutes_share",
}


def _table(headers: list[str], rows: list[tuple]) -> str:
    cells = [headers] + [["" if v is None else str(v) for v in row] for row in rows]
    widths = [max(len(row[i]) for row in cells) for i in range(len(headers))]
    lines = ["  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip() for row in cells]
    return "\n".join(lines)


def cmd_fetch(con, args) -> int:
    counts = fetch_esf(con, raw_dir=args.raw_dir, with_matches=args.matches, progress=print)
    if args.fotmob:
        counts.update(fetch_fotmob(con, raw_dir=args.raw_dir, progress=print))
    print("Saved: " + ", ".join(f"{rows} {what}" for what, rows in counts.items()))
    return 0


def cmd_status(con, args) -> int:
    tables = ["teams", "players", "player_snapshots", "fixtures", "player_matches", "player_seasons", "player_stats"]
    rows = [(t, con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]) for t in tables]
    print(_table(["table", "rows"], rows))
    last = con.execute("SELECT max(fetched_at) FROM fetch_log").fetchone()[0]
    print(f"\nLast fetched: {last or 'never. Run: speider fetch'}")
    return 0


def cmd_player(con, args) -> int:
    rows = con.execute(
        """SELECT display_name, first_name || ' ' || last_name, position, team, minutes, goals, assists,
                  goals_per_90, assists_per_90, minutes_share
           FROM player_current
           WHERE (first_name || ' ' || last_name || ' ' || display_name) ILIKE ?
           ORDER BY minutes DESC LIMIT 20""", [f"%{args.name}%"]).fetchall()
    if not rows:
        print(f"No player matching '{args.name}'.")
        return 1
    print(_table(["player", "full name", "pos", "team", "min", "goals", "ast", "goals/90", "ast/90", "min share"], rows))
    return 0


def cmd_top(con, args) -> int:
    column = METRICS[args.metric]
    where, params = ["minutes >= ?", f"{column} IS NOT NULL"], [args.min_minutes]
    if args.position:
        where.append("position = ?")
        params.append(args.position.upper())
    rows = con.execute(
        f"""SELECT display_name, position, team, minutes, goals, assists, {column}
            FROM player_current WHERE {' AND '.join(where)}
            ORDER BY {column} DESC, minutes DESC LIMIT ?""", params + [args.limit]).fetchall()
    print(_table(["player", "pos", "team", "min", "goals", "ast", args.metric], rows))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="speider", description="Local football player database.")
    parser.add_argument("--version", action="version", version=f"speider {__version__}")
    parser.add_argument("--db", default=str(DEFAULT_PATH), help="path to the database (default: data/speider.duckdb)")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="fetch fresh data into the local database")
    fetch.add_argument("--matches", action="store_true", help="also fetch match log and earlier seasons per player (a few minutes)")
    fetch.add_argument("--fotmob", action="store_true", help="also fetch FotMob statistics for all seasons (about 400 small files)")
    fetch.add_argument("--raw-dir", default="data/raw", help="where raw data is stored")
    fetch.set_defaults(func=cmd_fetch)

    sub.add_parser("status", help="show what the database contains").set_defaults(func=cmd_status)

    player = sub.add_parser("player", help="look up a player by name")
    player.add_argument("name")
    player.set_defaults(func=cmd_player)

    top = sub.add_parser("top", help="rank players on a metric")
    top.add_argument("--metric", choices=sorted(METRICS), default="goal_involvements_per_90")
    top.add_argument("--min-minutes", type=int, default=450)
    top.add_argument("--position", choices=["GK", "DEF", "MID", "FWD", "gk", "def", "mid", "fwd"])
    top.add_argument("--limit", type=int, default=15)
    top.set_defaults(func=cmd_top)

    args = parser.parse_args(argv)
    con = connect(args.db)
    try:
        return args.func(con, args)
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
