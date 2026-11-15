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

## Test 5: Price model v1 on actual fees

`python3 analysis/price_model.py`

Target: log(fee / price index). Train on 5,788 transfers up to 2024, test on
3,057 transfers in 2025–2026 (2,993 with a market value to compare against).
Gradient boosting. Third-party market value is not an input.

| Model | Median error | Within 2x | Rank correlation |
|---|---|---|---|
| B: age + league + role | 126 % | 44 % | 0.59 |
| Speider v1, statistics only | 93 % | 52 % | 0.73 |
| Speider v1 (+ team strength, earlier fees, career so far) | 76 % | 59 % | 0.79 |
| A: market value on the day (opponent) | 59 % | 67 % | 0.86 |
| 50/50 blend of Speider v1 and A (reference only) | 56 % | 70 % | 0.87 |

Per group, Speider v1 vs market value (median error): under 23: 82 % vs 63 %;
fee under 1m: 116 % vs 90 %; fee over 10m: 74 % vs 36 %.

- **Gate 4 is not passed.** Speider v1 clearly beats the simple reference but
  is behind the market value.
- **Speider carries information the market value lacks.** The blend beats the
  market value alone (56 vs 59 %; under 23: 61 vs 63 %, rank 0.88 vs 0.85).
- What the model leans on (error added when the input is shuffled): league
  108, age 61, team strength 16, earlier fees 14, rating 10, career so far 8,
  attacking statistics 5, playing time 4, role 3, passing/defending 1.
- The 80 % interval only covered 67 %. It must be calibrated.

**Reading the misses:** the largest errors are players whose previous season
does not describe them: reserve-team or youth-league minutes at a big club,
long-term injuries, and transfers with unusual terms. Detailed statistics
add little beyond rating in this version, which points at the quality layer
being too crude (one z-score per statistic, no role-specific weighting).

**Next for the price model:**
- Role-specific quality score instead of raw z-scores.
- League strength from test 3 as a number, so small leagues share strength.
- Parent club and loan status; several seasons of history, not one.
- Contract length at the selling club (not in the transfer feed).
- Calibrated intervals (conformal).
- Selection: only sold players have a fee.

## Test 3, rerun without cups

Cups are now excluded. Results unchanged (rating 9.4 %, passes 8.1 % better
than the damped reference). Top of the ranking: Premier League, Bundesliga,
LaLiga, Ligue 1, Serie A, Brazilian Série A.

## Test 6: Price model v2, finer quality layer

`python3 analysis/price_model_v2.py`

Changes from v1: eight roles instead of four, league strength as a number,
two seasons of history, and two extra variants to test the quality gate.

| Model | Median error | Rank correlation |
|---|---|---|
| B: age + league + role | 126 % | 0.59 |
| Goals + assists only | 105 % | 0.68 |
| v2 without any statistics | 79 % | 0.79 |
| Speider v2 | 76 % | 0.79 |
| A: market value (opponent) | 59 % | 0.86 |
| 50/50 blend (reference only) | 56 % | 0.87 |

Groups (Speider v2 vs market value): defenders and defensive midfielders 80 %
vs 57 %; small leagues 88 % vs 63 %; under 23: 82 % vs 63 %, and the blend at
58 % beats the market value there.

- **No improvement over v1.** Finer roles, league strength and a second
  season did not move the result.
- **Detailed statistics add almost nothing to fee prediction as used here**
  (79 → 76 %). Age, league, team strength, earlier fees and career so far
  carry the model.
- The quality gate ("explains fees better than goals and assists alone") is
  passed on paper (105 → 76 %), but not because of the statistics.
- Gate 4 is still not passed.

**Hypotheses to test next, in order:**
1. Season z-scores throw away level. Use league-translated absolute
   quality (test 3 per statistic), not rank within own league.
2. Fees price expected future value. Feed the career simulator's expected
   value at the player's age and level into the price model.
3. The previous season is the wrong window. Use form up to the transfer
   date from match-level data.
4. Missing inputs dominate: contract length at the selling club, parent club
   and loan status, national team minutes, injuries.

## Historical profile v0

`python3 analysis/historical_profile.py`

Career lines (matches, goals, assists per league and season) standardised
within league, season and position group, shrunk for few matches.

- Works on real data: Cristiano Ronaldo 2007/08 (34 matches, 31 goals) and
  Antonio Nusa 2025/26 (31 matches, 4 goals, 3 assists) are both in.
- Best seasons at age 22 or younger in the top five leagues come out as
  Haaland 2022/23, Mbappé 2018/19 and 2020/21, Haaland at Dortmund, Palmer
  2023/24, Bellingham 2023/24.

**Not yet valid across eras, two reasons:**
- Assists are missing before about 2009 in the source (Ronaldo 2007/08 shows
  0). Old seasons must be compared on goals only, or assists reconstructed.
- The comparison group is only players whose profile is loaded, that is
  players still active after 2021. For 2008 that is a few hundred survivors,
  who are better than the league average of the time, so old seasons are
  understated. Full historical squads are needed (SofaScore season lists for
  old seasons).

## Test 7: Price model v3, career path

`python3 analysis/price_model_v3.py`

Added what was known on the day about the player's path: matches in top five
leagues, European matches, youth and reserve matches, strongest league played
in, debut age, matches/goals/rating/level over the last three seasons, number
of clubs. All from career lines up to the transfer.

| Model | Median error | Within 2x | Rank correlation |
|---|---|---|---|
| Speider v2 | 76 % | 59 % | 0.79 |
| Speider v3 | 72 % | 61 % | 0.81 |
| A: market value (opponent) | 59 % | 67 % | 0.86 |
| 50/50 blend (reference only) | 54 % | 71 % | 0.88 |

Groups, v3 vs market value: under 23: 72 % vs 63 %; defenders and defensive
midfielders 72 % vs 57 %; small leagues 84 % vs 63 %; fee over 10m 62 % vs 36 %.

- Career path helps everywhere, most for players under 23 (82 → 72 %).
- The blend improves again (54 %), so the gap to the market value is closing
  while Speider's independent information grows.
- Gate 4 is still not passed. The interval still covers 67 % instead of 80 %.

## Test 7b: Calibrated interval for the price model

Same script. Conformalised quantile regression: quantile models fitted on
transfers up to 2023, widened using the misses on 2024, tested on 2025–2026.

- Coverage of the 80 % interval: 67 % → 76 %.
- The interval is wide: the upper bound is 8.8 times the lower bound (median).
- Per group: under 23: 76 %, defenders and defensive midfielders 78 %, small
  leagues 74 %. Transfers that turned out very cheap (under 1m: 63 %) or very
  expensive (over 10m: 66 %) fall outside more often, as expected when
  grouping by the outcome.

With career path in, the model leans on age (52), league (49) and career
path (47); team strength 9, earlier fees 8, rating 6. Detailed statistics
still add nothing measurable.

**Conclusion:** the calibrated interval replaces the raw one. A range of
almost nine times is the honest uncertainty of v3 and too wide to be useful
on its own; narrowing it is the purpose of the next model steps.

## Data: more profiles and SofaScore season statistics (2026-11-15, late)

- Player profiles: 25,505 of 48,341 loaded. 1.35M market value points,
  621,000 career lines.
- SofaScore season statistics (`scripts/load_sofascore.py`): 191,188
  player-seasons, 58,313 players, 64 leagues with detailed statistics so far
  (the discovery crawl is not finished), five latest seasons each.
- A history crawl for 21 large leagues (basic statistics for every squad
  member, all seasons) is running; three leagues are in.

## Test 8: Dropout

`python3 analysis/dropout.py`

Cohort without look-ahead: 54,191 regular player-seasons (≥ 900 min) in
2022–2025, in leagues that are covered the following year.

- Next year: 65 % still regulars, 16 % fringe (270–899 min), 18 % out
  (under 270 min or absent).
- Out two years running: 12 %. Of those out for one year, 20 % are regulars
  again the year after.
- By age (scaled to the overall rate): out-rate is 13–14 % a year from 20 to
  26, 18 % at 28, 25 % at 31, 35 % at 34.
- Chained: a regular at 21 is still in the data at 25 with 68 % probability
  and at 29 with 43 %. From 25: 64 % at 29, 31 % at 33.

**Reading:** "out" mixes retirement, long injury and moves to leagues we do
not cover, so it overstates leaving the game. SofaScore's wider coverage
will shrink the last part. Even so, dropout is large enough that every
career projection must carry it; the test 4 age curve describes survivors.

**Weakness:** only 86 % of the cohort has an age yet, and the missing ones
drop out more often (18.1 % overall vs 14.1 % with age). The age table is
scaled to compensate. Rerun when all profiles are in.

## Test 9: Price model v4, league-translated absolute quality

`python3 analysis/price_model_v4.py`

Each statistic is now also given as an absolute level: rank within own
league and role plus that league's offset for the statistic from test 3.

| Model | Median error | Rank correlation |
|---|---|---|
| Speider v3 | 72 % | 0.81 |
| Speider v4 | 71 % | 0.82 |
| A: market value (opponent) | 59 % | 0.86 |

- Hypothesis 1 (season z-scores throw away level) explains very little.
  Absolute quality takes over the role of the raw statistics in the model
  but adds no accuracy.
- Small leagues 83 % and defenders 73 % are unchanged.

**Conclusion so far on the price model:** four versions, 93 → 76 → 72 → 71 %.
What moved it was context (team strength, earlier fees, career path), not a
finer description of last season's play. Season-aggregate statistics from
this source are close to exhausted for predicting fees.

## Test 10: Sensitivity to hidden sell-on clauses

`SELLON=0.1 python3 analysis/price_model_v4.py`, then `python3 analysis/sellon_sensitivity.py`

Assumption, not data: players under 23 sold from weaker leagues (11 % of the
test transfers) carry a sell-on clause worth 10 or 20 % of the headline fee.

- Rank correlation between the adjusted and unadjusted "paid below
  estimate" ranking: 0.986 (10 %) and 0.985 (20 %).
- Top-100 overlap 86 of 100 in both cases; top-300 overlap 276 and 266.
- The segment's share of the top 300 moves from 14 % to 13 % and 12 %.

**Conclusion:** sell-on clauses of this size do not change which transfers
look cheap. Some of the difference is refit noise, not the assumption.
