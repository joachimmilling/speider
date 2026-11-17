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

## Test 11: Career curve with dropout built in

`python3 analysis/career_curve_with_dropout.py`

Expected value at an age = value if still playing × probability of still
playing. Chained age curve on 92,269 one-year transitions (2021–2026), dropout
from test 8 (one-year rate scaled by 0.66, the share still out a year later).

Regular at 21, value set to 1.00:

| Age | 21 | 23 | 25 | 27 | 29 | 31 | 33 |
|---|---|---|---|---|---|---|---|
| Value if still playing | 1.00 | 1.25 | 1.35 | 1.14 | 0.84 | 0.55 | 0.35 |
| Still playing | 100 % | 83 % | 69 % | 57 % | 44 % | 33 % | 22 % |
| Expected value | 1.00 | 1.04 | 0.93 | 0.64 | 0.38 | 0.18 | 0.08 |

From 19: value if playing peaks at 2.31 (age 25), expected value peaks at
1.46 (age 23). From 24: expected value falls from the start.

- Survivors peak at 24–25. With dropout included the expected value of a
  21-year-old regular peaks at 22–23 and is back below today's value by 25.
- This is the number that matters for a buyer: the survivor curve says
  "worth 35 % more at 25", the expected curve says "worth 7 % less".

**Weaknesses:** "out" includes moves to leagues we do not cover, so dropout is
overstated and the expected curve is too low. Level is not conditioned on
here (test 4 showed it matters); this is the average regular. Both are fixed
by moving dropout into the simulator as a state, with SofaScore's wider
league coverage.

## Data complete for stage 1 (2026-11-16)

- FotMob player profiles: all 48,339 loaded. 2.17M market value points,
  979,000 career lines.
- SofaScore season statistics: 352,957 player-seasons, 85,233 players, 95
  leagues with detailed statistics (five latest seasons each). Bosnia (WWIN
  Liga) and Cyprus are in, 2023/24 onwards; their season lists carry no xG.
- SofaScore history: full squads with minutes, goals, penalties, assists and
  shots for the big five and Eredivisie back to 2001/02, and 15 more leagues
  back to 2013/14.
- **Access note:** the SofaScore crawl was run without pauses near the end and
  the API started answering 403. The crawl was stopped. 28 of 275 country
  categories were not scanned. Future SofaScore runs must be paced (at most
  about one request a second) and resumed later.
- **Operational note:** Chrome throttles and discards background tabs. Crawls
  now run inside a Web Worker on a plain page of the same origin, which holds
  full speed while the tab is alive; the tab still has to be polled.

## Reruns on the full profile set

- **Test 8, dropout:** unchanged overall (65 % regular, 16 % fringe, 18 % out
  next year); every cohort player now has an age, so no scaling. Out-rate
  14–15 % a year from 21 to 26, 20 % at 29, 30 % at 34. A regular at 21 is
  still in the data at 25 with 66 % and at 29 with 41 %.
- **Test 4, career simulator** (122,711 training transitions, no longer
  survivor-heavy): ten-year median error 85 % for age + level against 128 %
  for a flat value; 80 % interval covers 81 %. Direction last year still adds
  nothing (84 %). The chained age curve is flatter than first measured: peak
  1.37 at 24–25 (was 1.58), 0.92 at 29, 0.66 at 31.
- **Test 11, with dropout:** for a regular at 21 the value if still playing is
  1.13 at 23 and 1.23 at 25, the share still playing 82 % and 67 %, so the
  expected value is 0.93 at 23 and 0.82 at 25. Expected value of the average
  21-year-old regular falls from day one; from 19 it peaks at 21 (1.22).
- **Test 9, price model v4:** 69 % median error (was 71 %), blend 53 %,
  market value 59 %. Under 23: 73 % vs 63 %. Small leagues 83 % vs 63 %.

## Test 12: Historical profile v1, against full squads

`python3 analysis/historical_profile_v1.py`

Non-penalty goals per 90, standardised among all outfield regulars (≥ 900
min) of the same league and season. 1,600–1,800 regulars a season in six
leagues for 2002–2012, 4,600–6,400 in about 21 leagues for 2014–2021.

- Cristiano Ronaldo 2007/08: 2,747 min, 31 goals (4 penalties), 0.88 per 90,
  5.2 standard deviations above the Premier League mean, top of the league.
  2006/07: 0.42 per 90, 97th percentile.
- Antonio Nusa 2025/26: 2,035 min, 4 goals, 0.18 per 90, 69th percentile in
  the Bundesliga.
- Best seasons since 2001/02 come out as Messi 2012/13, Ibrahimović 2015/16,
  Mbappé 2018/19, Messi 2018/19, Lewandowski 2020/21, Ronaldo 2014/15.
- League scoring per regular is stable (0.11 per 90 in 2002–2014, 0.127 in
  2026), so era adjustment is small for goals; standardising within the
  season handles it.

**Conclusion:** cross-era comparison on output is valid from 2001/02 for six
leagues. Decision 23 is lifted for goals.

**Limits:** no positions in this source, so wingers are compared with all
outfield players; ages come from FotMob profiles and only exist for players
still active after 2021; assists are missing for parts of 2006 and 2013;
everything other than goals, assists, minutes and shots still needs
reconstruction (model 11).

## Test 13: Growth conditioned on the player, not a fixed age curve

`python3 analysis/growth_model.py`

Objection (the owner's): two 18-year-olds with the same value can have very
different expected paths; growth must depend on role, characteristics and
standout skills, not on age alone.

Setup: for each player-season, predict (a) the change in value three years
ahead if still playing and (b) whether he is still playing, from age and
level alone versus age, level and the player's profile (role, 14 shrunk
role-relative statistics, league strength, team quality, minutes, height,
career matches). Train on seasons ending 2018–2021 (29,244), test on
2022–2023 (26,229).

(a) Value change three years ahead:

| Group | Explained by age + level | With the player's profile | Rank correlation |
|---|---|---|---|
| All | 30 % | 43 % | 0.58 → 0.66 |
| 21 or younger | 5 % | 18 % | 0.31 → 0.48 |
| 22–25 | 13 % | 27 % | 0.36 → 0.52 |
| 26 or older | 19 % | 36 % | 0.54 → 0.63 |

(b) Still playing after three years, AUC: 0.678 → 0.728 (21 or younger:
0.652 → 0.695).

Same age, same value, different futures: 116 players aged 20 or younger and
valued 0.8–1.5m in the test seasons, split by predicted growth.

| Quarter | Predicted growth | Actual growth (median) |
|---|---|---|
| Lowest | 1.0x | 1.4x |
| Second | 1.4x | 1.6x |
| Third | 2.0x | 2.6x |
| Highest | 3.0x | 6.1x |

What moves predicted growth for players of 21 or younger (strong vs weak on
one input): league strength +60 %, shots +26 %, team quality +22 %, rating
+19 %, minutes +14 %, height +13 %, passes +11 %, high ball wins +7 %,
dribbles +6 %. Tackles and interceptions: none. By role the top inputs are
rating, passes and shots for wingers; shots, rating, passes and xG for
strikers.

- **The objection holds.** For young players age and level explain 5 % of
  the growth; the profile more than triples that, and it separates players
  the market values the same today.
- A fixed age curve is only a fallback for players without data.

**Weaknesses:** the target is third-party market value; growth is measured
only for players still valued, with dropout modelled separately; "standout
skills" are not yet explicit inputs (the model sees each statistic, not the
shape of the profile); the effects per input are model sensitivities, not
causes; three years is one horizon.

**Next:** explicit profile-shape inputs (best skill, number of skills above
the 90th percentile, specialist vs all-rounder), several horizons, and this
model as the transition step inside the career simulator.

## Test 14: A projection per player, several horizons

`PYTHONPATH=analysis python3 analysis/player_projection.py [player names]`

For each horizon (1–5 years): quantile models for the value change if still
playing and a classifier for still playing, on the player's profile today.
Tested on the latest season whose outcome is known, fitted on earlier seasons.

| Horizon | Age + level | With profile | 21 or younger: age + level → profile | 80 % interval hit | Still playing: actual / predicted |
|---|---|---|---|---|---|
| 1 year | −2 % | 17 % | −28 % → 12 % | 85 % | 80 / 80 % |
| 2 years | 0 % | 22 % | −1 % → 25 % | 82 % | 73 / 76 % |
| 3 years | 35 % | 48 % | 8 % → 21 % | 75 % | 68 / 70 % |
| 4 years | 39 % | 50 % | 8 % → 22 % | 74 % | 64 / 66 % |
| 5 years | 38 % | 46 % | 3 % → 14 % | 75 % | 60 / 66 % |

(Share of the variance in value change explained.)

- The profile helps at every horizon, most clearly for young players, where
  age and level alone explain almost nothing.
- **Explicit profile-shape inputs added nothing** (best skill, second-best,
  number of standout and weak skills, spread): 48 % with or without them at
  three years. The model already sees every statistic; the shape carries no
  extra signal in season-level data. Standout skills need finer data
  (match-level, or statistics this source lacks such as pace and carrying).
- Intervals are slightly too narrow from three years out (75 % against 80 %),
  and dropout is underestimated at five years (66 % predicted, 60 % actual).

Example output, real data (values are third-party market values, current prices):

Antonio Nusa, 21, winger, 2,035 min in 2025/26, value now 46m:

| In | Age | Low | Likely | High | Still playing |
|---|---|---|---|---|---|
| 1 year | 22 | 34m | 48m | 73m | 98 % |
| 3 years | 24 | 25m | 51m | 97m | 97 % |
| 5 years | 26 | 10m | 41m | 93m | 93 % |

Same age and value, different projections today: among 77 players aged 20 or
younger valued 1.5–3m with at least 900 minutes, the three-year projection
runs from 0.65x to 3.6x.

**Weaknesses:** horizons stop at five years (features start in 2018); the
five-year model has 18,000 training rows; training outcomes overlap the test
period in calendar time; values are not yet deflated by the price index; this
is still the third-party value, to be replaced by Speider's own.

## Test 15: Fixing the three-year projection

`PYTHONPATH=analysis python3 analysis/projection_calibration.py` (the diagnosis)
`PYTHONPATH=analysis python3 analysis/projection_v2.py` (the fixes)

Diagnosis on season 2022/23 → 2026 (14,426 players): the model ranks well
(predicted deciles line up with actual, 0.24x → 0.19x at the bottom, 2.2x →
2.7x at the top) but pulls towards the middle: the youngest are
under-predicted, the oldest over-predicted, and the upside is too narrow for
young players (17–19: 20 % ended above the 90th percentile line).

| Age band | Bias V0 | Bias V3 | Inside 80 % V0 | Inside 80 % V3 | Above the upper line V0 → V3 |
|---|---|---|---|---|---|
| 17–19 | −31 % | 0 % | 75 % | 81 % | 20 % → 10 % |
| 20–21 | +1 % | +10 % | 78 % | 81 % | 13 % → 8 % |
| 22–24 | −2 % | +4 % | 76 % | 80 % | 12 % → 9 % |
| 25–28 | +13 % | +3 % | 74 % | 81 % | 9 % → 9 % |
| 29+ | +18 % | +7 % | 77 % | 85 % | 5 % → 8 % |
| All | +9 % | +5 % | 76 % | 82 % | 10 % → 9 % |

- **V1, momentum and career path as inputs: no effect.**
- **V2, young players weighted three times: small gain** in explained growth
  for 17–19 (6 % → 12 %), nothing elsewhere.
- **V3, calibration per age band on a held-out year: fixes what the plot
  showed.** Bias for 17–19 goes from −31 % to 0, for 29+ from +18 % to +7 %;
  every band now has 80–85 % inside the interval and the misses are split
  evenly above and below.
- V3 costs a little sharpness (explained growth 46 % → 43 %) because one year
  is held out for calibration; 20–21 moved from +1 % to +10 % bias.

**What is not fixed:** telling young players apart. Explained growth for
17–19 is 14 %, median error about 100 %. Calibration makes the level and the
interval honest; it does not add information. That needs data on the players
before they are regulars (youth national teams, academy level, minutes at 16–17).

## Test 16: Telling young players apart

`python3 scripts/load_national.py <profiles>` then
`PYTHONPATH=analysis python3 analysis/projection_young.py`

Problem left by test 15: for players of 21 or younger the projection had the
right level but could not say who would grow. Three changes:

1. **Ten times more young players.** Every player-year with a value at age
   16–23 from 2015, not only regulars in leagues with statistics: 63,837
   training rows (2015–2021), 10,987 test rows (2023 → 2026). Only 35 % of the
   test rows have season statistics.
2. **The career before the breakthrough:** senior, reserve and youth matches,
   goals, debut age, level of the leagues played in, matches before 19, last
   season's matches, goals and rating, value change the last two years, height.
3. **Track record of the environment:** how young players at the same club,
   in the same league and of the same nationality developed in earlier years,
   relative to their age and value. Only outcomes known at the time are used.

Three-year value change, share explained and rank correlation:

| Inputs | 17–19 | 20–21 | 22–23 |
|---|---|---|---|
| Age + level | −13 %, 0.37 | 6 %, 0.39 | 13 %, 0.40 |
| + career lines | −5 %, 0.45 | 12 %, 0.40 | 19 %, 0.44 |
| + national teams | −5 %, 0.45 | 13 %, 0.41 | 20 %, 0.45 |
| + club, league and nation track record | 24 %, 0.53 | 24 %, 0.51 | 21 %, 0.50 |
| + season statistics | 24 %, 0.53 | 25 %, 0.52 | 23 %, 0.51 |

What actually happened to the players the full model ranked highest and
lowest (median growth over three years):

| Age | Top tenth | Bottom tenth | Everyone |
|---|---|---|---|
| 17–19 | 11.3x | 1.0x | 3.5x |
| 20–21 | 5.2x | 0.7x | 2.0x |
| 22–23 | 3.1x | 0.6x | 1.6x |

- **The environment is the missing information.** Where a young player is
  developing says more about his next three years than his season statistics
  do. For 17–19 it moves the explained share from −5 % to 24 %.
- Career lines help the ranking (0.37 → 0.45 for 17–19).
- **National teams add nothing here**: the source lists almost only senior
  teams for men (189 age-group spells in 15,408), so youth internationals are
  still an untested idea.
- Season statistics add little on top, and exist for a third of these players.

**Weaknesses:** the outcome is third-party value, and a club or league "track
record" may partly capture how that provider revalues certain leagues rather
than real development; growth is only measured for players still valued three
years later; one test year. The track record must be checked against actual
transfer fees before it is trusted.

## Test 17: Is the track record real?

`PYTHONPATH=analysis python3 analysis/build_wide_frame.py` then
`PYTHONPATH=analysis python3 analysis/track_record_check.py`

Test 16 measured growth with third-party values. Here the same inputs are
scored on outcomes that do not come from the value provider, for players of
23 or younger, three years ahead (train to 2021, test 2023).

| Outcome | Without track record | With track record |
|---|---|---|
| Plays in a big-five league (base rate 5.6 %), AUC | 0.837 | 0.855 |
| Same, hit rate in the top tenth | 25.0 % | 27.1 % |
| Change in league strength, explained | 27.3 % | 28.0 % |
| Fee paid within three years, explained | 38.2 % | 39.2 % |

Among the 2,156 players sold, a club's track record correlates negatively
with the fee relative to the starting value (−0.14): fee/value is 3.2 in the
lowest quarter of clubs and 1.8 in the highest.

- **The track record is mostly an artefact.** It raised explained value
  growth from −5 % to 24 % for 17–19 in test 16, but adds one point or less on
  real outcomes. It describes how the provider revalues players at certain
  clubs and leagues more than how they develop.
- **Decision 37 is partly reversed:** the wide sample and career lines stay,
  the track record goes.
- Career lines and age alone already predict a big-five move well (AUC 0.84;
  one in four of the top tenth get there against one in eighteen overall).

## Test 18: One merged, calibrated projection

`PYTHONPATH=analysis python3 analysis/projection_v3.py H [names]`

All ages, wide sample (278,965 player-years), career lines and season
statistics, no track record; quantile models per horizon; calibration per
age band on a held-out year; separate still-playing model. Growth is measured
relative to the market that year.

| Horizon | Bias before → after calibration | Inside 80 % before → after | Explained | Rank |
|---|---|---|---|---|
| 1 year | −12 % → −7 % | 82 → 82 % | 0 % | 0.35 |
| 2 years | −17 % → −18 % | 80 → 87 % | 13 % | 0.48 |
| 3 years | −6 % → +2 % | 70 → 82 % | 45 % | 0.68 |
| 4 years | −13 % → +4 % | 70 → 80 % | 45 % | 0.68 |
| 5 years | −26 % → −15 % | 72 → 81 % | 43 % | 0.68 |

Players of 17–19 at three years: bias −61 % → −16 %, inside 65 → 80 %, rank 0.39.
Still playing (at least five senior matches in the season): AUC 0.83 at one
year, 0.74 at three, 0.72 at five; predicted about 87 % against 81–84 % actual.

- Calibration works at three and four years, the horizons a buyer cares most
  about. It is unstable at two and five years and for the youngest.
- **The larger finding is about the target.** The median value change of all
  players from one year to the next was x1.42 from 2023, x0.83 from 2024 and
  x0.94 from 2025. A market does not move like that; the provider's model
  does. One- and two-year "growth" in these values is dominated by the
  provider's own revisions, which is why short horizons look unpredictable.
- Tests 13–18 therefore say how a player's *third-party value* will move.
  That is not yet what Speider should project.

**Conclusion and next step:** the projection machinery (wide sample, career
lines, per-horizon quantiles, calibration, still-playing model) is in place.
The target has to change from third-party value to outcomes: fee-equivalent
value from the price model, league level reached and minutes played.
Per-player numbers from this test are not shown in the product.


## Test 20: can a signal known on the day tell good buys from bad ones?

Matching the fee is the wrong goal for judging buys: a model that predicts fees perfectly calls every buy fair. The test is whether a signal known on the day sorts buys by what happened afterwards.

**Correction.** The first version of this test used `fm_transfers.market_value` as the third-party value on the day. That field is the player's value at crawl time (within about 5 % of his latest value for every transfer year), so it leaked the future and made the third-party value look like the best predictor by far. All numbers below use the latest entry in the value history dated on or before the transfer (`analysis/transfers.py`). The fee model on the site was trained on the same wrong field and has been retrained.

Outcome: the next fee paid for the same player (same price level), 1,998 buys in 2018-2023 later sold on for a fee at least a year later. Walk-forward.

| Known on the day | Rank corr. with next fee | R2 for log next fee, together with the fee |
|---|---|---|
| The fee paid | 0.59 | 0.341 (alone) |
| Speider outcome model (expected value in three years) | 0.55 | 0.367 |
| Speider fee model | 0.54 | 0.355 |
| Third-party value on the day | 0.50 | 0.346 |

- The fee paid is the best single predictor of the next fee: the market is mostly right.
- Speider's estimates carry information the fee does not (R2 0.341 to 0.367); the third-party value adds almost nothing (0.346). Speider beats the third-party value on this test.
- Momentum inputs add nothing (C 0.289 vs C2 0.289 on resale per euro) and are removed everywhere.

Verdict used on the site: expected value in three years / fee, in fifths within the year and fee size. Resale / fee by fifth (2018-2023):

| Fifth | n | Median resale / fee | Sold on with a profit |
|---|---|---|---|
| Dearest | 370 | 0.89 | 48 % |
| 2 | 399 | 0.81 | 43 % |
| 3 | 386 | 0.98 | 49 % |
| 4 | 416 | 1.22 | 55 % |
| Cheapest | 429 | 1.41 | 63 % |

For the largest third of fees: dearest 0.52 (36 % profit), cheapest 1.05 (53 %).

"Speider above market value" flag (fee-model value / third-party value on the day, 26 or younger, 1,649 later sales, next fee / value on the day against the year's typical): top fifth x3.06 (78 % above typical), middle x0.96, bottom x0.48 (27 %); among buys priced near the value 2.10 vs 0.57.

Limits: only players sold on for a fee; a stale provider value (far below the fee) makes the verdict meaningless and such buys are left out of the lists.

`PYTHONPATH=analysis python3 analysis/buy_verdict_backtest.py`


## Test 21: the best eleven against how teams actually do

`analysis/team_strength_backtest.py`, result in `data/result_team_strength.json`.

Question: does the level of the best eleven (as the team page picks it) say anything about results?
Setup: 1,011 team seasons in 75 league seasons (2018-2026, leagues with 10+ teams). The eleven is picked by level per role slot
from players with 450+ minutes for the team that season, using only their numbers from the season before. Outcome: goal
difference per match (players' goals minus keepers' goals conceded). Everything standardised within the league season.

| Known before the season | Correlation with goal difference (829 team seasons) | Big five (403) |
|---|---|---|
| Level of the best eleven | 0.45 | 0.53 |
| Value of the eleven most valuable players | 0.59 | 0.80 |
| Last season's goal difference | 0.51 | 0.68 |

Out of time (fit to 2024, test 2025-26, 252 team seasons), R2: level 0.23, seven attributes 0.24, value 0.20, last season 0.26,
value + last season 0.28, value + last season + level 0.31.

Reading: the level is a real signal and adds to value and last season, but on its own it is weaker than the market value of the
eleven. The seven collective attributes add nothing beyond the level out of time. Their fitted weights (finishing 0.19,
creating 0.07, dribbling 0.09, passing 0.32, duels -0.08, ball winning 0.14, clearing -0.15) are confounded by team style:
teams that defend a lot make more tackles and clearances. The "does the team get better" verdict on the team page is therefore
a description of what changes, not a tested prediction of results.


## Test 22: a model of what makes a good squad

`analysis/squad_model.py`, result in `data/result_squad_model.json`.

Target: goal difference per match, standardised within the league season (3,570 team seasons, 2018-2026; missing inputs set to the league average).
Inputs known before the season, standardised the same way. The eleven is picked by market value per role slot.
Ridge models, fit to 2024 (2,499 team seasons), tested on 2025-26 (1,071):

| Inputs | R2 | Correlation |
|---|---|---|
| Last season only | 0.16 | 0.40 |
| Value and level of the eleven | 0.35 | 0.60 |
| + depth and age | 0.41 | 0.64 |
| + last season (site model) | 0.42 | 0.65 |
| + weakest line | 0.42 | 0.65 |
| + seven collective attributes | 0.42 | 0.65 |

Site model coefficients (standard deviations of goal difference per standard deviation of input): value of the eleven 0.45,
depth 0.20, last season 0.15, age 0.14 (older elevens do better within a league, flattening above 26.5), level 0.03.

Reading: with these measurements a good squad is expensive players in the eleven, a bench that is worth something, experience
and continuity. The level from last season's numbers adds almost nothing once value is known, and neither the weakest line nor
the mix of attributes adds anything out of time. That does not prove balance is irrelevant: the attributes are per-90 numbers
coloured by the team's own style, and there is no match-level data yet. It is the open question for the squad half of the platform.
One standard deviation of goal difference is 0.69 goals per match.

## Tail treatment in the value models (after the 600m peak for a teenager)

Above 40m the fee and growth models hand over gradually (fully from 100m) to a robust straight line in age and value fitted on the
expensive end only. In the data teenagers at 60m+ lost value against the market over three years (x0.86, n=18; x0.73 at 100m+, n=3),
and fees above 70m are 1.08 times the value on the day (n=24); the trees had carried the pattern from cheaper teenagers upward.
Held-out error is about unchanged (fees at 40m+: 0.227 trees, 0.236 with tail, n=81; growth mixed by horizon), because the held-out
data has almost nothing above 150m. The change is a choice about extrapolation, not a measured gain.


## Test 20, addendum (2026-11-16): the fee model as the site now runs it

Hypothesis: moving the fee model to a ratio target (B2) and adding the tail line above 40m (B3, and C3 for the outcome model) should not
hurt the buy test; a gain was not expected because few transfers are above 40m.
Result: next-fee rank B 0.538, B2 0.536, B3 0.536; C2 0.548, C3 0.548. Rank against the three-year outcome: B 0.362, B2 0.362, B3 0.362.
Resale rank among resold players: B 0.296, B2 0.275. Reading: no measurable change. The two changes correct the extremes and nothing else.


## Test 23: does an eleven that respects left and right predict results as well as one that does not?

Written before the run (2026-11-16). Reason: the owner pointed out that the eleven had two right wingers (Saka, Madueke) starting.

Hypothesis: picking one left and one right full-back and one left and one right wide player (side from the provider's position
code, best remaining player of the role if a side is empty) predicts goal difference at least as well as the two most valuable per role.
A small loss is expected at most, because the second-most valuable wide player is usually worth more than the best on the other side.
Data, split, metric: as test 22 (fit to 2024, test 2025-26, correlation and R2 of the site model against standardised goal difference).
Counts as better: correlation not lower than 0.645 (test 22: 0.650). If it holds, the side-aware eleven replaces the old one on the site and in the model.
Could mislead us: position codes are today's codes applied to past seasons; 3,806 players have no code.

Result (2026-11-16): correlation 0.649 with sides against 0.650 without; R2 0.420 against 0.421 (1,071 team seasons). The condition holds.
Reading: nothing is lost by making the eleven respect left and right, so the site and the model now do. Arsenal's eleven gets
Tzolis on the left instead of Madueke as a second right winger.
Lesson: a sided eleven predicts as well as an unsided one; use the one that looks like a team.


## Test 24: does performance leading up to a sale move the fee, beyond the market value on the day?

Written before the run (2026-11-16). Reason: the owner finds it odd that the Speider value leans so much on the market value, and asks
whether recent performance (Odegaard after his injury) decides the price.

Hypothesis: the market value on the day already contains most of what last season's numbers say, so removing all performance inputs from
the fee model costs little (under 2 points of typical miss). A rise in form from the season before (rating, minutes, goals) is expected
to push the fee above the market value a little, and adding it should help slightly.
Data: fee transfers with the value on the day (`analysis/transfers.py`), joined to the player's season before the transfer.
Split: fit to 2024, test on 2025-26. Target: log fee / market value. Metric: typical miss on the fee (median absolute percentage error).
Variants: (0) market value and age only; (1) site inputs without performance (season statistics, rating, minutes, last season's matches and goals);
(2) site inputs; (3) site inputs plus change from the season before in rating, minutes and goal threat.
Counts as "performance matters": (2) beats (1) by 2 points or more. Counts as "form matters": (3) beats (2) by 1 point or more.
Could mislead us: season totals only, no match-level form; a transfer in January is matched to the season that ended the summer before;
the market value itself may have reacted to the same form.

Result (2026-11-16), typical miss on fees in 2025-26 (3,409 transfers; 2,189 with season statistics):

| Fee model inputs | All | With statistics |
|---|---|---|
| (0) Market value and age | 51.0 % | 45.9 % |
| (1) Site inputs without performance | 46.5 % | 42.9 % |
| (2) Site inputs | 44.9 % | 40.2 % |
| (3) Site inputs plus change in form | 45.2 % | 40.6 % |
| Third-party market value alone | 42.4 % | 39.6 % |

Fee over market value (median), players with numbers in both seasons (3,612): rating low / middle / high third 0.91 / 1.07 / 1.23;
rating fell / same / rose 0.98 / 1.06 / 1.18; minutes fell / same / rose 0.98 / 1.09 / 1.15; goals per 90 fell / same / rose 1.03 / 1.11 / 1.17.

Reading: performance does move the price. A player in the top third on rating sells for 1.23 times his market value, one in the bottom third
for 0.91, and the fee model gets 1.6 points better with performance inputs (2.7 among players with statistics; the pre-set bar of 2 is met
there and missed overall). A rise in form goes with a higher fee in the raw table, but adds nothing once last season's level is in the model
(45.2 against 44.9): the bar for "form matters" is not met. What the model cannot see is the current season: the inputs are the last
finished season, so a comeback in the first months of a new season (Odegaard) is invisible to it.
Lesson: last season's level moves the fee (0.91 to 1.23 times market value); the change in form adds nothing on top. The current, unfinished season is not an input.


## Test 25: does the season in progress improve the price, so the Speider value rises when a player is doing very well?

Written before the run (2026-11-17). Reason: test 24 showed the fee model only sees the last finished season; the owner's point is that
the value must move when a player performs.

Hypothesis: for a transfer made while a season is running, the player's numbers so far that season at the selling club (minutes, rating,
goals, expected goals and assists per 90) carry information the last finished season and the market value on the day do not.
Data: fee transfers from clubs in leagues with split-year seasons, joined to the selling club's row for the season in progress
(July to May; the row holds what he did there before leaving). Calendar-year leagues are left out: their running season is already the model's latest season.
Split: fit to 2024, test on 2025-26. Target and metric as test 24.
Variants: (A) site inputs; (B) site inputs plus the season in progress (missing where there is none).
Counts as better: on test transfers with 270+ minutes in the running season, (B) has a typical miss at least 1 point lower than (A), and is not worse over all test transfers.
If it holds: (B) becomes the site model, and the page shows how much the season in progress moves the price.
Could mislead us: most summer transfers have almost no running-season minutes, so the signal is learned mainly from winter windows and applied
in November; the market value on the day may already have reacted; the rating is the provider's own.

Result (2026-11-17): typical miss, (A) site inputs against (B) plus the season in progress: all test transfers 44.9 % / 45.3 %;
test transfers with 270+ running-season minutes (413) 49.1 % / 51.7 %; winter windows (316) 53.0 % / 52.1 %. Third-party value: 42.4 / 49.2 / 51.5 %.
Only 699 training transfers have a running season. Raw table (450+ minutes, rating in both seasons, n=261): fee over market value 1.25 / 1.22 / 1.37
for running form worse / same / better, and 1.22 / 1.10 / 1.43 for running rating low / middle / high.
Reading: the condition is not met; (B) is not adopted. The raw table points the expected way, but 699 examples are too few for the tree model
to use six extra inputs without adding noise. Transfers made mid-season are also the hardest to price for everyone (miss near 50 %).
Lesson: feeding the running season straight into the fee trees makes it worse (too few mid-season fees). Retry only with a few-parameter adjustment or a data-rich target.


## Test 26: a few-parameter form adjustment

Written before the run (2026-11-17), directly after test 25 failed.

Hypothesis: the signal in the raw table of test 25 is real but needs a model with very few parameters. Two candidates on top of the site model (A):
(C1) a ridge line on the fee residual with two inputs, the minute-shrunk change in rating and in goal threat (goals + expected assists per 90) against the last finished season;
(C2) a revaluation nowcast: a model of how a player's third-party value moves during a season given what he does in it (rates and his share of the
team's minutes, so that a half-played season does not look like a benched player), trained on every player season (data-rich), then scaled by one
parameter fitted on the mid-season fees.
Split and metric: as test 25. Counts as better: typical miss at least 1 point lower than (A) on the 413 test transfers with a running season, and not worse over all.
Also reported: the nowcast's own out-of-time skill against a model with age and value only.
Could mislead us: the nowcast target is the provider's value (lessons: provider revisions); the mid-season test set is small.

Result (2026-11-17):

Nowcast on its own target (how the third-party value moves during a season, against the market; 52,547 player seasons to fit, 24,709 to test, 2025-26):
age and value alone R2 0.15, rank 0.38; with what the player did in the season R2 0.27, rank 0.52.

On fees (699 mid-season transfers to fit the adjustment, 413 to test): typical miss on transfers with a running season (A) 49.1 %,
(C1) 51.9 %, (C2) 51.3 %; over all test transfers 44.9 / 44.9 / 45.0 %.

Reading: the condition is not met for either candidate; the Speider price is left as it is. The season in progress clearly moves where the
third-party value is heading (the nowcast is a real, tested model of that), but on the few mid-season fees we have it does not make the fee
prediction better. Mid-season transfers are priced badly by every method here, including the market value (49 %).
Decision: the nowcast is shown on the site as its own signal ("form this season": expected change in value by the summer with and without
this season's numbers), and is not folded into the Speider price.
Lesson: what a player does in a season explains much of how his market value moves during it (R2 0.27 vs 0.15), but no form adjustment improved fee prediction for mid-season transfers.

During this test a leak was found in the team tests: see the correction below.


## Correction to tests 21, 22 and 23 (2026-11-17): the squad value was the value at the end of the season

`analysis/team_strength_backtest.py` joined each player's market value on the season it falls in, which is the value at the END of the
season being predicted, not before it. Fixed to the latest value before the season. Reruns:

| | With the leak | Corrected |
|---|---|---|
| Test 21: value of the top eleven vs goal difference (all / big five) | 0.59 / 0.80 | 0.54 / 0.75 |
| Test 21: level of the best eleven (not affected) | 0.45 / 0.53 | 0.45 / 0.53 |
| Test 22: site model, correlation out of time | 0.65 | 0.61 |
| Test 22: R2 | 0.42 | see `data/result_squad_model.json` |
| Test 23: sided against unsided eleven | 0.649 / 0.650 | 0.610 / 0.609 |

Coefficients of the site model after the fix: value of the eleven 0.35, last season 0.22, depth 0.15, level 0.09, age 0.06 (was 0.45, 0.15, 0.20, 0.03, 0.14).
The conclusions stand (value first; attributes and the weakest line add nothing; the sided eleven is as good), but the model is weaker than
reported, the level counts for more and age for less. Test set is 1,026 team seasons.
Lesson: a value "before the season" must be checked against the calendar; the season a value falls in is not the season it precedes.


## Test 27: is there a relationship at all between running form and the fee, measured properly?

Written before the run (2026-11-17). Reason: the owner does not accept that form has nothing to say for the fee, and test 26 had a flaw:
the adjustment was fitted on in-sample residuals of the tree model (which understate the real errors) and with an intercept, which moved
every mid-season prediction up by 6-8 %. The rank correlation between the nowcast and the model's error on the test transfers was +0.16, which
that set-up could not turn into a gain.

Hypothesis: transfers where the running season says "better than age and value imply" are paid above what the site model expects.
Method: the site model's errors on the training transfers are taken out of fold (five folds), so they are honest; one slope, no intercept, is
fitted for the form excess (nowcast minus what age and value alone say, zero without 270 running-season minutes). Fit to 2024, test on 2025-26.
Reported: the slope with a bootstrap interval, the rank correlation with the error on test transfers, and the typical miss with and without.
Counts as a relationship: the 90 % interval of the slope excludes zero and the test rank correlation is positive.
Counts as adoptable: in addition the typical miss on test transfers with a running season falls by at least 0.5 points (the bar is lower than
the 1 point of tests 25-26 because a single slope cannot overfit the way six tree inputs can), and is not worse over all.
If adopted: the Speider price is multiplied by exp(slope x form excess), so it moves with the season in progress.

Result (2026-11-17): slope 0.60 (90 % interval 0.25 to 0.92) on 699 mid-season transfers; rank correlation with the model's error on the 413 test
transfers +0.12. Test transfers split in thirds by form excess: the model's fee was beaten by a factor 0.84 / 0.82 / 1.12 (low / middle / high form).
Typical miss on test transfers with a running season 49.1 % -> 48.6 %; over all 44.9 % -> 44.9 %.

Reading: there is a relationship, and tests 25-26 missed it because of how they were built, not because it is absent. Players whose running season
is better than age and value imply are paid about 12 % above the model; the others about 17 % below it. The gain in typical miss is exactly at the
0.5 point bar, so this is a real but modest improvement, resting on 413 test transfers.
Decision: adopted. The Speider price is multiplied by exp(0.60 x form excess); a form lift of +9 % in expected value moves the price about +5 %.
Lesson: fit small adjustments on out-of-fold errors and without an intercept; the first attempt hid a real signal.


## Test 28: does injury history say something the minutes do not?

Written before the data is in (2026-11-17). Data being collected: FotMob match details for the big five leagues, 2022/23 to 2026/27
(about 7,600 matches): per match the players listed as unavailable with the reason (injury or suspension) and both line-ups.

Hypothesis: matches missed through injury in a season carry information beyond minutes played. Two players with the same minutes differ:
the one who missed matches injured is (a) more likely to miss matches injured the next season, and (b) not valued lower by buyers to the
same degree as one who was fit and left out.
Variables per player season: matches his team played, matches started, matches as substitute, matches listed injured, matches listed otherwise unavailable,
matches fit but not used; injury spells and their length.
Tests, fit on seasons to 2024/25, test on 2025/26 (and the part of 2026/27 played):
(a) share of matches missed injured next season; reference: last season's minutes share and age only. Counts as better: rank correlation up by 0.05 or more.
(b) the fee model's error on transfers (fee over model price) by injured share in the season before; and the site fee model with and without the
injury variables. Counts as better: typical miss down by 0.5 points or more on transfers where the data exists.
(c) the "regular after a transfer" outcome: do injured-then players make it as often as benched-then players?
Could mislead us: the unavailable lists may be incomplete in early seasons; only five leagues; long-term injured players may not be listed every match;
few transfers have a covered season before them.


## Test 29: does the balance of a line-up matter for the result, beyond how good the players are?

Written before the data is in (2026-11-17). Same match data: both starting elevens with positions, the score, and the players' season numbers from the season before.

Hypothesis (the owner's): a team that lacks a quality gets more out of a player who has it. In data terms: given the summed quality of the starters
(market value before the season and level from the season before), match goal difference is higher when the eleven covers the seven attributes
more evenly, and the gain from a strong ball winner (or creator, finisher) is larger in elevens that are weak on that attribute.
Unit: one team in one match (about 15,000 team matches), with the opponent's summed quality as a control and home advantage.
Variants: (1) quality of own and opposing eleven; (2) plus the eleven's seven attribute means; (3) plus the lowest attribute and the spread;
(4) plus interactions between a player's best attribute and the rest of the eleven's level on it.
Split: seasons to 2024/25 to fit, 2025/26 and 2026/27 to test. Metric: explained share of goal difference per match and rank correlation.
Counts as "balance matters": (3) or (4) beats (1) out of time by 0.5 points of explained share or more, with the sign the hypothesis says.
Could mislead us: attributes are per-90 numbers coloured by the team's own style (test 21); match results are noisy (expect low explained shares);
line-ups reflect injuries and rotation, not only the coach's best eleven.
