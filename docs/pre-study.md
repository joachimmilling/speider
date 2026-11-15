# Pre-study: does the data foundation hold?

Run 2026-11-15, before downloading anything at scale. All numbers are measured, not estimated, unless stated.

## Short answer

| # | Question | Answer |
|---|----------|--------|
| 1 | Can a plain script reach the sources? | **Not settled.** Must be tested on the owner's machine: `python3 scripts/check_access.py` |
| 2 | Enough transfers with a fee and performance data before? | **Yes.** About 6,300 since 2022 |
| 3 | Enough league switchers to measure league strength? | **Yes for large leagues, thin for small ones** |
| 4 | Can the same player be linked across sources? | **Yes**, and the core does not need it |
| 5 | Do FotMob and SofaScore agree? | **They are the same data.** Not two independent sources |
| 6 | Do small leagues have detailed enough data? | **Yes from 2023/24.** Nothing before |

## 1. Script access

Neither the cloud workspace nor the local VM can reach the data sources (network filter). Everything in this pre-study was fetched through the browser. Known risk: FotMob's `/api/data` requires a signed header outside a browser, and SofaScore often rejects scripts. FotMob's static lists (`data.fotmob.com`) are open.

If scripts are rejected, ingestion runs through the browser, as the pre-study did. Slower, but it works.

## 2. Ground truth for the price model

New source found: FotMob's transfer list (`/api/data/transfers` with `fromDate`, `toDate`, `minFee`). It has fee, date, clubs and **FotMob's own player id**.

| Year | Paid transfers (no loans) | With ≥ 900 min in FotMob before |
|------|------|------|
| 2019 | 899 | not fetched (*) |
| 2020 | 658 | not fetched (*) |
| 2021 | 800 | not fetched (*) |
| 2022 | 1,158 | 785 |
| 2023 | 1,495 | 1,161 |
| 2024 | 1,644 | 1,287 |
| 2025 | 2,030 | 1,601 |
| 2026 | 1,837 | 1,487 |

(*) The pre-study only fetched the six latest seasons per league. Older seasons exist for many leagues.

- Total since 2022 with performance data before: **6,321**.
- Fees since 2023: median EUR 2.0m, 10 % below 260,000, 1,291 below 500,000. Not only top football.
- 97 % also have a market value on the transfer date. It is used as an opponent in the test, never as an input.

Caveats: "before" is counted at season level, so winter transfers may include some matches after the move. The real number is slightly lower. Undisclosed fees are not included, and they are not random.

## 3. League switchers

FotMob, 70 men's leagues with deep statistics, six latest seasons:

- 252,686 player-seasons, 83,050 with ≥ 900 minutes, 68,183 players.
- **11,283 moves** with ≥ 900 minutes on both sides (19,122 with ≥ 450).
- 6,047 of them cross a border. 999 distinct league pairs.
- The median league has 55 moves.

Weak point: several small leagues have only two seasons in FotMob and therefore few moves (Slovakia 19, Iceland 21, Czechia 34, Serbia 36, Finland 36, Romania 45). League strength for these is uncertain and must be supported by club Elo and European cup matches. The uncertainty must be shown.

42 of the 70 have xG.

## 4. The same player in several sources

- FotMob uses the same id in statistics, transfers and player profiles. The core (performance → fee) needs no name matching.
- FotMob ↔ SofaScore, Eliteserien 2025: both have 442 players. Name alone matches 80 %. Name + minutes matches 90 %. The rest are the same players with different minute counts. Name + team resolves them.
- transfermarkt-datasets was not linked in this round. It is no longer needed as ground truth.

## 5. FotMob against SofaScore

Eliteserien 2025, 229 players with xG in both:

- xG sum: 536.9 vs 536.0. Correlation 1.00. Median difference 0.03.
- Goals: identical.
- Minutes: identical for 72 %, the rest differ by 2–5 % (stoppage time).

Conclusion: the same supplier underneath. Comparing them gives no quality control, and we do not need both for the same league. FotMob is the base. SofaScore fills the leagues FotMob lacks.

## 6. Small leagues (SofaScore)

Tested Bosnia (WWIN Liga) and Cyprus, one match per season:

| Season | Statistics per player per match | xG | Shot map | Average position |
|--------|------|----|-----------|---------------|
| 2023/24 → today | 40–53 | yes | yes, with xG | yes |
| 2022/23 and older | 0 | no | no | no |

- Position per match is only G/D/M/F, but formation + average position gives the role.
- Some matches have running data (distance, sprints, top speed).
- Transfer history with fees exists per player but is thin: in a sample of 40 Bosnian players, 8 had a paid transfer since 2023.
- One Cypriot season (2025/26) gave an empty sample. Possibly a postponed match. Must be checked before Cyprus counts as covered.

## History (added the same day)

- FotMob deep statistics start in 2016/17 (30 statistics at first, 37–46 later).
- SofaScore has 55+ per-match statistics and shot maps for the Premier League from 2014/15. Before that only goals, assists, minutes and shots (checked back to 2007/08).
- FotMob player profiles give career lines (matches, goals, assists, rating) back to 2002 and market values back to 2014.

## What this means

**We can:**
- Train the price model on real fees with several thousand examples.
- Measure league strength directly between most leagues.
- Cover Bosnia, Cyprus and similar leagues from 2023/24.

**We cannot:**
- Backtest small leagues further back than 2023.
- Use FotMob and SofaScore as a check on each other.
- Trust league strength for leagues with fewer than about 50 moves without support.

**Change to the model plan:**
- An own xG model matters less than assumed. Supplier xG now exists in small leagues. It is kept for control, for keepers and for 2014–2017.
- League strength for small leagues is the largest gap and gets top priority.
