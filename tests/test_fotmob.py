import json
from pathlib import Path

from speider.db import connect
from speider.ingest import load_fotmob_stat
from speider.sources import fotmob

SAMPLE = json.loads((Path(__file__).parent / "fixtures" / "fotmob_sample.json").read_text(encoding="utf-8"))


def test_url():
    assert fotmob.url(59, 30202, "total_tackle") == "https://data.fotmob.com/stats/59/season/30202/total_tackle.json"


def test_roles_from_first_position_code():
    assert [fotmob.role_of(p) for p in ([11], [36], [32], [66], [72, 74], [85], [107, 78], [105], [], None, [999])] == \
        ["GK", "CB", "FB", "DM", "CM", "AM", "W", "ST", None, None, None]


def test_parse_per_90_list():
    rows = fotmob.parse_stat_list(SAMPLE["total_tackle"], 59, "2026", "total_tackle")
    assert len(rows) == 3
    first = rows[0]
    assert (first["player_id"], first["value"], first["sub_value"], first["is_per_90"], first["role"]) == \
        ("fotmob:1", 4.5, 18, True, "CM")
    assert rows[2]["role"] is None and rows[2]["position_code"] is None


def test_totals_are_not_marked_per_90():
    rows = fotmob.parse_stat_list(SAMPLE["expected_goals"], 59, "2026", "expected_goals")
    assert rows[0]["is_per_90"] is False and rows[0]["value"] == 3.2


def test_empty_document():
    assert fotmob.parse_stat_list({}, 59, "2026", "rating") == []


def test_load_is_idempotent_and_long_format():
    con = connect(":memory:")
    for _ in range(2):
        load_fotmob_stat(con, SAMPLE["total_tackle"], 59, "2026", "total_tackle")
        load_fotmob_stat(con, SAMPLE["expected_goals"], 59, "2026", "expected_goals")
    assert con.execute("SELECT count(*) FROM player_stats").fetchone()[0] == 4
    assert con.execute("SELECT count(DISTINCT stat) FROM player_stats WHERE player_id = 'fotmob:1'").fetchone()[0] == 2
    con.close()
