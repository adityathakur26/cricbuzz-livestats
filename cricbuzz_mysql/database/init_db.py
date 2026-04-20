"""
database/init_db.py
Create MySQL database + tables + seed sample data.
Run once:  python -m database.init_db
"""

import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "utils", ".env"))

import mysql.connector
from mysql.connector import Error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_NAME = os.getenv("DB_NAME", "cricbuzz_db")

_BASE = {
    "host":              os.getenv("DB_HOST",     "localhost"),
    "port":          int(os.getenv("DB_PORT",     "3306")),
    "user":              os.getenv("DB_USER",     "root"),
    "password":          os.getenv("DB_PASSWORD", ""),
    "charset":           "utf8mb4",
    "use_unicode":       True,
    "connection_timeout": 10,
    "autocommit":        False,
}


def _conn_no_db():
    return mysql.connector.connect(**_BASE)


def _conn():
    return mysql.connector.connect(**_BASE, database=DB_NAME)


# ── 1. Create database ───────────────────────────────────────────────────────
def create_database():
    conn = _conn_no_db()
    try:
        cur = conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        logger.info(f"[DB] Database `{DB_NAME}` ready.")
    finally:
        conn.close()


# ── 2. Create tables ─────────────────────────────────────────────────────────
def create_tables():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        raw = f.read()

    statements = [
        s.strip() for s in raw.split(";")
        if s.strip() and not s.strip().startswith("--")
    ]

    conn = _conn()
    try:
        cur = conn.cursor()
        for stmt in statements:
            try:
                cur.execute(stmt)
                conn.commit()
            except Error as e:
                if e.errno == 1050:  # Table already exists — OK
                    pass
                else:
                    # Print ALL other errors so we can see them
                    logger.error(f"[DB] DDL FAILED ({e.errno}): {e.msg}")
                    logger.error(f"[DB] Statement: {stmt[:120]}")
        logger.info("[DB] All tables created / verified.")
    finally:
        conn.close()


# ── 3. Seed sample data ──────────────────────────────────────────────────────
def seed_data():
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM players")
        if cur.fetchone()[0] > 0:
            logger.info("[DB] Sample data already present — skipping seed.")
            return

        logger.info("[DB] Seeding sample data…")

        # TEAMS
        cur.executemany(
            "INSERT IGNORE INTO teams (team_id,team_name,team_short,country,team_type) VALUES (%s,%s,%s,%s,%s)",
            [
                ("T001","India","IND","India","International"),
                ("T002","Australia","AUS","Australia","International"),
                ("T003","England","ENG","England","International"),
                ("T004","Pakistan","PAK","Pakistan","International"),
                ("T005","South Africa","SA","South Africa","International"),
                ("T006","New Zealand","NZ","New Zealand","International"),
                ("T007","West Indies","WI","West Indies","International"),
                ("T008","Sri Lanka","SL","Sri Lanka","International"),
                ("T009","Bangladesh","BAN","Bangladesh","International"),
                ("T010","Afghanistan","AFG","Afghanistan","International"),
            ],
        )

        # VENUES
        cur.executemany(
            "INSERT IGNORE INTO venues (venue_id,venue_name,city,country,capacity) VALUES (%s,%s,%s,%s,%s)",
            [
                ("V001","Melbourne Cricket Ground","Melbourne","Australia",100024),
                ("V002","Lord's Cricket Ground","London","England",30000),
                ("V003","Eden Gardens","Kolkata","India",68000),
                ("V004","Wankhede Stadium","Mumbai","India",33108),
                ("V005","Headingley","Leeds","England",20000),
                ("V006","Sydney Cricket Ground","Sydney","Australia",48000),
                ("V007","National Stadium Karachi","Karachi","Pakistan",34228),
                ("V008","Newlands Cricket Ground","Cape Town","South Africa",25000),
                ("V009","Gaddafi Stadium","Lahore","Pakistan",27000),
                ("V010","Sharjah Cricket Stadium","Sharjah","UAE",16000),
            ],
        )

        # PLAYERS
        cur.executemany(
            "INSERT IGNORE INTO players "
            "(player_id,player_name,country,batting_style,bowling_style,playing_role,date_of_birth,team_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                ("P001","Virat Kohli","India","Right-hand bat","Right-arm medium","Batsman","1988-11-05","T001"),
                ("P002","Rohit Sharma","India","Right-hand bat","Right-arm off-break","Batsman","1987-04-30","T001"),
                ("P003","Pat Cummins","Australia","Right-hand bat","Right-arm fast","Bowler","1993-05-08","T002"),
                ("P004","Ben Stokes","England","Left-hand bat","Right-arm fast-medium","All-rounder","1991-06-04","T003"),
                ("P005","Babar Azam","Pakistan","Right-hand bat","Right-arm off-break","Batsman","1994-10-15","T004"),
                ("P006","Kagiso Rabada","South Africa","Right-hand bat","Right-arm fast","Bowler","1995-05-25","T005"),
                ("P007","Kane Williamson","New Zealand","Right-hand bat","Right-arm off-break","Batsman","1990-08-08","T006"),
                ("P008","Rashid Khan","Afghanistan","Right-hand bat","Right-arm leg-spin","Bowler","1998-09-20","T010"),
                ("P009","Jasprit Bumrah","India","Right-hand bat","Right-arm fast","Bowler","1993-12-06","T001"),
                ("P010","Steve Smith","Australia","Right-hand bat","Right-arm leg-break","Batsman","1989-06-02","T002"),
                ("P011","Joe Root","England","Right-hand bat","Right-arm off-break","Batsman","1990-12-30","T003"),
                ("P012","Shakib Al Hasan","Bangladesh","Left-hand bat","Left-arm orthodox","All-rounder","1987-03-24","T009"),
                ("P013","MS Dhoni","India","Right-hand bat","Right-arm medium","WK-Batsman","1981-07-07","T001"),
                ("P014","Trent Boult","New Zealand","Right-hand bat","Left-arm fast-medium","Bowler","1989-07-22","T006"),
                ("P015","Quinton de Kock","South Africa","Left-hand bat","Right-arm off-break","WK-Batsman","1992-12-17","T005"),
            ],
        )

        # MATCHES
        cur.executemany(
            "INSERT IGNORE INTO matches "
            "(match_id,description,match_type,series_name,team1_id,team2_id,"
            "team1_name,team2_name,venue_id,venue_name,city,start_date,end_date,"
            "status,winning_team,victory_margin,victory_type,toss_winner,toss_decision) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                ("M001","1st Test","TEST","Border-Gavaskar Trophy 2024","T001","T002",
                 "India","Australia","V001","Melbourne Cricket Ground","Melbourne",
                 1704067200,1704499200,"India won by 295 runs","India","295 runs","runs","India","bat"),
                ("M002","2nd ODI","ODI","SA tour of England 2024","T003","T005",
                 "England","South Africa","V002","Lord's Cricket Ground","London",
                 1705276800,1705320000,"England won by 47 runs","England","47 runs","runs","England","bat"),
                ("M003","T20I","T20I","NZ tour of Pakistan 2024","T004","T006",
                 "Pakistan","New Zealand","V007","National Stadium Karachi","Karachi",
                 1706486400,1706504400,"Pakistan won by 3 runs","Pakistan","3 runs","runs","New Zealand","bowl"),
                ("M004","3rd Test","TEST","Ashes 2024","T003","T002",
                 "England","Australia","V005","Headingley","Leeds",
                 1690848000,1691280000,"Australia won by an innings and 14 runs",
                 "Australia","inns & 14 runs","innings","Australia","bat"),
                ("M005","1st ODI","ODI","India tour of Sri Lanka 2024","T001","T008",
                 "India","Sri Lanka","V003","Eden Gardens","Kolkata",
                 1707696000,1707739200,"India won by 67 runs","India","67 runs","runs","India","bat"),
                ("M006","2nd T20I","T20I","West Indies tour of India 2024","T001","T007",
                 "India","West Indies","V004","Wankhede Stadium","Mumbai",
                 1708905600,1708923600,"India won by 49 runs","India","49 runs","runs","India","bat"),
                ("M007","1st Test","TEST","SA tour of NZ 2024","T006","T005",
                 "New Zealand","South Africa","V008","Newlands Cricket Ground","Cape Town",
                 1709510400,1709942400,"Draw",None,None,"draw","South Africa","bat"),
                ("M008","Finals","T20I","ICC T20 World Cup 2024","T001","T003",
                 "India","England","V001","Melbourne Cricket Ground","Melbourne",
                 1710720000,1710741600,"India won by 8 wickets","India","8 wickets","wickets","India","bowl"),
                ("M009","3rd ODI","ODI","Australia tour of Pakistan 2024","T004","T002",
                 "Pakistan","Australia","V009","Gaddafi Stadium","Lahore",
                 1711929600,1711972800,"Pakistan won by 1 wicket","Pakistan","1 wicket","wickets","Australia","bat"),
                ("M010","2nd Test","TEST","Border-Gavaskar Trophy 2024","T001","T002",
                 "India","Australia","V006","Sydney Cricket Ground","Sydney",
                 1713139200,1713571200,"Australia won by 6 wickets","Australia","6 wickets","wickets","Australia","bowl"),
            ],
        )

        # STATS
        cur.executemany(
            "INSERT IGNORE INTO stats "
            "(player_id,player_name,match_format,matches,innings,runs,highest_score,"
            "batting_avg,strike_rate,centuries,half_centuries,fours,sixes,"
            "wickets,bowling_avg,economy_rate,five_wickets,catches,stumpings) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                ("P001","Virat Kohli","ODI",292,283,13906,183,57.32,93.62,50,72,1233,141,4,54.25,5.38,0,139,0),
                ("P001","Virat Kohli","TEST",118,206,9230,254,49.09,55.60,29,30,1020,24,0,0,0,0,24,0),
                ("P001","Virat Kohli","T20I",125,121,4188,122,52.65,138.89,1,38,401,128,0,0,0,0,42,0),
                ("P002","Rohit Sharma","ODI",264,256,10890,264,49.27,89.18,31,55,1098,315,8,27.5,5.7,0,144,0),
                ("P002","Rohit Sharma","TEST",67,113,4301,212,40.57,56.43,12,18,492,38,0,0,0,0,44,0),
                ("P003","Pat Cummins","TEST",75,101,1282,66,15.49,52.00,0,2,98,40,263,21.23,2.80,8,35,0),
                ("P004","Ben Stokes","TEST",108,191,6626,258,36.19,57.00,13,30,810,128,195,29.74,3.02,4,108,0),
                ("P004","Ben Stokes","ODI",105,95,2924,102,36.55,95.42,3,21,300,112,74,32.00,5.67,1,61,0),
                ("P005","Babar Azam","ODI",131,129,6033,158,57.45,88.39,20,35,631,93,0,0,0,0,60,0),
                ("P005","Babar Azam","T20I",106,104,3570,122,40.34,129.06,3,33,383,76,0,0,0,0,45,0),
                ("P005","Babar Azam","TEST",58,104,3987,196,45.88,53.57,9,23,453,30,0,0,0,0,49,0),
                ("P006","Kagiso Rabada","TEST",60,92,889,51,12.16,53.00,0,0,75,30,252,22.13,3.05,13,30,0),
                ("P006","Kagiso Rabada","ODI",79,42,400,31,14.29,86.96,0,0,40,18,149,24.60,5.21,3,25,0),
                ("P007","Kane Williamson","TEST",99,180,8608,251,54.17,47.96,26,36,784,36,36,49.11,3.00,0,132,0),
                ("P008","Rashid Khan","T20I",88,59,926,60,19.28,159.31,0,4,69,66,145,13.40,6.19,2,49,0),
                ("P009","Jasprit Bumrah","TEST",40,55,348,35,8.70,47.00,0,0,33,15,173,20.34,2.77,7,18,0),
                ("P009","Jasprit Bumrah","ODI",85,30,176,30,8.38,113.55,0,0,14,14,149,24.50,4.61,2,24,0),
                ("P010","Steve Smith","TEST",108,194,9261,239,55.77,54.33,32,37,852,44,7,95.00,3.70,0,147,0),
                ("P011","Joe Root","TEST",148,268,12485,254,50.14,54.05,34,64,1360,52,54,49.42,3.21,0,164,0),
                ("P011","Joe Root","ODI",162,153,6207,133,45.65,86.03,16,39,670,139,41,54.12,4.78,0,102,0),
                ("P012","Shakib Al Hasan","ODI",244,228,7524,134,37.62,82.44,9,54,742,186,323,29.73,4.45,11,118,0),
                ("P013","MS Dhoni","ODI",350,297,10773,183,50.58,87.56,10,73,826,359,1,61.00,5.67,0,132,123),
                ("P014","Trent Boult","TEST",79,118,793,57,8.96,42.24,0,0,73,35,317,27.50,3.20,14,46,0),
                ("P015","Quinton de Kock","ODI",174,169,6561,178,44.02,95.07,16,41,682,185,0,0,0,0,144,31),
            ],
        )

        # SCORECARDS
        cur.executemany(
            "INSERT IGNORE INTO scorecards "
            "(match_id,innings_id,batting_team,player_id,player_name,"
            "batting_position,runs,balls,fours,sixes,strike_rate,dismissal) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                ("M001",1,"India","P001","Virat Kohli",3,89,132,7,2,67.42,"c Maxwell b Cummins"),
                ("M001",1,"India","P002","Rohit Sharma",1,46,62,5,1,74.19,"b Cummins"),
                ("M001",2,"Australia","P010","Steve Smith",3,34,58,3,0,58.62,"lbw b Bumrah"),
                ("M001",2,"Australia","P003","Pat Cummins",8,12,18,1,1,66.67,"c Kohli b Shami"),
                ("M002",1,"England","P004","Ben Stokes",4,78,80,9,3,97.50,"c de Kock b Rabada"),
                ("M002",2,"South Africa","P006","Kagiso Rabada",9,22,20,3,1,110.00,"b Archer"),
                ("M003",1,"Pakistan","P005","Babar Azam",1,110,72,12,5,152.78,"not out"),
                ("M005",1,"India","P001","Virat Kohli",3,120,130,14,3,92.31,"not out"),
                ("M005",1,"India","P009","Jasprit Bumrah",10,4,8,0,0,50.00,"b Kumara"),
                ("M008",1,"India","P001","Virat Kohli",3,76,60,8,3,126.67,"not out"),
                ("M008",1,"India","P002","Rohit Sharma",1,55,38,7,2,144.74,"c Root b Archer"),
                ("M010",1,"Australia","P010","Steve Smith",3,88,140,9,1,62.86,"c Kohli b Bumrah"),
                ("M010",2,"India","P009","Jasprit Bumrah",10,5,10,1,0,50.00,"b Hazlewood"),
            ],
        )

        conn.commit()
        logger.info("[DB] ✅ All sample data seeded.")

    except Error as e:
        logger.error(f"[DB] Seed error: {e}")
        conn.rollback()
    finally:
        conn.close()


# ── orchestrator ──────────────────────────────────────────────────────────────
def init_db():
    create_database()
    create_tables()
    seed_data()
    logger.info("[DB] ✅ MySQL database fully initialized.")


if __name__ == "__main__":
    init_db()
    print("\n✅ Done — MySQL database is ready.")
    print(f"   Host : {os.getenv('DB_HOST','localhost')}:{os.getenv('DB_PORT',3306)}")
    print(f"   DB   : {DB_NAME}")
