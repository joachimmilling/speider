# Lessons

One line per lesson, newest area first. Read before proposing a model, an input or a test.
"Retry only if" says what would have to change for the idea to be worth another run.

## Squads

- At match level (9,242 team matches) the eleven's attribute levels add a little beyond market value and level: ball winning +0.12, passing +0.19, finishing +0.10, clearing -0.15 per SD. Evenness, the weakest attribute and specialist interactions add nothing (test 29).
- The quality of both elevens explains about 19 % of a match's goal difference out of time.
- An eleven that respects left and right predicts as well as one that does not (0.610 vs 0.609 after the leak fix); the sided eleven is used (test 23).
- A team's goal difference follows the market value of its best eleven (0.35 of the model), then last season (0.22), depth (0.15), level (0.09) and age (0.06); out-of-time correlation 0.61 after the leak fix (test 22).
- The level from last season's per-90 numbers adds almost nothing once value is known (test 22). Retry only if: match-level data or a level that is not built from season aggregates.
- The mix of the seven collective attributes and the "weakest line" add nothing out of time (tests 21, 22). Retry only if: match-level data, or attributes cleaned of team style.
- Per-90 defensive volume (tackles, clearances) goes with weaker teams: it measures how much a team defends, not how well (test 21).
- The best eleven picked by level alone is a weaker signal than the value of the eleven most valuable players (0.45 vs 0.54; big five 0.53 vs 0.75) (test 21).

## Value and price

- Match line-ups improve the fee model: starts share and minutes share of the team's matches, then out-of-squad and bench shares (typical miss 36.9 -> 34.1 % where the data exists, 46.3 -> 45.1 % over all) (test 28). In the site model.
- The provider's per-match injury lists are incomplete (Odegaard autumn 2024 missing) and add nothing. "Out of the matchday squad" from line-ups is the usable signal; it predicts next season's absence (rank 0.24 -> 0.30).
- Running form does move the fee: players in form are paid about 12 % above the model, others about 17 % below (test 27). One slope (0.60) on the form excess is in the Speider price; gain in typical miss is small (49.1 -> 48.6 % mid-season).
- Feeding the running season straight into the fee trees made it worse (test 25): 699 mid-season fees are too few for six tree inputs.
- Tests 25-26 hid the signal: the adjustment was fitted on in-sample tree residuals with an intercept. Fit small adjustments on out-of-fold errors, slope only.
- What a player does in a season explains much of how his market value moves during it (R2 0.27 vs 0.15 for age and value) (test 26). It feeds the form excess used in the price (test 27).
- Mid-season transfers are the hardest to price: every method misses by about 50 %.
- Performance moves the fee: top third on last season's rating sells for 1.23 times market value, bottom third 0.91; performance inputs improve the fee model by 1.6 points (2.7 with statistics) (test 24).
- The change in form from the season before adds nothing once the level is in the model (test 24). Retry only if: in-season or match-level form.
- The fee model only sees the last finished season. A strong start to the current season is invisible to it (test 24).
- Matching the fee is the wrong goal: a perfect fee model calls every buy fair. The target is what happens next (decision 44, test 20).
- Expected value in three years against the fee sorts buys: cheapest fifth resold for 1.41 times the fee, dearest 0.89; largest fees 1.05 vs 0.52 (test 20).
- The Speider value does not beat the third-party value at hitting fees (miss 44.9 % vs 42.4 %) and does not beat the fee itself at predicting the next fee (rank 0.54-0.55 vs 0.59). Its use is the gap to the market value.
- Trees do not extrapolate: a fee target capped out at the largest fees seen and marked every 100m+ player as overpriced. Model the ratio to market value instead (2026-11-16).
- Above 40m the data is too thin for trees: patterns from cheap teenagers were carried up to a 600m projection. A line fitted on the expensive end takes over there. This is a choice about extrapolation, not a measured gain (held-out error unchanged).
- Moving the fee model to a ratio target and adding the tail changed nothing measurable on the buy test (B vs B2/B3 in test 20). They fix the extremes only.
- Momentum inputs (recent value change) add nothing out of time, punished top players, and can leak the fee. Out everywhere (test 20). Retry only if: a momentum measure that cannot postdate the transfer.
- `fm_transfers.market_value` is the value at crawl time. Using it leaked the future into test 20; the first table was retracted. Value on the day comes from the value history.
- The third-party values are revised market-wide from year to year (x1.42, x0.83, x0.94). Always measure growth relative to that year's market (test 18).
- A club or league "track record" raised explained value growth for teenagers but added about nothing on real outcomes: it described the provider, not development. Out (test 17).
- Season-aggregate statistics are close to exhausted for predicting fees; context (team strength, earlier fees, career path) moved the price model, finer play description did not (tests 5-9).
- Sell-on clauses of realistic size do not change which transfers look good or bad (test 10).

## Projection and careers

- For young players the environment (league strength, team quality) says more about the next three years than season statistics do (tests 13, 16).
- Value histories exist almost only for players active today. Growth from them is growth given survival; dropout must come from career lines and be mixed in (tests 8, 11, 19; decision 43).
- A hard ceiling on value is wrong (records fall), and "typical for the age" must be peers in age and value, not age alone.
- Calibration per age band works at three and four years; it is unstable at two and five years and for the youngest (test 18).
- Nearest comparables in age and value are a useful second opinion next to the model; the 50/50 blend weight has not been tested.

## Measuring players

- The provider's profile carries the current club and the current injury; use them before inferring either from minutes.
- A minutes floor for showing players hides the most interesting young ones. Show them without numbers instead.
- Today's club is the latest senior season row with any minutes, then the latest transfer since June; a minutes floor or a reserve-team rehab match puts players at the wrong club (Gabriel Jesus, Saliba).
- Shrink every per-90 number towards the role average by minutes (test 1).
- League strength from players who change league works; cups must be left out (test 3).
- One scale across leagues: 0.23 units of league strength per standard deviation of player quality, fitted on 1,609 movers.
- Percentiles early in a season are noise (a handful of players per group): use the latest season with 900+ minutes.
- Role codes: wide attackers are 83 and 87 in the attacking-midfield line. Similar players must be matched on level as well as style.
- "Regular after a transfer" must be league minutes for the buying club (1,500+), not matches.
- There is no injury data: low minutes cannot be read as "not good enough".

## Process

- Chrome blocks a second automatic download from the same tab without any message. Export each file from a fresh tab on the same origin.
- A leak sat in the team tests for a day: the squad's market value was taken at the end of the season being predicted. Check every "before" value against the calendar (correction to tests 21-23).
- Changing a model after one odd-looking player, without rerunning the tests, is how circles start. Hypothesis first, scoreboard after (this file exists because of 2026-11-16).
- The site and the backtest ran different model code for a day. One definition per model.
- Hiding a number is not a fix; find the technique that handles the data properly.
- Publishing: the artifact blocks remote images; logos only work in the local build.
