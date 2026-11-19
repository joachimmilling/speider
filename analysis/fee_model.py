"""The fee model: one definition, used by the site (site_models.py) and by the tests.

Target: log fee over the third-party value on the day, measured against the level of the fee's own calendar year (test 30c).
Prediction: model + value + the going rate of the previous 365 days in the value bracket (test 30b).
Inputs: age, career and season statistics, the value, availability from match line-ups (test 28); optionally buyer and seller tier (test 31).
The model is the mean of bootstrap fits on rows in a fixed order (test 31b).
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor as HGBR

from buyers import club_tiers
from projection_v3 import FEATS as _FEATS, KW
from transfers import LEVEL_EDGES, load, price_level

FEATS = [f for f in _FEATS if f not in ("mom1", "mom2")]
PF = [f for f in dict.fromkeys(FEATS + ["age"]) if f != "lv"] + ["val"]
AV = ["starts_sh", "min_sh", "absent_sh", "bench_sh"]
PFA = PF + AV
PFB = PFA + ["buy_tier", "sell_tier"]


class Bag:
    """Mean of n tree models, each fitted on a bootstrap sample of the rows: steadier than one model."""

    def __init__(self, n=25, **kw): self.n, self.kw = n, kw

    def fit(self, X, y):
        X, y, rs = pd.DataFrame(X).astype(float).values, np.asarray(y, float), np.random.RandomState(0); self.models = []
        for i in range(self.n):
            ix = rs.randint(0, len(y), len(y)); self.models.append(HGBR(**{**self.kw, "random_state": i}).fit(X[ix], y[ix]))
        return self

    def predict(self, X):
        X = pd.DataFrame(X).astype(float).values; return np.mean([m_.predict(X) for m_ in self.models], axis=0)


def frame(con, b):
    """Fee transfers with every model input. Returns (m, av, ct): transfers, availability per player-season, club tiers per year."""
    t = load(con).drop(columns=["name"])          # value on the day from the value history, not the crawl-time field
    t["y"] = np.where(t.mo >= 6, t.yy, t.yy - 1)
    m = t.merge(b, on=["player_id", "y"])
    from availability import table
    av = table(con); av = av.sort_values(["squad", "player_id", "ey"], kind="stable").groupby(["player_id", "ey"], as_index=False).last()
    av = av[av.squad + av.inj >= 5][["player_id", "ey"] + AV].rename(columns={"ey": "y"})
    m = m.merge(av, on=["player_id", "y"], how="left")
    ct = club_tiers(b[b.team_id.notna()], ["team_id", "y"])[["team_id", "y", "tier"]]
    fid = con.execute("select player_id, date, any_value(from_id) from_id from fm_transfers group by 1,2").fetchdf(); fid["date"] = pd.to_datetime(fid.date).astype(m.date.dtype)
    m = m.merge(fid, on=["player_id", "date"], how="left")
    m = m.merge(ct.rename(columns={"team_id": "to_id", "tier": "buy_tier"}), on=["to_id", "y"], how="left").merge(ct.rename(columns={"team_id": "from_id", "tier": "sell_tier"}), on=["from_id", "y"], how="left")
    m = m.sort_values(["date", "player_id", "fee"], kind="stable").reset_index(drop=True)   # query order varies between runs; the fit must not
    m["val"] = np.log(m.mv); m["target"] = np.log(m.fee); m["raw"] = m.target - m.val
    m["lev"] = price_level(m.date, m.raw, m.val, m.date, m.val)[1]
    band = np.digitize(m.val.values, LEVEL_EDGES); ya = m.raw.groupby(m.yy).transform("median")
    m["ratio"] = m.raw - (0.5 * ya + 0.5 * m.raw.groupby([m.yy, band]).transform("median"))
    return m, av, ct


def level_at(m, dates, vals):
    """The going rate at the given dates for the given log values, from the transfers in m."""
    return price_level(m.date, m.raw, m.val, dates, vals)[1]


def fit(tr, quantile=0.5, feats=PFA, n=25, target="ratio"):
    mono = [1 if f == "buy_tier" else 0 for f in feats] if "buy_tier" in feats else None   # the price never falls with the buyer's tier
    return Bag(n=n, loss="quantile", quantile=quantile, **KW, monotonic_cst=mono).fit(tr[feats], tr[target])


def predict(model, X, feats=PFA):
    """Log fee. X needs the inputs, `val` and `lev`."""
    return model.predict(X[feats]) + X.val.values + X.lev.values
