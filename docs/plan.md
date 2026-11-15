# Plan for Speider, versjon 2

Skrevet 15. november 2026, etter datarevisjonen og en ny gjennomgang av kildene.

## Målet

En plattform som svarer på tre spørsmål om en spiller:

1. Hvor god er han egentlig? (uavhengig av lag, flaks og skader)
2. Hva er han verdt i dag? (og er prisen et godt eller dårlig kjøp)
3. Hva er han ventet å være verdt om ett til tre år?

## Omfang

Speider er ikke bundet til Eliteserien. Målet er å finne underprisede spillere uansett liga, og en juvel i Serbia eller Colombia er like interessant som en i Norge. Eliteserien ble brukt i piloten fordi den var første liga som ble sjekket.

Det gjør én ting til kjernen i modellen: **liganivå**. Tall fra Slovakia må kunne oversettes til hva de betyr i Belgia. Det læres av spillere som har byttet liga og har tall fra begge.

Ligaer med dype tall hos FotMob (sjekket 15. november 2026, første og andre nivå i 94 land):

- 49 toppligaer har pasninger og forsvarstall. 16 andrenivåer har det også, blant dem Championship, 2. Bundesliga, Serie B, LaLiga2 og Ligue 2.
- 40 av de 65 ligaene har også xG.
- Dekket i Europa: de fem store, Nederland, Portugal, Belgia, Tyrkia, Skottland, Østerrike, Sveits, Danmark, Sverige, Norge, Finland, Island, Irland, Polen, Tsjekkia, Slovakia, Romania, Serbia, Kroatia, Hellas, Israel, Russland.
- Dekket ellers: Argentina, Brasil, Colombia, Chile, Ecuador, Paraguay, Peru, Bolivia, Mexico, USA, Canada, Japan, Sør-Korea, Kina, Thailand, India, Saudi-Arabia, Qatar, Emiratene, Egypt, Sør-Afrika, Australia.
- **Ikke dekket hos FotMob:** Bosnia og Kypros har bare mål og målgivende der. Det samme gjelder blant andre Ungarn, Bulgaria, Slovenia, Ukraina, Albania, Marokko og Uruguay.
- **SofaScore dekker flere:** 127 ligaer i 87 land har tall per spiller per kamp, også Bosnia, Kypros, Ungarn, Bulgaria, Slovenia og Marokko.

Historikken varierer: fra to sesonger (Serbia, Romania, Finland) til over ti (de store ligaene, Sverige, Norge, Danmark).

## Hva som gikk galt i første forsøk

Arbeidet startet med kildene som var lettest å nå, ikke med hva spørsmålene krever. Resultatet ble en modell som priser spillere på mål, målgivende og spilletid, og som ikke kan vurdere forsvarere, defensive midtbanespillere eller skadde spillere.

## Kilder, vurdert på nytt

| Kilde | Rolle | Status |
|---|---|---|
| SofaScore | Ryggraden: 45 til 78 tall per spiller per kamp i 127 ligaer, pluss alder, kontrakt, verdi og overganger. Se [kildeutforskning.md](kildeutforskning.md). | Gratis, uoffisiell. Data lagres bare lokalt. |
| FotMob | Skadehistorikk, skudd med xG, verdihistorikk fra SciSports og sesonglister i 65 ligaer. | Gratis, uoffisiell. Data lagres bare lokalt. |
| Sportmonks | Samme type tall gjennom et betalt, offisielt API. | Reserve hvis FotMob ikke holder, eller hvis data skal vises offentlig. |
| transfermarkt-datasets | Overgangssummer, verdihistorikk, alder, kontrakt. Dekker 31 toppligaer, så ikke alle FotMob-ligaene har pris. | I bruk. |
| Eliteserien Fantasy | Skader og status akkurat nå. | I bruk, lagres daglig. |
| StatsBomb Open Data | Trening av egne modeller på hendelsesdata. Ingen norske ligaer. | Senere. |
| Opta, Wyscout, StatsBomb | Bransjestandarden. | Selges til organisasjoner, ikke aktuelt. |

## Tre lag

**Lag 1: Kvalitet.** Én vurdering per spiller og posisjon, bygget på underliggende tall per 90 minutter. Justert for lagets nivå og dempet for spillere med få minutter. Skader og spilletid holdes utenfor.

**Lag 2: Verdi.** En modell trent på faktiske overgangssummer, med kvalitet, alder, kontrakt, posisjon og liganivå som inndata. Gir et anslag med usikkerhet.

**Lag 3: Fremtid.** Alderskurver per posisjon og utviklingen i kvalitet gir ventet verdi om ett til tre år.

## Faser, med krav for å gå videre

| Fase | Innhold | Krav for å gå videre |
|---|---|---|
| 0. Grunnmur | Repo på Macen, alle rådata lagret lokalt, hele kjeden kjørbar med én kommando. | `speider fetch` kjører på ekte data. |
| 1. FotMob-pilot | Hent én sesong Eliteserien. Sjekk dekning per posisjon. | Tallene finnes for minst 90 % av spillerne med over 450 minutter, også stoppere og defensive midtbanespillere. |
| 2. Holder tallene seg? | Sammenlign samme spiller i to sesonger på rad. | Kvalitetstallene henger tydelig sammen fra år til år. Tall som ikke gjør det, kastes. |
| 3. Kvalitet | Vurdering per posisjon. | Rangeringen gir mening for folk som følger ligaen, og forklarer senere overgangssummer bedre enn mål og målgivende alene. |
| 4. Verdi | Modell på overgangssummer, testet fremover i tid. | Treffer bedre enn Transfermarkt-verdien på salg modellen ikke har sett. |
| 5. Fremtid | Alderskurver og prognoser. | Prognoser laget på 2023-data treffer verdiene i 2025 bedre enn «samme som i dag». |
| 6. Produkt | Siden viser bare det som har bestått kravene, med usikkerhet. | |

## Kjente fallgruver

- Skader: spilletid skal aldri brukes som mål på kvalitet.
- Lagseffekt: tall må justeres for hvor godt laget er.
- Liganivå: krever spillere som har byttet liga, med tall fra begge.
- Pris mangler for noen ligaer: verdidatasettet dekker 31 ligaer, FotMob 65. For resten kan Speider anslå verdi, men ikke si hva markedet mener.
- Fasit: overgangssummer er også støyete. Bonuser og videresalg er ofte ukjente.
- Utvalg: bare solgte spillere har en sum. De er ikke et tilfeldig utvalg.
