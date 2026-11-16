# Speider

What football players are really worth. A hobby project: a local player database and our own models for quality, transfer value and future value, in any league.

Speider is built for the questions scouts and agents ask:

- What is this player really worth, and is the asking price a good or bad buy?
- What is he expected to be worth in one, three or eight years?
- Who is underpriced, in leagues few people watch?
- Who resembles this player but is younger or cheaper?

## Status

| Part | Status |
|---|---|
| Local database (DuckDB) | Done |
| FotMob season statistics, transfers with fees, player profiles | Loaded locally, profiles still downloading |
| Shrinkage for low-minute players | Tested, in |
| League strength from league switchers | Tested, in |
| Transfer price index with projection | First version |
| Career simulator (chained one-year transitions) | First version |
| Quality per role, fee-trained price model, "underpriced" backtest | Not started |
| Web app | Design mockup exists |

Working method and the reading order for a new session: [AGENTS.md](AGENTS.md). Current numbers: [docs/scoreboard.md](docs/scoreboard.md).

Start with [docs/plan.md](docs/plan.md). Test results are in [docs/results.md](docs/results.md), decisions in [docs/decisions.md](docs/decisions.md), planned models in [docs/models.md](docs/models.md).

## Getting started

Requires Python 3.10 or newer.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install numpy pandas

# Load a FotMob export and player profiles into data/speider.duckdb
python3 scripts/load_fotmob.py data/raw/fotmob/export-YYYYMMDD.ndjson.gz
python3 scripts/load_profiles.py data/raw/fotmob/profiler-*.ndjson.gz

# Run the tests behind docs/results.md
python3 analysis/shrinkage.py
python3 analysis/league_strength.py
python3 analysis/price_index.py
PYTHONPATH=analysis python3 analysis/price_index_age.py
python3 analysis/career_simulator.py
```

The exports are collected through a browser session (see [docs/pre-study.md](docs/pre-study.md)); plain scripts could not reach the sources from the development environment. The older `speider fetch` command covers Eliteserien Fantasy and FotMob season lists for one league.

## Data and terms

The repository contains code only. No third-party data is committed, and `data/` is ignored. Read [docs/data-sources.md](docs/data-sources.md) before using Speider for anything other than private exploration: the main sources are unofficial.

## Layout

```
src/speider/     package: schema, DuckDB access, source parsers, CLI
scripts/         loaders for browser exports, access check
analysis/        model tests; each prints the numbers quoted in docs/results.md
docs/            plan, pre-study, models, evaluation protocol, results, decisions
tests/           tests against invented sample data
```

## Tests

```bash
pytest
```

## License

The code is MIT licensed. The license does not cover the data you fetch.
