import json
from datetime import date
from pathlib import Path

import pytest

from speider import cli
from speider.db import connect
from speider.ingest import load_esf_bootstrap, load_esf_summary
from speider.sources import esf

SAMPLE = json.loads((Path(__file__).parent / "fixtures" / "esf_sample.json").read_text(encoding="utf-8"))


@pytest.fixture
def con():
    connection = connect(":memory:")
    load_esf_bootstrap(connection, SAMPLE["bootstrap"], SAMPLE["fixtures"], today=date(2026, 11, 15))
    load_esf_summary(connection, 1, SAMPLE["element_summary_1"], esf.season_of(SAMPLE["bootstrap"]))
    yield connection
    connection.close()


def test_season_comes_from_first_round():
    assert esf.season_of(SAMPLE["bootstrap"]) == "2026"


def test_loads_players_and_skips_removed(con):
    assert con.execute("SELECT count(*) FROM players").fetchone()[0] == 5
    assert con.execute("SELECT count(*) FROM players WHERE last_name = 'Spiller'").fetchone()[0] == 0


def test_teams_outside_the_game_have_no_league(con):
    leagues = dict(con.execute("SELECT name, league FROM teams").fetchall())
    assert leagues == {"Eksempel FK": "Eliteserien", "Prøve IL": "Eliteserien", "Utenfor BK": None}


def test_positions_cost_and_known_name(con):
    row = con.execute("SELECT position, fantasy_cost FROM player_current WHERE player_id = 'esf:1'").fetchone()
    assert row == ("DEF", 6.5)
    assert con.execute("SELECT display_name FROM players WHERE player_id = 'esf:5'").fetchone()[0] == "Kladden"


def test_per_90_and_minutes_share(con):
    row = con.execute(
        "SELECT goals_per_90, assists_per_90, goal_involvements_per_90, minutes_share "
        "FROM player_current WHERE player_id = 'esf:2'").fetchone()
    assert row == (1.0, 0.2, 1.2, 0.5)


def test_per_90_is_empty_below_one_full_match(con):
    row = con.execute("SELECT goals_per_90 FROM player_current WHERE player_id = 'esf:3'").fetchone()
    assert row == (None,)


def test_age_is_unknown_when_the_source_has_no_birth_date(con):
    assert con.execute("SELECT count(*) FROM player_current WHERE age IS NOT NULL").fetchone()[0] == 0


def test_a_second_fetch_adds_a_snapshot_not_a_duplicate_player(con):
    load_esf_bootstrap(con, SAMPLE["bootstrap"], today=date(2026, 11, 16))
    assert con.execute("SELECT count(*) FROM players").fetchone()[0] == 5
    assert con.execute("SELECT count(*) FROM player_snapshots WHERE player_id = 'esf:1'").fetchone()[0] == 2
    assert con.execute("SELECT snapshot_date FROM player_current WHERE player_id = 'esf:1'").fetchone()[0] == date(2026, 11, 16)


def test_same_day_fetch_replaces_the_snapshot(con):
    load_esf_bootstrap(con, SAMPLE["bootstrap"], today=date(2026, 11, 15))
    assert con.execute("SELECT count(*) FROM player_snapshots WHERE player_id = 'esf:1'").fetchone()[0] == 1


def test_fixtures_and_match_log(con):
    assert con.execute("SELECT home_score, away_score, finished FROM fixtures WHERE fixture_id = 'esf:2026:1'").fetchone() == (2, 1, True)
    match = con.execute("SELECT fixture_id, minutes, goals, opponent_team_id, fantasy_cost FROM player_matches").fetchone()
    assert match == ("esf:2026:1", 90, 1, "esf:2", 6.5)
    assert con.execute("SELECT season, minutes, end_cost FROM player_seasons").fetchone() == ("2025", 2100, 6.0)


def test_cli_top_and_player(tmp_path, capsys):
    db = tmp_path / "t.duckdb"
    connection = connect(db)
    load_esf_bootstrap(connection, SAMPLE["bootstrap"], today=date(2026, 11, 15))
    connection.close()
    assert cli.main(["--db", str(db), "top", "--metric", "goals_per_90"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[1].startswith("Prøve")
    assert cli.main(["--db", str(db), "player", "jonas"]) == 0
    assert "Eksempel FK" in capsys.readouterr().out
    assert cli.main(["--db", str(db), "player", "finnesikke"]) == 1
