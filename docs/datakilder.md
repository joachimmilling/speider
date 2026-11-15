# Datakilder

Speider deler kode, ikke data. Denne siden sier hva hver kilde gir, og hva du har lov til.

## I bruk

### Eliteserien Fantasy

- **Hva:** JSON-strømmen bak fantasy.eliteserien.no. Alle spillere i Eliteserien med klubb, posisjon, minutter, mål, målgivende, kort og redninger. Kamplogg per spiller og sesongtall tilbake i tid.
- **Mangler:** fødselsdato og nasjonalitet. Feltene finnes, men var tomme for spilleren vi sjekket i november 2026. Kjør `speider fetch` og tell selv før du stoler på det. Ingen pasninger, skudd eller xG.
- **Nyttig:** hver spiller har `opta_code` og `fiks_id` (NFFs spiller-id), som kan brukes til å koble mot andre kilder.
- **Vilkår:** strømmen er udokumentert og uoffisiell. Det finnes ingen avtale som gir rett til å bruke den. Speider henter rolig (én forespørsel av gangen, med pause) og lagrer bare lokalt.
- **Du kan:** utforske dataene privat.
- **Du kan ikke:** legge dataene ut, sjekke dem inn i et repo eller bygge en offentlig tjeneste på dem uten å avklare det med eieren.

Fantasy-prisen er et mål på popularitet i spillet. Den er ikke en markedsverdi.

## Planlagt

### StatsBomb Open Data

- **Hva:** hendelsesdata (hver pasning, hvert skudd) for utvalgte turneringer, blant annet VM, EM, La Liga og Premier League-sesonger. Ingen norske ligaer.
- **Til hva:** trene egne modeller for xG og verdi per aksjon.
- **Vilkår:** fri bruk til forskning og analyse, ikke kommersielt. Kilden skal oppgis som StatsBomb, med logoen deres.

### OpenFootball

- **Hva:** kamper og resultater for store ligaer og turneringer.
- **Vilkår:** public domain. Kan brukes fritt, også lagt ved i repoet.

## Det vi mangler en ryddig kilde til

- **Alder:** trengs for alderskurver og verdimodell.
- **Kontraktslengde og markedsverdi:** finnes hos Transfermarkt, som ikke tillater skraping.
- **Hendelsesdata for Eliteserien:** finnes hos betalte leverandører.

Regelen for nye kilder: koden kan ligge her, dataene kan ikke. Skriv alltid ned vilkårene på denne siden før kilden tas i bruk.
