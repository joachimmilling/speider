"""Fee transfers with the third-party value on the day.

fm_transfers.market_value is NOT the value on the day: it is the player's value at crawl time (within about
5 % of his latest value for every transfer year). Using it as "value on the day" leaks the future. The value
on the day is the latest entry in the value history dated on or before the transfer.
"""
import numpy as np
import pandas as pd

SQL = """select t.player_id, t.name, t.date, year(t.date) yy, month(t.date) mo, t.from_name, t.to_name, t.to_id, t.fee,
                (select arg_max(m.value, m.date) from fm_mv m where m.player_id = t.player_id and m.date <= t.date and m.value > 0) mv
         from fm_transfers t where t.fee >= 50000 and not t.loan and not t.extension and year(t.date) >= 2016"""


def load(con) -> pd.DataFrame:
    t = con.execute(SQL).fetchdf()
    return t[t.mv.notna() & (t.mv > 0)].reset_index(drop=True)


LEVEL_EDGES = np.log([1e6, 5e6, 2e7])


def price_level(h_date, h_ratio, h_val, q_date, q_val, window=365):
    """The going rate: median log fee over market value among transfers in the `window` days strictly before each query date.
    (Also used with the model's forward errors in place of the raw ratio: test 33.)

    Returns (overall, blended); blended is halfway between the level in the query's value bracket and the overall
    level (test 30b). Fewer than 30 transfers overall gives 0, fewer than 20 in the bracket gives the overall level.
    """
    hd = np.asarray(h_date, dtype="datetime64[D]").astype(int); hr = np.asarray(h_ratio, float); hb = np.digitize(np.asarray(h_val, float), LEVEL_EDGES)
    qd = np.asarray(q_date, dtype="datetime64[D]").astype(int); qb = np.digitize(np.asarray(q_val, float), LEVEL_EDGES)
    all_, mix, cache = np.zeros(len(qd)), np.zeros(len(qd)), {}
    for i, key in enumerate(zip(qd.tolist(), qb.tolist())):
        if key not in cache:
            k = (hd < key[0]) & (hd >= key[0] - window); a = float(np.median(hr[k])) if k.sum() >= 30 else 0.0
            kb = k & (hb == key[1]); cache[key] = (a, 0.5 * a + 0.5 * (float(np.median(hr[kb])) if kb.sum() >= 20 else a))
        all_[i], mix[i] = cache[key]
    return all_, mix
