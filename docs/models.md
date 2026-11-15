# Own models that make up for missing data

Free data lacks three things professional clubs have: event data (every pass with coordinates), tracking, and a clean register of transfer terms. The idea is to build models that extract as much as possible from what we do have, and to measure each one against a simple reference before it is allowed in.

Rule: a model is in only if it beats its reference on data it has not seen. Otherwise we use the reference.

## 1. Own xG model

- **Gap:** supplier xG is missing for older seasons (2014–2017) and some leagues.
- **We have:** shot maps with coordinates, body part and situation.
- **Model:** gradient boosting or logistic regression on distance, angle, body part, situation.
- **Training:** leagues with supplier xG; calibrated per league.
- **Test:** log loss and calibration against actual goals, compared with supplier xG. Reference: all shots are worth the same.
- **Also gives:** goals prevented for keepers.

## 2. Shrinkage for low minutes

- **Gap:** the most interesting players (young, small leagues) have few minutes. Raw per-90 numbers are then mostly noise.
- **Model:** empirical Bayes. Each statistic is pulled towards the mean for role, league and age, less so the more minutes the player has.
- **Test:** predict next season. **Passed** (results, test 1).

## 3. League strength per statistic

- **Gap:** ten tackles a match in Cyprus is not ten tackles in the Netherlands.
- **Model:** players who change league give the exchange rate. A translation factor per league and statistic, with club Elo as support where switchers are few.
- **Important:** the translation differs by statistic.
- **Test:** hold out the latest season's switchers. **Passed** (test 3). Team strength still to be separated out.

## 4. Team impact (adjusted plus/minus)

- **Gap:** centre-backs and defensive midfielders show up poorly in counts.
- **We have:** line-ups, substitution times and shots with timestamps.
- **Model:** matches split into stints with the same 22 players. Ridge regression on xG difference per stint gives each player a contribution, with the count statistics as a prior.
- **Limitation:** very noisy for one season. One signal among several, never alone.
- **Test:** predicts the team's xG difference next season from who plays.

## 5. Role from data

- **Gap:** "midfielder" hides a ball winner, a number eight and a number ten.
- **Model:** clustering on statistic profile and position per match. Players are only compared within their role.
- **Test:** roles should be stable from season to season for the same player.

## 6. Imputing missing statistics

- **Gap:** some leagues have about 50 statistics per match, others about 70.
- **Model:** learn the missing ones from those present, in leagues that have everything.
- **Test:** hide columns in rich leagues and measure the hit. Used only where the error is small, and marked as computed.

## 7. From counts to ball value

- **Gap:** without event data we do not know how much a pass is worth.
- **We have:** StatsBomb's open event data for a selection of competitions.
- **Model:** compute real ball value there (xT/VAEP type) and learn the mapping to the counts we have everywhere.
- **Limitation:** open data covers few leagues, mostly top level.

## 8. Age curves per role

- **Model:** year-on-year change for the same player, per role and statistic, corrected for those who stop playing dropping out of the data.
- **Use:** future quality, and through it future value.

## 9. Price model on actual fees

- **Gap:** fees are often unknown, and only players someone wanted are sold.
- **Model:** trained on paid transfers. Gives an interval (quantiles). A separate model for the probability of being sold corrects for selection.
- **Never an input:** third-party market value. Used only as an opponent in the test.

## 10. Career simulator (chained from short windows)

- **Gap:** detailed statistics cover few whole careers.
- **Idea:** whole careers are not needed. Two to three years of all players give the transitions 20→21, 21→22, …, 33→34. Chain them.
- **Model:** transition model. State = age, role, quality level, league level, share of playing time. The model gives the distribution of next year's state. The player is simulated many times, year by year.
- **Dropout is an outcome:** "out of the data" and "down a level" are states of their own. Otherwise the curve looks too good.
- **Value:** simulated state at age X → the price model, in today's prices and with the projected price index.
- **Test:** chained short windows must reproduce real long careers. First version **passed** (test 4): level is needed, direction last year is not.

## 11. Detailed profile for old seasons (reconstruction)

- **Gap:** before 2014/15 only goals, assists, minutes and shots exist.
- **Model:** learn in modern data the mapping from the simple (output, position, team strength and style, age) to the detailed. Apply it backwards. The result is an estimated profile with an interval, clearly marked.
- **Support:** team statistics per match often go further back and constrain the sum of the players' numbers.
- **Test:** hide the detail for 2016–2018, reconstruct, compare.

## 12. Market value as a weak quality signal backwards

- For eras without statistics, value development and who bought the player can serve as a noisy measure of level. Historical profile only, never in the price model.

## 13. Clauses priced with the simulator

- **Gap:** the fees we have are headline numbers. Bonuses, sell-on shares, buy-backs and wages are not in the data.
- **Idea:** a clause is an option on the player's future, and the simulator gives exactly the distribution over that future. The user enters the terms of a deal and Speider computes expected value:
  - Sell-on share: share × expected gain on sale × probability of a sale.
  - Bonus on matches, goals or promotion: probability the threshold is reached × amount.
  - Buy-back: value above the agreed price, in the outcomes where it pays.
- **Systematic bias in the ground truth:** young players from small clubs are often sold with a sell-on share, so the headline fee understates the real price and the model may think they are cheaper than they are. Sensitivity test: assume a typical share (for example 10–20 %, an assumption) for such sales and see whether the "underpriced" list changes.
- **Wages:** not in free data. The purchase verdict covers the fee, not total cost, until we have wage estimates.

## Order

1. Shrinkage (2) and role (5): cheap, everything else builds on them.
2. League strength (3): decides whether we can compare across leagues at all.
3. Career simulator (10), age curves (8) and price model (9).
4. Clauses (13) and reconstruction (11).
5. Own xG (1), team impact (4), imputation (6), ball value (7).
