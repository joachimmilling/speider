# Datarevisjon, 15. november 2026

Hva kildene faktisk inneholder, sjekket mot de ekte dataene. Skrevet før verdimodellen bygges på nytt.

## Eliteserien Fantasy

| Hva | Funn |
|---|---|
| Spillere | 546, alle i Eliteserien. 449 har spilt i år. |
| Kamptall | Minutter, mål, målgivende, kort, redninger, baklengs, kamper uten baklengs. Per sesong og per kamp. |
| Tidligere sesonger | Sesongtall per spiller tilbake til 2017. |
| Fødselsdato, nasjonalitet, draktnummer | Tomme for alle 546. |
| Opta-indeks | Feltet finnes, men er 0 for alle i 2026, både per sesong og per kamp. I et utvalg på 20 spillere var det bare fylt ut for 2023-sesongen. |
| Skader og status | `status` og `news` for hver spiller: 39 skadet, 30 usikre, 4 utestengt, 100 utilgjengelige. Teksten sier hva og hvor lenge («Kne - Ute resten av sesongen»). Gjelder bare akkurat nå. |
| Solgte spillere | Står i `news` («Overgang til Celtic»). |
| Forsvarsspill og pasninger | Finnes ikke. |

Skadehistorikk kan ikke hentes bakover. Den må bygges ved å lagre et øyeblikksbilde jevnlig fra nå av.

## transfermarkt-datasets

| Hva | Funn |
|---|---|
| Oppdatert til | Verdier til mai 2026, kamper til 30. mai 2026. Oppdateringene står stille. |
| Spillerprofiler | Fødselsdato, posisjon, fot, høyde, kontraktsslutt, landskamper, agent. 424 spillere i Eliteserien-klubber. |
| Verdihistorikk | 4 354 verdier for 708 spillere i Eliteserien, fra 2008. Median fem per spiller. |
| Overganger | 175 165 totalt, 17 554 med oppgitt sum. 287 salg fra Eliteserien-klubber med sum, 982 fra Norge, Sverige og Danmark. |
| Kamper i Eliteserien | 329, fra 29. mars 2025. Ingen eldre. |
| Tropper og hendelser | Startoppstilling, benk, bytter, mål, målgivende og kort per kamp. Minutter regnet ut fra dette stemmer med fasiten i de 14 ligaene som har den. |
| Forsvarsspill og pasninger | Finnes ikke. |

Overgangssum mot Transfermarkt-verdi på salgstidspunktet: median 0,94. Halvparten av salgene ligger mellom 0,53 og 1,5 ganger verdien. Det er referansen en egen modell må slå.

## Hva dette betyr

Du kan:
- trene en verdimodell på faktiske overgangssummer i stedet for Transfermarkt-anslag
- teste den fremover i tid, siden både summer og verdier har datoer
- skille skade fra benk fremover, ved å lagre status hver dag
- se utvikling per spiller over flere sesonger

Du kan ikke:
- måle kvaliteten på en midtstopper, en defensiv midtbanespiller eller en kreativ åtter. Ingen av kildene har tall på forsvarsspill eller pasninger.
- bruke Opta-indeksen
- rekonstruere skader bakover i tid

Uten en kilde til forsvarsspill og pasninger kan Speider bare prise spillere ut fra mål, målgivende, alder, kontrakt og nivå. Det holder for angripere og offensive midtbanespillere, ikke for resten.
