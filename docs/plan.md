# Plan for Speider

Version 2, written 15 November 2026 after the data audit, and updated the same day after the pre-study.

## The goal

A platform that answers three questions about a player:

1. How good is he really? (independent of team, luck and injuries)
2. What is he worth today? (and is the price a good or bad buy)
3. What is he expected to be worth over the rest of his career?

The users in mind are scouts and agents. The model for the ambition is how clubs like Brentford work.

## Scope

Speider is not tied to any league. The aim is to find underpriced players wherever they play; a gem in Bosnia or Cyprus is as interesting as one in Norway. Eliteserien was used in the pilot only because it was the first league checked.

That makes **league level** the core of the model. Numbers from Slovakia must translate into what they mean in Belgium. This is learned from players who changed league and have numbers on both sides.

Everything is free data for local, private use. This is not a business. Paid data is an option once the value is proven.

## Sources

| Source | Role |
|---|---|
| FotMob | Base: season statistics in 70 men's leagues, transfers with fees, player profiles with career and value history. One player id throughout. |
| SofaScore | Fills leagues FotMob lacks (from 2023/24) and gives per-match detail and shot maps; Premier League detail from 2014/15. |
| transfermarkt-datasets | Extra check only. |
| Eliteserien Fantasy | Current injuries and status for one league. |
| StatsBomb Open Data | Training own models on event data. |
| Opta, Wyscout, StatsBomb (paid) | Industry standard, sold to organisations. Not in scope. |

Details and terms: [data-sources.md](data-sources.md), [source-exploration.md](source-exploration.md), [pre-study.md](pre-study.md).

## What went wrong in the first attempt

Work started from the sources that were easiest to reach, not from what the questions require. The result was a model that priced players on goals, assists and playing time and could not assess defenders, defensive midfielders or injured players. The rule since: explore the data and write the tests before building.

## Three layers

**Layer 1: Quality.** One assessment per player and role, built on underlying per-90 numbers. Shrunk for low minutes, translated for league strength, adjusted for team level. Injuries and playing time are kept out.

**Layer 2: Value.** A model trained on actual transfer fees, with quality, age, contract, role and league level as inputs. Gives an interval, not a single number. Expressed against a price index.

**Layer 3: Future.** A career simulator built from chained one-year transitions gives the distribution of quality and value at any later age, in today's prices and with projected market inflation.

The models that make up for missing data are described in [models.md](models.md). Compensating for thin data with our own models is at least half the job.

## Two data tiers

- **Full profile:** detailed statistics. Large leagues from 2014/15 (SofaScore), FotMob from 2016/17, small leagues from 2023/24.
- **Historical profile:** goals, assists, minutes, shots, league, age, transfers and market value history, as far back as the sources go (career lines from 2002). Detailed numbers for old seasons are reconstructed and marked as estimates.

This is what allows comparing a player from 2007 with one from 2026.

## Phases and gates

| Phase | Content | Gate |
|---|---|---|
| 0. Foundation | Repository, raw data stored locally, loaders. | Done. |
| 1. Shrinkage and role | Per-90 numbers shrunk towards role, league and age. | Beats raw numbers on next season. **Passed** (test 1). |
| 2. League strength | Per-statistic translation from league switchers. | Beats "no translation" on held-out moves. **Passed** (test 3). |
| 3. Quality | Assessment per role. | Explains later fees better than goals and assists alone. |
| 4. Value | Model on fees, tested forward in time. | On par with third-party market value on unseen sales, without having seen it. |
| 5. Future | Career simulator, price index projection. | Calibrated intervals on real long careers. First version **passed** (test 4). |
| 6. "Underpriced" | Lists made at T checked two to three years later. | Beats a random sample with the same age, league and price. |
| 7. Product | The site shows only what has passed its gate, with uncertainty. | |

The full protocol is in [evaluation.md](evaluation.md). Results are logged in [results.md](results.md), decisions in [decisions.md](decisions.md).

## Known pitfalls

- Injuries: playing time must never be used as a measure of quality.
- Team effect: numbers must be adjusted for how good the team is.
- League level: needs players who changed league, with numbers on both sides. Thin for small leagues.
- Ground truth: fees are noisy. Bonuses, sell-on clauses and wages are usually unknown, and sell-on clauses bias the fees of young players from small clubs downwards.
- Selection: only sold players have a fee. They are not a random sample.
- Survivorship: players who drop out of the data must be modelled as an outcome.
- Market inflation: a player's development must be separated from the price level of the market.

## Next steps

1. Finish downloading player profiles; load them.
2. Dropout as a state in the career simulator.
3. Role inference and quality per role.
4. Fee-trained price model with the price index.
5. Verdict on signing day for transfers, and clause pricing.
6. Second ingestion stage: SofaScore match data for leagues FotMob lacks and for older seasons.
