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
- Earlier the same day: data model, ESF and FotMob parsers, CLI, 17 tests.
