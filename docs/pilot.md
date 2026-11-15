# FotMob-pilot, 15. november 2026

Test av de to første kravene i [planen](plan.md). Kjørt mot FotMobs sesonglister for Eliteserien, 2017 til 2026. Tallene ble regnet ut i en nettleserfane, ikke med koden i dette repoet, og må kjøres på nytt herfra før de regnes som bekreftet.

## Hva FotMob har

41 lister per sesong, ti sesonger. Hver liste har én rad per spiller med verdi, minutter, kamper, klubb og posisjon.

| Type tall | Fra sesong |
|---|---|
| Minutter, mål, målgivende, karakter, skudd, pasninger, lange pasninger, driblinger, sjanser skapt | 2017 |
| Taklinger, brudd, klareringer, blokkeringer, gjenvinninger, defensive handlinger | 2017 |
| xG, xG på mål, xA, avverget mål for keepere | 2020 |
| Linjebrytende pasninger | 2024 |
| Keeper: høye baller og feiing | 2025 |

Minuttlisten for 2026 har 449 spillere, og 307 av dem har minst 450 minutter. Det er nøyaktig de samme tallene som i Eliteserien Fantasy.

## Krav 1: dekning

Kravet var tall for minst 90 % av spillerne med over 450 minutter. **Ikke bestått ved 450 minutter, bestått ved 900.**

Andel spillere med defensive handlinger per 90 i 2026:

| Posisjon | Minst 450 min | Minst 900 min |
|---|---|---|
| Alle | 80 % | 93 % |
| Midtstopper | 72 % | 98 % |
| Back | 89 % | 97 % |
| Defensiv midtbane | 60 % | 75 % |
| Sentral midtbane | 88 % | 97 % |
| Offensiv midtbane | 71 % | 100 % |
| Ving | 78 % | 92 % |
| Spiss | 79 % | 92 % |
| Keeper | 70 % | 76 % |

Årsaken er at listene per 90 bare tar med spillere som har vært med i omtrent halvparten av kampene. Totaler som xG og xA har alle. Bare fem spillere er registrert som defensiv midtbane, så det tallet er usikkert.

Konsekvens: sesonglistene holder for faste spillere. For reserver og unge med få kamper trengs kampdata, som er neste kilde å undersøke.

## Krav 2: holder tallene seg fra år til år?

Samme spiller i to sesonger på rad, minst 900 minutter i begge, standardisert innen posisjonsgruppe og sesong. Alle sesongpar fra 2017 til 2026 samlet. **Bestått.**

| Tall | Sammenheng | Samme lag | Byttet lag | Antall |
|---|---|---|---|---|
| Presise pasninger per 90 | 0,83 | 0,85 | 0,67 | 997 |
| Presise lange pasninger per 90 | 0,77 | 0,78 | 0,70 | 922 |
| Sjanser skapt | 0,73 | 0,75 | 0,58 | 1059 |
| Vellykkede driblinger per 90 | 0,73 | 0,72 | 0,74 | 879 |
| xA per 90 | 0,71 | 0,73 | 0,49 | 652 |
| Defensive handlinger per 90 | 0,70 | 0,71 | 0,68 | 997 |
| Gjenvinninger per 90 | 0,70 | 0,70 | 0,68 | 997 |
| Skudd per 90 | 0,68 | 0,69 | 0,57 | 917 |
| Klareringer per 90 | 0,67 | 0,70 | 0,54 | 994 |
| Taklinger per 90 | 0,66 | 0,66 | 0,67 | 926 |
| Linjebrytende pasninger per 90 | 0,59 | 0,60 | 0,08 | 196 |
| Brudd per 90 | 0,53 | 0,55 | 0,46 | 915 |
| FotMob-karakter | 0,53 | 0,53 | 0,49 | 946 |
| xG per 90 | 0,50 | 0,51 | 0,45 | 598 |
| Redningsprosent | 0,38 | 0,40 | | 75 |
| Mål per 90 | 0,31 | 0,32 | 0,24 | 620 |
| Målgivende | 0,31 | 0,32 | 0,22 | 608 |
| Minutter spilt | 0,20 | 0,19 | 0,22 | 1126 |
| Avverget mål (keeper) | 0,14 | 0,18 | | 51 |

Lesning:

- De underliggende tallene er omtrent dobbelt så stabile som mål og målgivende. Det er de som bør bære kvalitetsvurderingen.
- Minutter spilt holder seg nesten ikke (0,20). Spilletid er et dårlig mål på hvem en spiller er.
- Driblinger, taklinger, gjenvinninger og defensive handlinger er like stabile når spilleren bytter lag. De følger spilleren.
- xA, sjanser skapt og linjebrytende pasninger faller mye ved lagbytte. De avhenger av laget og må justeres. Tallet for linjebrytende pasninger bygger på få spillere.
- Keepertallene er svake. Avverget mål er nesten bare støy fra år til år.

Stabilitet viser at et tall måler noe varig ved spilleren. Det viser ikke at tallet betyr noe for verdi. Det testes i neste fase mot overgangssummer.
