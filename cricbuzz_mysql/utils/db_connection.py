"""
utils/db_connection.py
MySQL connection factory using mysql-connector-python.
"""

import os
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host":               os.getenv("DB_HOST",     "localhost"),
    "port":           int(os.getenv("DB_PORT",     "3306")),
    "user":               os.getenv("DB_USER",     "root"),
    "password":           os.getenv("DB_PASSWORD", ""),
    "database":           os.getenv("DB_NAME",     "cricbuzz_db"),
    "charset":            "utf8mb4",
    "use_unicode":        True,
    "connection_timeout": 10,
    "autocommit":         False,
}

_CONFIG_NO_DB = {k: v for k, v in DB_CONFIG.items() if k != "database"}


def get_connection() -> mysql.connector.MySQLConnection:
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        logger.error(f"[DB] Connection failed: {e}")
        raise


def get_connection_no_db() -> mysql.connector.MySQLConnection:
    try:
        return mysql.connector.connect(**_CONFIG_NO_DB)
    except Error as e:
        logger.error(f"[DB] Connection (no-db) failed: {e}")
        raise


def test_connection() -> bool:
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception:
        return False


def execute_write(sql: str, params: tuple = ()) -> bool:
    """Single INSERT / UPDATE / DELETE. Returns True on success."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return True
    except Error as e:
        logger.error(f"[DB] execute_write error: {e}\nSQL: {sql}")
        conn.rollback()
        return False
    finally:
        conn.close()


def execute_many(sql: str, data: list) -> int:
    """
    Bulk INSERT using executemany.
    Returns len(data) on success, 0 on failure.
    Prints the actual MySQL error so you can see what's failing.
    """
    if not data:
        return 0
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.executemany(sql, data)
        conn.commit()
        logger.info(f"[DB] execute_many OK: {len(data)} rows submitted")
        return len(data)
    except Error as e:
        logger.error(f"[DB] execute_many FAILED: {e}")
        # Print to stdout so it appears in the Streamlit terminal
        print(f"[DB ERROR] execute_many: {e}")
        print(f"[DB ERROR] SQL: {sql[:200]}")
        if data:
            print(f"[DB ERROR] First row: {data[0]}")
        conn.rollback()
        return 0
    finally:
        conn.close()
