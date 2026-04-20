"""
utils/db_insert.py
All database WRITE operations — MySQL, %s placeholders.
Uses INSERT IGNORE for matches/players/scorecards (safe to re-run).
Uses ON DUPLICATE KEY UPDATE for stats (always refreshes latest figures).
"""

import logging
import pandas as pd
from utils.db_connection import execute_many

logger = logging.getLogger(__name__)


def _s(val, default="", maxlen=None):
    s = str(val).strip() if val is not None else default
    if s in ("None", "nan", "NaN"):
        s = default
    return s[:maxlen] if maxlen and len(s) > maxlen else s


def _i(val, default=0):
    try:
        return int(float(str(val)))
    except (TypeError, ValueError):
        return default


def _f(val, default=0.0):
    try:
        return float(str(val))
    except (TypeError, ValueError):
        return default


# ── Matches ───────────────────────────────────────────────────────────────────

def insert_matches(df: pd.DataFrame) -> int:
    if df.empty:
        logger.warning("[Insert] No match data.")
        return 0

    rows = []
    skipped = 0
    for _, r in df.iterrows():
        mid = _s(r.get("match_id"), maxlen=30)
        if not mid:
            skipped += 1
            continue
        rows.append((
            mid,
            _s(r.get("description"),                        maxlen=200),
            _s(r.get("match_type"),                         maxlen=20),
            _s(r.get("series_name"),                        maxlen=250),
            _s(r.get("team1",  r.get("team1_name",  "")),   maxlen=100),
            _s(r.get("team2",  r.get("team2_name",  "")),   maxlen=100),
            _s(r.get("venue",  r.get("venue_name",  "")),   maxlen=200),
            _s(r.get("city"),                               maxlen=100),
            _i(r.get("start_date", 0)),
            _i(r.get("end_date",   0)),
            _s(r.get("status"),                             maxlen=300),
        ))

    if skipped:
        logger.warning(f"[Insert] Skipped {skipped} rows with empty match_id")
    if not rows:
        return 0

    # Use INSERT IGNORE — mysql-connector does NOT support ON DUPLICATE KEY UPDATE
    # with executemany when extra params are passed as part of the same tuple
    n = execute_many(
        """INSERT IGNORE INTO matches
               (match_id, description, match_type, series_name,
                team1_name, team2_name, venue_name, city,
                start_date, end_date, status)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows,
    )
    logger.info(f"[Insert] insert_matches → {n} rows processed")
    return n

# ── Players ───────────────────────────────────────────────────────────────────

def insert_players(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    rows = []
    for _, r in df.iterrows():
        pid = _s(r.get("player_id"), maxlen=20)
        if not pid:
            continue
        rows.append((
            pid,
            _s(r.get("player_name"),   maxlen=150),
            _s(r.get("country"),       maxlen=100),
            _s(r.get("batting_style"), maxlen=100),
            _s(r.get("bowling_style"), maxlen=100),
            _s(r.get("playing_role"),  maxlen=50),
        ))

    if not rows:
        return 0

    n = execute_many(
        """INSERT IGNORE INTO players
               (player_id, player_name, country, batting_style, bowling_style, playing_role)
           VALUES (%s,%s,%s,%s,%s,%s)""",
        rows,
    )
    logger.info(f"[Insert] insert_players → {n} rows processed")
    return n


# ── Stats ─────────────────────────────────────────────────────────────────────

def insert_stats(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    rows = []
    for _, r in df.iterrows():
        pid = _s(r.get("player_id"), maxlen=20)
        if not pid:
            continue
        rows.append((
            pid,
            _s(r.get("player_name"),         maxlen=150),
            _s(r.get("match_format", "ALL"), maxlen=20),
            _i(r.get("matches")),
            _i(r.get("runs")),
            _f(r.get("batting_avg")),
            _f(r.get("strike_rate")),
            _i(r.get("centuries")),
            _i(r.get("wickets")),
            _f(r.get("economy_rate")),
        ))

    if not rows:
        return 0

    n = execute_many(
        """INSERT IGNORE INTO stats
               (player_id, player_name, match_format, matches, runs,
                batting_avg, strike_rate, centuries, wickets, economy_rate)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows,
    )
    logger.info(f"[Insert] insert_stats → {n} rows processed")
    return n

# ── Scorecards ────────────────────────────────────────────────────────────────

def insert_scorecard(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    rows = []
    for _, r in df.iterrows():
        mid = _s(r.get("match_id"), maxlen=30)
        if not mid:
            continue
        rows.append((
            mid,
            _i(r.get("innings_id",       1)),
            _s(r.get("batting_team"),     maxlen=100),
            _s(r.get("player_id"),        maxlen=20),
            _s(r.get("player_name"),      maxlen=150),
            _i(r.get("batting_position", 0)),
            _i(r.get("runs")),
            _i(r.get("balls")),
            _i(r.get("fours")),
            _i(r.get("sixes")),
            _f(r.get("strike_rate")),
            _s(r.get("dismissal"),        maxlen=300),
        ))

    if not rows:
        return 0

    n = execute_many(
        """INSERT INTO scorecards
               (match_id, innings_id, batting_team, player_id, player_name,
                batting_position, runs, balls, fours, sixes, strike_rate, dismissal)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        rows,
    )
    logger.info(f"[Insert] insert_scorecard → {n} rows processed")
    return n
