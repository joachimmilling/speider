"""Build the wide player-year table used by the projection (all ages) and cache it.

One row per player and year with a value: profile, career to date, track
record of club, league and nationality, season statistics where they exist,
and outcomes one to five years ahead. Written to data/frame_wide.pkl.
"""
import duckdb

from projection_young import frame

con = duckdb.connect("data/speider.duckdb", read_only=True)
b = frame(con, 16, 45)
b.to_pickle("data/frame_wide.pkl")
print(len(b), "player-years", b.y.min(), "-", b.y.max(), "columns", len(b.columns))
