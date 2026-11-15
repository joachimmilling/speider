# Utforsking av datakilder, 15. november 2026

Hva som faktisk finnes, sjekket mot de ekte tjenestene fra en nettleser. Der noe bare er sjekket for én spiller eller én kamp, står det.

## Oppsummert

| Kilde | Ligaer med dype spillertall | Nivå | Historikk | Ekstra |
|---|---|---|---|---|
| SofaScore | 127 ligaer i 87 land | Per spiller per kamp, 45 til 78 tall | Norge fra 2018, Bosnia og Kypros fra 2023/24 | Fødselsdato, kontrakt, markedsverdi, overgangssummer |
| FotMob | 65 ligaer i 49 land | Per sesong, og per spiller per kamp | Eliteserien fra 2017 | Skudd med xG, utilgjengelige spillere per kamp, verdihistorikk fra SciSports |
| transfermarkt-datasets | 31 toppligaer | Kamper, tropper, hendelser | Varierer | 17 554 overganger med sum |
| Eliteserien Fantasy | Én liga | Sesong og kamp, bare grunntall | Fra 2017 | Skadestatus nå |
| NFF | Stengt | | | |

## SofaScore

- 7 649 fotballturneringer i 275 kategorier. Jeg sjekket de to første ligaene i hver kategori, 485 til sammen, ved å se på siste ferdigspilte kamp.
- 127 ligaer har taklinger per spiller per kamp. 114 av dem har xG eller xA, 107 har SofaScores egne verdier for pasninger, driblinger og forsvar, og 64 har ballføringer.
- To nivåer: rundt 70 tall per spiller i de største ligaene, rundt 50 i de mindre.
- **Bosnia (WWIN Liga BiH) og Kypros er dekket**, med rundt 50 tall per spiller og xG. Det samme gjelder blant andre Bulgaria, Slovenia, Ungarn, Marokko, Armenia, Aserbajdsjan, Malta, Færøyene, Estland, Kasakhstan, Wales og Nord-Irland.
- Tallene per kamp i de mindre ligaene: pasninger (egen og motstanders halvdel, lange, innlegg), dueller, luftdueller, taklinger, klareringer, blokkeringer, gjenvinninger, driblinger, berøringer, balltap, skudd, xG, xA, karakter.
- Skuddkart per kamp med posisjon, kroppsdel, situasjon og xG.
- Spillerprofil: fødselsdato, kontraktsslutt, markedsverdi, høyde, fot, detaljert posisjon. Sjekket for én spiller.
- Overgangshistorikk per spiller med sum der den er kjent. Sjekket for én spiller, der begge summene var ukjente eller null.
- Historikk for kamptall: Eliteserien 2018 til 2026. Bosnia og Kypros bare fra 2023/24.

Usikkerhet: en liga som viste null, kan ha tall i andre kamper. Ukraina og toppligaen i Georgia viste null og bør sjekkes på nytt.

## FotMob

- Sesonglister: se [pilot.md](pilot.md). 65 ligaer har pasnings- og forsvarstall, 40 har xG.
- Kampdata, sjekket for én kamp i Eliteserien: tall for alle 40 spillerne i troppen. Berøringer, berøringer i motstanders felt, pasninger inn i siste tredel, innlegg, driblinger, taklinger, blokkeringer, klareringer, brudd, gjenvinninger, driblet forbi, bakkedueller, luftdueller, xA.
- Skudd per kamp med posisjon, xG, xG på mål, situasjon og keeper.
- Oppstillinger med en liste over **utilgjengelige spillere per kamp**, med type (skade eller utestengelse) og ventet retur. Det gir skadehistorikk bakover i tid.
- Spillerprofil: fødselsdato, kontraktsslutt, kamplogg med minutter og om spilleren satt på benken, karrierehistorikk med lån.
- **Verdihistorikk fra SciSports**: månedlige verdier med øvre og nedre grense. For spilleren jeg sjekket: 48 verdier fra november 2022. SciSports er en profesjonell leverandør, så dette er en bedre referanse enn Transfermarkt.
- Bosnia og Kypros har ikke spillertall per kamp hos FotMob.

## NFF og andre forbund

- NFF gir som hovedregel ikke eksterne tilgang til API-et sitt (EPS) eller underliggende fotballdata. Tilgang gis bare til utvalgte samarbeidspartnere med avtale. Klubber henvises til Fotballdata.no og medier til NTB.
- NFF eier dataene i FIKS, og gjenbruk er bare tillatt etter avtale.
- fotball.no avviser automatisk lesing av spillersidene.
- Dataene er uansett grunntall: kamper, tropper, mål og kort.

Konsekvens: NFF er ikke en kilde for Speider. Forbundsdata generelt gir ikke mer enn det FotMob og SofaScore allerede har.

## Lagstyrke

ClubElo gir styrketall for europeiske klubber med historikk, gratis som CSV. Jeg fikk ikke lest tjenesten herfra, så dekningen er ikke bekreftet. Python-biblioteket soccerdata har en ferdig henter.

## Hva dette betyr

Du kan:
- vurdere spillere i alle posisjoner i 127 ligaer, også Bosnia og Kypros
- regne per 90 minutter for alle spillere, også reserver, fordi tallene finnes per kamp
- bygge skadehistorikk fra FotMobs lister over utilgjengelige spillere
- måle egne verdianslag mot en profesjonell modell (SciSports) i tillegg til Transfermarkt
- hente alder, kontrakt og overgangssummer for alle ligaene, ikke bare de 31 i verdidatasettet

Du kan ikke:
- få hendelsesdata, altså hver pasning med posisjon. Tallene er summert per spiller per kamp. Egne modeller for pasningsverdi kan derfor ikke bygges, men egne xG-modeller kan, fordi skuddene har posisjon.
- gå lenger tilbake enn 2023/24 i de minste ligaene. Det gir kort historikk for testing der.
- bruke NFF

Kostnaden: kampdata betyr mange forespørsler. Én liga har rundt 250 kamper i sesongen. 127 ligaer over fire sesonger er over 100 000 kamper. Det må hentes rolig over flere dager fra en egen maskin, og begge kildene er uoffisielle og kan stenge tilgangen.
