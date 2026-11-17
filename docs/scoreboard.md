# Scoreboard

Rebuilt 2026-11-17 at commit `bb3cea0` by `scripts/scoreboard.py`. History: `docs/scoreboard_history.csv`.

| Area | Measure | Now | Reference | Note |
|---|---|---|---|---|
| Pricing | Speider value: typical miss on fees not seen (2025-26) | **0.449** | third-party value 0.424 | n=3409, lower is better |
| Pricing | Speider value: rank correlation with fees | **0.852** | third-party value 0.838 |  |
| Pricing | Share of fees inside the 80 % range | **0.75** | target 0.80 |  |
| Pricing | Miss on fees for players worth 40m+ | **0.236** | trees alone 0.227 | n=81 |
| Pricing | Predicting the next fee: Speider outcome model (rank) | **0.548** | fee paid 0.593, third-party value 0.501 | higher is better |
| Pricing | Buys judged cheapest: resale / fee (median) | **1.41** | dearest fifth 0.89 | n=429 |
| Pricing | Same, largest third of fees | **1.05** | dearest fifth 0.52 | n=191 |
| Pricing | Speider above market value, top fifth: next fee vs typical | **3.06** | bottom fifth 0.48 | n=1649 |
| Squads | Squad model: correlation with goal difference, seasons not seen | **0.61** | last season only 0.409 | n=1026 |
| Squads | Squad model: explained share | **0.372** | value and level of the eleven 0.337 |  |
| Squads | Same with the seven attributes added | **0.372** | no gain = attributes add nothing |  |
| Squads | Level of the best eleven alone: correlation with goal difference | **0.451** | value of top eleven 0.544, last season 0.508 | n=829 |
| Pricing | Form nowcast: explained share of value change during a season | **0.267** | age and value 0.152 | n=24709 |
| Pricing | Miss on mid-season fees, site model | **0.491** | with form line 0.519, with nowcast 0.513 | n=413, form not adopted |

## Changed since the previous row

- `squad_corr`: 0.649 -> 0.61
- `squad_r2`: 0.42 -> 0.372
- `squad_attr_r2`: 0.419 -> 0.372
