# Beslutninger

Valg som er tatt, hvorfor, og hva som ble valgt bort. Nyeste nederst.
Testresultatene bak står i `resultater.md`.

| # | Dato | Beslutning | Hvorfor | Valgt bort |
|---|------|-----------|---------|------------|
| 1 | 2026-11-15 | Omfang er alle ligaer, ikke Eliteserien | Joachim: en underpriset spiller i Bosnia er like interessant som en i Norge | Eliteserien-fokus (min feil) |
| 2 | 2026-11-15 | Gratis data, lokal privat bruk. Data aldri i repoet | Ikke en business. Uoffisielle kilder | Betalt data inntil verdien er vist |
| 3 | 2026-11-15 | Evalueringsprotokoll skrives før modellene | Unngå å tilpasse testen til resultatet | – |
| 4 | 2026-11-15 | FotMob er basekilde. SofaScore bare der FotMob mangler | De er samme data i bunnen (xG-sum 536,9 mot 536,0). FotMob har samme id i statistikk, overganger og profil | Bruke begge som kontroll på hverandre |
| 5 | 2026-11-15 | Fasit for pris er FotMobs overgangsliste | Sum + spiller-id, 22 190 overganger fra 2015 | Transfermarkt-datasettet (krever navnekobling) |
| 6 | 2026-11-15 | Markedsverdi fra andre er aldri inndata i prismodellen | Lekkasje. Brukes som motstander og som karriereforløp | – |
| 7 | 2026-11-15 | Innhenting går via nettleser, lagres i nettleserens lager, eksporteres til `data/raw/` | Skript når ikke kildene fra arbeidsmiljøet | Skript (ikke testet på Macen) |
| 8 | 2026-11-15 | Alle tall per 90 krympes | Test 1: bedre på 17 av 17 statistikker | Rå tall |
| 9 | 2026-11-15 | Sammenligning på tvers av ligaer er med | Test 3: bedre på 14 av 15 | – |
| 10 | 2026-11-15 | Prisindeks v1 uten prestasjonskontroll | Versjonen med prestasjon var ustabil før 2020 | Indeks med prestasjon (tas opp igjen) |
| 11 | 2026-11-15 | Karrierer simuleres ved å lenke ettårs-overganger | Test 4: halverer feilen over ti år, spennet er kalibrert | Kreve hele karrierer i data |
| 12 | 2026-11-15 | Simulatorens tilstand er alder + nivå | Retning siste år ga ingenting ekstra | Retning som tilstand |
| 13 | 2026-11-15 | To datanivåer: full profil og historisk profil | Detaljer finnes fra 2014/16, enkle tall fra 2002 | Bare moderne data |
| 14 | 2026-11-15 | Verdi vises både i dagens priser og med fremskrevet prisindeks | Joachim: dagens prisnivå alene er ikke nok | Bare dagens prisnivå |
| 15 | 2026-11-15 | Kjøp får to dommer: på kjøpsdagen og i ettertid | Må kunne dømme overganger som skjer nå | Bare etterpåklokskap |
| 16 | 2026-11-15 | Klausuler prises som opsjoner med simulatoren | Slik fungerer avtaler i virkeligheten | Se bort fra klausuler |

## Åpne spørsmål

- Frafall som egen tilstand i simulatoren (overlevelsesskjevhet).
- Lagstyrke skilt fra ligastyrke (klubb-Elo).
- Hvor mye videresalgsandeler forskyver fasiten for unge fra små ligaer.
- Lønn: ingen gratis kilde funnet.
- Om skript kan nå kildene direkte fra Macen (`scripts/nettsjekk.py`).
