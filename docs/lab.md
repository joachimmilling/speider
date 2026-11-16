# How the lab works

Speider makes two kinds of claims: what a player is worth and will be worth, and what makes a team better.
Both are only as good as the tests behind them. This is the routine.

## The loop

1. **Question.** Taken from `docs/open-questions.md`, or added there first.
2. **Pre-registration.** A new numbered section in `docs/results.md`, written before the run, using the template below.
3. **Run.** A script in `analysis/` that writes `data/result_<name>.json`. No notebook-only results.
4. **Result.** Tables and a short reading, added under the pre-registration. The pre-registered text is not edited afterwards; corrections are added below it with a date.
5. **Lesson.** One line in `docs/lessons.md`. If the idea failed, say under what condition it would be worth trying again.
6. **Decision.** If the product changes, a numbered entry in `docs/decisions.md`.
7. **Scoreboard.** `python3 scripts/run_all.py`, commit the new row in `docs/scoreboard_history.csv`.

## Template for a test

```
## Test N: <question as a question>

Hypothesis: <what we expect and why>
Data: <rows, years, filters>
Split: <train to year T, test after>
Metric: <one primary metric>, reference: <the simple alternative>
Counts as better: <threshold decided now>
Could mislead us: <leaks, survivorship, small samples>

Result (date): <table>
Reading: <what it means, what it does not mean>
Lesson: <the line that goes into lessons.md>
```

## Standing rules

- Forward in time only. No random splits.
- Always a reference next to the number. Not beating it is a result.
- Report per group where it matters: age, role, league level, price bracket.
- Small samples are named as such (n next to every number below about 100).
- A change made because one player looked wrong is a hypothesis about a general fault: say how many players it moves, and check the scoreboard.
- Choices that cannot be tested with the data at hand (how to extrapolate beyond the data, thresholds in advice) are written down as choices.
- The site never shows a number from a model whose test has not been rerun since the model changed.

## Reference numbers to beat

See `docs/scoreboard.md`. The references that matter: the third-party market value on the day (for fees),
the fee itself (for the next fee), last season's goal difference and the value of the eleven most valuable players (for teams).
