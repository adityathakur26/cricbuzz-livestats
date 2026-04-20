"""
pages/4_SQL_Analytics.py
25 SQL queries – all written for MySQL (no SQLite functions).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db_connection import get_connection

st.set_page_config(page_title="SQL Analytics", page_icon="🧮", layout="wide")
st.title("🧮 SQL Analytics")
st.caption("25 queries — Beginner → Advanced — all running on MySQL")


def run_query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


# ── 25 Queries ────────────────────────────────────────────────────────────────
QUERIES = {
    "Q1 – All Indian Players": {
        "level": "Beginner",
        "desc": "List every Indian player with their role and batting/bowling style.",
        "sql": """
SELECT player_name, playing_role, batting_style, bowling_style
FROM players
WHERE country = 'India'
ORDER BY player_name;""",
    },
    "Q2 – Recent Matches (Last 30 Days)": {
        "level": "Beginner",
        "desc": "Matches played in the last 30 days, newest first.",
        "sql": """
SELECT description, team1_name, team2_name, venue_name, city,
       FROM_UNIXTIME(start_date) AS match_date, status
FROM matches
WHERE start_date >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 30 DAY))
ORDER BY start_date DESC;""",
    },
    "Q3 – Top 10 ODI Run Scorers": {
        "level": "Beginner",
        "desc": "Highest run-scorers in ODI cricket with batting average and centuries.",
        "sql": """
SELECT player_name, runs, batting_avg, centuries, half_centuries
FROM stats
WHERE match_format = 'ODI'
ORDER BY runs DESC
LIMIT 10;""",
    },
    "Q4 – Venues with Capacity > 50,000": {
        "level": "Beginner",
        "desc": "Cricket grounds that can host more than 50,000 spectators.",
        "sql": """
SELECT venue_name, city, country, capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC;""",
    },
    "Q5 – Total Wins per Team": {
        "level": "Beginner",
        "desc": "Number of match wins for every team in the database.",
        "sql": """
SELECT winning_team AS team, COUNT(*) AS total_wins
FROM matches
WHERE winning_team IS NOT NULL AND winning_team <> ''
GROUP BY winning_team
ORDER BY total_wins DESC;""",
    },
    "Q6 – Players by Playing Role": {
        "level": "Beginner",
        "desc": "How many players fall into each playing role.",
        "sql": """
SELECT playing_role, COUNT(*) AS player_count
FROM players
WHERE playing_role IS NOT NULL
GROUP BY playing_role
ORDER BY player_count DESC;""",
    },
    "Q7 – Highest Individual Score per Format": {
        "level": "Beginner",
        "desc": "The highest recorded individual innings per match format.",
        "sql": """
SELECT match_format, MAX(highest_score) AS highest_score
FROM stats
WHERE highest_score > 0
GROUP BY match_format
ORDER BY highest_score DESC;""",
    },
    "Q8 – Matches per Series": {
        "level": "Beginner",
        "desc": "How many matches each series has, sorted by most matches.",
        "sql": """
SELECT series_name, match_type,
       COUNT(*) AS match_count,
       FROM_UNIXTIME(MIN(start_date)) AS series_start
FROM matches
GROUP BY series_name, match_type
ORDER BY match_count DESC;""",
    },
    "Q9 – All-rounders with 1000+ Runs AND 50+ Wickets": {
        "level": "Intermediate",
        "desc": "True all-rounders who have contributed significantly with both bat and ball.",
        "sql": """
SELECT p.player_name, s.match_format, s.runs, s.wickets, s.batting_avg, s.bowling_avg
FROM stats s
JOIN players p ON s.player_id = p.player_id
WHERE p.playing_role LIKE '%All-rounder%'
  AND s.runs    > 1000
  AND s.wickets >   50
ORDER BY s.runs DESC;""",
    },
    "Q10 – Last 20 Completed Matches with Results": {
        "level": "Intermediate",
        "desc": "Most recent completed matches showing winner and margin.",
        "sql": """
SELECT description, team1_name, team2_name,
       winning_team, victory_margin, victory_type, venue_name,
       FROM_UNIXTIME(start_date) AS played_on
FROM matches
WHERE winning_team IS NOT NULL
ORDER BY start_date DESC
LIMIT 20;""",
    },
    "Q11 – Cross-Format Batting Comparison": {
        "level": "Intermediate",
        "desc": "Players who have stats in at least two formats — runs side by side.",
        "sql": """
SELECT player_name,
       MAX(CASE WHEN match_format='TEST' THEN runs  END) AS test_runs,
       MAX(CASE WHEN match_format='ODI'  THEN runs  END) AS odi_runs,
       MAX(CASE WHEN match_format='T20I' THEN runs  END) AS t20i_runs,
       ROUND(AVG(batting_avg), 2) AS avg_batting_avg
FROM stats
GROUP BY player_id, player_name
HAVING COUNT(DISTINCT match_format) >= 2
ORDER BY avg_batting_avg DESC;""",
    },
    "Q12 – Teams with Most Boundaries (Fours+Sixes)": {
        "level": "Intermediate",
        "desc": "Batting teams with the highest total boundaries in the scorecard data.",
        "sql": """
SELECT batting_team,
       SUM(fours) AS total_fours,
       SUM(sixes) AS total_sixes,
       SUM(fours + sixes) AS total_boundaries
FROM scorecards
GROUP BY batting_team
ORDER BY total_boundaries DESC;""",
    },
    "Q13 – Batting Partnerships ≥ 50 Runs": {
        "level": "Intermediate",
        "desc": "Adjacent batting pairs (by position) whose combined runs exceeded 50.",
        "sql": """
SELECT a.match_id, a.innings_id, a.batting_team,
       a.player_name AS bat1, b.player_name AS bat2,
       (a.runs + b.runs) AS combined_runs
FROM scorecards a
JOIN scorecards b
  ON a.match_id = b.match_id
 AND a.innings_id = b.innings_id
 AND b.batting_position = a.batting_position + 1
WHERE (a.runs + b.runs) >= 50
ORDER BY combined_runs DESC;""",
    },
    "Q14 – Top Scorers per Match": {
        "level": "Intermediate",
        "desc": "Highest individual scorer in each innings of each match.",
        "sql": """
SELECT sc.match_id, sc.innings_id, sc.batting_team,
       sc.player_name, sc.runs, sc.balls, sc.strike_rate
FROM scorecards sc
INNER JOIN (
    SELECT match_id, innings_id, MAX(runs) AS max_runs
    FROM scorecards
    GROUP BY match_id, innings_id
) mx ON sc.match_id = mx.match_id
     AND sc.innings_id = mx.innings_id
     AND sc.runs = mx.max_runs
ORDER BY sc.runs DESC;""",
    },
    "Q15 – Players with Highest Strike Rate in T20I (min 20 matches)": {
        "level": "Intermediate",
        "desc": "T20I batsmen with the most explosive strike rates (minimum 20 matches).",
        "sql": """
SELECT player_name, strike_rate, runs, matches, batting_avg
FROM stats
WHERE match_format = 'T20I'
  AND matches >= 20
  AND strike_rate > 0
ORDER BY strike_rate DESC
LIMIT 15;""",
    },
    "Q16 – Best Bowling Economy in Limited Overs (min 30 matches)": {
        "level": "Intermediate",
        "desc": "Most economical bowlers in ODI and T20I cricket.",
        "sql": """
SELECT player_name, match_format, economy_rate, wickets, matches
FROM stats
WHERE match_format IN ('ODI','T20I')
  AND matches >= 30
  AND economy_rate > 0
  AND wickets    > 0
ORDER BY economy_rate ASC
LIMIT 15;""",
    },
    "Q17 – Toss Win → Match Win Analysis": {
        "level": "Advanced",
        "desc": "Does winning the toss help? Win percentage by toss decision (bat/bowl).",
        "sql": """
SELECT toss_decision,
       COUNT(*) AS total_matches,
       SUM(CASE WHEN toss_winner = winning_team THEN 1 ELSE 0 END) AS toss_winner_won,
       ROUND(
           100.0 * SUM(CASE WHEN toss_winner = winning_team THEN 1 ELSE 0 END)
           / COUNT(*), 1
       ) AS win_pct
FROM matches
WHERE toss_winner IS NOT NULL
  AND winning_team IS NOT NULL
GROUP BY toss_decision;""",
    },
    "Q18 – Head-to-Head Team Records": {
        "level": "Advanced",
        "desc": "Win/loss record between every pair of teams.",
        "sql": """
SELECT team1_name, team2_name,
       COUNT(*) AS matches_played,
       SUM(CASE WHEN winning_team = team1_name THEN 1 ELSE 0 END) AS team1_wins,
       SUM(CASE WHEN winning_team = team2_name THEN 1 ELSE 0 END) AS team2_wins,
       SUM(CASE WHEN winning_team IS NULL OR winning_team = '' THEN 1 ELSE 0 END) AS draws,
       ROUND(
           100.0 * SUM(CASE WHEN winning_team = team1_name THEN 1 ELSE 0 END)
           / COUNT(*), 1
       ) AS team1_win_pct
FROM matches
GROUP BY team1_name, team2_name
HAVING matches_played >= 1
ORDER BY matches_played DESC;""",
    },
    "Q19 – Consistent Batsmen (Low Score Variance)": {
        "level": "Advanced",
        "desc": "Batsmen with smallest standard deviation in scores — most reliable performers.",
        "sql": """
SELECT player_name,
       COUNT(*)                                   AS innings,
       ROUND(AVG(runs), 2)                        AS avg_runs,
       ROUND(STD(runs), 2)                        AS std_dev,
       MAX(runs)                                  AS highest,
       MIN(runs)                                  AS lowest
FROM scorecards
WHERE balls >= 10
GROUP BY player_name
HAVING innings >= 2
ORDER BY std_dev ASC;""",
    },
    "Q20 – Multi-Format Career Summary": {
        "level": "Advanced",
        "desc": "Complete career summary across all three formats for every player.",
        "sql": """
SELECT player_name,
       SUM(matches)  AS total_matches,
       SUM(runs)     AS total_runs,
       SUM(wickets)  AS total_wickets,
       MAX(CASE WHEN match_format='TEST' THEN batting_avg END) AS test_avg,
       MAX(CASE WHEN match_format='ODI'  THEN batting_avg END) AS odi_avg,
       MAX(CASE WHEN match_format='T20I' THEN batting_avg END) AS t20_avg,
       MAX(CASE WHEN match_format='TEST' THEN bowling_avg END) AS test_bowl_avg,
       MAX(CASE WHEN match_format='ODI'  THEN bowling_avg END) AS odi_bowl_avg
FROM stats
GROUP BY player_id, player_name
ORDER BY total_runs DESC;""",
    },
    "Q21 – Composite Player Performance Score": {
        "level": "Advanced",
        "desc": "Weighted score combining batting, bowling, and fielding contributions.",
        "sql": """
SELECT player_name, match_format,
       ROUND(
           COALESCE(runs,0)         * 0.01
         + COALESCE(batting_avg,0)  * 0.50
         + COALESCE(strike_rate,0)  * 0.30
         + COALESCE(wickets,0)      * 2.00
         + (50 - LEAST(COALESCE(bowling_avg,50),50)) * 0.50
         + (6  - LEAST(COALESCE(economy_rate, 6), 6)) * 2.00
         + COALESCE(catches,0)      * 3.00
         + COALESCE(stumpings,0)    * 5.00
       , 2) AS composite_score,
       runs, wickets, catches, stumpings
FROM stats
ORDER BY composite_score DESC
LIMIT 15;""",
    },
    "Q22 – Player Form Categories": {
        "level": "Advanced",
        "desc": "Categorise players by current form based on average scorecard runs.",
        "sql": """
SELECT player_name,
       COUNT(*)             AS innings,
       ROUND(AVG(runs), 2)  AS avg_runs,
       ROUND(AVG(strike_rate), 2) AS avg_sr,
       SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END) AS scores_50_plus,
       CASE
           WHEN AVG(runs) >= 60 THEN '🔥 Excellent'
           WHEN AVG(runs) >= 40 THEN '✅ Good'
           WHEN AVG(runs) >= 20 THEN '😐 Average'
           ELSE '❌ Poor'
       END AS form
FROM scorecards
GROUP BY player_name
HAVING innings >= 1
ORDER BY avg_runs DESC;""",
    },
    "Q23 – Venue Performance Analysis": {
        "level": "Advanced",
        "desc": "How many matches each venue has hosted and total runs scored there.",
        "sql": """
SELECT m.venue_name, m.city,
       COUNT(DISTINCT m.match_id) AS matches_hosted,
       SUM(sc.runs)               AS total_runs_scored,
       ROUND(AVG(sc.runs), 2)     AS avg_runs_per_innings
FROM matches m
LEFT JOIN scorecards sc ON m.match_id = sc.match_id
GROUP BY m.venue_name, m.city
ORDER BY matches_hosted DESC;""",
    },
    "Q24 – Best Batting Partnerships": {
        "level": "Advanced",
        "desc": "Most productive batting pairs ordered by average combined runs.",
        "sql": """
SELECT a.player_name AS bat1, b.player_name AS bat2,
       COUNT(*) AS times_batted_together,
       ROUND(AVG(a.runs + b.runs), 2)  AS avg_partnership,
       MAX(a.runs + b.runs)            AS best_partnership,
       SUM(CASE WHEN a.runs + b.runs >= 50 THEN 1 ELSE 0 END) AS fifty_plus_stands
FROM scorecards a
JOIN scorecards b
  ON  a.match_id        = b.match_id
 AND  a.innings_id      = b.innings_id
 AND  b.batting_position = a.batting_position + 1
GROUP BY a.player_name, b.player_name
ORDER BY avg_partnership DESC;""",
    },
    "Q25 – Victory Type Distribution per Team": {
        "level": "Advanced",
        "desc": "How each team wins — by runs, wickets, innings, or draw.",
        "sql": """
SELECT winning_team AS team,
       SUM(CASE WHEN victory_type = 'runs'    THEN 1 ELSE 0 END) AS by_runs,
       SUM(CASE WHEN victory_type = 'wickets' THEN 1 ELSE 0 END) AS by_wickets,
       SUM(CASE WHEN victory_type = 'innings' THEN 1 ELSE 0 END) AS by_innings,
       COUNT(*) AS total_wins
FROM matches
WHERE winning_team IS NOT NULL AND winning_team <> ''
GROUP BY winning_team
ORDER BY total_wins DESC;""",
    },
}

# ── Filter buttons ────────────────────────────────────────────────────────────
st.markdown("**Filter by difficulty:**")
c1, c2, c3, c4, _ = st.columns([1,1,1,1,5])
if c1.button("🔵 All",          key="f_all"): st.session_state["lvl"] = "All"
if c2.button("🟢 Beginner",     key="f_beg"): st.session_state["lvl"] = "Beginner"
if c3.button("🟡 Intermediate", key="f_mid"): st.session_state["lvl"] = "Intermediate"
if c4.button("🔴 Advanced",     key="f_adv"): st.session_state["lvl"] = "Advanced"

lvl = st.session_state.get("lvl", "All")
st.caption(f"Showing: **{lvl}**")
st.divider()

badge_col = {"Beginner":"#2ecc71","Intermediate":"#f39c12","Advanced":"#e74c3c"}

# ── Render each query ─────────────────────────────────────────────────────────
for title, meta in QUERIES.items():
    if lvl != "All" and meta["level"] != lvl:
        continue

    icon = "🟢" if meta["level"]=="Beginner" else "🟡" if meta["level"]=="Intermediate" else "🔴"
    with st.expander(f"{title}  ·  {icon} {meta['level']}"):
        st.markdown(f"**{meta['desc']}**")

        col_btn, col_sql = st.columns([3,1])
        with col_btn:
            if st.button("▶ Run Query", key=f"run_{title}"):
                with st.spinner("Running…"):
                    df = run_query(meta["sql"])
                if df.empty:
                    st.warning("Query returned no rows (sample data may not cover this scenario).")
                else:
                    st.success(f"{len(df)} row(s)")
                    st.dataframe(df, use_container_width=True)
                    # auto-chart if numeric col exists
                    nums = df.select_dtypes("number").columns.tolist()
                    strs = df.select_dtypes("object").columns.tolist()
                    if nums and strs:
                        try:
                            fig = px.bar(df.head(12), x=strs[0], y=nums[0],
                                         color_discrete_sequence=["#e94560"],
                                         title=f"{nums[0]} by {strs[0]}")
                            fig.update_layout(
                                plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                                font_color="#ddd")
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception:
                            pass

        with col_sql:
            with st.popover("📄 SQL"):
                st.code(meta["sql"].strip(), language="sql")

# ── Custom SQL ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🔧 Custom SQL Query")
custom = st.text_area("Write your own MySQL query:", "SELECT * FROM players LIMIT 10;", height=120)
if st.button("▶ Run Custom SQL", type="primary"):
    df = run_query(custom)
    if df.empty:
        st.warning("No results.")
    else:
        st.success(f"{len(df)} row(s)")
        st.dataframe(df, use_container_width=True)
