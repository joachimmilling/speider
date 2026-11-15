# Egne modeller som kompenserer for manglende data

Gratis data mangler tre ting profflubbene har: hendelsesdata (hver pasning med
koordinater), tracking og et rent register over overgangssummer. Ideen er å
bygge modeller som henter mest mulig ut av det vi faktisk har, og å måle hver
av dem mot en enkel referanse før den får lov til å bli med videre.

Regel: en modell er bare med hvis den slår referansen sin på data den ikke har
sett. Ellers bruker vi referansen.

## 1. Egen xG-modell

- **Hull:** Bare ca. 40 av FotMobs 65 dype ligaer har xG. Små ligaer mangler.
- **Vi har:** Skuddkart med koordinater, kroppsdel og situasjon for 127 ligaer
  (SofaScore).
- **Modell:** Gradient boosting / logistisk regresjon på avstand, vinkel,
  kroppsdel, situasjon (åpent spill, dødball, kontring, straffe).
- **Trening:** Ligaer som har leverandørens xG; kalibreres per liga.
- **Test:** Log-loss og kalibrering mot faktiske mål, sammenlignet med
  leverandørens xG der den finnes. Referanse: «alle skudd er like mye verdt».
- **Gir også:** Mål forhindret for keepere (skudd på mål med plassering).

## 2. Krymping for få minutter

- **Hull:** De mest interessante spillerne (unge, små ligaer) har få minutter.
  Rå tall per 90 er da mest støy.
- **Modell:** Empirisk Bayes. Hver statistikk trekkes mot snittet for rolle,
  liga og alder, og mindre jo flere minutter spilleren har.
- **Test:** Spådd neste sesong. Krympede tall skal treffe bedre enn rå tall.
  Piloten viste at stabiliteten varierer fra 0,83 (pasninger) til 0,14 (mål
  forhindret), så krympingen må læres per statistikk.

## 3. Ligastyrke per statistikk

- **Hull:** 10 taklinger per kamp på Kypros er ikke 10 taklinger i Nederland.
- **Modell:** Spillere som bytter liga gir oss vekslingskursen. For hver
  statistikk estimeres en omregningsfaktor per liga, med klubb-Elo som støtte
  der vi har få byttere.
- **Viktig:** Omregningen er forskjellig per statistikk. Dribler faller mer
  enn pasningsprosent når nivået øker.
- **Test:** Hold av siste sesongs byttere. Referanse: ingen omregning.

## 4. Lagpåvirkning (justert pluss/minus)

- **Hull:** Stoppere og defensive midtbanespillere syns dårlig i tellinger.
- **Vi har:** Lagoppstillinger, byttetidspunkt og skudd med tidspunkt.
- **Modell:** Kampene deles i perioder med samme 22 spillere. Ridge-regresjon
  på xG-forskjell per periode gir hver spiller et bidrag, med telletallene
  som forhåndsantakelse.
- **Ærlig begrensning:** Svært støyete for én sesong. Brukes som ett signal
  blant flere, aldri alene.
- **Test:** Spår lagets xG-forskjell i neste sesong ut fra hvem som spiller.

## 5. Rolle fra data

- **Hull:** «Midtbane» skjuler en ballvinner, en 8-er og en 10-er.
- **Modell:** Klynging på statistikkprofil og posisjon per kamp. Spillere
  sammenlignes bare med egen rolle.
- **Test:** Roller skal være stabile fra sesong til sesong for samme spiller.

## 6. Fylle inn manglende statistikk

- **Hull:** Noen ligaer har ca. 50 statistikker per kamp, andre ca. 70.
- **Modell:** Lær de manglende fra de som finnes, i ligaer som har alt.
- **Test:** Skjul kolonner i rike ligaer og mål treffet. Brukes bare der
  feilen er liten, og merkes som beregnet.

## 7. Fra telletall til ballverdi

- **Hull:** Uten hendelsesdata vet vi ikke hvor mye en pasning er verdt.
- **Vi har:** StatsBombs åpne hendelsesdata for et utvalg turneringer.
- **Modell:** Regn ut ekte ballverdi (xT/VAEP-type) der, og lær sammenhengen
  til de telletallene vi har overalt (progressive pasninger, nøkkelpasninger,
  dribler, ballvinninger).
- **Ærlig begrensning:** Åpne data dekker få ligaer og mest toppnivå.
  Overføring til Bosnia må testes indirekte.

## 8. Alderskurver per rolle

- **Modell:** Endring fra år til år for samme spiller, per rolle og per
  statistikk, justert for at de som slutter å spille faller ut av dataene.
- **Bruk:** Fremtidig kvalitet, og dermed fremtidig verdi.

## 9. Prismodell på faktiske summer

- **Hull:** Summer er ofte ukjente, og bare spillere noen ville ha blir solgt.
- **Modell:** Trenes på betalte overganger. Gir et spenn (kvantiler), ikke ett
  tall. Egen modell for sannsynligheten for å bli solgt, for å rette opp
  utvalgsskjevheten.
- **Aldri som inndata:** Markedsverdi fra Transfermarkt, SofaScore eller
  SciSports. De brukes bare som motstandere i testen.

## Rekkefølge

1. Krymping (2) og rolle (5): billig, alt annet bygger på dem.
2. Ligastyrke (3): avgjør om vi kan sammenligne på tvers i det hele tatt.
3. Egen xG (1): låser opp små ligaer.
4. Alderskurver (8) og prismodell (9).
5. Lagpåvirkning (4), innfylling (6), ballverdi (7): mest usikre, størst
   mulig gevinst for forsvarere.

## 10. Karrieresimulator (lappet sammen av korte vinduer)

- **Hull:** Detaljert statistikk dekker få hele karrierer.
- **Idé:** Vi trenger ikke hele karrierer. To–tre år med alle spillere gir
  overgangene 20→21, 21→22, … , 33→34. De lenkes sammen.
- **Modell:** Overgangsmodell. Tilstand = alder, rolle, kvalitetsnivå,
  liganivå, andel spilletid, retning siste år. Modellen gir fordelingen over
  neste års tilstand. Spilleren simuleres mange ganger år for år.
- **Frafall er et utfall:** «Ute av dataene» og «ned til lavere nivå» er egne
  tilstander. Ellers ser kurven for pen ut (bare de som overlever telles).
- **Ikke bare alder:** Betinger på nivå og retning, så stjerner ikke
  trekkes mot snittet for fort.
- **Verdi:** Simulert tilstand ved alder X → prismodellen, i dagens prisnivå.
- **Test:** Lenkede korte vinduer skal gjenskape ekte lange karrierer fra den
  enkle historikken (mål, minutter, liga). Historikken er fasit, ikke krav.

## 11. Detaljert profil for gamle sesonger (rekonstruksjon)

- **Hull:** Før 2014/15 finnes bare mål, assist, minutter og skudd.
- **Modell:** Lær i moderne data sammenhengen fra det enkle (uttelling,
  posisjon, lagets styrke og stil, alder) til det detaljerte. Bruk den
  bakover. Resultatet er en anslått profil med spenn, tydelig merket.
- **Støtte:** Lagstatistikk per kamp finnes ofte lenger tilbake og låser
  summen av spillernes tall.
- **Test:** Skjul detaljene for 2016–2018, rekonstruer, sammenlign.

## 12. Markedsverdi som svakt kvalitetssignal bakover

- For epoker uten statistikk kan verdiutvikling og hvem som kjøpte brukes
  som støyete mål på nivå. Bare for historisk profil, aldri i prismodellen.

## 13. Klausuler priset med simulatoren

- **Hull:** Summene vi har er overskriftstall. Bonuser, videresalgsandel,
  tilbakekjøp og lønn står ikke i dataene.
- **Idé:** En klausul er en opsjon på spillerens fremtid, og simulatoren gir
  nettopp fordelingen over fremtiden. Brukeren legger inn vilkårene for en
  avtale, Speider regner forventet verdi:
  - Videresalgsandel: andel × forventet (gevinst ved salg) × sjanse for salg.
  - Bonus ved kamper/mål/opprykk: sjanse for at terskelen nås × beløp.
  - Tilbakekjøp: verdi over avtalt pris, i de utfallene der det lønner seg.
- **Systematisk skjevhet i fasiten:** Unge spillere fra små klubber selges
  ofte med videresalgsandel. Da er overskriftssummen lavere enn reell pris,
  og modellen kan tro de er billigere enn de er. Følsomhetstest: anta
  typisk andel (f.eks. 10–20 %) for slike salg og se om «underpriset»-
  listen endrer seg.
- **Lønn:** Ikke i gratis data. Kjøpsdommen gjelder overgangssum, ikke
  totalkostnad, inntil vi har lønnsanslag.
