# FotMob pilot, 15 November 2026

A test of the first two requirements in the [plan](plan.md), run against FotMob's season lists for Eliteserien, 2017 to 2026. The numbers were computed in a browser tab, not with the code in this repository.

## What FotMob has

41 lists per season, ten seasons. Each list has one row per player with value, minutes, matches, club and position.

| Type of number | From season |
|---|---|
| Minutes, goals, assists, rating, shots, passes, long passes, dribbles, chances created | 2017 |
| Tackles, interceptions, clearances, blocks, recoveries, defensive actions | 2017 |
| xG, xG on target, xA, goals prevented for keepers | 2020 |
| Line-breaking passes | 2024 |
| Keeper: high claims and sweeping | 2025 |

The 2026 minutes list has 449 players, 307 of them with at least 450 minutes. Exactly the same numbers as in Eliteserien Fantasy.

## Requirement 1: coverage

The requirement was numbers for at least 90 % of players above 450 minutes. **Not passed at 450 minutes, passed at 900.**

Share of players with defensive actions per 90 in 2026:

| Position | At least 450 min | At least 900 min |
|---|---|---|
| All | 80 % | 93 % |
| Centre-back | 72 % | 98 % |
| Full-back | 89 % | 97 % |
| Defensive midfield | 60 % | 75 % |
| Central midfield | 88 % | 97 % |
| Attacking midfield | 71 % | 100 % |
| Winger | 78 % | 92 % |
| Striker | 79 % | 92 % |
| Goalkeeper | 70 % | 76 % |

The cause is that per-90 lists only include players who took part in roughly half the matches. Totals such as xG and xA include everyone. Only five players are registered as defensive midfielders, so that number is uncertain.

Consequence: season lists are enough for regulars. For reserves and young players with few matches, match data is needed.

## Requirement 2: do the numbers hold from year to year?

Same player in two consecutive seasons, at least 900 minutes in both, standardised within position group and season. All season pairs from 2017 to 2026 pooled. **Passed.**

| Number | Correlation | Same team | Changed team | Count |
|---|---|---|---|---|
| Accurate passes per 90 | 0.83 | 0.85 | 0.67 | 997 |
| Accurate long passes per 90 | 0.77 | 0.78 | 0.70 | 922 |
| Chances created | 0.73 | 0.75 | 0.58 | 1059 |
| Successful dribbles per 90 | 0.73 | 0.72 | 0.74 | 879 |
| xA per 90 | 0.71 | 0.73 | 0.49 | 652 |
| Defensive actions per 90 | 0.70 | 0.71 | 0.68 | 997 |
| Recoveries per 90 | 0.70 | 0.70 | 0.68 | 997 |
| Shots per 90 | 0.68 | 0.69 | 0.57 | 917 |
| Clearances per 90 | 0.67 | 0.70 | 0.54 | 994 |
| Tackles per 90 | 0.66 | 0.66 | 0.67 | 926 |
| Line-breaking passes per 90 | 0.59 | 0.60 | 0.08 | 196 |
| Interceptions per 90 | 0.53 | 0.55 | 0.46 | 915 |
| FotMob rating | 0.53 | 0.53 | 0.49 | 946 |
| xG per 90 | 0.50 | 0.51 | 0.45 | 598 |
| Save percentage | 0.38 | 0.40 | | 75 |
| Goals per 90 | 0.31 | 0.32 | 0.24 | 620 |
| Assists | 0.31 | 0.32 | 0.22 | 608 |
| Minutes played | 0.20 | 0.19 | 0.22 | 1126 |
| Goals prevented (keeper) | 0.14 | 0.18 | | 51 |

Reading:

- The underlying numbers are about twice as stable as goals and assists. They should carry the quality assessment.
- Minutes played barely persist (0.20). Playing time is a poor measure of who a player is.
- Dribbles, tackles, recoveries and defensive actions are as stable when the player changes team. They follow the player.
- xA, chances created and line-breaking passes drop a lot on a team change. They depend on the team and must be adjusted.
- Keeper numbers are weak. Goals prevented is almost pure noise from year to year.

Stability shows that a number measures something lasting about the player. It does not show that the number matters for value. That is tested against transfer fees.
