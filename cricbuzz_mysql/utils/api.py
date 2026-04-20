"""
utils/api.py
Cricbuzz Cricket API via RapidAPI.
All calls include 429 retry with backoff.
"""

import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")
BASE_URL      = f"https://{RAPIDAPI_HOST}"

HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}

MAX_RETRIES  = 3
RETRY_DELAY  = 5    # seconds


def _request(endpoint: str, params: dict = None) -> dict:
    """Generic GET with 429 retry + exponential backoff."""
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"[API] GET {url} (attempt {attempt})")
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)

            if resp.status_code == 429:
                wait = RETRY_DELAY * attempt
                logger.warning(f"[API] 429 rate-limit — waiting {wait}s…")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            logger.error(f"[API] Timeout on attempt {attempt}")
        except requests.exceptions.ConnectionError:
            logger.error(f"[API] Connection error on attempt {attempt}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"[API] HTTP {e.response.status_code}: {e}")
            break
        except Exception as e:
            logger.error(f"[API] Unexpected: {e}")
            break

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    logger.error(f"[API] All attempts failed for {url}")
    return {}


def is_api_key_configured() -> bool:
    return bool(RAPIDAPI_KEY and RAPIDAPI_KEY not in ("", "your_rapidapi_key_here"))


def get_live_matches()    -> dict: return _request("/matches/v1/live")
def get_recent_matches()  -> dict: return _request("/matches/v1/recent")
def get_upcoming_matches()-> dict: return _request("/matches/v1/upcoming")
def get_scorecard(mid: str) -> dict: return _request(f"/mcenter/v1/{mid}/hscard")
def get_player_stats(pid: str) -> dict: return _request(f"/stats/v1/player/{pid}")
def get_batting_stats(params=None) -> dict: return _request("/stats/v1/rankings/batsmen", params)
def get_bowling_stats(params=None) -> dict: return _request("/stats/v1/rankings/bowlers",  params)
