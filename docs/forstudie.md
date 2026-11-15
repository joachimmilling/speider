# Forstudie: holder datagrunnlaget?

Kjørt 2026-11-15, før noe lastes ned i stor skala. Alle tall er målt, ikke
anslått, med mindre det står noe annet.

## Kort svar

| # | Spørsmål | Svar |
|---|----------|------|
| 1 | Når et vanlig skript kildene? | **Ikke avklart.** Må testes på Macen: `python3 scripts/nettsjekk.py` |
| 2 | Nok overganger med sum og prestasjonsdata før? | **Ja.** Ca. 6 300 siden 2022 |
| 3 | Nok ligabyttere til å måle ligastyrke? | **Ja for store ligaer, tynt for små** |
| 4 | Kan vi koble samme spiller på tvers av kilder? | **Ja**, og for kjernen trengs det ikke |
| 5 | Er FotMob og SofaScore enige? | **De er samme data.** Ikke to uavhengige kilder |
| 6 | Har små ligaer detaljert nok data? | **Ja fra 2023/24.** Ingenting før |

## 1. Skripttilgang

Verken skyarbeidsområdet eller den lokale VM-en slipper ut til datakildene
(nettverksfilter). Alt i denne forstudien er hentet gjennom nettleseren.
Testen må derfor kjøres direkte på Macen. Kjent risiko: FotMobs `/api/data`
krever en signert header utenfor nettleser, og SofaScore avviser ofte skript.
FotMobs statiske lister (`data.fotmob.com`) er åpne.

Hvis skript blir avvist: innhentingen kjøres gjennom nettleseren, slik
forstudien er gjort. Tregere, men det virker.

## 2. Fasit for prismodellen

Ny kilde funnet: FotMobs overgangsliste (`/api/data/transfers` med `fromDate`,
`toDate`, `minFee`). Den har sum, dato, klubber og **FotMobs egen spiller-id**.

| År | Betalte overganger (uten lån) | Har ≥ 900 min i FotMob før |
|----|------|------|
| 2019 | 899 | ikke hentet (*) |
| 2020 | 658 | ikke hentet (*) |
| 2021 | 800 | ikke hentet (*) |
| 2022 | 1 158 | 785 |
| 2023 | 1 495 | 1 161 |
| 2024 | 1 644 | 1 287 |
| 2025 | 2 030 | 1 601 |
| 2026 | 1 837 | 1 487 |

(*) Forstudien hentet bare de seks siste sesongene per liga. Eldre sesonger
finnes for mange ligaer.

- Sum siden 2022 med prestasjonsdata før: **6 321**.
- Summer siden 2023: median 2,0 mill. euro, 10 % under 260 000, 1 291 under
  500 000. Altså ikke bare toppfotball.
- 97 % har også markedsverdi på overgangsdagen. Den brukes som motstander i
  testen, aldri som inndata.

Forbehold: «før» er regnet på sesongnivå. Vinteroverganger kan ha fått med
noen kamper etter overgangen. Det reelle tallet er litt lavere. Ukjente
summer («undisclosed») er ikke med, og de er ikke tilfeldige.

## 3. Ligabyttere

FotMob, 70 herreligaer med dyp statistikk, seks siste sesonger:

- 252 686 spillersesonger, 83 050 med ≥ 900 minutter, 68 183 spillere.
- **11 283 bytter** med ≥ 900 minutter på begge sider (19 122 med ≥ 450).
- 6 047 av dem går mellom land. 999 ulike ligapar.
- Median liga har 55 bytter. 

Svakt punkt: Flere små ligaer har bare to sesonger i FotMob og derfor få
bytter (Slovakia 19, Island 21, Tsjekkia 34, Serbia 36, Finland 36, Romania 45).
Ligastyrke for disse blir usikker og må støttes av klubb-Elo og
europacupkamper. Usikkerheten skal vises.

42 av de 70 har xG.

## 4. Samme spiller i flere kilder

- FotMob bruker samme id i statistikk, overganger og spillerprofil. Kjernen
  (prestasjon → sum) trenger ingen navnekobling.
- FotMob ↔ SofaScore, Eliteserien 2025: begge har 442 spillere. Bare navn
  treffer 80 %. Navn + minutter treffer 90 %. Resten er samme spiller med
  ulik minutt-telling. Navn + lag løser dem.
- Transfermarkt-datasettet ble ikke koblet i denne runden. Det trengs ikke
  lenger som fasit, bare som ekstra sjekk.

## 5. FotMob mot SofaScore

Eliteserien 2025, 229 spillere med xG i begge:

- xG-sum: 536,9 mot 536,0. Korrelasjon 1,00. Median avvik 0,03.
- Mål: identisk.
- Minutter: identisk for 72 %, resten avviker 2–5 % (tilleggstid).

Konklusjon: Samme leverandør i bunnen. Vi får ingen kvalitetskontroll av å
sammenligne dem, og vi trenger ikke begge for samme liga. FotMob er basen.
SofaScore fyller ligaene FotMob mangler.

## 6. Små ligaer (SofaScore)

Testet Bosnia (WWIN Liga) og Kypros, én kamp per sesong:

| Sesong | Statistikker per spiller per kamp | xG | Skuddkart | Snittposisjon |
|--------|------|----|-----------|---------------|
| 2023/24 → i dag | 40–53 | ja | ja, med xG | ja |
| 2022/23 og eldre | 0 | nei | nei | nei |

- Posisjon per kamp er bare K/F/M/A, men formasjon + snittposisjon gir rollen.
- Enkelte kamper har løpsdata (distanse, sprinter, toppfart).
- Overgangshistorikk med summer finnes per spiller, men tynt: i et utvalg på
  40 bosniske spillere hadde 8 en betalt overgang siden 2023.
- Én kypriotisk sesong (2025/26) ga tom prøve. Kan være en utsatt kamp. Må
  sjekkes før Kypros regnes som dekket.

## Hva dette betyr

**Vi kan:**
- Trene prismodell på ekte summer med flere tusen eksempler.
- Måle ligastyrke direkte mellom de fleste ligaer.
- Dekke Bosnia, Kypros og lignende fra 2023/24.

**Vi kan ikke:**
- Backteste små ligaer lenger tilbake enn 2023. «Underpriset»-testen der
  får maks to–tre år.
- Bruke FotMob og SofaScore som kontroll på hverandre.
- Stole på ligastyrke for ligaer med under ca. 50 bytter uten støtte.

**Endring i modellplanen:**
- Egen xG-modell er mindre viktig enn antatt. Leverandørens xG finnes nå i
  små ligaer. Den beholdes for kontroll og for keepere.
- Ligastyrke for små ligaer er det største hullet. Den får høyest prioritet.
