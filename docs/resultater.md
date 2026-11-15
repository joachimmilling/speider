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

## Test 3: Ligastyrke hjelper når spillere bytter liga

`python3 analyse/ligastyrke.py`

Oppgave: spå spillerens tall i ny liga, relativt til rollesnittet der.
Lært på bytter til og med 2025, testet på ca. 2 000 bytter i 2026–27.

| Statistikk | Mot «samme nivå som før» | Mot dempet nivå uten ligastyrke |
|---|---|---|
| Rating | 37 % mindre feil | 9 % |
| Pasninger | 21 % | 8 % |
| Skudd | 19 % | 5 % |
| xA | 17 % | 4 % |
| Mål | 26 % | 2 % |
| Dribler | 12 % | 2 % |
| xG | 21 % | 2 % |
| Taklinger | 12 % | 1 % |
| Brudd | 16 % | 0 % |

- Bedre på 14 av 15 statistikker. Brudd: ingen effekt.
- Det meste av gevinsten kommer fra demping (en spiller som var langt over
  snittet, havner nærmere snittet i ny liga). Ligastyrke gir 1–9 % i tillegg.
- Ligastyrke betyr mest for rating, pasninger og skudd, minst for
  defensive tellinger.

Rangering som faller ut (offensive tall): Premier League, Bundesliga, LaLiga,
Ligue 1, Serie A, brasiliansk Série A … nederst Island, Irland, dansk 1.
divisjon, India. Stemmer med det man venter, uten at vi har fortalt
modellen noe om nivå.

**Konklusjon:** Stoppregelen er passert. Sammenligning på tvers av ligaer
er med.

**Må fikses:** Cuper ligger i dataene som egne ligaer (Copa del Rey havnet
øverst) og skal ut. Lagstyrke er ikke med ennå: en spiller som går fra et
bunnlag til et topplag blandes med ligaeffekten. Klubb-Elo skal testes som
tillegg.

## Data: spillerprofiler (2026-11-15, delvis)

19 242 av 48 341 profiler inne (spillere med overgang først). Gir fødselsdato,
kontrakt, 1,03 mill. markedsverdi-punkter tilbake til 2014 og 470 000
sesonglinjer med kamper, mål, assist og rating tilbake til 2002.

Last inn: `python3 scripts/last_profiler.py data/raw/fotmob/profiler-*.ndjson.gz`

## Test 4: Karrieresimulator lenket av korte vinduer

`python3 analyse/karrieresimulator.py`

Idé (Joachim): man trenger ikke hele karrierer. Lær ettårs-overganger for
hver alder fra noen få år, og lenk dem.

Oppsett: overganger lært bare fra 2022–2026 (58 232 stk). Test: start i 2016,
simuler ti år frem, sammenlign med faktisk verdi i 2026. 2 000 spillere som
var 18–26 år ved start.

| Modell | Median feil etter 10 år | 80 %-spennet traff | Rangkorrelasjon |
|---|---|---|---|
| Verdien står stille | 213 % | – | 0,23 |
| A: bare alder | 190 % | 88 % | 0,47 |
| B: alder + nivå | 107 % | 81 % | 0,46 |
| C: alder + nivå + retning siste år | 111 % | 81 % | 0,46 |

Åtte år (start 2018): B 139 %, dekning 77 %. Stille: 201 %.

- Lenkingen virker. Spennet er riktig kalibrert: 80 %-spennet traff 81 %.
- Nivå må være med (190 → 107 %). Retning siste år ga ingenting ekstra.
- Feil på faktor 2 etter ti år er størrelsen på usikkerheten, ikke en feil i
  modellen. Derfor vises alltid spenn.

Lenket alderskurve (verdi relativt til 21 år):

| Alder | 18 | 19 | 20 | 21 | 23 | 25 | 27 | 29 | 31 | 33 | 35 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Verdi | 0,21 | 0,44 | 0,70 | 1,00 | 1,42 | 1,58 | 1,33 | 0,99 | 0,61 | 0,36 | 0,22 |

Topp ved 25 år. Tilbake på 21-årsnivå ved 29.

**Svakheter:**
- Overlevelsesskjevhet: profilene er hentet for spillere som fortsatt spilte
  etter 2021. De som forsvant før er ikke med, så kurven er for pen.
  Frafall som egen tilstand er neste steg.
- Testspillernes egne siste år ligger i treningsbanken (lite, men ikke rent).
- Tilstanden er markedsverdi fra leverandør, i løpende priser. Neste versjon
  bruker Speiders egen kvalitet og verdi, og prisindeksen.
- Bare 40 % av profilene er inne.

## Definisjon: godt og dårlig kjøp

To dommer, begge i samme prisnivå:

1. **På kjøpsdagen** (kan gis for overganger i dag): betalt sum mot Speiders
   verdi den dagen, der verdien inkluderer forventet utvikling og
   videresalg i kontraktsperioden (fra karrieresimulatoren). Gis som
   sannsynlighet for at kjøpet lønner seg, ikke bare ja/nei.
2. **I ettertid**: betalt sum mot faktisk verdi og spilletid senere.

Dom 2 brukes til å teste dom 1: holdt «godt kjøp på dagen» seg to år etter?
