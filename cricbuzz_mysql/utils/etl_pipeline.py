"""
utils/etl_pipeline.py
ETL orchestrator: Extract → Transform → Load
"""

import logging
import pandas as pd
from utils import api, data_transformer
from utils.db_insert import insert_matches, insert_players, insert_stats

logger = logging.getLogger(__name__)


def extract_data() -> dict:
    logger.info("[ETL] EXTRACT…")
    raw = {"live": {}, "recent": {}, "batting": {}, "bowling": {}}
    if not api.is_api_key_configured():
        logger.warning("[ETL] No API key — skipping extract.")
        return raw
    raw["live"]    = api.get_live_matches()
    raw["recent"]  = api.get_recent_matches()
    raw["batting"] = api.get_batting_stats({"formatType": "ODI"})
    raw["bowling"] = api.get_bowling_stats({"formatType": "ODI"})
    return raw


def transform_data(raw: dict) -> dict:
    logger.info("[ETL] TRANSFORM…")
    live_df   = data_transformer.transform_live_matches(raw.get("live",   {}))
    recent_df = data_transformer.transform_recent_matches(raw.get("recent", {}))

    matches_df = pd.concat([live_df, recent_df], ignore_index=True)
    if not matches_df.empty and "match_id" in matches_df.columns:
        matches_df = matches_df.drop_duplicates(subset=["match_id"])

    stats_df = data_transformer.transform_player_stats(raw.get("batting", {}))
    if not stats_df.empty:
        stats_df["match_format"] = "ODI"

    return {"matches": matches_df, "players": pd.DataFrame(), "stats": stats_df}


def load_data(transformed: dict) -> dict:
    logger.info("[ETL] LOAD…")
    return {
        "matches_loaded": insert_matches(transformed["matches"]),
        "players_loaded": insert_players(transformed["players"]),
        "stats_loaded":   insert_stats(transformed["stats"]),
    }


def run_etl() -> dict:
    logger.info("[ETL] ===== Pipeline start =====")
    summary = {"status": "success", "matches_loaded": 0,
                "players_loaded": 0, "stats_loaded": 0, "errors": []}
    try:
        raw         = extract_data()
        transformed = transform_data(raw)
        counts      = load_data(transformed)
        summary.update(counts)
    except Exception as e:
        summary["status"] = "error"
        summary["errors"].append(str(e))
        logger.error(f"[ETL] Pipeline error: {e}", exc_info=True)
    logger.info(f"[ETL] ===== Done: {summary} =====")
    return summary
