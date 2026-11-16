# Changelog

## 2026-11-16 – Sporting verdict for the buying club, fitted scale, place by value

- Sporting outcome counts matches for the buying club only (a loan elsewhere no longer counts): regular 20+ in one of the first two seasons (10+ in the half season after a winter move), rotation 10+.
- Step success now separates: 83 % regulars after a step down, 80 % sideways, 79 % a small step up, 68 % after the largest steps. By price verdict: 74 % for the dearest fifth, 78-79 % for the rest.
- The common scale is fitted instead of assumed: 1,609 players who changed league between the two latest seasons give 0.23 strength units per standard deviation (was 0.35 by assumption), so league level counts for more.
- "Place in the role" in best fit is ranked by Speider value, not by the style level.

## 2026-11-16 – Common scale, sporting verdict, best fit, club report card, cheaper alternatives

- One scale across leagues: rank within the own league moved by league strength and read as rank among big-five players. Assumption, not fitted: 0.35 strength units per standard deviation, reference 0.30. Used in the team view, best fit and the new "level" sort in Find.
- The season shown per player is the latest with 900+ minutes, so ranks are no longer computed against a handful of players early in a season.
- Sporting outcome of each transfer: matches in the two seasons after (any club): regular 20+, rotation 10-19, otherwise did not make it. Shown next to the price verdict.
- Player page: "Best fit" (clubs at the same level or a step up where he beats the current players in the role on something the squad needs, his place in the role, how often a step that size ends as a regular) and "Like him, but cheaper".
- Team view: report card for buys since 2022 (share good on price, share that became regulars, both verdicts per buy).
- Known: the sporting outcome barely differs between price verdicts (81-84 % regulars) and is too lenient; it counts any club and the sample is players with a value history. Step success is 86 % for small steps and 78 % for the largest. Squad role groups are incomplete where positions are coded differently.

## 2026-11-16 – Value on the day corrected; buy verdicts; team view

- Found and fixed a leak: `fm_transfers.market_value` is the value at crawl time, not on the day. `analysis/transfers.py` now takes the value on the day from the value history. Test 20 redone (the earlier table was wrong), fee model retrained: typical miss 45.5 % vs 42.4 % for the third-party value, rank 0.849 vs 0.838.
- Test 20 corrected result: the fee paid predicts the next fee best (0.59), Speider outcome model 0.55, third-party value on the day 0.50; Speider adds information beyond the fee, the third-party value almost none.
- Buy verdicts on the player page (five levels) from the walk-forward expected value in three years against the fee; this year's best and most expensive buys on the market page.
- Team view: squad profile per role against its own league, the three biggest gaps, and candidates for each (27 or younger, strong on that dimension, league at the team's level or a little below, within a price the squad has seen).
- Known: team profile and candidates use rank within the player's own league, not adjusted for league level; no tactics.

## 2026-11-16 – Test 20: judging buys by what happens next

- `analysis/buy_verdict_backtest.py`: walk-forward test of which estimate on the day predicts the next fee. Third-party value 0.72, Speider outcome model 0.69, Speider fee model 0.61, the fee paid 0.59.
- The gap between Speider value and third-party value sorts later sales: furthest above x1.76 of the year's typical, furthest below x0.57 (1,647 sales, every year 2018-2023).
- Momentum inputs removed from the value model and the path models. Player page text now states this result.

## 2026-11-16 – Ceiling removed; path anchored on realised outcomes of comparables

- The fixed value ceiling is gone: the record value has risen from 99m (2014) to 226m (2026), so a cap at today's record is wrong.
- The cause is handled instead. For each player and horizon, the 60 past player-years closest in age and value give the realised growth against the market (10th, 50th, 90th percentile). The shown path is half model, half these realised outcomes; the 50/50 weight is a choice, not yet backtested.
- Evidence behind it: players aged 21 or younger valued at 60m+ were typically worth x0.96 three years later (10-90 %: 0.49-2.23) and x0.81 after five; the model alone gave Yamal x3.3.
- The dotted line is now the realised median of those comparables, labelled "how similar players turned out".

## 2026-11-16 – Value ceiling and peer path by nearest neighbours

- No quantile of a value path may exceed the highest value the provider has ever published (226m): untouched up to 60 % of that, then bending towards it. Before this, growth multiples learned on cheap teenagers put Yamal at 358m in three years with a band to 845m.
- Peer path is the median of the 40 players closest in age and value today, replacing the age-and-value bins that fell back to age alone for rare players. Label changed to "peers of the same age and value".
- Known: the path of the very top players now leans on the ceiling rather than on evidence (too few comparable players); the momentum penalty on top players is still in.

## 2026-11-16 – Survivorship handled instead of hidden

- Corrected diagnosis: profiles and career lines cover players who have stopped (about four in five players per season have a profile). It is the value histories that exist almost only for players active today (86 % of those active now, 15 % of those last seen in 2022). So the value frame is the survivor sample, not the profile table.
- `analysis/dropout_career.py` (test 19): still playing by age and horizon from career lines. Regular at 30: 55 % still playing five years on; at 35: 16 %; at 39: 6 %.
- Still-playing model now trained on career lines (age, matches in the last three seasons, rating; monotone in age). Messi: 93 % next year, 18 % in 2031.
- Value path is a mixture: with probability 1 - p the player has stopped and is worth nothing, otherwise the survivor path applies. The shown quantiles are those of the mixture.
- "Typical" line compares with players of the same age and about the same value today, not age alone (expensive players lose more in relative terms).
- Momentum features are measured relative to the market-wide move that year.
- Check on elite players (value 25m+, age 26-29): three years on the provider's value is typically 0.42 of today's relative to the market (10-90 %: 0.15-0.97), and a two-year fall beforehand makes no difference (0.43 vs 0.42). The model gives Odegaard 0.24, so it still overweights momentum for top players.
- `analysis/dropout_true.py` is kept as a record of the stable-age-mix estimate; it measures "has a profile", not "still playing", and is not used.
- Decision 43 is replaced by this entry. Player page shows still-playing chances again; radar layout fixed.

## 2026-11-16 – Survivorship found; radar for playing style

- Found: the profile table only holds players who are in today's squads, so every player-year in the frame belongs to someone still active in 2026. "Still playing" rates and value growth are therefore biased upwards, most for older players (a 37-year-old in the data appears 60 % likely to play five years later). The dropout numbers in tests 9 and 18 carry the same bias.
- Removed the "chance of still playing" row from the player page until dropout can be measured on full historical squads with birth dates.
- Typical path is now by exact age instead of age band and is hidden from age 30, where the bias dominates. Calibration bands split into 29-32 and 33+. Still-playing model made monotone in age.
- Player page: radar of seven style dimensions with a similar player overlaid; tapping a name swaps the overlay.

## 2026-11-16 – Player types, "Speider recommends", players over 35

- Frame extended from age 35 to 45, so older players (Messi, Ronaldo, Modrić) get a value and a path. After the rebuild: Speider 49 % vs third party 45 % typical miss; under 23: 48 % vs 49 %.
- Player type per role (rule-based, from percentile profile): e.g. finisher, pressing forward, playmaker, ball winner, ball-playing defender. "All-rounder" when no group stands out.
- "Speider recommends" flag: age 26 or younger, 600+ minutes, market value 300k+, Speider value at least 30 % above market value and expected three-year value at least x1.15. 620 players.
- Find can filter on player type and on the flag; player landing has a "Speider recommends" carousel (reserve and youth sides left out of the carousel).

## 2026-11-16 – Charts, finder and player landing reworked

- Charts: readout above the plot instead of a tooltip, crosshair and markers that follow the pointer, smooth curves, animation when scrolled into view.
- Value path is a fan chart (2, 5 and 8 in 10 outcomes; inner bands assume a log-normal shape around the modelled 10/50/90 percentiles) and includes the Speider value back in time.
- Today's numbers start from the latest third-party value, not the mid-year one (fixes tile and history disagreeing).
- Find: sort by top-league chance, Speider value, expected growth or Speider above market; filter on role, nationality, league, club and any age range.
- Player landing: large search and carousels (expected growth, Speider above market, top-league chance).
- Eras: search dropdown no longer hidden behind the card; names link to the player page.
- Known issues: historical Speider value is in-sample for training years; the fee model overvalues older players with a low market value; country names are English in both languages.

## 2026-11-16 – Player page: Speider value, value path, profile

- `analysis/site_models.py`: fee-trained Speider value with interval, and a calibrated value path for 1 to 5 years per player (relative to the market, today's prices) with the chance of still playing.
- Out-of-time test on 3,387 transfers in 2025–26: typical miss 50 % for Speider vs 44 % for the third-party value (under 23: 49 % vs 49 %). Shown on the page as a separate estimate with this result stated.
- Player page now shows Speider value, third-party value, value in three years, the value path against a typical player of the same age, strengths and weaknesses, and the five most similar players by style.
- Find lists the Speider value. Page titles made plain.
- Known issues: percentiles are coarse early in a season (few players with 270+ minutes); horizons are separate models, so the path is lightly smoothed; similarity ignores league level.

## 2026-11-16 – First runnable local site

- `scripts/build_site.py` builds a static site in `data/site/` (git-ignored) that opens straight from disk, no server.
- `web/` holds the app (index.html, app.css, app.js), Norwegian and English from one translation table.
- Views: Find (young players outside the big five ranked by chance of reaching one within three years), Player (shrunk per-90 numbers with percentile in role, career, third-party market value as background), Eras (non-penalty goals per 90 against full squads back to 2001/02), Market (price index with projection, league strength).
- Only outputs that have passed their tests are shown. Speider's own value and price projection are not shown (gate 4 not passed).
- Known issue: `big_chance_created` is a season total in the source, not per 90; hidden in the UI until fixed in the loader.

## 2026-11-15

- Pre-study of the data foundation (`docs/pre-study.md`).
- Plan for own models (`docs/models.md`, 13 models) and evaluation protocol
  (`docs/evaluation.md`).
- FotMob ingestion: 4.17M statistic rows, 22,190 transfers with fees,
  19,242 player profiles (in progress).
- Loaders: `scripts/load_fotmob.py`, `scripts/load_profiles.py`.
- Test 1 shrinkage, test 2 price index (2b with age), test 3 league strength,
  test 4 career simulator (`analysis/`, results in `docs/results.md`).
- Decision log (`docs/decisions.md`).
- Platform UI with sample data (design canvas, not in the repository).
- Repository switched to English: docs, file names, CLI and script output.
- UI mockup now exists in Norwegian and English (design canvas).
- Test 5: price model v1 on fees (`analysis/price_model.py`). Cups excluded from league strength.
- SofaScore season-level ingestion started (browser, in progress).
- Test 6: price model v2 (`analysis/price_model_v2.py`), no gain over v1.
- Historical profile v0 (`analysis/historical_profile.py`).
- Test 7: price model v3 with career path features (`analysis/price_model_v3.py`).
- Test 7b: calibrated price intervals.
- More profiles (25,505) and SofaScore season statistics loaded (`scripts/load_sofascore.py`).
- Test 8 dropout, test 9 price model v4, test 10 sell-on sensitivity.
- Test 11: career curve with dropout (`analysis/career_curve_with_dropout.py`).
- Earlier the same day: data model, ESF and FotMob parsers, CLI, 17 tests.

## 2026-11-16

- All 48,339 FotMob profiles loaded; SofaScore season statistics for 95
  leagues and squad history back to 2001/02 loaded.
- Reran dropout, career simulator, career curve with dropout and price model
  v4 on the full data (`docs/results.md`).
- Test 12: historical profile v1 against full squads
  (`analysis/historical_profile_v1.py`).
- Test 13: player-conditioned growth model (`analysis/growth_model.py`).
- Test 14: per-player projection over 1–5 years (`analysis/player_projection.py`).
- Test 15: projection diagnosis and calibration (`analysis/projection_calibration.py`, `analysis/projection_v2.py`).
- Test 16: young-player projection on the wide sample (`analysis/projection_young.py`, `scripts/load_national.py`).
- Test 17 track-record check, test 18 merged calibrated projection (`analysis/track_record_check.py`, `analysis/projection_v3.py`, `analysis/build_wide_frame.py`).
- New logo (design system and UI mockup, not in the repository).
- SofaScore API answered 403 after an unpaced run; crawl stopped, 28 country
  categories left to scan.
