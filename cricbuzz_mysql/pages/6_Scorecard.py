"""
pages/6_📋_Scorecard.py
Full match scorecard viewer with:
  - Match selector (by series / format filter)
  - Innings batting card with colour-coded performance
  - Innings summary KPIs
  - Bowling figures (derived from dismissal data)
  - Top individual scores (all-time leaderboard)
  - Player batting history across all stored matches
  - Live scorecard fetch from Cricbuzz API
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.db_fetch import (
    fetch_all_matches_with_scorecards,
    fetch_scorecard,
    fetch_innings_summary,
    fetch_match_bowling,
    fetch_top_scores_all_time,
    fetch_player_batting_history,
    fetch_all_players,
    fetch_recent_matches,
)
from utils.db_insert import insert_scorecard, insert_matches
from utils import api, data_transformer

st.set_page_config(page_title="Scorecard", page_icon="📋", layout="wide")
st.title("📋 Match Scorecard")
st.caption("Detailed batting & bowling breakdown for every stored match")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_view, tab_live, tab_top, tab_history = st.tabs([
    "📄 View Scorecard",
    "📡 Fetch from API",
    "🏆 Top Scores (All-Time)",
    "👤 Player Batting History",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – View stored scorecard
# ═══════════════════════════════════════════════════════════════════════════════
with tab_view:
    st.subheader("Select a Match")

    all_matches = fetch_recent_matches(limit=100)

    if all_matches.empty:
        st.warning(
            "No matches in the database yet.\n\n"
            "Go to **Live Matches → Fetch → Save to MySQL** first, "
            "then use the **Fetch from API** tab to load scorecards.",
            icon="📭",
        )
    else:
        # ── Filters ───────────────────────────────────────────────────────────
        fc1, fc2, fc3 = st.columns([2, 2, 2])

        formats = ["All"] + sorted(all_matches["match_type"].dropna().unique().tolist())
        sel_fmt = fc1.selectbox("Format", formats, key="sc_fmt")

        filtered_m = all_matches if sel_fmt == "All" else \
                     all_matches[all_matches["match_type"] == sel_fmt]

        series_list = ["All"] + sorted(filtered_m["series_name"].dropna().unique().tolist())
        sel_series  = fc2.selectbox("Series", series_list, key="sc_series")

        if sel_series != "All":
            filtered_m = filtered_m[filtered_m["series_name"] == sel_series]

        if filtered_m.empty:
            st.info("No matches match the selected filters.")
            st.stop()

        # Build label: "Description – Team1 vs Team2"
        def _label(r):
            d  = r.get("description", "")
            t1 = r.get("team1_name", "")
            t2 = r.get("team2_name", "")
            return f"{d}  –  {t1} vs {t2}"

        match_labels  = filtered_m.apply(_label, axis=1).tolist()
        match_ids     = filtered_m["match_id"].tolist()
        label_map     = dict(zip(match_labels, match_ids))

        sel_label = fc3.selectbox("Match", match_labels, key="sc_match")
        sel_mid   = label_map[sel_label]
        sel_row   = filtered_m[filtered_m["match_id"] == sel_mid].iloc[0]

        # ── Match header ──────────────────────────────────────────────────────
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a2340,#1e2d4a);
                    border:1px solid #2a3a5c;border-radius:12px;
                    padding:1.1rem 1.4rem;margin:1rem 0">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <span style="color:#e0e8ff;font-weight:700;font-size:1.15rem">
                        {sel_row.get('team1_name','')}
                        <span style="color:#445"> vs </span>
                        {sel_row.get('team2_name','')}
                    </span>
                    <div style="color:#7a8aaa;font-size:.82rem;margin-top:3px">
                        🏆 {sel_row.get('series_name','')} &nbsp;·&nbsp;
                        {sel_row.get('description','')}
                    </div>
                </div>
                <div style="text-align:right">
                    <span style="background:#e9456022;color:#e94560;border:1px solid #e9456055;
                                 padding:3px 10px;border-radius:10px;font-size:.8rem;font-weight:700">
                        {sel_row.get('match_type','')}
                    </span>
                    <div style="color:#7a8aaa;font-size:.8rem;margin-top:4px">
                        📍 {sel_row.get('venue_name','')} · {sel_row.get('city','')}
                    </div>
                </div>
            </div>
            <div style="color:#7dda58;font-size:.88rem;margin-top:.6rem;font-weight:500">
                {sel_row.get('status','') or 'Result not available'}
                {'  🏆 ' + str(sel_row.get('winning_team','')) if sel_row.get('winning_team') else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Load scorecard ────────────────────────────────────────────────────
        sc_df   = fetch_scorecard(sel_mid)
        sum_df  = fetch_innings_summary(sel_mid)
        bowl_df = fetch_match_bowling(sel_mid)

        if sc_df.empty:
            st.info(
                "No scorecard data for this match.\n\n"
                "Use the **📡 Fetch from API** tab to load it from Cricbuzz.",
                icon="📭",
            )
        else:
            innings_ids = sorted(sc_df["innings_id"].dropna().unique().tolist())

            for inn_id in innings_ids:
                inn_df   = sc_df[sc_df["innings_id"] == inn_id].copy()
                inn_team = inn_df["batting_team"].iloc[0] if not inn_df.empty else f"Innings {inn_id}"

                # Summary KPIs for this innings
                if not sum_df.empty:
                    s = sum_df[sum_df["innings_id"] == inn_id]
                    if not s.empty:
                        sr = s.iloc[0]
                        k1, k2, k3, k4, k5 = st.columns(5)
                        k1.metric("🏏 Innings",    f"{inn_id}")
                        k2.metric("🏆 Team",        str(sr.get("batting_team","")))
                        k3.metric("📊 Total Runs",  f"{sr.get('total_runs',0)}/{sr.get('wickets',0)}")
                        k4.metric("4️⃣  Fours",      str(sr.get("total_fours",0)))
                        k5.metric("6️⃣  Sixes",      str(sr.get("total_sixes",0)))

                st.markdown(f"### 🏏 Innings {inn_id} — {inn_team} Batting")

                # ── Batting table with colour highlights ──────────────────────
                display_cols = [c for c in [
                    "batting_position","player_name","runs","balls",
                    "fours","sixes","strike_rate","dismissal"
                ] if c in inn_df.columns]

                inn_disp = inn_df[display_cols].copy()
                inn_disp.columns = [c.replace("_"," ").title() for c in display_cols]

                def _row_style(row):
                    runs = row.get("Runs", 0)
                    if runs >= 100:
                        return ["background-color:#1a3a1a; color:#7dda58"] * len(row)
                    elif runs >= 50:
                        return ["background-color:#2a2a14; color:#ffc107"] * len(row)
                    elif runs == 0:
                        return ["background-color:#2a1a1a; color:#e94560"] * len(row)
                    return [""] * len(row)

                styled = inn_disp.style.apply(_row_style, axis=1)
                st.dataframe(styled, use_container_width=True, hide_index=True)

                # ── Batting performance bar chart ─────────────────────────────
                if "runs" in inn_df.columns and len(inn_df) > 0:
                    fig = px.bar(
                        inn_df.sort_values("runs", ascending=False),
                        x="player_name", y="runs",
                        color="strike_rate",
                        color_continuous_scale="RdYlGn",
                        text="runs",
                        title=f"Innings {inn_id} — Runs per Batsman (colour = Strike Rate)",
                        labels={"player_name":"Batsman","runs":"Runs","strike_rate":"SR"},
                    )
                    fig.update_traces(textposition="outside")
                    fig.update_layout(
                        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                        font_color="#ddd", height=320,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # ── Bowling figures for this innings ──────────────────────────
                if not bowl_df.empty:
                    inn_bowl = bowl_df[bowl_df["innings_id"] == inn_id]
                    if not inn_bowl.empty:
                        st.markdown(f"#### 🎳 Innings {inn_id} — Bowling Figures")
                        bowl_disp = inn_bowl[["bowler","wickets","runs_conceded","bowling_avg"]].copy()
                        bowl_disp.columns = ["Bowler","Wickets","Runs Conceded","Bowling Avg"]
                        st.dataframe(bowl_disp, use_container_width=True, hide_index=True)

                st.divider()

            # ── Innings comparison radar chart ────────────────────────────────
            if not sum_df.empty and len(sum_df) >= 2:
                st.subheader("📊 Innings Comparison")
                cats = ["total_runs","total_fours","total_sixes","avg_strike_rate"]
                cats_label = ["Total Runs","Fours","Sixes","Avg SR"]
                fig_r = go.Figure()
                colors = ["#e94560","#0dcaf0","#ffc107","#7dda58"]
                for i, (_, row) in enumerate(sum_df.iterrows()):
                    vals = [float(row.get(c, 0) or 0) for c in cats]
                    vals.append(vals[0])
                    fig_r.add_trace(go.Scatterpolar(
                        r=vals,
                        theta=cats_label + [cats_label[0]],
                        fill="toself",
                        name=f"Inn {int(row.get('innings_id',i+1))} – {row.get('batting_team','')}",
                        line_color=colors[i % len(colors)],
                        opacity=0.75,
                    ))
                fig_r.update_layout(
                    polar=dict(radialaxis=dict(visible=True, color="#7a8aaa")),
                    paper_bgcolor="#0e1117", font_color="#ddd",
                    title="Batting Performance Radar",
                )
                st.plotly_chart(fig_r, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Fetch scorecard from API
# ═══════════════════════════════════════════════════════════════════════════════
with tab_live:
    st.subheader("Fetch Scorecard from Cricbuzz API")

    if not api.is_api_key_configured():
        st.error(
            "API key not set. Configure it on the **Live Matches** page.",
            icon="🔑",
        )
    else:
        st.info(
            "Enter a Cricbuzz match ID to pull its full scorecard. "
            "Match IDs appear in the **Live Matches** Raw JSON debug panel.",
            icon="💡",
        )

        # Also let user pick from already-stored matches
        all_m = fetch_recent_matches(limit=50)
        col_pick, col_manual = st.columns([3, 2])

        with col_pick:
            if not all_m.empty:
                opts = ["— type manually —"] + [
                    f"{r['match_id']}  ({r.get('description','')} – "
                    f"{r.get('team1_name','')} vs {r.get('team2_name','')})"
                    for _, r in all_m.iterrows()
                ]
                chosen = st.selectbox("Pick a stored match", opts, key="sc_pick")
                if chosen != "— type manually —":
                    st.session_state["sc_mid_input"] = chosen.split("  ")[0].strip()

        with col_manual:
            mid_input = st.text_input(
                "Match ID",
                value=st.session_state.get("sc_mid_input", ""),
                placeholder="e.g. 12345",
                key="sc_mid_input",
            )

        col_fetch, col_save = st.columns([1, 1])
        fetch_sc  = col_fetch.button("📡 Fetch Scorecard", type="primary", key="sc_fetch_btn")
        save_sc   = col_save.button("💾 Save to MySQL",                    key="sc_save_btn")

        if fetch_sc and mid_input.strip():
            with st.spinner(f"Fetching scorecard for match {mid_input.strip()}…"):
                try:
                    raw_sc = api.get_scorecard(mid_input.strip())
                    if raw_sc:
                        sc_df_api = data_transformer.transform_scorecard(raw_sc, mid_input.strip())
                        st.session_state["api_sc_df"]  = sc_df_api
                        st.session_state["api_sc_mid"] = mid_input.strip()
                        with st.expander("🔍 Raw API JSON"):
                            st.json(raw_sc)
                    else:
                        st.error("API returned empty response. Check the match ID.")
                        st.session_state.pop("api_sc_df", None)
                except Exception as e:
                    st.error(f"API error: {e}")

        api_sc_df = st.session_state.get("api_sc_df")

        if save_sc:
            if api_sc_df is not None and not api_sc_df.empty:
                n = insert_scorecard(api_sc_df)
                st.success(f"✅ Saved {n} scorecard rows to MySQL.")
            else:
                st.warning("Nothing to save — fetch a scorecard first.")

        if api_sc_df is not None and not api_sc_df.empty:
            st.success(f"✅ {len(api_sc_df)} batting rows fetched for match `{st.session_state.get('api_sc_mid','')}`")
            st.dataframe(api_sc_df, use_container_width=True)

            # Quick chart
            if "runs" in api_sc_df.columns:
                fig = px.bar(
                    api_sc_df.sort_values("runs", ascending=False),
                    x="player_name", y="runs",
                    color="strike_rate", color_continuous_scale="RdYlGn",
                    text="runs", title="Runs per Batsman",
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                    font_color="#ddd",
                )
                st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – All-time top scores leaderboard
# ═══════════════════════════════════════════════════════════════════════════════
with tab_top:
    st.subheader("🏆 Highest Individual Scores (All Stored Matches)")

    n_top = st.slider("Show top N innings", 5, 50, 20, key="top_n")
    top_df = fetch_top_scores_all_time(limit=n_top)

    if top_df.empty:
        st.info("No scorecard data yet. Fetch some scorecards from the API tab.", icon="📭")
    else:
        # Podium-style top 3
        podium = top_df.head(3)
        p_cols = st.columns(3)
        medals = ["🥇","🥈","🥉"]
        for i, (_, pr) in enumerate(podium.iterrows()):
            with p_cols[i]:
                st.markdown(f"""
                <div style="background:#1a2340;border:1px solid #2a3a5c;
                            border-radius:12px;padding:1rem;text-align:center">
                    <div style="font-size:2rem">{medals[i]}</div>
                    <div style="color:#e94560;font-weight:700;font-size:1.1rem">
                        {pr.get('runs',0)} runs
                    </div>
                    <div style="color:#e0e8ff;font-weight:600">
                        {pr.get('player_name','')}
                    </div>
                    <div style="color:#7a8aaa;font-size:.8rem;margin-top:4px">
                        {pr.get('batting_team','')} · {pr.get('balls',0)} balls<br>
                        4s: {pr.get('fours',0)}  6s: {pr.get('sixes',0)}<br>
                        SR: {pr.get('strike_rate',0)}<br>
                        {pr.get('description','')}
                    </div>
                </div>""", unsafe_allow_html=True)

        st.divider()

        # Full leaderboard table
        disp_cols = [c for c in [
            "player_name","runs","balls","fours","sixes",
            "strike_rate","dismissal","batting_team","description","series_name"
        ] if c in top_df.columns]
        st.dataframe(top_df[disp_cols], use_container_width=True, hide_index=True)

        # Chart: top 15
        fig = px.bar(
            top_df.head(15),
            x="player_name", y="runs",
            color="strike_rate",
            color_continuous_scale="YlOrRd",
            text="runs",
            hover_data=["batting_team","description","fours","sixes"],
            title="Top 15 Individual Scores",
            labels={"player_name":"Batsman","runs":"Runs","strike_rate":"Strike Rate"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font_color="#ddd", height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Scatter: Runs vs Strike Rate
        fig2 = px.scatter(
            top_df, x="strike_rate", y="runs",
            size="sixes", color="batting_team",
            hover_name="player_name",
            title="Runs vs Strike Rate  (bubble size = Sixes hit)",
            labels={"strike_rate":"Strike Rate","runs":"Runs"},
        )
        fig2.update_layout(
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font_color="#ddd",
        )
        st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 – Player batting history
# ═══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.subheader("👤 Individual Player Batting History")

    all_players = fetch_all_players()
    sc_players_df = fetch_top_scores_all_time(limit=200)

    # Build player list from scorecard data first, fall back to players table
    if not sc_players_df.empty and "player_name" in sc_players_df.columns:
        player_names = sorted(sc_players_df["player_name"].dropna().unique().tolist())
    elif not all_players.empty:
        player_names = sorted(all_players["player_name"].dropna().unique().tolist())
    else:
        player_names = []

    if not player_names:
        st.info("No player data available. Fetch some scorecards first.", icon="📭")
    else:
        sel_player = st.selectbox("Select Player", player_names, key="hist_player")

        hist_df = fetch_player_batting_history(sel_player)

        if hist_df.empty:
            st.info(f"No batting records found for **{sel_player}** in the scorecard table.")
        else:
            # KPIs
            h1, h2, h3, h4, h5 = st.columns(5)
            h1.metric("Innings",    len(hist_df))
            h2.metric("Total Runs", int(hist_df["runs"].sum()))
            h3.metric("Highest",    int(hist_df["runs"].max()))
            h4.metric("Average",    f"{hist_df['runs'].mean():.2f}")
            h5.metric("Avg SR",     f"{hist_df['strike_rate'].mean():.2f}")

            st.divider()

            # Innings-by-innings table
            disp = [c for c in [
                "played_on","description","series_name","match_type",
                "batting_team","runs","balls","fours","sixes","strike_rate","dismissal"
            ] if c in hist_df.columns]
            st.dataframe(hist_df[disp], use_container_width=True, hide_index=True)

            # Run trend line chart
            if "played_on" in hist_df.columns:
                hist_sorted = hist_df.sort_values("played_on")
                fig = px.line(
                    hist_sorted,
                    x="played_on", y="runs",
                    markers=True,
                    title=f"{sel_player} — Innings Run Trend",
                    labels={"played_on":"Date","runs":"Runs"},
                )
                fig.add_hline(
                    y=hist_df["runs"].mean(),
                    line_dash="dash",
                    line_color="#ffc107",
                    annotation_text=f"Average: {hist_df['runs'].mean():.1f}",
                )
                fig.update_layout(
                    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                    font_color="#ddd",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Dismissal type pie chart
            if "dismissal" in hist_df.columns:
                def _dtype(d):
                    d = str(d).lower()
                    if "not out" in d:       return "Not Out"
                    if "c " in d and "b " in d: return "Caught"
                    if d.startswith("b "):   return "Bowled"
                    if "lbw" in d:           return "LBW"
                    if "run out" in d:       return "Run Out"
                    if "st " in d:           return "Stumped"
                    if "hit wicket" in d:    return "Hit Wicket"
                    return "Other"

                hist_df["dismissal_type"] = hist_df["dismissal"].apply(_dtype)
                dc = hist_df["dismissal_type"].value_counts().reset_index()
                dc.columns = ["Type","Count"]
                fig2 = px.pie(
                    dc, names="Type", values="Count",
                    title=f"{sel_player} — Dismissal Breakdown",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#ddd")
                st.plotly_chart(fig2, use_container_width=True)
