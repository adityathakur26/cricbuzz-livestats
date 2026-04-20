"""
utils/db_fetch.py
All database READ operations.  Returns pandas DataFrames.
Uses %s placeholders (MySQL).
"""

import logging
import pandas as pd
from utils.db_connection import get_connection

logger = logging.getLogger(__name__)


def _df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Internal helper: run SQL → DataFrame."""
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn, params=params)
    except Exception as e:
        logger.error(f"[Fetch] {e}\nSQL: {sql}")
        return pd.DataFrame()
    finally:
        conn.close()


# ── Matches ───────────────────────────────────────────────────────────────────

def fetch_recent_matches(limit: int = 20) -> pd.DataFrame:
    return _df(
        """SELECT match_id, description, match_type, series_name,
                  team1_name, team2_name, venue_name, city, status,
                  winning_team, victory_margin, victory_type,
                  toss_winner, toss_decision
           FROM matches
           ORDER BY start_date DESC
           LIMIT %s""",
        (limit,),
    )


def fetch_matches_by_format(fmt: str) -> pd.DataFrame:
    return _df(
        "SELECT * FROM matches WHERE match_type = %s ORDER BY start_date DESC",
        (fmt,),
    )


def fetch_scorecard(match_id: str) -> pd.DataFrame:
    return _df(
        """SELECT innings_id, batting_team, batting_position,
                  player_name, runs, balls, fours, sixes, strike_rate, dismissal
           FROM scorecards
           WHERE match_id = %s
           ORDER BY innings_id, batting_position""",
        (match_id,),
    )


# ── Players ───────────────────────────────────────────────────────────────────

def fetch_all_players() -> pd.DataFrame:
    return _df(
        """SELECT p.player_id, p.player_name, p.country,
                  p.batting_style, p.bowling_style, p.playing_role,
                  p.date_of_birth, t.team_name
           FROM players p
           LEFT JOIN teams t ON p.team_id = t.team_id
           ORDER BY p.player_name"""
    )


def fetch_player_by_id(player_id: str) -> pd.DataFrame:
    return _df("SELECT * FROM players WHERE player_id = %s", (player_id,))


def fetch_players_by_country(country: str) -> pd.DataFrame:
    return _df(
        "SELECT * FROM players WHERE country = %s ORDER BY player_name",
        (country,),
    )


def fetch_top_players(stat: str = "runs", limit: int = 10,
                      match_format: str = None) -> pd.DataFrame:
    _allowed = {
        "runs", "wickets", "batting_avg", "centuries",
        "strike_rate", "half_centuries", "economy_rate", "matches",
    }
    if stat not in _allowed:
        stat = "runs"

    params = []
    fmt_clause = ""
    if match_format:
        fmt_clause = "AND s.match_format = %s"
        params.append(match_format)

    params.append(limit)
    return _df(
        f"""SELECT s.player_name, s.match_format, s.matches, s.runs,
                   s.batting_avg, s.strike_rate, s.centuries, s.half_centuries,
                   s.wickets, s.bowling_avg, s.economy_rate,
                   p.country, p.playing_role
            FROM stats s
            LEFT JOIN players p ON s.player_id = p.player_id
            WHERE 1=1 {fmt_clause}
            ORDER BY s.{stat} DESC
            LIMIT %s""",
        tuple(params),
    )


# ── Analytics helpers ─────────────────────────────────────────────────────────

def fetch_team_wins() -> pd.DataFrame:
    return _df(
        """SELECT winning_team AS team, COUNT(*) AS total_wins
           FROM matches
           WHERE winning_team IS NOT NULL AND winning_team <> ''
           GROUP BY winning_team
           ORDER BY total_wins DESC"""
    )


def fetch_venue_stats() -> pd.DataFrame:
    return _df(
        "SELECT venue_name, city, country, capacity FROM venues ORDER BY capacity DESC"
    )


def fetch_player_stats_by_id(player_id: str) -> pd.DataFrame:
    return _df(
        """SELECT match_format, matches, runs, batting_avg, strike_rate,
                  centuries, half_centuries, wickets, bowling_avg, economy_rate,
                  catches, stumpings
           FROM stats
           WHERE player_id = %s
           ORDER BY FIELD(match_format,'TEST','ODI','T20I')""",
        (player_id,),
    )


# ── Scorecard extras ──────────────────────────────────────────────────────────

def fetch_all_matches_with_scorecards() -> pd.DataFrame:
    """Return all matches that have at least one scorecard row."""
    return _df("""
        SELECT DISTINCT m.match_id, m.description, m.match_type,
               m.series_name, m.team1_name, m.team2_name,
               m.venue_name, m.city, m.status, m.winning_team,
               m.victory_margin, FROM_UNIXTIME(m.start_date) AS played_on
        FROM matches m
        INNER JOIN scorecards sc ON m.match_id = sc.match_id
        ORDER BY m.start_date DESC
    """)


def fetch_match_bowling(match_id: str) -> pd.DataFrame:
    """
    Approximate bowling figures per player per innings.
    Aggregates runs conceded from batting rows where the bowler name
    appears in the dismissal field.
    """
    return _df("""
        SELECT innings_id, batting_team,
               TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(dismissal,' b ',- 1),' ',1)) AS bowler,
               COUNT(*)            AS wickets,
               SUM(runs)           AS runs_conceded,
               ROUND(SUM(runs) / NULLIF(COUNT(*),0), 2) AS bowling_avg
        FROM scorecards
        WHERE match_id = %s
          AND dismissal NOT IN ('not out','retired hurt','')
          AND dismissal LIKE '%b %'
        GROUP BY innings_id, batting_team, bowler
        ORDER BY innings_id, wickets DESC
    """, (match_id,))


def fetch_innings_summary(match_id: str) -> pd.DataFrame:
    """Return innings-level totals: runs, wickets, boundaries."""
    return _df("""
        SELECT innings_id, batting_team,
               SUM(runs)   AS total_runs,
               COUNT(CASE WHEN dismissal NOT IN ('not out','retired hurt','')
                          AND dismissal <> '' THEN 1 END) AS wickets,
               SUM(fours)  AS total_fours,
               SUM(sixes)  AS total_sixes,
               ROUND(AVG(strike_rate), 2) AS avg_strike_rate
        FROM scorecards
        WHERE match_id = %s
        GROUP BY innings_id, batting_team
        ORDER BY innings_id
    """, (match_id,))


def fetch_top_scores_all_time(limit: int = 20) -> pd.DataFrame:
    """Highest individual innings scores across all stored matches."""
    return _df("""
        SELECT sc.player_name, sc.runs, sc.balls, sc.fours, sc.sixes,
               sc.strike_rate, sc.dismissal, sc.batting_team,
               m.description, m.series_name,
               FROM_UNIXTIME(m.start_date) AS played_on
        FROM scorecards sc
        JOIN matches m ON sc.match_id = m.match_id
        ORDER BY sc.runs DESC
        LIMIT %s
    """, (limit,))


def fetch_player_batting_history(player_name: str) -> pd.DataFrame:
    """All scorecard innings for a given player name."""
    return _df("""
        SELECT sc.runs, sc.balls, sc.fours, sc.sixes,
               sc.strike_rate, sc.dismissal, sc.batting_team,
               sc.innings_id, m.match_id, m.description,
               m.series_name, m.match_type,
               FROM_UNIXTIME(m.start_date) AS played_on
        FROM scorecards sc
        JOIN matches m ON sc.match_id = m.match_id
        WHERE sc.player_name = %s
        ORDER BY m.start_date DESC
    """, (player_name,))
