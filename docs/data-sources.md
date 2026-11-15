# Data sources

Speider shares code, not data. This page says what each source gives and what you are allowed to do.

## In use

### FotMob

- **What:** season statistic lists per player for every league with deep statistics (passing, dribbling, tackles, interceptions, recoveries, clearances, xG and xA where available), a transfer list with fees from 2015, and player profiles with birth date, contract end, career history and market value history. See [pre-study.md](pre-study.md) and [results.md](results.md).
- **Missing:** per-90 lists only include players above a minutes threshold.
- **Terms:** unofficial source, no agreement. Speider fetches slowly and stores locally only.
- **You can:** use the data privately on your own machine.
- **You cannot:** publish the data, commit it, or show it on a public site.

### Eliteserien Fantasy

- **What:** the JSON feed behind fantasy.eliteserien.no. All Eliteserien players with club, position, minutes, goals, assists, cards and saves. Match log per player and season totals back in time.
- **Missing:** birth date and nationality (the fields exist but were empty in November 2026). No passes, shots or xG.
- **Useful:** each player has `opta_code` and `fiks_id` (the Norwegian FA's player id), usable for joining sources.
- **Terms:** the feed is undocumented and unofficial. Speider fetches slowly (one request at a time, with pauses) and stores locally only.
- **You can:** explore the data privately.
- **You cannot:** publish the data, commit it, or build a public service on it without clearing it with the owner.

The fantasy price measures popularity in the game. It is not a market value.

### SofaScore

- **What:** per-player per-match statistics in 127 leagues, including leagues FotMob lacks (Bosnia, Cyprus and others) from 2023/24. Shot maps with coordinates. See [source-exploration.md](source-exploration.md).
- **Terms:** unofficial source, no agreement. Same rules as FotMob.

## Planned

### StatsBomb Open Data

- **What:** event data (every pass, every shot) for selected competitions. No Norwegian leagues.
- **For:** training own models for xG and value per action.
- **Terms:** free for research and analysis, not commercial. Credit StatsBomb, with their logo.

### OpenFootball

- **What:** fixtures and results for major leagues and tournaments.
- **Terms:** public domain.

## What we lack a clean source for

- **Wages.**
- **Contract clauses** (sell-on, bonuses, buy-back).
- **Event data** outside the open StatsBomb competitions.

Rule for new sources: the code may live here, the data may not. Always write the terms on this page before a source is taken into use.
