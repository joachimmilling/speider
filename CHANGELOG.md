# Changelog

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
- SofaScore API answered 403 after an unpaced run; crawl stopped, 28 country
  categories left to scan.
