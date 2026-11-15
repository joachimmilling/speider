-- Speider database schema (DuckDB).
-- One row per real-world thing; ids are prefixed with the source they came from
-- ("esf:12") so several sources can be joined in later without collisions.

CREATE TABLE IF NOT EXISTS teams (
    team_id        VARCHAR PRIMARY KEY,
    source         VARCHAR NOT NULL,
    name           VARCHAR NOT NULL,
    short_name     VARCHAR,
    league         VARCHAR,
    updated_at     TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    player_id      VARCHAR PRIMARY KEY,
    source         VARCHAR NOT NULL,
    first_name     VARCHAR,
    last_name      VARCHAR,
    display_name   VARCHAR NOT NULL,
    position       VARCHAR,          -- GK, DEF, MID, FWD
    team_id        VARCHAR,
    birth_date     DATE,
    nationality    VARCHAR,
    squad_number   INTEGER,
    status         VARCHAR,
    opta_code      VARCHAR,          -- keys for linking other sources later
    fiks_id        BIGINT,
    updated_at     TIMESTAMP NOT NULL
);

-- Season totals as they stood on the day we fetched them. Keeping every
-- snapshot is what lets us draw a curve over time later.
CREATE TABLE IF NOT EXISTS player_snapshots (
    player_id       VARCHAR NOT NULL,
    snapshot_date   DATE NOT NULL,
    season          VARCHAR NOT NULL,
    team_id         VARCHAR,
    minutes         INTEGER,
    goals           INTEGER,
    assists         INTEGER,
    clean_sheets    INTEGER,
    goals_conceded  INTEGER,
    own_goals       INTEGER,
    yellow_cards    INTEGER,
    red_cards       INTEGER,
    saves           INTEGER,
    penalties_saved INTEGER,
    penalties_missed INTEGER,
    fantasy_points  INTEGER,
    fantasy_cost    DOUBLE,          -- fantasy price, a popularity signal and not a market value
    selected_pct    DOUBLE,
    PRIMARY KEY (player_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS fixtures (
    fixture_id     VARCHAR PRIMARY KEY,
    source         VARCHAR NOT NULL,
    season         VARCHAR NOT NULL,
    round          INTEGER,
    kickoff        TIMESTAMP,
    home_team_id   VARCHAR,
    away_team_id   VARCHAR,
    home_score     INTEGER,
    away_score     INTEGER,
    finished       BOOLEAN
);

CREATE TABLE IF NOT EXISTS player_matches (
    player_id       VARCHAR NOT NULL,
    fixture_id      VARCHAR NOT NULL,
    season          VARCHAR NOT NULL,
    round           INTEGER,
    kickoff         TIMESTAMP,
    opponent_team_id VARCHAR,
    was_home        BOOLEAN,
    minutes         INTEGER,
    goals           INTEGER,
    assists         INTEGER,
    clean_sheets    INTEGER,
    goals_conceded  INTEGER,
    yellow_cards    INTEGER,
    red_cards       INTEGER,
    saves           INTEGER,
    fantasy_points  INTEGER,
    fantasy_cost    DOUBLE,
    PRIMARY KEY (player_id, fixture_id)
);

-- Earlier seasons, one row per player and season.
CREATE TABLE IF NOT EXISTS player_seasons (
    player_id       VARCHAR NOT NULL,
    season          VARCHAR NOT NULL,
    minutes         INTEGER,
    goals           INTEGER,
    assists         INTEGER,
    clean_sheets    INTEGER,
    goals_conceded  INTEGER,
    yellow_cards    INTEGER,
    red_cards       INTEGER,
    saves           INTEGER,
    fantasy_points  INTEGER,
    start_cost      DOUBLE,
    end_cost        DOUBLE,
    PRIMARY KEY (player_id, season)
);

CREATE TABLE IF NOT EXISTS fetch_log (
    fetched_at     TIMESTAMP NOT NULL,
    source         VARCHAR NOT NULL,
    what           VARCHAR NOT NULL,
    rows           INTEGER
);

-- Latest snapshot per player, with the first numbers Speider works out itself.
CREATE OR REPLACE VIEW player_current AS
WITH latest AS (
    SELECT *, row_number() OVER (PARTITION BY player_id ORDER BY snapshot_date DESC) AS rn
    FROM player_snapshots
),
team_minutes AS (
    SELECT team_id, snapshot_date, max(minutes) AS max_minutes
    FROM player_snapshots GROUP BY ALL
)
SELECT
    p.player_id, p.display_name, p.first_name, p.last_name, p.position,
    t.name AS team, t.league, p.birth_date,
    date_diff('year', p.birth_date, s.snapshot_date) AS age,
    s.season, s.snapshot_date, s.minutes, s.goals, s.assists,
    s.clean_sheets, s.goals_conceded, s.yellow_cards, s.red_cards, s.saves,
    s.fantasy_points, s.fantasy_cost, s.selected_pct,
    CASE WHEN s.minutes >= 90 THEN round(s.goals * 90.0 / s.minutes, 2) END AS goals_per_90,
    CASE WHEN s.minutes >= 90 THEN round(s.assists * 90.0 / s.minutes, 2) END AS assists_per_90,
    CASE WHEN s.minutes >= 90 THEN round((s.goals + s.assists) * 90.0 / s.minutes, 2) END AS goal_involvements_per_90,
    -- share of the minutes played by the most-used player in the same squad
    CASE WHEN tm.max_minutes > 0 THEN round(s.minutes * 1.0 / tm.max_minutes, 2) END AS minutes_share
FROM latest s
JOIN players p USING (player_id)
LEFT JOIN teams t ON t.team_id = s.team_id
LEFT JOIN team_minutes tm ON tm.team_id = s.team_id AND tm.snapshot_date = s.snapshot_date
WHERE s.rn = 1;
