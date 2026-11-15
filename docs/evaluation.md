# Evaluation protocol

Written before the models. Not changed after seeing results without logging
the change at the bottom.

## Ground rules

1. **Forward in time only.** Train on everything before date T, test on what
   happens after. Never a random split.
2. **No leakage.** A model only sees what was known on the day. Third-party
   market values (Transfermarkt, SofaScore, SciSports) are never inputs.
3. **Always a reference.** Every number is reported next to a simple
   reference. If we do not beat it, we say so.
4. **Uncertainty is shown.** Every estimate has an interval, and the interval
   is tested: the 80 % interval should contain the truth about 80 % of the time.
5. **Results per group.** Role, age, league level. A good average can hide a
   model that is useless for centre-backs.

## Tests per layer

### Quality
- Predict next season's numbers per statistic. Metrics: correlation and error.
- Reference: last season's raw numbers.
- For league switchers: predict numbers in the new league. Reference: no translation.

### Value
- Predict the fee paid for transfers after T. Metrics: median percentage error
  and rank correlation.
- References: (a) third-party market value the day before, (b) age + league + position.
- Clearly beating (a) is unlikely and not the bar. The bar is to be on par
  without having seen it, and to be able to explain the differences.

### "Underpriced"
The real test. At each T the model lists players it considers underpriced.
Two to three years later we check:
- Did they move to a stronger league more often than equally priced players?
- Did their market value rise more?
- Were they sold for more?
Reference: a random sample with the same age, league and price.

### Good and bad buys
- For purchases after T: did the model's verdict on signing day show up in
  minutes and value change two years later?

## Stop rules

- Quality does not beat raw numbers → stop, no value model on top.
- League translation does not beat "no translation" → no cross-league
  comparison in the product.
- The "underpriced" list does not beat a random sample → the feature is not shown.

## Change log

- 2026-11-15: First version.
