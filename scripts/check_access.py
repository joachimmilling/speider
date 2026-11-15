"""Check whether a plain script on this machine can reach the data sources.

Run:  python3 scripts/check_access.py

Nothing is stored. One request per source; prints the status code.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

SOURCES = [
    ("FotMob stat lists", "https://data.fotmob.com/stats/59/season/24542/mins_played.json"),
    ("FotMob league (API)", "https://www.fotmob.com/api/data/leagues?id=59"),
    ("FotMob transfers (API)", "https://www.fotmob.com/api/data/transfers?page=1&minFee=1"),
    ("FotMob player (API)", "https://www.fotmob.com/api/data/playerData?id=188971"),
    ("SofaScore seasons", "https://www.sofascore.com/api/v1/unique-tournament/222/seasons"),
    ("SofaScore match", "https://www.sofascore.com/api/v1/event/17431358/lineups"),
    ("Transfermarkt dataset", "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/transfers.csv.gz"),
    ("Eliteserien Fantasy", "https://fantasy.eliteserien.no/api/bootstrap-static/"),
    ("ClubElo", "http://api.clubelo.com/2026-11-01"),
]


def check(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(4096)
            kind = "json" if body[:1] in (b"{", b"[") else "other"
            return f"OK {r.status} ({kind})"
    except urllib.error.HTTPError as e:
        return f"REJECTED {e.code}"
    except Exception as e:  # noqa: BLE001
        return f"ERROR {type(e).__name__}"


def main() -> None:
    res = {}
    for name, url in SOURCES:
        res[name] = check(url)
        print(f"{name:28s} {res[name]}")
    print()
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
