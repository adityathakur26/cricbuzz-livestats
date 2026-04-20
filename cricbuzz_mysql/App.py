"""
App.py  –  Cricbuzz LiveStats entry point.
Checks MySQL connection, shows sidebar ETL controls.
"""

import os, sys, logging
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s")

st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def _boot():
    """Run once per Streamlit session: verify DB and init tables."""
    from utils.db_connection import test_connection
    if not test_connection():
        return False, "Cannot connect to MySQL. Check utils/.env credentials."
    try:
        from database.init_db import init_db
        init_db()
        return True, "OK"
    except Exception as e:
        return False, str(e)


ok, msg = _boot()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:.5rem 0 1rem">
        <span style="font-size:2.2rem">🏏</span><br>
        <span style="color:#e94560;font-weight:700;font-size:1.1rem">Cricbuzz LiveStats</span><br>
        <span style="color:#7a8aaa;font-size:.78rem">Real-Time Cricket Analytics</span>
    </div>""", unsafe_allow_html=True)

    st.divider()

    # MySQL status
    if ok:
        from utils.db_connection import DB_CONFIG
        st.success(
            f"✅ MySQL connected\n`{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}`",
            icon="🗄️",
        )
    else:
        st.error(f"❌ MySQL error\n{msg}", icon="🗄️")

    st.divider()

    # API key status
    from utils.api import is_api_key_configured
    if is_api_key_configured():
        st.success("✅ RapidAPI key set", icon="🔑")
    else:
        st.warning("🔑 API key missing\nSet it on the Live Matches page")

    st.divider()

    # ETL trigger
    st.subheader("⚙️ ETL Pipeline")
    if st.button("🔄 Run Full ETL", type="primary", use_container_width=True):
        with st.spinner("Running ETL…"):
            from utils.etl_pipeline import run_etl
            result = run_etl()
        if result["status"] == "success":
            st.success(
                f"✅ ETL complete\n"
                f"Matches: {result['matches_loaded']} | "
                f"Stats: {result['stats_loaded']}",
            )
        else:
            st.error(f"ETL failed: {result['errors']}")

    st.divider()
    st.caption("Navigate via pages ↑")

# ── Landing page ──────────────────────────────────────────────────────────────
st.title("🏏 Cricbuzz LiveStats Dashboard")

if not ok:
    st.error(
        f"**MySQL connection failed:** {msg}\n\n"
        "1. Make sure MySQL is running\n"
        "2. Edit `utils/.env` with correct credentials\n"
        "3. Restart the app",
        icon="🗄️",
    )
else:
    st.success("MySQL connected — database ready.", icon="✅")
    st.markdown("Select a page from the **left sidebar** to get started.")

    c1,c2,c3,c4 = st.columns(4)
    for col, (icon, name, desc) in zip([c1,c2,c3,c4], [
        ("📺","Live Matches","Real-time IPL & international scores"),
        ("📊","Player Stats","Top batsmen & bowlers with charts"),
        ("🧮","SQL Analytics","25 MySQL queries with auto-charts"),
        ("🛠️","CRUD Ops","Add / update / delete players"),
    ]):
        with col:
            st.markdown(f"""
            <div style="background:#1a2340;border:1px solid #2a3a5c;
                        border-radius:10px;padding:1.2rem;text-align:center">
                <div style="font-size:2rem">{icon}</div>
                <div style="color:#e0e8ff;font-weight:700">{name}</div>
                <div style="color:#7a8aaa;font-size:.82rem;margin-top:4px">{desc}</div>
            </div>""", unsafe_allow_html=True)
