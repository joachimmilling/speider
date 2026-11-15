# Decisions

Choices made, why, and what was rejected. Newest last. The test results behind
them are in `results.md`.

| # | Date | Decision | Why | Rejected |
|---|------|----------|-----|----------|
| 1 | 2026-11-15 | Scope is every league, not Eliteserien | Owner: an underpriced player in Bosnia is as interesting as one in Norway | Eliteserien focus (an early mistake) |
| 2 | 2026-11-15 | Free data, local private use. Data never in the repository | Not a business. Unofficial sources | Paid data until value is shown |
| 3 | 2026-11-15 | The evaluation protocol is written before the models | Avoid fitting the test to the result | – |
| 4 | 2026-11-15 | FotMob is the base source. SofaScore only where FotMob is missing | Same underlying data (xG sum 536.9 vs 536.0). FotMob shares one id across statistics, transfers and profiles | Using both as a cross-check |
| 5 | 2026-11-15 | Ground truth for price is FotMob's transfer list | Fee + player id, 22,190 transfers from 2015 | transfermarkt-datasets (needs name matching) |
| 6 | 2026-11-15 | Third-party market value is never an input to the price model | Leakage. Used as an opponent and as a career-path measure | – |
| 7 | 2026-11-15 | Ingestion runs in a browser, stored in browser storage, exported to `data/raw/` | Scripts cannot reach the sources from the work environment | Scripts (not yet tested on the owner's machine) |
| 8 | 2026-11-15 | All per-90 numbers are shrunk | Test 1: better on 17 of 17 statistics | Raw numbers |
| 9 | 2026-11-15 | Cross-league comparison is in | Test 3: better on 14 of 15 | – |
| 10 | 2026-11-15 | Price index v1 without performance controls | The version with performance was unstable before 2020 | Index with performance (to be revisited) |
| 11 | 2026-11-15 | Careers are simulated by chaining one-year transitions | Test 4: halves the error over ten years, interval is calibrated | Requiring whole careers in the data |
| 12 | 2026-11-15 | Simulator state is age + level | Direction last year added nothing | Direction as state |
| 13 | 2026-11-15 | Two data tiers: full profile and historical profile | Detail exists from 2014/16, simple numbers from 2002 | Modern data only |
| 14 | 2026-11-15 | Value is shown both in today's prices and with a projected price index | Owner: today's price level alone is not enough | Today's prices only |
| 15 | 2026-11-15 | A purchase gets two verdicts: on signing day and in hindsight | Must be able to judge transfers happening now | Hindsight only |
| 16 | 2026-11-15 | Clauses are priced as options with the simulator | That is how real deals work | Ignoring clauses |
| 17 | 2026-11-15 | Age is in the price index | Test 2b: growth moves from 3.0 to 3.3 % a year | Index without age |
| 18 | 2026-11-15 | Everything in the repository is in English | Owner's requirement | Norwegian docs |

| 19 | 2026-11-15 | The UI ships in Norwegian and English | Owner's requirement. All UI strings go through one translation table; numbers and currency follow the locale | Single-language UI |

| 20 | 2026-11-15 | Price model v1 is not shipped as "Speider says" yet | Test 5: median error 76 % vs 59 % for market value; gate 4 not passed | Showing v1 estimates as final |
| 21 | 2026-11-15 | Cups are excluded from league data | They appeared as leagues and distorted the ranking | – |

## Open questions

- Dropout as its own state in the simulator (survivorship bias).
- Team strength separated from league strength (club Elo).
- How much sell-on clauses shift the ground truth for young players from small leagues.
- Wages: no free source found.
- Whether scripts can reach the sources directly from the owner's machine (`scripts/check_access.py`).
