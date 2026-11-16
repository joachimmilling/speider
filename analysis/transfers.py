"""Fee transfers with the third-party value on the day.

fm_transfers.market_value is NOT the value on the day: it is the player's value at crawl time (within about
5 % of his latest value for every transfer year). Using it as "value on the day" leaks the future. The value
on the day is the latest entry in the value history dated on or before the transfer.
"""
import pandas as pd

SQL = """select t.player_id, t.name, t.date, year(t.date) yy, month(t.date) mo, t.from_name, t.to_name, t.to_id, t.fee,
                (select arg_max(m.value, m.date) from fm_mv m where m.player_id = t.player_id and m.date <= t.date and m.value > 0) mv
         from fm_transfers t where t.fee >= 50000 and not t.loan and not t.extension and year(t.date) >= 2016"""


def load(con) -> pd.DataFrame:
    t = con.execute(SQL).fetchdf()
    return t[t.mv.notna() & (t.mv > 0)].reset_index(drop=True)
