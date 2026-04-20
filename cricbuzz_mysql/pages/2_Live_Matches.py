"""
pages/2_Live_Matches.py
Live & Recent matches – fetches from Cricbuzz API and saves to MySQL.
"""

import os, time
import streamlit as st
import pandas as pd
from utils import api, data_transformer
from utils.db_insert import insert_matches
from utils.db_fetch import fetch_recent_matches

st.set_page_config(page_title="Live Matches", page_icon="📺", layout="wide")
st.title("📺 Live & Recent Matches")
st.caption("Powered by Cricbuzz Cricket API via RapidAPI")

# ── Inline API key setup ──────────────────────────────────────────────────────
ENV_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "utils", ".env"))

def _read_env():
    out = {}
    try:
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
    except Exception:
        pass
    return out

def _save_key(key: str):
    env = _read_env()
    env["RAPIDAPI_KEY"] = key
    with open(ENV_PATH, "w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")
    os.environ["RAPIDAPI_KEY"] = key
    api.RAPIDAPI_KEY = key
    api.HEADERS["x-rapidapi-key"] = key

if not api.is_api_key_configured():
    with st.expander("🔑 Configure RapidAPI Key", expanded=True):
        st.warning(
            "Add your free Cricbuzz API key to see live IPL 2026 & international matches.\n\n"
            "Get it at → https://rapidapi.com/cricketapilive/api/cricbuzz-cricket (Free: 500 req/month)",
            icon="🔑",
        )
        k = st.text_input("Paste X-RapidAPI-Key", type="password", key="key_input")
        if st.button("✅ Save Key", type="primary"):
            if k.strip():
                _save_key(k.strip())
                st.success("Key saved! Fetching live data now…")
                st.rerun()
            else:
                st.error("Please enter a valid key.")
else:
    st.success("✅ API key active — pulling real Cricbuzz data", icon="🔑")

st.divider()


def _badge(text, color="#e94560"):
    return (f'<span style="background:{color}22;color:{color};border:1px solid {color}55;'
            f'padding:2px 9px;border-radius:10px;font-size:.78rem;font-weight:700">{text}</span>')


def _card(row):
    fmt_col = {"TEST":"#e94560","ODI":"#0dcaf0","T20I":"#ffc107",
                "T20":"#ff9800","IPL":"#ff9800"}.get(str(row.get("match_type","")).upper(), "#aaa")
    t1 = row.get("team1", row.get("team1_name","Team 1"))
    t2 = row.get("team2", row.get("team2_name","Team 2"))
    s1 = str(row.get("team1_score","")).strip("/") or "–"
    s2 = str(row.get("team2_score","")).strip("/") or "–"
    status = row.get("status","")
    sc = "#7dda58" if any(w in status.lower() for w in ["won","win"]) else \
         "#ffc107" if any(w in status.lower() for w in ["live","progress","inn"]) else "#aab4c8"
    st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a2340,#1e2d4a);
                    border:1px solid #2a3a5c;border-radius:12px;
                    padding:1rem 1.3rem;margin-bottom:.7rem;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <span style="color:#e0e8ff;font-weight:700;font-size:1.05rem">
                        {t1} <span style="color:#445">vs</span> {t2}
                    </span>
                    <div style="color:#7a8aaa;font-size:.8rem;margin-top:2px">
                        🏆 {row.get("series_name","")}
                    </div>
                </div>
                <div style="text-align:right">
                    {_badge(str(row.get("match_type","")).upper(), fmt_col)}
                    <div style="color:#7a8aaa;font-size:.78rem;margin-top:4px">
                        {row.get("description","")}
                    </div>
                </div>
            </div>
            <div style="background:#111c30;border-radius:8px;padding:.5rem 1rem;
                        margin-top:.6rem;display:flex;gap:2rem">
                <span style="color:#ddd;font-size:.9rem">🏏 <b>{t1}:</b> {s1}</span>
                <span style="color:#ddd;font-size:.9rem">🏏 <b>{t2}:</b> {s2}</span>
            </div>
            <div style="color:{sc};font-size:.85rem;margin-top:.5rem;font-weight:500">{status}</div>
            <div style="color:#445;font-size:.77rem;margin-top:3px">
                📍 {row.get("venue", row.get("venue_name",""))} · {row.get("city","")}
            </div>
        </div>""", unsafe_allow_html=True)


tab_live, tab_recent, tab_db = st.tabs(["🔴 Live (API)", "🕐 Recent (API)", "🗄️ From Database"])

# ── LIVE ──────────────────────────────────────────────────────────────────────
with tab_live:
    c1, c2, c3 = st.columns([2,1,1])
    fetch_btn  = c1.button("🔄 Fetch Live Matches", type="primary", key="btn_live")
    auto_ref   = c2.checkbox("Auto-refresh 60s", key="auto_live")
    save_btn   = c3.button("💾 Save to MySQL", key="save_live")

    if auto_ref:
        time.sleep(1); st.rerun()

    # auto-fetch on first load if key present
    if fetch_btn or ("live_df" not in st.session_state and api.is_api_key_configured()):
        with st.spinner("📡 Contacting Cricbuzz API…"):
            try:
                raw = api.get_live_matches()
                df  = data_transformer.transform_live_matches(raw) if raw else pd.DataFrame()
                if raw:
                    with st.expander("🔍 Raw JSON (debug)"):
                        st.json(raw)
            except Exception as e:
                st.error(f"API error: {e}")
                df = pd.DataFrame()
        st.session_state["live_df"]   = df
        st.session_state["live_time"] = time.strftime("%H:%M:%S")

    df = st.session_state.get("live_df")
    if df is None:
        st.info("Click **Fetch Live Matches** to load current scores.", icon="🏏")
    else:
        st.caption(f"Last fetched: {st.session_state.get('live_time','—')}")

        if save_btn:
            if df.empty:
                st.warning("Nothing to save.")
            else:
                # Debug: show what we're about to save
                st.info(f"Attempting to save {len(df)} rows... match_id sample: {df['match_id'].head(3).tolist()}")
                n = insert_matches(df)
                if n > 0:
                    st.success(f"✅ Saved {n} records to MySQL.")
                else:
                    st.error(
                        "❌ Save returned 0. Check the terminal/console window where "
                        "you ran `streamlit run app.py` — the exact MySQL error is printed there."
                    )
        else:
            fmts = ["All"] + sorted(df["match_type"].dropna().unique().tolist())
            sel  = st.selectbox("Filter format", fmts, key="fmt_live")
            view = df if sel == "All" else df[df["match_type"] == sel]
            st.markdown(f"**{len(view)} match(es)**")
            for _, r in view.iterrows():
                _card(r.to_dict())
            with st.expander("📋 Raw table"):
                st.dataframe(view, use_container_width=True)

# ── RECENT ────────────────────────────────────────────────────────────────────
with tab_recent:
    c1, c2 = st.columns([2,1])
    rfetch = c1.button("🔄 Fetch Recent Matches", type="primary", key="btn_recent")
    rsave  = c2.button("💾 Save to MySQL", key="save_recent")

    if rfetch or ("recent_df" not in st.session_state and api.is_api_key_configured()):
        with st.spinner("📡 Fetching recent matches…"):
            try:
                raw = api.get_recent_matches()
                df  = data_transformer.transform_recent_matches(raw) if raw else pd.DataFrame()
                if raw:
                    with st.expander("🔍 Raw JSON (debug)"):
                        st.json(raw)
            except Exception as e:
                st.error(f"API error: {e}")
                df = pd.DataFrame()
        st.session_state["recent_df"]   = df
        st.session_state["recent_time"] = time.strftime("%H:%M:%S")

    df = st.session_state.get("recent_df")
    if df is None:
        st.info("Click **Fetch Recent Matches**.", icon="🏏")
    else:
        st.caption(f"Last fetched: {st.session_state.get('recent_time','—')}")
        if rsave:
            if df.empty:
                st.warning("Nothing to save.")
            else:
                # Debug: show what we're about to save
                st.info(f"Attempting to save {len(df)} rows... match_id sample: {df['match_id'].head(3).tolist()}")
                n = insert_matches(df)
                if n > 0:
                    st.success(f"✅ Saved {n} records to MySQL.")
                else:
                    st.error(
                        "❌ Save returned 0. Check the terminal/console window where "
                        "you ran `streamlit run app.py` — the exact MySQL error is printed there."
                    )
        else:
            fmts2 = ["All"] + sorted(df["match_type"].dropna().unique().tolist())
            sel2  = st.selectbox("Filter format", fmts2, key="fmt_recent")
            view2 = df if sel2 == "All" else df[df["match_type"] == sel2]
            st.markdown(f"**{len(view2)} match(es)**")
            for _, r in view2.head(20).iterrows():
                _card(r.to_dict())

# ── DATABASE ──────────────────────────────────────────────────────────────────
with tab_db:
    st.subheader("Matches in MySQL database")
    col_lim, col_ref = st.columns([3,1])
    lim = col_lim.slider("Show last N", 5, 100, 20, key="db_lim")
    if col_ref.button("🔁 Refresh", key="db_ref"):
        st.rerun()

    db_df = fetch_recent_matches(limit=lim)
    if db_df.empty:
        st.warning(
            "No matches saved yet.\n\n"
            "1. Go to **Live** or **Recent** tab → Fetch → **Save to MySQL**",
            icon="📭",
        )
    else:
        k1, k2, k3 = st.columns(3)
        k1.metric("Matches", len(db_df))
        k2.metric("Formats", db_df["match_type"].nunique() if "match_type" in db_df.columns else "–")
        k3.metric("Series",  db_df["series_name"].nunique() if "series_name" in db_df.columns else "–")
        st.dataframe(db_df, use_container_width=True)
