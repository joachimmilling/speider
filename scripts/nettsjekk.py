"""Sjekker om et vanlig skript på denne maskinen når datakildene.

Kjør:  python3 scripts/nettsjekk.py

Ingenting lagres. Skriptet gjør ett kall per kilde og skriver ut statuskoden.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)

KILDER = [
    ("FotMob statistikklister", "https://data.fotmob.com/stats/59/season/24542/mins_played.json"),
    ("FotMob liga (API)", "https://www.fotmob.com/api/data/leagues?id=59"),
    ("FotMob overganger (API)", "https://www.fotmob.com/api/data/transfers?page=1&minFee=1"),
    ("FotMob spiller (API)", "https://www.fotmob.com/api/data/playerData?id=188971"),
    ("SofaScore sesonger", "https://www.sofascore.com/api/v1/unique-tournament/222/seasons"),
    ("SofaScore kamp", "https://www.sofascore.com/api/v1/event/17431358/lineups"),
    ("Transfermarkt-datasett", "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/transfers.csv.gz"),
    ("Eliteserien Fantasy", "https://fantasy.eliteserien.no/api/bootstrap-static/"),
    ("ClubElo", "http://api.clubelo.com/2026-11-01"),
]


def sjekk(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(4096)
            kind = "json" if body[:1] in (b"{", b"[") else "annet"
            return f"OK {r.status} ({kind})"
    except urllib.error.HTTPError as e:
        return f"AVVIST {e.code}"
    except Exception as e:  # noqa: BLE001
        return f"FEIL {type(e).__name__}"


def main() -> None:
    res = {}
    for navn, url in KILDER:
        res[navn] = sjekk(url)
        print(f"{navn:28s} {res[navn]}")
    print()
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
