# Working in this repository

Read this first, every session. Speider is run as a small research lab: every claim on the site traces back to a test,
and every test result is kept so the same ground is not covered twice.

## Before any work

1. Read `docs/lessons.md` (what has been learned, including what did not work) and `docs/open-questions.md` (what is not known, in priority order).
2. Read `docs/scoreboard.md` (where every model stands right now).
3. Skim the latest entries in `CHANGELOG.md` and the last tests in `docs/results.md`.

## The owner

- Joachim, Norwegian. Talk to him in Norwegian, short, with plain "you can / you cannot" conclusions and no jargon.
- Everything in the repository is in English: code, comments, docs, file names, commit messages, output.
- The site UI is in Norwegian and English. Design: system font, black and white, no borders, colour only as a signal. No emoji.
- Free and local only. This is a hobby project, not a business. Data from unofficial sources stays in `data/` (git-ignored) and is never committed.
- His email address is private. Commits use the noreply address in the git log.
- Work in large chunks without asking for a go-ahead at each step. Fix the cause in the data or the model instead of hiding a symptom.

## Method (details in `docs/lab.md`)

1. **Write the hypothesis first.** Before running anything, add the question, the expected result, the metric and what counts as "better" to `docs/results.md` under a new test number.
2. **Test forward in time only**, against a simple reference, on data the model has not seen (`docs/evaluation.md`).
3. **Record the result whatever it shows**, then add one line to `docs/lessons.md` and update `docs/open-questions.md`.
4. **A model change is not done until the scoreboard is rerun** (`python3 scripts/run_all.py`) and the row is committed. If a number gets worse, say so.
5. **A bug report from the owner is a lead, not a patch target.** Find the general cause, state whether it was the model, the data or the presentation, and check how many players it affects.
6. **One definition per model.** The site and the backtest must run the same model code. Where they still differ it is listed in `docs/open-questions.md`.
7. **Rules are labelled as rules.** Thresholds chosen by hand (advice, flags, player types) are not presented as tested models, in the docs or on the site.

## Commands

```bash
python3 scripts/run_all.py                # whole chain: frame, models, backtests, site, scoreboard
python3 scripts/run_all.py --from site_models
python3 scripts/scoreboard.py             # only rebuild docs/scoreboard.md from the result files
SITE_LOGOS=1 PYTHONPATH=analysis python3 scripts/build_site.py                           # local site in data/site (open index.html)
SITE_OUT=data/site_pub SITE_SHARDS=32 PYTHONPATH=analysis python3 scripts/build_site.py  # build for the private artifact
node --check web/app.js                   # always before building
```

## Where things are

| Path | What |
|---|---|
| `docs/lab.md` | The method in full, with the test template |
| `docs/lessons.md` | One line per lesson. Read before proposing anything |
| `docs/open-questions.md` | Prioritised unknowns and known weaknesses |
| `docs/scoreboard.md`, `docs/scoreboard_history.csv` | Current metrics, and one row per model change |
| `docs/results.md` | Every test in full, numbered |
| `docs/decisions.md` | Numbered decisions with the reason |
| `docs/evaluation.md` | Evaluation protocol |
| `analysis/` | Models and backtests. `scripts/` loaders, site build, chain |
| `web/` | The site (`index.html`, `app.css`, `app.js`, `flags.js`) |
| `data/` | Local only: database, result files, built site |

## Practical traps

- Strings in the translation table in `web/app.js` are single-quoted: never put an apostrophe inside one (add new strings with double quotes).
- `fm_transfers.market_value` is the value at crawl time, not on the day. Use `analysis/transfers.py`.
- Value histories exist almost only for players active today (a survivor sample). Dropout comes from career lines.
- Trees do not extrapolate. Check the most expensive and the youngest players after any change to a value model.
- Keep `CHANGELOG.md`, `docs/results.md` and `docs/decisions.md` updated in the same commit as the change.
