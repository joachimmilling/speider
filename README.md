# Speider

Åpen spillerdatabase og egne modeller for scouting i norsk fotball. Et hobbyprosjekt, laget for å se hva man kan regne ut selv: estimert markedsverdi, prognoser og likhetssøk.

Speider er for dem som jobber som scouter og agenter, og svarer på spørsmål som:

- Hvem ligner på denne spilleren, men er yngre eller billigere?
- Hva er spilleren verdt nå, og hvor er verdien på vei?
- Hvem presterer over nivået sitt og går ut av kontrakt snart?

## Status

Første byggestein er på plass: en lokal database med alle spillere i Eliteserien. Veien videre står i [docs/plan.md](docs/plan.md), og resultatene fra første test i [docs/pilot.md](docs/pilot.md).

| Del | Status |
|---|---|
| Lokal database (DuckDB) | Ferdig |
| Spillere, lag, minutter, mål, målgivende (Eliteserien Fantasy) | Ferdig |
| Kamplogg og tidligere sesonger per spiller | Ferdig |
| Prestasjonstall fra FotMob (pasninger, forsvar, xG, xA) | Henting ferdig, ikke kjørt på ekte data herfra |
| Alder, kontrakt, overgangssummer | Kilde funnet, henting ikke skrevet |
| Verdimodell, likhetssøk, prognoser | Ikke startet |
| Nettside | Ikke startet, design finnes |

## Kom i gang

Krever Python 3.10 eller nyere.

```bash
git clone https://github.com/joachimmilling/speider.git
cd speider
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

speider fetch              # henter spillere, lag og kamper (noen sekunder)
speider fetch --matches    # henter også kamplogg per spiller (noen minutter)
speider fetch --fotmob     # henter også FotMob-statistikk for alle sesonger
speider status
speider top --metric goals_per_90 --min-minutes 900
speider player "berg"
```

Dataene havner i `data/speider.duckdb`. Hver gang du kjører `speider fetch`, lagres et nytt øyeblikksbilde, så du etter hvert kan se utvikling over tid.

Du kan også spørre databasen direkte:

```bash
duckdb data/speider.duckdb "SELECT display_name, team, minutes, goal_involvements_per_90 FROM player_current WHERE position = 'DEF' AND minutes > 900 ORDER BY 4 DESC LIMIT 10"
```

## Data og vilkår

Repoet inneholder bare kode. Ingen data fra tredjeparter er sjekket inn, og `data/` er utelatt i `.gitignore`. Du henter dataene selv til din egen maskin.

Les [docs/datakilder.md](docs/datakilder.md) før du bruker Speider til noe annet enn privat utforsking. Flere av kildene er uoffisielle eller tillater bare ikke-kommersiell bruk.

## Slik er det bygget

```
src/speider/
  schema.sql        tabeller og visningen player_current
  db.py             kobling til DuckDB
  sources/esf.py    oversetter Eliteserien Fantasy til våre tabeller
  sources/http.py   rolig henting med rådata-kopi
  ingest.py         henter og laster inn
  cli.py            kommandoene over
tests/              tester mot oppdiktede eksempeldata
```

Hver kilde får sin egen fil under `sources/` og sitt eget prefiks på id-ene (`esf:12`), så flere kilder kan kobles sammen senere.

## Tester

```bash
pytest
```

## Lisens

Koden er MIT-lisensiert. Lisensen gjelder ikke dataene du henter.
