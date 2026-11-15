"""Test 10: how much would hidden sell-on clauses move the "underpriced" list?

Assumption (not data): young players (under 23) sold from weaker leagues carry
a sell-on clause worth 10 or 20 % of the headline fee. Those fees are scaled
up, the price model is refitted, and the list of transfers paid furthest below
Speider's estimate is compared with the unadjusted list.

Run price_model_v4.py with SELLON=0, 0.1 and 0.2 first.
"""
import numpy as np
import pandas as pd

base = pd.read_csv("data/result_price_model_v4_test_sellon0.csv")
base["ratio"] = np.exp(base.pred - base.y_log)
print(f"test transfers {len(base)}, in the assumed sell-on segment {int(base.sellon_segment.sum())} ({100*base.sellon_segment.mean():.0f} %)")
top = lambda d, n: set(d.sort_values("ratio", ascending=False).head(n).apply(lambda r: (r.player_id, r.date), axis=1))
for s in (10, 20):
    d = pd.read_csv(f"data/result_price_model_v4_test_sellon{s}.csv")
    d["ratio"] = np.exp(d.pred - d.y_log)
    j = base.merge(d, on=["player_id", "date"], suffixes=("", "_s"))
    seg = j[j.sellon_segment]
    print(f"sell-on {s} %: rank correlation of the ratio {j.ratio.corr(j.ratio_s, method='spearman'):.3f}; "
          f"top-100 overlap {len(top(base,100) & top(d,100))}/100, top-300 overlap {len(top(base,300) & top(d,300))}/300; "
          f"segment share in top 300: {100*base.sort_values('ratio',ascending=False).head(300).sellon_segment.mean():.0f} % -> {100*d.sort_values('ratio',ascending=False).head(300).sellon_segment.mean():.0f} %; "
          f"median ratio in segment {seg.ratio.median():.2f} -> {seg.ratio_s.median():.2f}")
