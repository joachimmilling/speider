# Results

Running log of what has been tested and what came out. Newest last.

## Data in (2026-11-15)

FotMob, fetched through a browser, stored in `data/` (not in the repository):

- 4.17M statistic rows, 81,149 players, 109 leagues with playing time.
- 22,190 transfers with a known fee, 2015–2026.
- Player profiles (birth date, contract, career history, market value over time): 19,242 of 48,341 loaded, players with a transfer first. 1.03M market value points back to 2014 and 470,000 season lines back to 2002.

Load: `python3 scripts/load_fotmob.py <export>` and `python3 scripts/load_profiles.py <profiles...>`

## Test 1: Shrinkage beats raw numbers

`python3 analysis/shrinkage.py`

Task: predict the player's numbers next season (same league, ≥ 900 min next year). Shrinkage strength learned on seasons up to 2024, tested on 2025–2026.

| Statistic (per 90) | Lower error than raw | For players under 900 min |
|---|---|---|
| Possession won, final third | 18 % | 36 % |
| Goals | 15 % | 35 % |
| Interceptions | 12 % | 24 % |
| Shots on target | 11 % | 26 % |
| Tackles | 11 % | 26 % |
| Successful dribbles | 9 % | 20 % |
| xG | 7 % | 19 % |
| xA | 5 % | 14 % |
| Passes | 4 % | 6 % |
| Clearances | 2 % | 13 % |

All 17 statistics tested improved. None got worse. 8,000–15,000 players in the test per statistic.

Shrinkage strength (minutes before own numbers count as much as the mean): passes 300, dribbles and xG 500, tackles 800, goals 1,800, possession won high 2,700.

**Conclusion:** shrinkage is in. All per-90 numbers in Speider are shrunk.

## Test 2: Price index, first version

`python3 analysis/price_index.py`

Year effect in a regression on log(fee), holding selling league, buying league and position fixed. 13,386 transfers.

| Year | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Index | 76 | 84 | 90 | 94 | 98 | 84 | 84 | 85 | 92 | 88 | 97 | 100 |

- Mean growth 2.5 % a year. The 2020 covid drop was 14 %, recovered in 2025–26.
- The raw median moves the other way (2.7 → 2.0m) because the source covers more small transfers now. Hence the index.

Projection (random walk with drift, 80 % interval): 2029 = 108 (91–127), 2031 = 113 (91–140), 2034 = 122 (93–160).

**Weaknesses:**
- The version that also holds performance fixed was unstable before 2020 (too few leagues with history) and is set aside for now.
- The projection is the simplest possible. Alternatives to test against it: link to club revenues and TV deals, separate index per price band.

## Test 2b: Price index with age

`PYTHONPATH=analysis python3 analysis/price_index_age.py`

12,667 of 13,386 transfers now have a birth date.

- Median age at transfer is stable: 24.1–25.0 in every year 2015–2026. The worry that buyers are getting younger did not hold.
- With age held fixed: growth 3.3 % a year (without age, same sample: 3.0 %).
- Index 2015 = 70, 2019 = 95, 2020 = 82, 2026 = 100.
- Projection: 2029 = 110 (92–133), 2034 = 129 (96–175).

**Conclusion:** age is in the index from now on. It changes little.

## Test 3: League strength helps when players change league

`python3 analysis/league_strength.py`

Task: predict the player's numbers in the new league, relative to the role mean there. Learned on moves up to 2025, tested on about 2,000 moves in 2026–27.

| Statistic | Against "same level as before" | Against damped level without league strength |
|---|---|---|
| Rating | 37 % lower error | 9 % |
| Passes | 21 % | 8 % |
| Shots | 19 % | 5 % |
| xA | 17 % | 4 % |
| Goals | 26 % | 2 % |
| Dribbles | 12 % | 2 % |
| xG | 21 % | 2 % |
| Tackles | 12 % | 1 % |
| Interceptions | 16 % | 0 % |

- Better on 14 of 15 statistics. Interceptions: no effect.
- Most of the gain comes from damping (a player far above the mean lands nearer the mean in a new league). League strength adds 1–9 % on top.
- League strength matters most for rating, passes and shots, least for defensive counts.

Ranking that falls out (attacking numbers): Premier League, Bundesliga, LaLiga, Ligue 1, Serie A, Brazilian Série A … at the bottom Iceland, Ireland, Danish second tier, India. Matches expectations without the model being told anything about level.

**Conclusion:** the stop rule is passed. Cross-league comparison is in.

**To fix:** cups sit in the data as leagues of their own (Copa del Rey came out on top) and must be removed. Team strength is not in yet: a player going from a bottom team to a top team is mixed up with the league effect. Club Elo to be tested as an addition.

## Test 4: Career simulator chained from short windows

`python3 analysis/career_simulator.py`

Idea (the owner's): whole careers are not needed. Learn one-year transitions for each age from a few years and chain them.

Setup: transitions learned only from 2022–2026 (58,232). Test: start in 2016, simulate ten years ahead, compare with actual value in 2026. 2,000 players aged 18–26 at the start.

| Model | Median error after 10 years | 80 % interval hit | Rank correlation |
|---|---|---|---|
| Value stays flat | 213 % | – | 0.23 |
| A: age only | 190 % | 88 % | 0.47 |
| B: age + level | 107 % | 81 % | 0.46 |
| C: age + level + direction last year | 111 % | 81 % | 0.46 |

Eight years (start 2018): B 139 %, coverage 77 %. Flat: 201 %.

- Chaining works. The interval is well calibrated: the 80 % interval hit 81 %.
- Level must be in (190 → 107 %). Direction last year added nothing.
- An error of a factor of two after ten years is the size of the uncertainty, not a fault in the model. That is why intervals are always shown.

Chained age curve (value relative to age 21):

| Age | 18 | 19 | 20 | 21 | 23 | 25 | 27 | 29 | 31 | 33 | 35 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Value | 0.21 | 0.44 | 0.70 | 1.00 | 1.42 | 1.58 | 1.33 | 0.99 | 0.61 | 0.36 | 0.22 |

Peak at 25. Back at the age-21 level at 29.

**Weaknesses:**
- Survivorship bias: profiles were fetched for players still playing after 2021. Those who disappeared earlier are missing, so the curve is too good. Dropout as a state is the next step.
- The test players' own latest years are in the training pool (small, but not clean).
- The state is supplier market value in current prices. The next version uses Speider's own quality and value, and the price index.
- Only 40 % of the profiles are in.

## Definition: good and bad buy

Two verdicts, both at the same price level:

1. **On signing day** (available for transfers happening now): fee paid against Speider's value that day, where the value includes expected development and resale during the contract (from the career simulator). Given as the probability that the purchase pays off, not just yes or no.
2. **In hindsight:** fee paid against actual value and playing time later.

Verdict 2 is used to test verdict 1: did "good buy on the day" hold up two years later?
