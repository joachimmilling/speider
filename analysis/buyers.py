"""Buyer tiers: one definition, used by the tests, the site models and the site build (test 31)."""
import numpy as np
import pandas as pd

TIER_RANKS = [20, 60, 150, 400]          # tier 5: rank 1-20, 4: 21-60, 3: 61-150, 2: 151-400, 1: the rest
TIERS = [1, 2, 3, 4, 5]


def tier_of_rank(rank):
    return 5 - np.digitize(np.asarray(rank, float), TIER_RANKS, right=True)


def club_tiers(df: pd.DataFrame, by: list[str], lv: str = "lv") -> pd.DataFrame:
    """Club quality q = mean log value of the eleven most valuable players (at least eight valued), ranked within `by[1:]`."""
    q = df[df[lv].notna()].groupby(by)[lv].apply(lambda x: x.nlargest(11).mean() if len(x) >= 8 else np.nan).rename("q").reset_index().dropna()
    q["rank"] = q.groupby(by[1:]).q.rank(ascending=False, method="first") if len(by) > 1 else q.q.rank(ascending=False, method="first")
    q["tier"] = tier_of_rank(q["rank"])
    return q
