# Data audit, 15 November 2026

What the first two sources actually contain, checked against the real data. Written before the value model was rebuilt. Superseded in part by [pre-study.md](pre-study.md).

## Eliteserien Fantasy

| What | Finding |
|---|---|
| Players | 546, all in Eliteserien. 449 have played this year. |
| Match numbers | Minutes, goals, assists, cards, saves, goals conceded, clean sheets. Per season and per match. |
| Earlier seasons | Season totals per player back to 2017. |
| Birth date, nationality, shirt number | Empty for all 546. |
| Opta index | The field exists but is 0 for everyone in 2026, per season and per match. In a sample of 20 players it was only filled for 2023. |
| Injuries and status | `status` and `news` per player: 39 injured, 30 doubtful, 4 suspended, 100 unavailable. The text says what and for how long. Current state only. |
| Sold players | Listed in `news`. |
| Defending and passing | Not present. |

Injury history cannot be fetched backwards. It has to be built by storing a snapshot regularly from now on.

## transfermarkt-datasets

| What | Finding |
|---|---|
| Updated to | Values to May 2026, matches to 30 May 2026. Updates have stopped. |
| Player profiles | Birth date, position, foot, height, contract end, caps, agent. 424 players in Eliteserien clubs. |
| Value history | 4,354 values for 708 Eliteserien players, from 2008. Median five per player. |
| Transfers | 175,165 in total, 17,554 with a stated fee. 287 sales from Eliteserien clubs with a fee, 982 from Norway, Sweden and Denmark. |
| Eliteserien matches | 329, from 29 March 2025. None older. |
| Line-ups and events | Starting eleven, bench, substitutions, goals, assists and cards per match. Minutes derived from these match the ground truth in the 14 leagues that have it. |
| Defending and passing | Not present. |

Transfer fee against Transfermarkt value at the time of sale: median 0.94. Half the sales fall between 0.53 and 1.5 times the value. That is the reference an own model has to beat.

## What this means

You can:
- train a value model on actual transfer fees instead of Transfermarkt estimates
- test it forward in time, since both fees and values are dated
- separate injury from bench going forward, by storing status daily
- follow a player over several seasons

You cannot:
- measure the quality of a centre-back, a defensive midfielder or a creative number eight from these two sources. Neither has defending or passing numbers.
- use the Opta index
- reconstruct injuries backwards in time

Without a source for defending and passing, Speider could only price players on goals, assists, age, contract and level. That is why FotMob and SofaScore were brought in.
