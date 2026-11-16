# Changelog

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
