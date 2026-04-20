# 🏏 Cricbuzz LiveStats — Real-Time Cricket Analytics Dashboard

## Project Overview
A production-level cricket analytics platform built with Python, 
Streamlit, MySQL, and the Cricbuzz API.

## Tech Stack
- Python 3.10+
- Streamlit (Multi-page dashboard)
- MySQL (Cloud hosted on Railway)
- Pandas (Data transformation)
- Plotly (Visualizations)
- Cricbuzz API via RapidAPI (Live data)

## Project Structure
cricbuzz_mysql/
├── app.py                  ← Main entry point
├── requirements.txt        ← Dependencies
├── database/
│   ├── schema.sql          ← MySQL DDL (6 tables)
│   └── init_db.py          ← DB initialization + seed data
├── utils/
│   ├── api.py              ← Cricbuzz API integration
│   ├── etl_pipeline.py     ← ETL orchestrator
│   ├── data_transformer.py ← JSON → DataFrame
│   ├── db_connection.py    ← MySQL connection
│   ├── db_insert.py        ← Write operations
│   └── db_fetch.py         ← Read operations
└── pages/
    ├── 1_Home.py
    ├── 2_Live_Matches.py
    ├── 3_Player_Stats.py
    ├── 4_SQL_Analytics.py
    ├── 5_CRUD_Operations.py
    └── 6_Scorecard.py

## Setup Instructions

### 1. Clone the repository
git clone https://github.com/adityathakur26/cricbuzz-livestats.git
cd cricbuzz-livestats/cricbuzz_mysql

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

### 3. Install dependencies
pip install -r requirements.txt

### 4. Configure API Key
Edit utils/.env:
    RAPIDAPI_KEY=your_key_here
    RAPIDAPI_HOST=cricbuzz-cricket.p.rapidapi.com
    DB_HOST=your_mysql_host
    DB_PORT=3306
    DB_USER=your_user
    DB_PASSWORD=your_password
    DB_NAME=railway

Get free API key at:
https://rapidapi.com/cricketapilive/api/cricbuzz-cricket

### 5. Initialize Database
python -m database.init_db

### 6. Run the App
streamlit run app.py

## Live Demo
🔗 https://your-app.streamlit.app

## API Key Configuration
- Platform: RapidAPI
- API: Cricbuzz Cricket by cricketapilive
- Free Plan: 500 requests/month
- Endpoints used:
  - /matches/v1/live
  - /matches/v1/recent
  - /mcenter/v1/{id}/hscard
  - /stats/v1/rankings/batsmen
  - /stats/v1/rankings/bowlers

## Database Schema
6 tables:
- teams       → International teams
- venues      → Cricket grounds
- players     → Player profiles
- matches     → Match metadata + results
- scorecards  → Batting performance rows
- stats       → Aggregated career statistics

## Four Main Modules
1. Live Matches  → Real-time scores from API + save to DB
2. Player Stats  → Rankings, charts, player profiles
3. SQL Analytics → 25 queries (Easy/Medium/Hard)
4. CRUD Ops      → Add/Update/Delete players
