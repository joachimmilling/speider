# Scoreboard

Rebuilt 2026-11-19 at commit `e71f181` by `scripts/scoreboard.py`. History: `docs/scoreboard_history.csv`.

| Area | Measure | Now | Reference | Note |
|---|---|---|---|---|
| Pricing | Speider value: typical miss on fees not seen (2025-26) | **0.416** | third-party value 0.432 | n=3595, lower is better |
| Pricing | Speider value: rank correlation with fees | **0.854** | third-party value 0.836 |  |
| Pricing | Share of fees inside the 80 % range | **0.751** | target 0.80 |  |
| Pricing | Speider value: median prediction over fee (1 is unbiased) | **0.91** | third-party value 1.027 | 2025-26 |
| Pricing | Speider value: typical miss, six years each predicted from earlier years (2021-26) | **0.4478** | third-party value 0.4848, model before test 30 0.4737 | lower is better |
| Pricing | Same, when the buying club's tier is known | **0.4195** | without buyer 0.4478, exact buyer inputs 0.3993 | buyer and seller tier |
| Pricing | Miss on fees for players worth 40m+ | **0.229** | trees alone 0.206 | n=81 |
| Pricing | Predicting the next fee: Speider outcome model (rank) | **0.546** | fee paid 0.592, third-party value 0.5 | higher is better |
| Pricing | Buys judged cheapest: resale / fee (median) | **1.43** | dearest fifth 0.89 | n=431 |
| Pricing | Same, largest third of fees | **1.07** | dearest fifth 0.56 | n=186 |
| Pricing | Speider above market value, top fifth: next fee vs typical | **3.01** | bottom fifth 0.45 | n=1656 |
| Squads | Squad model: correlation with goal difference, seasons not seen | **0.61** | last season only 0.409 | n=1026 |
| Squads | Squad model: explained share | **0.372** | value and level of the eleven 0.337 |  |
| Squads | Same with the seven attributes added | **0.372** | no gain = attributes add nothing |  |
| Squads | Level of the best eleven alone: correlation with goal difference | **0.451** | value of top eleven 0.544, last season 0.508 | n=829 |
| Pricing | Form nowcast: explained share of value change during a season | **0.267** | age and value 0.152 | n=24709 |
| Pricing | Miss on mid-season fees, site model | **0.491** | with form line 0.519, with nowcast 0.513 | n=413, form not adopted |
| Pricing | Form lift in the price: slope for form above expectation | **1.183** | 90 % interval 0.71 to 1.619; below expectation -0.373 (not used) | mid-season miss 0.487 -> 0.484, n=417; below the 0.5-point bar, kept by decision 49 |
| Pricing | Predicting next season's share out of the squad (rank) | **0.296** | minutes and age 0.235 | n=1890 |
| Squads | Match goal difference explained by both elevens' quality | **0.1895** | with attribute means 0.1975, with balance terms 0.1964 | n=2058 |

## Changed since the previous row

- `next_fee_rank`: 0.548 -> 0.546
- `verdict_cheap`: 1.41 -> 1.43
- `verdict_cheap_large`: 1.05 -> 1.07
- `flag_top`: 3.06 -> 3.01
- `form_slope`: 0.597 -> 1.183
