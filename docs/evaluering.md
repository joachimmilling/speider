# Evalueringsprotokoll

Skrevet før modellene. Endres ikke etter at vi har sett resultatene uten at
endringen loggføres nederst.

## Grunnregler

1. **Bare fremover i tid.** Tren på alt før dato T, test på det som skjer
   etter. Aldri tilfeldig splitt.
2. **Ingen lekkasje.** En modell får bare se det som var kjent på dagen.
   Markedsverdier fra andre (Transfermarkt, SofaScore, SciSports) er aldri
   inndata.
3. **Alltid en referanse.** Hvert tall rapporteres ved siden av en enkel
   referanse. Slår vi den ikke, sier vi det.
4. **Usikkerhet vises.** Alle estimater har et spenn. Spennet testes: 80 %-
   spennet skal inneholde fasiten ca. 80 % av gangene.
5. **Resultater per gruppe.** Rolle, alder, liganivå. Et godt snitt kan
   skjule at modellen er ubrukelig for stoppere.

## Tester per lag

### Kvalitet
- Spå neste sesongs tall per statistikk. Mål: korrelasjon og feil.
- Referanse: fjorårets rå tall.
- For ligabyttere: spå tall i ny liga. Referanse: ingen omregning.

### Verdi
- Spå betalt sum for overganger etter T. Mål: median feil i prosent og
  rangkorrelasjon.
- Referanser: (a) Transfermarkt-verdi dagen før, (b) alder + liga + posisjon.
- Å slå (a) klart er usannsynlig og heller ikke kravet. Kravet er å være
  på nivå uten å ha sett den, og å kunne forklare avvikene.

### «Underpriset»
Den egentlige testen. Hver T lager modellen en liste over spillere den mener
er underpriset. To–tre år senere sjekker vi:
- Gikk de til en sterkere liga oftere enn like dyre spillere?
- Steg markedsverdien mer?
- Ble de solgt for mer?
Referanse: tilfeldig utvalg med samme alder, liga og pris.

### Gode og dårlige kjøp
- For kjøp etter T: ga modellens vurdering på kjøpsdagen utslag i minutter
  og verdiendring to år senere?

## Stoppregler

- Kvalitet slår ikke rå tall → stopp, ingen verdimodell på toppen.
- Ligaomregning slår ikke «ingen omregning» → ingen sammenligning på tvers
  av ligaer i produktet.
- «Underpriset»-listen slår ikke tilfeldig utvalg → funksjonen vises ikke.

## Endringslogg

- 2026-11-15: Første versjon.
