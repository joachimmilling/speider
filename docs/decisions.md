# Decisions

Choices made, why, and what was rejected. Newest last. The test results behind
them are in `results.md`.

| # | Date | Decision | Why | Rejected |
|---|------|----------|-----|----------|
| 1 | 2026-11-15 | Scope is every league, not Eliteserien | Owner: an underpriced player in Bosnia is as interesting as one in Norway | Eliteserien focus (an early mistake) |
| 2 | 2026-11-15 | Free data, local private use. Data never in the repository | Not a business. Unofficial sources | Paid data until value is shown |
| 3 | 2026-11-15 | The evaluation protocol is written before the models | Avoid fitting the test to the result | – |
| 4 | 2026-11-15 | FotMob is the base source. SofaScore only where FotMob is missing | Same underlying data (xG sum 536.9 vs 536.0). FotMob shares one id across statistics, transfers and profiles | Using both as a cross-check |
| 5 | 2026-11-15 | Ground truth for price is FotMob's transfer list | Fee + player id, 22,190 transfers from 2015 | transfermarkt-datasets (needs name matching) |
| 6 | 2026-11-15 | Third-party market value is never an input to the price model | Leakage. Used as an opponent and as a career-path measure | – |
| 7 | 2026-11-15 | Ingestion runs in a browser, stored in browser storage, exported to `data/raw/` | Scripts cannot reach the sources from the work environment | Scripts (not yet tested on the owner's machine) |
| 8 | 2026-11-15 | All per-90 numbers are shrunk | Test 1: better on 17 of 17 statistics | Raw numbers |
| 9 | 2026-11-15 | Cross-league comparison is in | Test 3: better on 14 of 15 | – |
| 10 | 2026-11-15 | Price index v1 without performance controls | The version with performance was unstable before 2020 | Index with performance (to be revisited) |
| 11 | 2026-11-15 | Careers are simulated by chaining one-year transitions | Test 4: halves the error over ten years, interval is calibrated | Requiring whole careers in the data |
| 12 | 2026-11-15 | Simulator state is age + level | Direction last year added nothing | Direction as state |
| 13 | 2026-11-15 | Two data tiers: full profile and historical profile | Detail exists from 2014/16, simple numbers from 2002 | Modern data only |
| 14 | 2026-11-15 | Value is shown both in today's prices and with a projected price index | Owner: today's price level alone is not enough | Today's prices only |
| 15 | 2026-11-15 | A purchase gets two verdicts: on signing day and in hindsight | Must be able to judge transfers happening now | Hindsight only |
| 16 | 2026-11-15 | Clauses are priced as options with the simulator | That is how real deals work | Ignoring clauses |
| 17 | 2026-11-15 | Age is in the price index | Test 2b: growth moves from 3.0 to 3.3 % a year | Index without age |
| 18 | 2026-11-15 | Everything in the repository is in English | Owner's requirement | Norwegian docs |

| 19 | 2026-11-15 | The UI ships in Norwegian and English | Owner's requirement. All UI strings go through one translation table; numbers and currency follow the locale | Single-language UI |

| 20 | 2026-11-15 | Price model v1 is not shipped as "Speider says" yet | Test 5: median error 76 % vs 59 % for market value; gate 4 not passed | Showing v1 estimates as final |
| 21 | 2026-11-15 | Cups are excluded from league data | They appeared as leagues and distorted the ranking | – |

| 22 | 2026-11-15 | Finer roles and league strength as inputs do not fix the price model; next step is league-translated absolute quality and the simulator's expected value as inputs | Test 6: v2 equals v1 (76 %); statistics add 3 points | More feature engineering on season z-scores |
| 23 | 2026-11-15 | Cross-era comparison is not shown until full historical squads are loaded | Historical profile v0 normalises against survivors only | Showing v0 numbers |

| 24 | 2026-11-15 | Career path features are in the price model | Test 7: 76 → 72 %, under 23: 82 → 72 % | – |

| 25 | 2026-11-15 | Price intervals are conformal-calibrated | Test 7b: coverage 67 → 76 % against a target of 80 % | Raw quantile intervals |

| 26 | 2026-11-15 | Dropout is a required part of every career projection | Test 8: a regular at 21 is still in the data at 29 with 43 % probability | Survivor-only age curves |
| 27 | 2026-11-15 | Stop engineering season-aggregate statistics for the price model | Tests 6 and 9: no gain. Next: match-level form up to the transfer date, contract length, loan status | More season-level features |
| 28 | 2026-11-15 | Sell-on clauses are handled as a user-entered clause, not as a correction of the training fees | Test 10: assumed 10–20 % clauses leave the ranking almost unchanged (0.985) | Adjusting historical fees |

| 29 | 2026-11-15 | Projections show both "if still playing" and expected value including dropout | Test 11: for a 21-year-old regular the two differ by 35 % up vs 7 % down at 25 | Survivor curve alone |

| 30 | 2026-11-16 | Historical output is standardised against full SofaScore squads | Test 12: valid from 2001/02 in six leagues; replaces the survivor-based v0 and lifts decision 23 for goals | FotMob career lines as comparison group |
| 31 | 2026-11-16 | Crawls run in a Web Worker and SofaScore is paced to about one request a second | Background tabs were throttled and discarded; an unpaced run got the API blocked (403) | Main-thread crawls, unpaced requests |

| 32 | 2026-11-16 | Career projections are conditioned on the player's profile; the fixed age curve is only a fallback | Test 13: for players of 21 or younger the profile explains 18 % of three-year growth against 5 % for age and level; same-value players split 1.4x vs 6.1x | One age curve for everyone |

| 33 | 2026-11-16 | Projections are direct per-horizon models on the profile (1–5 years), with a separate still-playing probability | Test 14: 48 % of three-year value change explained against 35 % for age and level; 21 % against 8 % for young players | Chaining one fixed transition table |
| 34 | 2026-11-16 | Profile-shape inputs are dropped | Test 14: no gain at any horizon | Best-skill and standout-count features |

| 35 | 2026-11-16 | Projections are calibrated per age band on a held-out year (median shift and conformal interval) | Test 15: bias for 17–19 from −31 % to 0, coverage 76 → 82 % | Uncalibrated quantile models |
| 36 | 2026-11-16 | Momentum and career-path inputs are not added to the projection | Test 15: no effect | – |

| 37 | 2026-11-16 | Young-player projections use the wide sample (all valued players aged 16–23), career lines and the track record of club, league and nationality | Test 16: explained three-year growth for 17–19 from −13 % to 24 %; top tenth grew 11x, bottom tenth 1x | Regulars-only sample with season statistics |

| 38 | 2026-11-16 | Logo is a pair of angular sunglasses, black, with one thin green reflection per lens | Owner: the two rings with dots looked like Tripadvisor; chose this after several rounds | Binocular rings, rounded sunglasses, green lenses |

| 39 | 2026-11-16 | The club/league/nation track record is removed from the projection | Test 17: large effect on third-party value growth, one point or less on big-five moves, league step and fees; negative relation with fee/value | Keeping it for its effect on the value metric |
| 40 | 2026-11-16 | Third-party market value is no longer the projection target; projections will target outcomes (fee-equivalent value, league level, minutes) | Test 18: the provider's values move x1.42 and x0.83 market-wide in consecutive years; tests 13–18 predict the provider, not the player | Continuing to tune projections of third-party value |

## 41. First product is a static local site

The first runnable version is a static site built by `scripts/build_site.py` into `data/site/` and opened from disk. No server, no account, nothing leaves the machine. It shows only what has passed its test: top-league chance (step model), shrunk per-90 numbers, era comparison, price index and league strength. Speider's own player value stays hidden until the price model beats third-party value. Players already in a top-five league get no top-league chance.

## 42. Show the Speider value and value path, with the test result next to them

Replaces the display part of decision 20. An empty player page is worse than an uncertain estimate. The page shows the fee-trained Speider value with its interval, the third-party value beside it, and the value path with an 80 % band, and states the out-of-time result (Speider 50 % typical miss, third party 44 %). Speider does not yet beat the third-party value; that stays the target.

## 43. Survivorship is modelled, not hidden

Value histories exist almost only for players active today, so anything trained on them describes survivors. Dropout is therefore estimated from career lines, which cover players who have stopped, and every value path shown is a mixture of "stopped, worth nothing" and the survivor path. Nothing is removed from the page because of this bias; it is corrected for. (An earlier version of this decision blamed the profile table and hid the affected numbers; both were wrong.)

## Open questions

- Dropout is measured (test 8) but not yet a state inside the simulator.
- Team strength separated from league strength (club Elo).
- How much sell-on clauses shift the ground truth for young players from small leagues.
- Wages: no free source found.
- Whether scripts can reach the sources directly from the owner's machine (`scripts/check_access.py`).
