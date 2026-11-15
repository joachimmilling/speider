# Source exploration, 15 November 2026

What actually exists, checked against the live services from a browser. Where something was only checked for one player or one match, it says so.

## Summary

| Source | Leagues with deep player numbers | Level | History | Extras |
|---|---|---|---|---|
| SofaScore | 127 leagues in 87 countries | Per player per match, 45 to 78 numbers | Norway from 2018, Bosnia and Cyprus from 2023/24 | Birth date, contract, market value, transfer fees |
| FotMob | 65 leagues in 49 countries | Per season, and per player per match | Eliteserien from 2017 | Shots with xG, unavailable players per match, value history from SciSports |
| transfermarkt-datasets | 31 top leagues | Matches, line-ups, events | Varies | 17,554 transfers with a fee |
| Eliteserien Fantasy | One league | Season and match, basic numbers only | From 2017 | Current injury status |
| Norwegian FA (NFF) | Closed | | | |

## SofaScore

- 7,649 football tournaments in 275 categories. The first two leagues in each category were checked, 485 in total, by looking at the latest finished match.
- 127 leagues have tackles per player per match. 114 of them have xG or xA, 107 have SofaScore's own values for passing, dribbling and defending, and 64 have ball carries.
- Two tiers: about 70 numbers per player in the largest leagues, about 50 in the smaller ones.
- **Bosnia (WWIN Liga BiH) and Cyprus are covered**, with about 50 numbers per player and xG. So are Bulgaria, Slovenia, Hungary, Morocco, Armenia, Azerbaijan, Malta, the Faroe Islands, Estonia, Kazakhstan, Wales and Northern Ireland, among others.
- Per-match numbers in the smaller leagues: passes (own and opposition half, long, crosses), duels, aerial duels, tackles, clearances, blocks, recoveries, dribbles, touches, possession lost, shots, xG, xA, rating.
- Shot map per match with position, body part, situation and xG.
- Player profile: birth date, contract end, market value, height, foot, detailed position. Checked for one player.
- Transfer history per player with the fee where known.
- Match-number history: Eliteserien 2018 to 2026. Bosnia and Cyprus from 2023/24 only.

Uncertainty: a league that showed nothing may have numbers in other matches. Ukraine and the Georgian top league showed nothing and should be rechecked.

## FotMob

- Season lists: see [fotmob-pilot.md](fotmob-pilot.md). 65 leagues have passing and defending numbers, 40 have xG.
- Match data, checked for one Eliteserien match: numbers for all 40 players in the squads. Touches, touches in the opposition box, passes into the final third, crosses, dribbles, tackles, blocks, clearances, interceptions, recoveries, dribbled past, ground duels, aerial duels, xA.
- Shots per match with position, xG, xG on target, situation and goalkeeper.
- Line-ups with a list of **unavailable players per match**, with type (injury or suspension) and expected return. This gives injury history backwards in time.
- Player profile: birth date, contract end, match log with minutes and bench appearances, career history with loans.
- **Value history from SciSports**: monthly values with upper and lower bounds.
- Bosnia and Cyprus have no per-match player numbers at FotMob.

## The Norwegian FA and other federations

- NFF does not, as a rule, give outsiders access to its API or underlying football data. Access is granted only to selected partners under agreement.
- NFF owns the data in its registry, and reuse is only allowed by agreement.
- fotball.no rejects automated reading of player pages.
- The data is basic anyway: matches, squads, goals and cards.

Consequence: NFF is not a source for Speider. Federation data in general gives nothing beyond what FotMob and SofaScore already have.

## Team strength

ClubElo publishes strength ratings for European clubs with history, free as CSV. The service could not be read from the work environment, so coverage is unconfirmed.

## What this means

You can:
- assess players in every position in 127 leagues, including Bosnia and Cyprus
- compute per 90 minutes for all players, including reserves, because the numbers exist per match
- build injury history from FotMob's lists of unavailable players
- measure own value estimates against a professional model (SciSports)
- get age, contract and transfer fees for all leagues

You cannot:
- get event data, that is every pass with a position. The numbers are summed per player per match. Own pass-value models cannot be built directly, but own xG models can, because shots have positions.
- go further back than 2023/24 in the smallest leagues.
- use NFF

The cost: match data means many requests. One league has about 250 matches a season. 127 leagues over four seasons is more than 100,000 matches. Both sources are unofficial and can close access.
