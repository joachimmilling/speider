# Resultater

Løpende logg over hva som er testet og hva som kom ut. Nyeste nederst.

## Data inne (2026-11-15)

FotMob, hentet via nettleser, lagret i `data/` (ikke i repoet):

- 4,17 mill. statistikkrader, 81 149 spillere, 109 ligaer med spilletid.
- 22 190 overganger med kjent sum, 2015–2026.
- Spillerprofiler (fødselsdato, kontrakt, karrierehistorikk, markedsverdi
  over tid) hentes fortsatt: 48 341 spillere, de med overgang først.

Last inn: `python3 scripts/last_fotmob.py data/raw/fotmob/export-20261115.ndjson.gz`

## Test 1: Krymping slår rå tall

`python3 analyse/krymping.py`

Oppgave: spå spillerens tall neste sesong (samme liga, ≥ 900 min neste år).
Krympestyrken er lært på sesonger til og med 2024 og testet på 2025–2026.

| Statistikk (per 90) | Mindre feil enn rå tall | For spillere under 900 min |
|---|---|---|
| Ballvinning siste tredjedel | 18 % | 36 % |
| Mål | 15 % | 35 % |
| Brudd | 12 % | 24 % |
| Skudd på mål | 11 % | 26 % |
| Taklinger | 11 % | 26 % |
| Vellykkede dribler | 9 % | 20 % |
| xG | 7 % | 19 % |
| xA | 5 % | 14 % |
| Pasninger | 4 % | 6 % |
| Klareringer | 2 % | 13 % |

Alle 17 testede statistikker ble bedre. Ingen ble dårligere. 8 000–15 000
spillere i testen per statistikk.

Krympestyrke (minutter før egne tall teller like mye som snittet): pasninger
300, dribler og xG 500, taklinger 800, mål 1 800, ballvinning høyt 2 700.

**Konklusjon:** Krymping er med. Alle tall per 90 i Speider skal være krympet.

## Test 2: Prisindeks, første versjon

`python3 analyse/prisindeks.py`

Årseffekt i regresjon på log(sum), med selgende liga, kjøpende liga og
posisjon holdt fast. 13 386 overganger.

| År | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Indeks | 76 | 84 | 90 | 94 | 98 | 84 | 84 | 85 | 92 | 88 | 97 | 100 |

- Snitt vekst 2,5 % per år. Korona-fallet i 2020 var 14 %, hentet inn i 2025–26.
- Rå median går motsatt vei (2,7 → 2,0 mill.) fordi kilden dekker flere små
  overganger nå. Derfor trengs indeksen.

Fremskriving (tilfeldig gang med drift, 80 %-spenn):

| År | Indeks | Spenn |
|---|---|---|
| 2029 | 108 | 91–127 |
| 2031 | 113 | 91–140 |
| 2034 | 122 | 93–160 |

**Svakheter, må fikses:**
- Alder er ikke med ennå. Blir kjøperne yngre, undervurderer indeksen veksten.
- Versjonen som også holder prestasjon fast ble ustabil før 2020 (for få
  ligaer med historikk) og er forkastet inntil videre.
- Fremskrivingen er den enkleste mulige. Alternativer som skal testes mot
  den: kobling til klubbenes inntekter/TV-avtaler, egen indeks per prisklasse.
