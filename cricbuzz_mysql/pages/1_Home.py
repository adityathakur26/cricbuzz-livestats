"""
pages/1_Home.py  –  Project overview
"""
import streamlit as st

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);
            padding:2.5rem 2rem;border-radius:12px;margin-bottom:1.5rem">
    <h1 style="color:#e94560;margin:0;font-size:2.6rem">🏏 Cricbuzz LiveStats</h1>
    <p style="color:#a8b2d8;margin:.4rem 0 0;font-size:1.1rem">
        Real-Time Cricket Analytics  ·  MySQL  ·  ETL  ·  Streamlit
    </p>
</div>""", unsafe_allow_html=True)

c1, c2 = st.columns([3,2], gap="large")

with c1:
    st.subheader("🎯 What this app does")
    st.markdown("""
    **Cricbuzz LiveStats** is an end-to-end cricket analytics platform:

    - **Live API data** from Cricbuzz (via RapidAPI) — live scores, recent matches, player rankings
    - **ETL Pipeline** — Extract → Transform → Load into MySQL
    - **MySQL Database** — 6 normalized tables with foreign keys and indexes
    - **25 SQL Queries** — from simple SELECTs to composite scoring and head-to-head analysis
    - **CRUD Operations** — full player management (add, edit, delete)
    - **Plotly charts** — bar, scatter, pie across all pages
    """)

    st.subheader("📂 Project Structure")
    st.code("""
cricbuzz_app/
├── app.py                   ← entry point + ETL sidebar
├── requirements.txt
├── database/
│   ├── schema.sql           ← MySQL DDL (6 tables)
│   └── init_db.py           ← CREATE DATABASE + seed data
├── utils/
│   ├── .env                 ← API key + MySQL credentials
│   ├── api.py               ← Cricbuzz API + 429 retry
│   ├── etl_pipeline.py      ← Extract / Transform / Load
│   ├── data_transformer.py  ← JSON → DataFrame
│   ├── db_connection.py     ← MySQL connection factory
│   ├── db_insert.py         ← INSERT IGNORE / UPSERT
│   └── db_fetch.py          ← SELECT → DataFrame
└── pages/
    ├── 1_Home.py
    ├── 2_Live_Matches.py
    ├── 3_Player_Stats.py
    ├── 4_SQL_Analytics.py
    └── 5_CRUD_Operations.py
    """, language="")

with c2:
    st.subheader("⚙️ Setup")
    st.info("""
**1 – Install deps**
```
pip install -r requirements.txt
```

**2 – Edit `utils/.env`**
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cricbuzz_db
RAPIDAPI_KEY=your_key_here
```

**3 – Init MySQL**
```
cd cricbuzz_app
python -m database.init_db
```

**4 – Run**
```
streamlit run app.py
```
""", icon="🚀")

    pages = [
        ("📺","Live Matches","Live IPL + international scores → save to MySQL"),
        ("📊","Player Stats","Rankings, charts, individual profiles"),
        ("🧮","SQL Analytics","25 MySQL queries with auto-charts"),
        ("🛠️","CRUD Ops","Add / Update / Delete players"),
    ]
    for icon, name, desc in pages:
        st.markdown(f"""
        <div style="background:#1e2a3a;border-left:3px solid #e94560;
                    padding:.6rem 1rem;margin-bottom:.5rem;border-radius:4px">
            <b style="color:#e94560">{icon} {name}</b><br>
            <span style="color:#a8b2d8;font-size:.87rem">{desc}</span>
        </div>""", unsafe_allow_html=True)
