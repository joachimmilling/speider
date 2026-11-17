# Changelog

## All missing profiles loaded, match crawl started, tests 28 and 29 registered

- The remaining 10,564 profiles are loaded (`profiler-5.ndjson.gz` holds all 16,789 from this download). 65,128 profiles in all; the site has 38,126 players, 3,672 of them without a 270-minute season.
- Fee model on the larger test set (3,595 transfers): typical miss 46.3 % against 43.2 % for the market value alone.
- Tests 28 (injury history) and 29 (line-up balance) are written down in `docs/results.md` before the data is in. The match crawl for the big five leagues, 2022/23 to 2026/27 (7,583 finished matches), is running in the browser.

## More profiles, current club and injury from the profile, low-minute players on the site

- 6,225 missing profiles downloaded (players active this season, Max Dowman among them) into `data/raw/fotmob/profiler-4.ndjson.gz`; the rest is being downloaded.
- `scripts/load_profiles.py`: new columns `cur_team_id`, `cur_team`, `injury`, `status` (profiles from 2026-11-17); later files win.
- `scripts/build_site.py`: players with a market value but no season of 270 league minutes are shown (2,068); the profile's current club wins over season rows and transfers; current injury in the shard (`inj`).
- Player page: "Injured now" tag; an injured player is not told to find playing time elsewhere.
- Site now has 35,285 players (was 32,010).

## Form in the price (test 27), form cell, "like him but better", attributes beside the pitch

- Test 27 (`analysis/form_slope_test.py`): one slope (0.60) for running form on out-of-fold errors; adopted. The Speider price and its range are multiplied by exp(0.60 x form excess) in `scripts/build_site.py`.
- Player page: "Form this season" is a verdict cell (lift in expected value, effect on the price, minutes, rating) instead of a line among the facts. New carousel "Like him, but better" after "Like him, but cheaper" (`better` in the shards).
- Team page: the verdict and the team's attributes sit beside the pitch (below it on a phone) and update with every sale and signing.

## Form this season, tests 25 and 26, leak fix in the team tests

- Tests 25 and 26: the season in progress does not improve fee prediction (trees, a two-input line, a scaled nowcast). The Speider price is unchanged.
- `analysis/form_nowcast.py`: where the third-party value is heading by the summer given the running season (tested: R2 0.27 vs 0.15). Shown on the player page ("Form this season") and as a sort in the finder (field 24 in `players.js`, `form` in the shards).
- Fixed a leak: the team tests used the market value at the end of the season being predicted. Squad model correlation 0.61 (was 0.65); coefficients and site text updated.
- New: `analysis/current_season.py`, `analysis/current_season_test.py`, `analysis/form_adjust_test.py`.

## Today's club, sided eleven, sell from the pitch, tests 23 and 24

- `scripts/build_site.py`: today's club is the latest senior season row with any minutes, then the latest transfer since June (Gabriel Jesus is at Barcelona, Martinelli at Al Hilal; Saliba stays at Arsenal despite a reserve match).
- Test 23: the eleven now takes one left and one right full-back and wide player; prediction unchanged (0.649 vs 0.650). Site and squad model updated.
- Team page: a tap on a player on the pitch opens a menu to sell him (or undo a signing) or open his page.
- Test 24 (`analysis/form_fee_test.py`): performance inputs improve the fee model by 1.6 points; change in form adds nothing on top; the current season is not an input.

## Pitch as a depth chart

- Team page: the pitch is now one card per position (left and right for full-backs and wide players) listing everyone who plays there, starters in bold first, with the chosen tag and a signal dot per player. Short money format on the cards.

## Pitch without a fixed formation

- Team page: the whole squad is placed where each player plays most (line from the role, side from the provider's position code, new field 23 in `players.js`). No fixed formation; the eleven the model counts as starters are drawn in full, the rest as names.

## Lab routine, scoreboard, squad on a pitch

- `AGENTS.md` (read first every session), `docs/lab.md` (method and test template), `docs/lessons.md`, `docs/open-questions.md`. Decision 46.
- `scripts/run_all.py` runs the whole chain; `scripts/scoreboard.py` writes `docs/scoreboard.md` and appends to `docs/scoreboard_history.csv`.
- Test 20 rerun with the fee model as the site runs it (ratio target, tail line): no measurable change on the buy test (variants B2, B3, C3).
- Team page: the best eleven drawn on a pitch (4-2-3-1) with second choices, and a choice of tag per player: Speider value, peak value, level, age, growth, contract, advice.
- Corrected: the squad model was tested on 1,071 team seasons, not 252.

## Squad model (test 22) and tail treatment for the most expensive players

- `analysis/squad_model.py`: expected goal difference from the value and level of the best eleven, depth, age and last season; out-of-time correlation 0.65 (R2 0.42). Coefficients shipped in `market.js` (`squad`).
- Team page: expected goal difference over the season and league rank, before and after sales and signings, with what moves the number. The best eleven is now picked by market value. Collective attributes stay as a description.
- `analysis/site_models.py`: above 40m the fee and growth models hand over to a line fitted on the expensive end. The largest expected peak falls from 605m to 338m.

## Team attributes, expected peak value, test 21

- Team page: collective attributes (mean of the ten outfield starters on each of the seven dimensions) with rank in the league; a signing is counted as a starter and the verdict weighs the change by where the team is weakest.
- Finder: sort by expected peak value (highest point of the median path, with the year). New fields 21-22 in `players.js`.
- Test 21 (`analysis/team_strength_backtest.py`): level of the best eleven vs goal difference, correlation 0.45; value of the top eleven 0.59. See `docs/results.md`.

## Squad builder answers whether the team gets better

- Team page: new tiles for the best eleven (average level of ten outfield players by role slots) and depth (second choices), with the change after sales and signings.
- A verdict card says per move whether the player makes the best eleven, whom he displaces, or who takes over after a sale. Level-based only; no tactics or chemistry.

## Fee model learns the ratio to market value; advice counts the pitch first

- `analysis/site_models.py`: the Speider value models now predict the log ratio of fee to third-party value instead of the fee itself. Tree models cannot extrapolate, so the old target capped out near the largest fees seen and marked every 100m+ player as overpriced (median Speider/market 0.68 above 100m; now 1.21). Out-of-time miss 44.9 % (was 45.5 %), rank 0.852 (was 0.849).
- Player page: the "ahead" cell shows expected value in three years and is coloured by how the player does against peers of the same age and value, not by raw direction.
- Advice: new head "At the top" for regulars at a high level with no stronger club available; club action "Keep" for regulars at level 70+ (and first-choice keepers) even when resale value falls with age.

## 2026-11-16 – Squad builder, club advice per player, minutes-based sporting verdict, real flags

- Team view: full squad by role with level, value and Speider's advice to the club per player (sell now, extend or sell, sell or loan out, sell on an offer, keep and extend, keep). Sell and sign players to see profile, gaps, squad value and net spend change. Nothing is saved.
- Player page: club picker lists who is in the role at that club and can drop him into its squad; price cell shows the Speider price coloured by the assessment; advice to the current club uses the same rule set as the squad table.
- Sporting verdict uses league minutes for the buying club (regular 1,500+ in a season), matches only as fallback. Regular share is now 54-59 % by price verdict and 63 / 59 / 55 / 44 % from a step down to the largest step up. Norgaard at Arsenal: 360 minutes, did not make it.
- The club shown is today's club even when the numbers come from last season at another club (Konsa, Guimaraes).
- No injury data: a club's two most valuable players in a role are treated as regulars even with few minutes, and the text says so.
- Flags are real drawings from the flag-icons package (MIT), 206 countries, loaded on demand from web/flags.js.

## 2026-11-16 – Role mapping fixed, similarity on style and level, club fit check

- Role mapping was wrong for wide attackers: position codes 83 and 87 are the wide players of the attacking-midfield line, not central attacking midfielders. Wingers went from 1,814 to 4,237 players; Saka, Martinelli, Trossard and Vinicius are wingers now. This was why squads had too few players per role.
- Similar players are picked on the league-adjusted dimensions with the level counted three times one dimension, so a Bundesliga winger is no longer compared with a Serie C one. "Like him, but cheaper" uses the same neighbours.
- Player page: basic facts row, drawn flags (62 countries, 74 % of players; emblems left out), similar-player panel compares price and facts, level explained as "better than N % in the same role in the big five leagues", and a club picker under Speider's advice that shows the fit with any club.
- Club and league marks are initials; a local build with SITE_LOGOS=1 loads crests from the source's image server (URL pattern not verified from this environment; falls back to initials).

## 2026-11-16 – Player page redesigned; Speider's advice

- The page now answers, in order: who he is (one generated sentence), level, price, direction and potential (four verdict cells), Speider's advice, strengths and weaknesses on the common scale, playing style against similar players, where he fits, value ahead, transfers. Per-90 numbers, career and third-party value sit under "The numbers behind it".
- Speider's advice: rule-based reading of playing time, place in the squad by value, value path and its peak, contract length and the fit list. Five outcomes (last big contract, find playing time, ready for the next step, stay one more year, stay but listen to offers) with reasons and one line each for player and agent, current club and buyer. Rules, not a tested model.

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
