-- ============================================================
-- Cricbuzz LiveStats  –  MySQL Schema
-- Run via:  python -m database.init_db
-- ============================================================

CREATE TABLE IF NOT EXISTS teams (
    team_id    VARCHAR(20)  NOT NULL,
    team_name  VARCHAR(100) NOT NULL,
    team_short VARCHAR(10)  DEFAULT NULL,
    country    VARCHAR(100) DEFAULT NULL,
    team_type  VARCHAR(50)  DEFAULT NULL,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id),
    INDEX idx_teams_country (country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS venues (
    venue_id   VARCHAR(20)  NOT NULL,
    venue_name VARCHAR(200) NOT NULL,
    city       VARCHAR(100) DEFAULT NULL,
    country    VARCHAR(100) DEFAULT NULL,
    capacity   INT          DEFAULT 0,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (venue_id),
    INDEX idx_venues_country (country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS players (
    player_id     VARCHAR(20)  NOT NULL,
    player_name   VARCHAR(150) NOT NULL,
    country       VARCHAR(100) DEFAULT NULL,
    batting_style VARCHAR(100) DEFAULT NULL,
    bowling_style VARCHAR(100) DEFAULT NULL,
    playing_role  VARCHAR(50)  DEFAULT NULL,
    date_of_birth DATE         DEFAULT NULL,
    team_id       VARCHAR(20)  DEFAULT NULL,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id),
    INDEX idx_players_country (country),
    INDEX idx_players_role    (playing_role),
    INDEX idx_players_team    (team_id),
    CONSTRAINT fk_players_team FOREIGN KEY (team_id)
        REFERENCES teams(team_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS matches (
    match_id       VARCHAR(30)  NOT NULL,
    description    VARCHAR(200) DEFAULT NULL,
    match_type     VARCHAR(20)  DEFAULT NULL,
    series_name    VARCHAR(250) DEFAULT NULL,
    team1_id       VARCHAR(20)  DEFAULT NULL,
    team2_id       VARCHAR(20)  DEFAULT NULL,
    team1_name     VARCHAR(100) DEFAULT NULL,
    team2_name     VARCHAR(100) DEFAULT NULL,
    venue_id       VARCHAR(20)  DEFAULT NULL,
    venue_name     VARCHAR(200) DEFAULT NULL,
    city           VARCHAR(100) DEFAULT NULL,
    start_date     BIGINT       DEFAULT NULL,
    end_date       BIGINT       DEFAULT NULL,
    status         VARCHAR(300) DEFAULT NULL,
    winning_team   VARCHAR(100) DEFAULT NULL,
    victory_margin VARCHAR(100) DEFAULT NULL,
    victory_type   VARCHAR(30)  DEFAULT NULL,
    toss_winner    VARCHAR(100) DEFAULT NULL,
    toss_decision  VARCHAR(10)  DEFAULT NULL,
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (match_id),
    INDEX idx_matches_type   (match_type),
    INDEX idx_matches_date   (start_date),
    INDEX idx_matches_series (series_name(100)),
    INDEX idx_matches_team1  (team1_id),
    INDEX idx_matches_team2  (team2_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scorecards (
    scorecard_id     BIGINT       NOT NULL AUTO_INCREMENT,
    match_id         VARCHAR(30)  DEFAULT NULL,
    innings_id       INT          DEFAULT NULL,
    batting_team     VARCHAR(100) DEFAULT NULL,
    player_id        VARCHAR(20)  DEFAULT NULL,
    player_name      VARCHAR(150) DEFAULT NULL,
    batting_position INT          DEFAULT NULL,
    runs             INT          DEFAULT 0,
    balls            INT          DEFAULT 0,
    fours            INT          DEFAULT 0,
    sixes            INT          DEFAULT 0,
    strike_rate      DECIMAL(7,2) DEFAULT 0.00,
    dismissal        VARCHAR(300) DEFAULT NULL,
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (scorecard_id),
    INDEX idx_sc_match   (match_id),
    INDEX idx_sc_player  (player_id),
    INDEX idx_sc_innings (innings_id),
    CONSTRAINT fk_sc_match  FOREIGN KEY (match_id)
        REFERENCES matches(match_id) ON DELETE CASCADE,
    CONSTRAINT fk_sc_player FOREIGN KEY (player_id)
        REFERENCES players(player_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stats (
    stat_id        BIGINT       NOT NULL AUTO_INCREMENT,
    player_id      VARCHAR(20)  DEFAULT NULL,
    player_name    VARCHAR(150) DEFAULT NULL,
    match_format   VARCHAR(20)  DEFAULT NULL,
    matches        INT          DEFAULT 0,
    innings        INT          DEFAULT 0,
    runs           INT          DEFAULT 0,
    highest_score  INT          DEFAULT 0,
    batting_avg    DECIMAL(6,2) DEFAULT 0.00,
    strike_rate    DECIMAL(6,2) DEFAULT 0.00,
    centuries      INT          DEFAULT 0,
    half_centuries INT          DEFAULT 0,
    fours          INT          DEFAULT 0,
    sixes          INT          DEFAULT 0,
    wickets        INT          DEFAULT 0,
    bowling_avg    DECIMAL(6,2) DEFAULT 0.00,
    economy_rate   DECIMAL(5,2) DEFAULT 0.00,
    five_wickets   INT          DEFAULT 0,
    catches        INT          DEFAULT 0,
    stumpings      INT          DEFAULT 0,
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (stat_id),
    UNIQUE KEY uq_player_format (player_id, match_format),
    INDEX idx_stats_runs    (runs),
    INDEX idx_stats_wickets (wickets),
    INDEX idx_stats_format  (match_format),
    CONSTRAINT fk_stats_player FOREIGN KEY (player_id)
        REFERENCES players(player_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
