"""
pages/5_CRUD_Operations.py
Full Create / Read / Update / Delete for the players table.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db_connection import execute_write, get_connection
from utils.db_fetch import fetch_all_players

st.set_page_config(page_title="CRUD Operations", page_icon="🛠️", layout="wide")
st.title("🛠️ CRUD Operations – Player Management")
st.caption("Create · Read · Update · Delete player records in MySQL")


def _players():
    return fetch_all_players()


tab_view, tab_add, tab_upd, tab_del = st.tabs(
    ["👁️ View Players", "➕ Add Player", "✏️ Update Player", "🗑️ Delete Player"]
)

# ── VIEW ──────────────────────────────────────────────────────────────────────
with tab_view:
    st.subheader("All Players in Database")
    if st.button("🔁 Refresh", key="v_ref"):
        st.rerun()

    df = _players()
    if df.empty:
        st.info(
            "No players found.  \n"
            "Run `python -m database.init_db` to seed sample data, "
            "or add a player using the **Add Player** tab.",
            icon="📭",
        )
    else:
        search = st.text_input("🔍 Search name / country / role", "")
        if search:
            mask = df.apply(lambda r: search.lower() in r.to_string().lower(), axis=1)
            df = df[mask]

        st.dataframe(df, use_container_width=True)
        st.caption(f"Showing {len(df)} player(s)")

        if "country" in df.columns and len(df) > 0:
            cnt = df["country"].value_counts().reset_index()
            cnt.columns = ["Country", "Players"]
            fig = px.bar(cnt, x="Country", y="Players",
                         color="Players", color_continuous_scale="Reds",
                         title="Players by Country")
            fig.update_layout(plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                               font_color="#ddd")
            st.plotly_chart(fig, use_container_width=True)

# ── ADD ───────────────────────────────────────────────────────────────────────
with tab_add:
    st.subheader("Add New Player")
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            pid   = st.text_input("Player ID *",  placeholder="e.g. P100")
            pname = st.text_input("Full Name *",   placeholder="e.g. Hardik Pandya")
            country = st.selectbox("Country *", [
                "India","Australia","England","Pakistan","South Africa",
                "New Zealand","West Indies","Sri Lanka","Bangladesh","Afghanistan","Other"])
            dob = st.text_input("Date of Birth (YYYY-MM-DD)", placeholder="1996-10-11")
        with c2:
            role  = st.selectbox("Playing Role *", ["Batsman","Bowler","All-rounder","WK-Batsman"])
            bat   = st.selectbox("Batting Style",  ["Right-hand bat","Left-hand bat"])
            bowl  = st.selectbox("Bowling Style", [
                "Right-arm fast","Right-arm fast-medium","Right-arm medium",
                "Right-arm off-break","Right-arm leg-break",
                "Left-arm fast","Left-arm fast-medium","Left-arm medium",
                "Left-arm orthodox","Left-arm chinaman","Does not bowl"])

        if st.form_submit_button("➕ Add Player", type="primary"):
            if not pid.strip() or not pname.strip():
                st.error("Player ID and Full Name are required.")
            else:
                ok = execute_write(
                    """INSERT INTO players
                           (player_id, player_name, country, playing_role,
                            batting_style, bowling_style, date_of_birth)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (pid.strip(), pname.strip(), country, role, bat, bowl,
                     dob.strip() or None),
                )
                if ok:
                    st.success(f"✅ **{pname}** added to MySQL!")
                    st.balloons()
                else:
                    st.error("❌ Insert failed. Player ID may already exist.")

# ── UPDATE ────────────────────────────────────────────────────────────────────
with tab_upd:
    st.subheader("Update Player Record")
    df_up = _players()
    if df_up.empty:
        st.info("No players to update.")
    else:
        sel = st.selectbox("Select player to update", df_up["player_name"].tolist(), key="upd_sel")
        row = df_up[df_up["player_name"] == sel].iloc[0]

        with st.form("upd_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_name    = st.text_input("Full Name",    value=str(row.get("player_name","")))
                new_country = st.text_input("Country",      value=str(row.get("country","")))
                new_dob     = st.text_input("Date of Birth",value=str(row.get("date_of_birth","") or ""))
            with c2:
                new_role = st.text_input("Playing Role",  value=str(row.get("playing_role","")))
                new_bat  = st.text_input("Batting Style", value=str(row.get("batting_style","")))
                new_bowl = st.text_input("Bowling Style", value=str(row.get("bowling_style","")))

            if st.form_submit_button("💾 Save Changes", type="primary"):
                ok = execute_write(
                    """UPDATE players
                       SET player_name=%s, country=%s, playing_role=%s,
                           batting_style=%s, bowling_style=%s, date_of_birth=%s
                       WHERE player_id=%s""",
                    (new_name, new_country, new_role, new_bat, new_bowl,
                     new_dob or None, str(row.get("player_id",""))),
                )
                st.success(f"✅ **{new_name}** updated.") if ok else st.error("❌ Update failed.")

# ── DELETE ────────────────────────────────────────────────────────────────────
with tab_del:
    st.subheader("Delete Player")
    df_del = _players()
    if df_del.empty:
        st.info("No players to delete.")
    else:
        sel_d = st.selectbox("Select player to delete", df_del["player_name"].tolist(), key="del_sel")
        tgt   = df_del[df_del["player_name"] == sel_d].iloc[0]
        st.warning(
            f"⚠️ About to permanently delete **{sel_d}** "
            f"(ID: `{tgt.get('player_id','')}`, Country: {tgt.get('country','')}).",
            icon="⚠️",
        )
        confirm = st.checkbox(f"Yes, delete {sel_d}", key="del_confirm")
        if st.button("🗑️ Delete Player", type="primary", disabled=not confirm):
            ok = execute_write(
                "DELETE FROM players WHERE player_id = %s",
                (str(tgt.get("player_id","")),),
            )
            if ok:
                st.success(f"✅ {sel_d} deleted.")
                st.rerun()
            else:
                st.error("❌ Delete failed.")
