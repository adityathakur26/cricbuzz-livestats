"""
pages/3_Player_Stats.py
Player statistics with charts and individual profiles.
Safely handles cases where DB is empty (falls back to sample data).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db_fetch import fetch_top_players, fetch_all_players, fetch_player_stats_by_id
from utils.data_transformer import get_sample_players

st.set_page_config(page_title="Player Stats", page_icon="📊", layout="wide")
st.title("📊 Player Statistics")
st.caption("Top performers from the MySQL database")

with st.sidebar:
    st.header("🔍 Filters")
    sel_fmt  = st.selectbox("Format", ["All", "TEST", "ODI", "T20I"])
    sel_stat = st.selectbox("Rank by", ["runs", "wickets", "batting_avg", "centuries", "strike_rate"])
    sel_n    = st.slider("Top N", 5, 30, 10)
    sel_ctry = st.text_input("Country filter", "")


@st.cache_data(ttl=60)
def _top(stat, n, fmt):
    f = None if fmt == "All" else fmt
    df = fetch_top_players(stat=stat, limit=n, match_format=f)
    if df.empty:
        df = get_sample_players()
    return df


@st.cache_data(ttl=60)
def _all():
    df = fetch_all_players()
    if df.empty:
        df = get_sample_players()
    return df


df_top = _top(sel_stat, sel_n, sel_fmt)
df_all = _all()

# Country filter
if sel_ctry.strip() and "country" in df_top.columns:
    df_top = df_top[df_top["country"].str.lower() == sel_ctry.strip().lower()]

# ── KPIs ──────────────────────────────────────────────────────────────────────
if not df_top.empty:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Players",     len(df_top))
    k2.metric("Avg Runs",    f"{df_top['runs'].mean():.0f}"        if "runs"        in df_top.columns else "–")
    k3.metric("Avg Wickets", f"{df_top['wickets'].mean():.0f}"     if "wickets"     in df_top.columns else "–")
    k4.metric("Avg Bat Avg", f"{df_top['batting_avg'].mean():.2f}" if "batting_avg" in df_top.columns else "–")

st.divider()

tab_bat, tab_bowl, tab_table, tab_profile = st.tabs(
    ["🏏 Batting", "🎳 Bowling", "📋 All Players", "👤 Profile"]
)

# ── BATTING ───────────────────────────────────────────────────────────────────
with tab_bat:
    bat_df = _top("runs", sel_n, sel_fmt)

    # Guard: need player_name + runs columns
    if bat_df.empty or "player_name" not in bat_df.columns or "runs" not in bat_df.columns:
        st.info("No batting data available.")
    else:
        plot_df = bat_df.head(10).copy()

        # colour column — use batting_avg if present, else plain bars
        color_col = "batting_avg" if "batting_avg" in plot_df.columns else None

        fig = px.bar(
            plot_df,
            x="player_name",
            y="runs",
            color=color_col,
            color_continuous_scale="Reds" if color_col else None,
            text="runs",
            title="Top Run Scorers",
            labels={"player_name": "Player", "runs": "Runs", "batting_avg": "Avg"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font_color="#ddd", xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Scatter: Runs vs Batting Average
        has_avg = "batting_avg" in bat_df.columns
        has_cen = "centuries"   in bat_df.columns
        if has_avg and has_cen:
            # size must be non-negative integers; fill NaN
            plot_scatter = bat_df.copy()
            plot_scatter["centuries"] = plot_scatter["centuries"].fillna(1).clip(lower=1).astype(int)
            fig2 = px.scatter(
                plot_scatter,
                x="batting_avg",
                y="runs",
                size="centuries",
                color="country" if "country" in bat_df.columns else None,
                hover_name="player_name",
                title="Runs vs Batting Average  (bubble = centuries)",
                labels={"batting_avg": "Batting Average", "runs": "Runs"},
            )
            fig2.update_layout(
                plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#ddd"
            )
            st.plotly_chart(fig2, use_container_width=True)

# ── BOWLING ───────────────────────────────────────────────────────────────────
with tab_bowl:
    bowl_df = _top("wickets", sel_n, sel_fmt)

    if bowl_df.empty or "player_name" not in bowl_df.columns or "wickets" not in bowl_df.columns:
        st.info("No bowling data available.")
    else:
        color_col2 = "bowling_avg" if "bowling_avg" in bowl_df.columns else None

        fig = px.bar(
            bowl_df.head(10),
            x="player_name",
            y="wickets",
            color=color_col2,
            color_continuous_scale="Blues" if color_col2 else None,
            text="wickets",
            title="Top Wicket Takers",
            labels={"player_name": "Player", "wickets": "Wickets", "bowling_avg": "Bowl Avg"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font_color="#ddd", xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, use_container_width=True)

        if "economy_rate" in bowl_df.columns:
            fig2 = px.scatter(
                bowl_df,
                x="economy_rate",
                y="wickets",
                hover_name="player_name",
                color="country" if "country" in bowl_df.columns else None,
                title="Economy Rate vs Wickets",
                labels={"economy_rate": "Economy Rate", "wickets": "Wickets"},
            )
            fig2.update_layout(
                plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="#ddd"
            )
            st.plotly_chart(fig2, use_container_width=True)

# ── ALL PLAYERS TABLE ─────────────────────────────────────────────────────────
with tab_table:
    if df_all.empty:
        st.info("No player data available.")
    else:
        if "playing_role" in df_all.columns:
            rc = df_all["playing_role"].value_counts().reset_index()
            rc.columns = ["Role", "Count"]
            c1, c2 = st.columns([1, 2])
            with c1:
                fig3 = px.pie(
                    rc, names="Role", values="Count",
                    title="Players by Role",
                    color_discrete_sequence=px.colors.sequential.RdBu,
                )
                fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#ddd")
                st.plotly_chart(fig3, use_container_width=True)
            with c2:
                # Show only profile columns in this table
                profile_cols = [c for c in [
                    "player_name", "country", "playing_role",
                    "batting_style", "bowling_style", "date_of_birth", "team_name",
                ] if c in df_all.columns]
                st.dataframe(df_all[profile_cols], use_container_width=True, height=340)
        else:
            st.dataframe(df_all, use_container_width=True)

# ── PROFILE ───────────────────────────────────────────────────────────────────
with tab_profile:
    if df_all.empty:
        st.info("No players available.")
    else:
        names  = sorted(df_all["player_name"].dropna().unique().tolist())
        sel_p  = st.selectbox("Select player", names)
        prow   = df_all[df_all["player_name"] == sel_p].iloc[0]

        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"""
            <div style="background:#1a2340;border-radius:10px;padding:1.2rem">
                <h3 style="color:#e94560;margin:0">{prow.get('player_name','')}</h3>
                <p style="color:#a8b2d8;margin:6px 0">
                    🌍 {prow.get('country','')}<br>
                    🏏 {prow.get('playing_role','')}<br>
                    🦇 {prow.get('batting_style','')}<br>
                    🎳 {prow.get('bowling_style','')}<br>
                    📅 {prow.get('date_of_birth','N/A')}
                </p>
            </div>""", unsafe_allow_html=True)

        with c2:
            pid_val = prow.get("player_id", "")
            if pid_val:
                stats_df = fetch_player_stats_by_id(str(pid_val))
                if not stats_df.empty:
                    show_cols = [c for c in [
                        "match_format", "matches", "runs", "batting_avg",
                        "centuries", "half_centuries", "wickets",
                        "bowling_avg", "economy_rate", "catches", "stumpings",
                    ] if c in stats_df.columns]
                    st.dataframe(stats_df[show_cols], use_container_width=True)
                else:
                    st.info("No detailed stats in database for this player.")
            else:
                st.info("Player ID not available.")
