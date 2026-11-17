# Open questions and known weaknesses

In priority order within each half. Move a line to `docs/lessons.md` when it is answered.

## Squad building

1. Does balance matter (a ball winner helping most where the team lacks one)? Not detectable with season aggregates (test 22). Needs match-level data: who played together and the result per match. Blocked on the paced SofaScore crawl.
2. The squad model is linear with 3,570 team seasons. Interactions are untested.
3. Outcome is goal difference from player goals and keeper totals, not league tables or points. No table data is loaded.
4. The squad model still picks its eleven by market value in fixed slots (4-2-3-1-like), while the pitch shows players by their own position. A formation-free eleven for the model is untested.
9. 3,806 players have no position code in `fm_players` (they default to central midfield). Possibly the same players as the ~3,800 without a value.
5. The Premier League shows 19 teams on the team page: clubs with under eight valued players in the data fall out (West Ham has 7 players listed). Squad coverage per club is not checked.
6. Collective attributes average all ten outfield players equally on every attribute; they should be weighted by role.
7. Keepers have no level.
8. Loans ending and free transfers without a row in the transfer table can still leave a player at the wrong club.

## Pricing

0. The form slope in the price rests on 413 test transfers and sits exactly on the adoption bar (test 27). Recheck when the winter window adds fees. Open: should the one-year value path use the nowcast too? Not tested.
1. The Speider value does not beat the third-party value on fees or the fee on the next fee. What would: wages, contract length at the time, injury history, match-level performance.
2. Injury history is missing. Step 1: availability from minutes share per season. Step 2: a real injury source (Transfermarkt), crawled slowly and kept local.
3. The backtest (test 20) and the site do not yet share model code: the site's transfer verdicts come from the backtest's outcome model (C2), the live player values from `analysis/site_models.py`.
4. The 50/50 blend of model and comparables is not tested.
5. About 3,800 players have no value. Cause not investigated.
6. Lewis-Skelly at 102m looks high. Not investigated.
7. Advice ("sell", "keep", "at the top") and "Speider recommends" are hand-set rules. `clubAct` gives a sell-type action to roughly a third of players.
8. The tail line above 40m is an extrapolation choice with almost no test data above 150m.
9. Player types and the seven attributes are hand-defined. Data-driven types and a type-by-age test are untested ideas.
10. Wages: no free source found.

## Data and plumbing

- Profiles: all 16,789 missing ones with matches since 2024/25 are loaded. About 16,000 players with older seasons only still have no profile.
- The Speider price of a player with almost no numbers moves with every retrain (Dowman 95m -> 104m after more profiles were added). The range shown should say so.
- Players without a 270-minute season are shown without level and attributes; their value path rests on age, value and career only (Dowman: upper outcome 396m in three years looks too wide).
- Injury history and match-level line-ups: FotMob match pages list unavailable players with injury type and both line-ups (checked on one 2022/23 match). Crawl planned for the big five leagues 2022/23-2026/27; pre-register the injury and squad-balance tests before running them.
- SofaScore returned 403 after an unpaced crawl. Resume slowly.
- Club and league logo URLs are unverified; logos only in the local build.
- Country names are English in the Norwegian UI.
- `analysis/growth_model.py` still has the old role mapping for 83-87.
- No GitHub remote yet (the owner creates an empty private repo first).
