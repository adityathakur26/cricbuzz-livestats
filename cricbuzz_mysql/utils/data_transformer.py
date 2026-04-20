"""
utils/data_transformer.py
Transform raw Cricbuzz JSON → clean pandas DataFrames.
Handles actual Cricbuzz API field names and structures.
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)


# ── Safe helpers ──────────────────────────────────────────────────────────────

def _g(d, *keys, default=None):
    """Safely navigate nested dict."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is None:
            return default
    return d


def _s(v):
    """Safe string — returns '' for None/nan."""
    if v is None:
        return ""
    s = str(v).strip()
    return "" if s in ("None", "nan", "NaN") else s


def _i(v):
    try:
        return int(float(str(v)))
    except Exception:
        return 0


def _f(v):
    try:
        return float(str(v))
    except Exception:
        return 0.0


# ── Score extraction helper ───────────────────────────────────────────────────

def _extract_score(score_obj: dict) -> str:
    """
    Extract 'runs/wickets' from a Cricbuzz score object.
    Tries inngs2 first (completed innings), then inngs1 (ongoing),
    then direct runs/wickets on the object itself.
    Returns '—' if no score data found.
    """
    if not isinstance(score_obj, dict):
        return "—"

    # Try inngs2 first (recently completed innings), then inngs1
    for key in ("inngs2", "inngs1"):
        inn = score_obj.get(key)
        if isinstance(inn, dict):
            runs = inn.get("runs")
            wkts = inn.get("wickets")
            if runs is not None:
                return f"{runs}/{wkts}" if wkts is not None else str(runs)

    # Fallback: direct keys on score object
    runs = score_obj.get("runs")
    wkts = score_obj.get("wickets")
    if runs is not None:
        return f"{runs}/{wkts}" if wkts is not None else str(runs)

    return "—"


# ── Live / Recent matches ─────────────────────────────────────────────────────

def transform_live_matches(raw: dict) -> pd.DataFrame:
    """
    Transform /matches/v1/live or /matches/v1/recent response.
    Both endpoints share the same typeMatches → seriesMatches → matches structure.
    """
    records = []

    for type_block in (raw.get("typeMatches") or []):
        for series_block in (type_block.get("seriesMatches") or []):
            wrapper     = series_block.get("seriesAdWrapper") or {}
            series_name = wrapper.get("seriesName", "Unknown Series")

            for match in (wrapper.get("matches") or []):
                mi = match.get("matchInfo")  or {}
                ms = match.get("matchScore") or {}

                t1_score_obj = ms.get("team1Score") or {}
                t2_score_obj = ms.get("team2Score") or {}

                records.append({
                    "match_id":    _s(mi.get("matchId")),
                    "description": _s(mi.get("matchDesc")),
                    "match_type":  _s(mi.get("matchFormat")),
                    "series_name": _s(series_name),
                    "team1":       _s(_g(mi, "team1", "teamName")),
                    "team2":       _s(_g(mi, "team2", "teamName")),
                    "team1_short": _s(_g(mi, "team1", "teamSName")),
                    "team2_short": _s(_g(mi, "team2", "teamSName")),
                    "team1_score": _extract_score(t1_score_obj),
                    "team2_score": _extract_score(t2_score_obj),
                    "status":      _s(mi.get("status")),
                    "venue":       _s(_g(mi, "venueInfo", "ground")),
                    "city":        _s(_g(mi, "venueInfo", "city")),
                    "start_date":  _i(mi.get("startDate")),
                    "end_date":    _i(mi.get("endDate")),
                })

    df = pd.DataFrame(records)
    # Drop rows with empty match_id
    if not df.empty and "match_id" in df.columns:
        df = df[df["match_id"].str.strip() != ""]
    logger.info(f"[Transform] live/recent → {len(df)} valid match rows")
    return df


def transform_recent_matches(raw: dict) -> pd.DataFrame:
    return transform_live_matches(raw)


# ── Scorecard ─────────────────────────────────────────────────────────────────

def transform_scorecard(raw: dict, match_id: str) -> pd.DataFrame:
    """
    Transform scorecard API response into batting rows.

    Actual Cricbuzz API structure (from observed JSON):
    {
      "scorecard": [                    ← lowercase key
        {
          "inningsid": 1,               ← lowercase
          "batTeamName": "...",         ← OR inside batTeamDetails
          "batsman": [                  ← LIST of batsmen
            {
              "id": 10694,
              "name": "Player Name",    ← OR "batName"
              "runs": 68,
              "balls": 83,
              "fours": 9,
              "sixes": 2,
              "strikeRate": 81.92,
              "outDec": "c ... b ...",  ← dismissal
              "pos": 1                  ← batting position
            }
          ]
        }
      ]
    }
    """
    records = []

    # API uses "scorecard" (lowercase); old code used "scoreCard"
    innings_list = raw.get("scorecard") or raw.get("scoreCard") or []

    for innings in innings_list:
        if not isinstance(innings, dict):
            continue

        innings_id = _i(
            innings.get("inningsid") or innings.get("inningsId") or 0
        )

        # Batting team name — multiple possible locations
        batting_team = _s(
            innings.get("batTeamName")
            or innings.get("battingTeam")
            or _g(innings, "batTeamDetails", "batTeamName")
            or f"Innings {innings_id}"
        )

        # Batsmen — actual API returns a LIST called "batsman"
        # Older/different endpoint may use dict inside "batTeamDetails"
        batsmen_raw = (
            innings.get("batsman")                              # list (actual API)
            or _g(innings, "batTeamDetails", "batsmenData")    # dict (older API)
            or []
        )

        # Normalise to list
        if isinstance(batsmen_raw, dict):
            batsmen_list = list(batsmen_raw.values())
        elif isinstance(batsmen_raw, list):
            batsmen_list = batsmen_raw
        else:
            batsmen_list = []

        for b in batsmen_list:
            if not isinstance(b, dict):
                continue

            # Field names differ between API versions
            player_id   = _s(b.get("id")    or b.get("batId")   or "")
            player_name = _s(b.get("name")  or b.get("batName") or "Unknown")
            bat_pos     = _i(b.get("pos")   or b.get("batPos")  or 0)
            dismissal   = _s(b.get("outDec") or b.get("dismissal") or b.get("outDesc") or "not out")

            records.append({
                "match_id":         match_id,
                "innings_id":       innings_id,
                "batting_team":     batting_team,
                "player_id":        player_id,
                "player_name":      player_name,
                "batting_position": bat_pos,
                "runs":             _i(b.get("runs",       0)),
                "balls":            _i(b.get("balls",      0)),
                "fours":            _i(b.get("fours",      0)),
                "sixes":            _i(b.get("sixes",      0)),
                "strike_rate":      _f(b.get("strikeRate", b.get("strikerate", 0.0))),
                "dismissal":        dismissal,
            })

    df = pd.DataFrame(records)
    logger.info(f"[Transform] scorecard {match_id} → {len(df)} batting rows")
    return df


# ── Player stats (rankings) ───────────────────────────────────────────────────

def transform_player_stats(raw: dict) -> pd.DataFrame:
    records = []
    for p in (raw.get("rank") or []):
        records.append({
            "player_id":   _s(p.get("id")),
            "player_name": _s(p.get("name")),
            "country":     _s(p.get("country")),
            "rank":        _i(p.get("rank")),
            "rating":      _i(p.get("rating")),
        })
    return pd.DataFrame(records)


# ── Sample / demo data ────────────────────────────────────────────────────────

def get_sample_live_matches() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "match_id": "DM001", "description": "37th Match", "match_type": "T20",
            "series_name": "IPL 2026", "team1": "Mumbai Indians",
            "team2": "Chennai Super Kings", "team1_short": "MI", "team2_short": "CSK",
            "team1_score": "186/5", "team2_score": "142/8",
            "status": "Mumbai Indians won by 44 runs",
            "venue": "Wankhede Stadium", "city": "Mumbai",
            "start_date": 1713600000, "end_date": 1713618000,
        },
        {
            "match_id": "DM002", "description": "38th Match", "match_type": "T20",
            "series_name": "IPL 2026", "team1": "Royal Challengers Bengaluru",
            "team2": "Kolkata Knight Riders", "team1_short": "RCB", "team2_short": "KKR",
            "team1_score": "201/4", "team2_score": "198/7",
            "status": "RCB won by 3 runs",
            "venue": "M Chinnaswamy Stadium", "city": "Bengaluru",
            "start_date": 1713686400, "end_date": 1713704400,
        },
        {
            "match_id": "DM003", "description": "1st Test, Day 3", "match_type": "TEST",
            "series_name": "India vs England 2026", "team1": "India", "team2": "England",
            "team1_short": "IND", "team2_short": "ENG",
            "team1_score": "320/6", "team2_score": "185/10",
            "status": "India leads by 135 runs",
            "venue": "Eden Gardens", "city": "Kolkata",
            "start_date": 1713340800, "end_date": 1713772800,
        },
    ])


def get_sample_players() -> pd.DataFrame:
    """
    Sample data used when DB is empty.
    Includes both profile columns AND stats columns so charts don't crash.
    """
    return pd.DataFrame([
        {
            "player_id": "P001", "player_name": "Virat Kohli", "country": "India",
            "batting_style": "Right-hand bat", "bowling_style": "Right-arm medium",
            "playing_role": "Batsman", "date_of_birth": "1988-11-05",
            "match_format": "ODI", "matches": 292, "runs": 13906,
            "batting_avg": 57.32, "strike_rate": 93.62, "centuries": 50,
            "half_centuries": 72, "wickets": 4, "bowling_avg": 54.25,
            "economy_rate": 5.38, "catches": 139,
        },
        {
            "player_id": "P002", "player_name": "Rohit Sharma", "country": "India",
            "batting_style": "Right-hand bat", "bowling_style": "Right-arm off-break",
            "playing_role": "Batsman", "date_of_birth": "1987-04-30",
            "match_format": "ODI", "matches": 264, "runs": 10890,
            "batting_avg": 49.27, "strike_rate": 89.18, "centuries": 31,
            "half_centuries": 55, "wickets": 8, "bowling_avg": 27.5,
            "economy_rate": 5.7, "catches": 144,
        },
        {
            "player_id": "P003", "player_name": "Pat Cummins", "country": "Australia",
            "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast",
            "playing_role": "Bowler", "date_of_birth": "1993-05-08",
            "match_format": "TEST", "matches": 75, "runs": 1282,
            "batting_avg": 15.49, "strike_rate": 52.0, "centuries": 0,
            "half_centuries": 2, "wickets": 263, "bowling_avg": 21.23,
            "economy_rate": 2.80, "catches": 35,
        },
        {
            "player_id": "P005", "player_name": "Babar Azam", "country": "Pakistan",
            "batting_style": "Right-hand bat", "bowling_style": "Right-arm off-break",
            "playing_role": "Batsman", "date_of_birth": "1994-10-15",
            "match_format": "ODI", "matches": 131, "runs": 6033,
            "batting_avg": 57.45, "strike_rate": 88.39, "centuries": 20,
            "half_centuries": 35, "wickets": 0, "bowling_avg": 0.0,
            "economy_rate": 0.0, "catches": 60,
        },
        {
            "player_id": "P009", "player_name": "Jasprit Bumrah", "country": "India",
            "batting_style": "Right-hand bat", "bowling_style": "Right-arm fast",
            "playing_role": "Bowler", "date_of_birth": "1993-12-06",
            "match_format": "TEST", "matches": 40, "runs": 348,
            "batting_avg": 8.70, "strike_rate": 47.0, "centuries": 0,
            "half_centuries": 0, "wickets": 173, "bowling_avg": 20.34,
            "economy_rate": 2.77, "catches": 18,
        },
    ])
