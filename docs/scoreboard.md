# Scoreboard

Rebuilt 2026-11-19 at commit `9fdb20b` by `scripts/scoreboard.py`. History: `docs/scoreboard_history.csv`.

| Area | Measure | Now | Reference | Note |
|---|---|---|---|---|
| Pricing | Speider value: typical miss on fees not seen (2025-26) | **0.414** | third-party value 0.432 | n=3609, lower is better |
| Pricing | Speider value: rank correlation with fees | **0.854** | third-party value 0.836 |  |
| Pricing | Share of fees inside the 80 % range | **0.758** | target 0.80 |  |
| Pricing | Speider value: median prediction over fee (1 is unbiased) | **0.971** | third-party value 1.027 | 2025-26 |
| Pricing | Speider value: typical miss, six years each predicted from earlier years (2021-26) | **0.4478** | third-party value 0.4848, model before test 30 0.4737 | lower is better |
| Pricing | Same, when the buying club's tier is known | **0.4195** | without buyer 0.4478, exact buyer inputs 0.3993 | buyer and seller tier |
| Pricing | Speider value: median prediction over fee, six rolling years (1 is unbiased) | **0.991** | before test 33 0.974; miss 0.4466 | ten bags |
| Pricing | Same, buyer-tier model | **0.989** | before test 33 0.928; miss 0.4201 | ten bags |
| Pricing | Miss on fees for players worth 40m+ | **0.221** | trees alone 0.204 | n=81 |
| Pricing | Predicting the next fee: Speider outcome model (rank) | **0.542** | fee paid 0.592, third-party value 0.499 | higher is better |
| Pricing | Buys judged cheapest: resale / fee (median) | **1.41** | dearest fifth 0.89 | n=425 |
| Pricing | Same, largest third of fees | **1.08** | dearest fifth 0.5 | n=183 |
| Pricing | Speider above market value, top fifth: next fee vs typical | **3.08** | bottom fifth 0.46 | n=1657 |
| Squads | Squad model: correlation with goal difference, seasons not seen | **0.61** | last season only 0.409 | n=1026 |
| Squads | Squad model: explained share | **0.372** | value and level of the eleven 0.337 |  |
| Squads | Same with the seven attributes added | **0.372** | no gain = attributes add nothing |  |
| Squads | Level of the best eleven alone: correlation with goal difference | **0.451** | value of top eleven 0.544, last season 0.508 | n=829 |
| Pricing | Form nowcast: explained share of value change during a season | **0.267** | age and value 0.152 | n=24709 |
| Pricing | Miss on mid-season fees, site model | **0.491** | with form line 0.519, with nowcast 0.513 | n=413, form not adopted |
| Pricing | Form lift in the price: slope for form above expectation | **1.166** | 90 % interval 0.718 to 1.599; below expectation -0.385 (not used) | mid-season miss 0.487 -> 0.48, n=417; decision 49 |
| Pricing | Predicting next season's share out of the squad (rank) | **0.296** | minutes and age 0.235 | n=1890 |
| Squads | Match goal difference explained by both elevens' quality | **0.1895** | with attribute means 0.1975, with balance terms 0.1964 | n=2058 |

## Changed since the previous row

- `fee_miss`: 0.419 -> 0.414
- `fee_inside80`: 0.763 -> 0.758
- `fee_bias_rolling`: 0.986 -> 0.991
- `fee_bias_buyer`: 0.988 -> 0.989
- `fee_miss_40m`: 0.225 -> 0.221
- `next_fee_rank`: 0.546 -> 0.542
- `verdict_cheap`: 1.43 -> 1.41
- `verdict_cheap_large`: 1.07 -> 1.08
- `flag_top`: 3.01 -> 3.08
- `form_slope`: 1.183 -> 1.166
