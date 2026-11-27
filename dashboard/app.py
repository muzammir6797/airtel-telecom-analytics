import base64
import gzip
import sqlite3
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# Airtel Telecom Analytics | Revenue Intelligence Dashboard
# Database: ../data/raw/airtel.db (relative to this file)
# ------------------------------------------------------------
st.set_page_config(
    page_title="Airtel | Revenue Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "airtel.db"
DB_GZ_PATH = PROJECT_ROOT / "data" / "raw" / "airtel.db.gz"

if not DB_PATH.exists():
    candidates = [
        DB_GZ_PATH,
        Path.cwd() / "data" / "raw" / "airtel.db.gz",
        Path(__file__).resolve().parent / "data" / "raw" / "airtel.db.gz",
    ]
    compressed_db = next((path for path in candidates if path.exists()), None)
    if compressed_db is not None:
        try:
            extracted_db = DB_PATH
            extracted_db.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(compressed_db, "rb") as source, extracted_db.open("wb") as destination:
                shutil.copyfileobj(source, destination)
        except (OSError, gzip.BadGzipFile):
            try:
                extracted_db = Path(tempfile.gettempdir()) / "airtel.db"
                with gzip.open(compressed_db, "rb") as source, extracted_db.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
            except (OSError, gzip.BadGzipFile):
                extracted_db = DB_PATH
        DB_PATH = extracted_db

AIRTEL_LOGO_B64 = ""

# --------------------------- Theme ---------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --airtel:#e40000; --navy:#0b1020; --ink:#172033; --muted:#7c879b; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    /* Full-dashboard Airtel-inspired animated background.
       Keep the animation on the app background itself so it cannot cover
       Streamlit's content or place it behind the app stacking context. */
    .stApp {
      min-height:100vh;
      background:
        radial-gradient(ellipse at 12% 18%,rgba(228,0,0,.24),transparent 32%),
        radial-gradient(ellipse at 86% 22%,rgba(255,45,65,.18),transparent 30%),
        radial-gradient(ellipse at 55% 88%,rgba(120,15,45,.22),transparent 36%),
        linear-gradient(125deg,#080d1d 0%,#11172c 42%,#24101d 100%);
      background-size:150% 150%;
      animation:airtelBackground 22s ease-in-out infinite alternate;
    }
    @keyframes airtelBackground {
      0% {background-position:0% 0%;}
      50% {background-position:55% 35%;}
      100% {background-position:100% 80%;}
    }
    @media (prefers-reduced-motion:reduce) {.stApp {animation:none;}}
    [data-testid="stHeader"] {background:transparent;}
    .block-container {max-width:1680px;padding-top:1rem;padding-bottom:1.3rem;}
    .hero {
      position:relative;overflow:hidden;border-radius:24px;padding:25px 30px 23px;
      color:white;background:
        radial-gradient(ellipse at 78% 5%,rgba(255,0,74,.26),transparent 30%),
        radial-gradient(ellipse at 48% 120%,rgba(0,196,255,.17),transparent 42%),
        linear-gradient(112deg,#080d1d 0%,#101c39 48%,#24102e 78%,#3a1025 100%);
      border:1px solid rgba(255,255,255,.14);box-shadow:0 20px 55px rgba(14,19,48,.28);
      margin-bottom:17px;
    }
    .hero:before {
      content:"";position:absolute;width:460px;height:460px;right:-90px;top:-285px;border-radius:50%;
      border:1px solid rgba(255,255,255,.16);
      box-shadow:0 0 0 35px rgba(255,255,255,.025),0 0 0 75px rgba(255,255,255,.025),
                 0 0 0 120px rgba(255,255,255,.018);
    }
    .hero:after {
      content:"";position:absolute;width:8px;height:8px;right:19%;top:35px;border-radius:50%;
      background:#ff3348;box-shadow:0 0 18px 7px rgba(255,51,72,.5);
    }
    .brand-row {display:flex;align-items:center;gap:14px;position:relative;z-index:2;}
    .airtel-mark {width:54px;height:54px;border-radius:15px;display:flex;align-items:center;justify-content:center;
      background:linear-gradient(145deg,#fff 0%,#ffe7eb 100%);box-shadow:0 0 0 1px rgba(255,255,255,.32),0 8px 22px rgba(228,0,0,.22);}
    .airtel-mark svg {width:42px;height:42px;filter:drop-shadow(0 2px 5px rgba(228,0,0,.18));}
    .brand-name {font-family:'Space Grotesk',sans-serif;font-size:30px;font-weight:700;letter-spacing:-1.7px;color:#fff;}
    .brand-divider {height:42px;width:1px;background:rgba(255,255,255,.23);margin:0 7px;}
    .hero-title {font-family:'Space Grotesk',sans-serif;font-size:25px;font-weight:700;letter-spacing:-.6px;margin:0;}
    .hero-sub {color:#aeb8cc;font-size:10px;margin-top:5px;letter-spacing:1.5px;font-weight:600;}
    .hero-meta {font-size:9px;color:#aeb8cc;letter-spacing:1.3px;}
    .hero-bottom {display:flex;align-items:center;justify-content:space-between;position:relative;z-index:2;margin-top:15px;}
    .live-pill {display:inline-flex;align-items:center;gap:7px;border:1px solid rgba(255,255,255,.20);
      background:rgba(255,255,255,.07);backdrop-filter:blur(8px);border-radius:99px;padding:6px 11px;
      color:#e1e8f7;font-size:9px;letter-spacing:1px;}
    .live-dot {width:6px;height:6px;border-radius:50%;background:#ff344c;box-shadow:0 0 10px #ff344c;}
    .section-label {font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:700;color:#26324a;
      letter-spacing:1.4px;margin:5px 0 10px;}
    .metric {
      position:relative;overflow:hidden;background:linear-gradient(135deg,rgba(255,255,255,.96),rgba(245,247,255,.91));
      border:1px solid rgba(255,255,255,.9);
      border-radius:17px;padding:14px 16px;box-shadow:0 8px 24px rgba(20,34,64,.055);
      min-height:100px;border-top:3px solid #e40000;
    }
    .metric:after {content:"";position:absolute;width:75px;height:75px;border-radius:50%;right:-28px;bottom:-38px;
      background:rgba(228,0,0,.045);}
    .metric-label {font-size:9px;color:#7c879b;font-weight:700;text-transform:uppercase;letter-spacing:1.1px;}
    .metric-value {font-family:'Space Grotesk',sans-serif;font-size:26px;font-weight:700;color:#111a2d;margin-top:6px;letter-spacing:-.6px;}
    .metric-note {font-size:10px;color:#8d97a8;margin-top:2px;}
    .chart-card {
      background:linear-gradient(145deg,rgba(255,255,255,.96),rgba(247,249,255,.90));
      border:1px solid rgba(255,255,255,.95);border-radius:18px;
      padding:14px 15px 7px;box-shadow:0 8px 24px rgba(20,34,64,.045);margin-bottom:13px;
      transition:transform .2s ease,box-shadow .2s ease;
    }
    .chart-heading {font-family:'Space Grotesk',sans-serif;font-size:14px;font-weight:700;color:#172033;margin:0 0 3px;}
    .chart-caption {font-size:10px;color:#8792a5;margin-bottom:10px;}
    div[data-testid="stSelectbox"] label,div[data-testid="stDateInput"] label {font-size:10px!important;color:#68758a!important;}
    div[data-testid="stSelectbox"] [data-baseweb="select"] {font-size:11px;}
    div[data-testid="stTabs"] button {font-weight:700;font-size:12px;}
    div[data-testid="stTabs"] button[aria-selected="true"] {color:#d40000;border-bottom-color:#e40000;}
    div[data-testid="stExpander"] {border:1px solid #e5eaf2;border-radius:13px;background:rgba(255,255,255,.7);}
    div[data-testid="stAlert"] {border-radius:12px;}

    [data-testid="stSidebar"] {
      background:
        radial-gradient(ellipse at 15% 0%,rgba(0,196,255,.20),transparent 34%),
        radial-gradient(ellipse at 100% 65%,rgba(228,0,0,.18),transparent 35%),
        linear-gradient(160deg,#0a1022 0%,#111c37 55%,#21132f 100%);
      border-right:1px solid rgba(255,255,255,.10);
    }
    [data-testid="stSidebar"] * {color:#eaf0ff;}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#aebbd3;font-size:11px;}
    [data-testid="stSidebar"] label {color:#dce6fa!important;font-size:11px!important;font-weight:600!important;}
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
      background:rgba(255,255,255,.09)!important;border:1px solid rgba(255,255,255,.16)!important;
      border-radius:10px!important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] * {color:#fff!important;}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] hr {border-color:rgba(255,255,255,.14);}
    .side-brand {display:flex;align-items:center;gap:10px;margin:4px 0 18px;}
    .side-logo {width:35px;height:35px;border-radius:11px;background:#fff;display:flex;align-items:center;
      justify-content:center;box-shadow:0 0 20px rgba(228,0,0,.25);}
    .side-logo svg {width:27px;height:27px;}
    .side-title {font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:700;color:#fff;}
    .side-kicker {font-size:8px;letter-spacing:1.5px;color:#91a5c8;margin-top:2px;}
    .side-section {font-family:'Space Grotesk',sans-serif;font-size:10px;letter-spacing:1.5px;
      font-weight:700;color:#64d9ff!important;margin:12px 0 7px;}
    .side-status {border:1px solid rgba(91,230,190,.28);background:rgba(37,196,147,.09);
      border-radius:10px;padding:9px 10px;font-size:10px;color:#b9f7e4;margin:10px 0 15px;}
    .side-status span {display:inline-block;width:6px;height:6px;border-radius:50%;background:#3de0a9;
      box-shadow:0 0 9px #3de0a9;margin-right:7px;}

    .footer {text-align:center;color:#9aa4b5;font-size:9px;letter-spacing:1px;padding:9px 0 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="hero-grid"></div>
      <div class="brand-row">
        <div class="airtel-mark">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Airtel logo symbol">
            <path d="M7.137 23.862c.79 0 1.708-.19 2.751-.554 1.55-.538 2.784-1.281 3.986-2.009l.316-.205a29.733 29.733 0 0 0 3.764-2.72 16.574 16.574 0 0 0 5.457-7.529c.395-1.138.949-3.384.268-5.487a7.117 7.117 0 0 0-2.862-3.749c-.158-.126-1.898-1.47-5.203-1.47-3.005 0-6.31 1.107-9.806 3.32l-.11.08-.317.205a20.133 20.133 0 0 0-2.309 1.693C1.585 6.813-.091 9.106.004 11.067c.031.79.427 1.534 1.075 2.008a3.472 3.472 0 0 0 2.214.68c1.803 0 3.765-.948 5.109-1.74l.253-.157.696-.443.237-.158c1.898-1.234 3.875-2.515 6.105-3.258a5.255 5.255 0 0 1 1.55-.285 3.163 3.163 0 0 1 .664.08 2.112 2.112 0 0 1 1.47 1.106c.523 1.012.396 2.61-.316 4.08a17.871 17.871 0 0 1-4.887 5.836 19.488 19.488 0 0 1-3.194 2.215l-.095.031a9.634 9.634 0 0 1-1.471.696l-.08.032-.41.158c-2.23.57-.87-1.329-.87-1.329.474-.537.98-1.028 1.518-1.502.316-.269.633-.554.933-.854l.064-.063c.395-.38.933-.902.901-1.645-.047-.98-1.075-1.582-2.056-1.613h-.063c-.95 0-1.819.522-2.404.98a7.27 7.27 0 0 0-1.598 1.74c-.6.901-1.85 3.226-.632 5.077.49.743 1.313 1.123 2.42 1.123z" fill="#E40000"/>
          </svg>
        </div>
        <span class="brand-name">airtel</span>
        <span class="brand-divider"></span>
        <div>
          <div class="hero-title">Telecom Revenue Intelligence</div>
          <div class="hero-sub">REVENUE PERFORMANCE &nbsp;•&nbsp; CUSTOMER VALUE &nbsp;•&nbsp; FINANCE ANALYTICS</div>
        </div>
      </div>
      <div class="hero-bottom">
        <span class="live-pill"><span class="live-dot"></span> LIVE ANALYTICS VIEW</span>
        <span class="hero-meta">FINANCE COMMAND CENTRE &nbsp; / &nbsp; INDIA</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------ Data access ------------------------
@st.cache_data(show_spinner="Loading Airtel data...")
def load_data(db_path: str):
    con = sqlite3.connect(db_path)
    try:
        recharges = pd.read_sql_query(
            """
            SELECT r.recharge_id, r.customer_id, r.recharge_date, r.amount_inr,
                   r.plan_id, r.channel, r.txn_type,
                   c.connection_type, c.circle_id, ci.circle_name, ci.region,
                   p.plan_name, p.plan_type
            FROM recharges r
            LEFT JOIN customers c ON r.customer_id = c.customer_id
            LEFT JOIN circles ci ON c.circle_id = ci.circle_id
            LEFT JOIN plans p ON r.plan_id = p.plan_id
            WHERE r.recharge_date >= '2025-01-01'
              AND r.recharge_date < '2025-07-01'
            """, con
        )
        features = pd.read_sql_query(
            """
            SELECT customer_id, circle_name, region, plan_name, plan_type,
                   connection_type, age_band, gender, device_type,
                   stated_arpu, actual_arpu_6m, arpu_gap,
                   recharge_total_6m, recharge_count, complaint_count
            FROM customer_features
            """, con
        )
    finally:
        con.close()
    recharges["recharge_date"] = pd.to_datetime(recharges["recharge_date"], errors="coerce")
    recharges["month"] = recharges["recharge_date"].dt.to_period("M").dt.to_timestamp()
    for col in ["amount_inr", "stated_arpu", "actual_arpu_6m", "arpu_gap", "recharge_total_6m"]:
        if col in recharges.columns:
            recharges[col] = pd.to_numeric(recharges[col], errors="coerce")
        if col in features.columns:
            features[col] = pd.to_numeric(features[col], errors="coerce")
    return recharges, features

def money(value):
    return f"₹{value:,.0f}"

def metric(label, value, note=""):
    st.markdown(
        f'<div class="metric"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

def chart_frame(fig, height=300):
    fig.update_layout(
        height=height, margin=dict(l=12,r=12,t=25,b=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", size=10, color="#344054"),
        colorway=["#E40000", "#276EF1", "#7B4DFF", "#00A8A8", "#F59E0B"],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="#151b2c", font_color="white"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e7eaf1", zeroline=False)
    fig.update_yaxes(gridcolor="#e4e9f3", zeroline=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def chart_type(key, options=("Bar", "Line", "Area", "Scatter", "Treemap")):
    variety = ["Bar", "Line", "Area", "Scatter", "Pie", "Donut", "Treemap",
               "Sunburst", "Histogram", "Box", "Violin", "Funnel", "Waterfall"]
    # Put the chart's original choices first, then expose additional styles.
    choices = list(dict.fromkeys(list(options) + variety))
    return st.selectbox("Chart style", choices, key=f"{key}_type", label_visibility="collapsed")

def make_chart(df, x, y, kind, color=None, title=None, labels=None):
    labels = labels or {}
    if df.empty:
        st.info("No records match this chart's filters.")
        return

    # Drop unusable rows for the selected dimensions.
    plot_df = df.copy()
    if x in plot_df.columns:
        plot_df = plot_df.dropna(subset=[x])
    if y in plot_df.columns:
        plot_df[y] = pd.to_numeric(plot_df[y], errors="coerce")
        plot_df = plot_df.dropna(subset=[y])
    if plot_df.empty:
        st.info("There is no numeric data available for this chart style.")
        return

    if kind == "Line":
        fig = px.line(plot_df, x=x, y=y, color=color, markers=True, labels=labels, title=title)
    elif kind == "Area":
        fig = px.area(plot_df, x=x, y=y, color=color, labels=labels, title=title)
    elif kind == "Scatter":
        fig = px.scatter(plot_df, x=x, y=y, color=color, labels=labels, title=title)
    elif kind == "Pie":
        fig = px.pie(plot_df, names=x, values=y, color=color, labels=labels, title=title)
    elif kind == "Donut":
        fig = px.pie(plot_df, names=x, values=y, color=color, hole=.58, labels=labels, title=title)
    elif kind == "Treemap":
        fig = px.treemap(plot_df, path=[x], values=y, color=y,
                         color_continuous_scale=["#ffd5dc", "#e50920"], labels=labels, title=title)
    elif kind == "Sunburst":
        fig = px.sunburst(plot_df, path=[x], values=y, color=y,
                          color_continuous_scale=["#ffd5dc", "#e50920"], labels=labels, title=title)
    elif kind == "Histogram":
        fig = px.histogram(plot_df, x=y, color=color, nbins=18, labels=labels, title=title)
    elif kind == "Box":
        fig = px.box(plot_df, x=x, y=y, color=color, points="outliers", labels=labels, title=title)
    elif kind == "Violin":
        fig = px.violin(plot_df, x=x, y=y, color=color, box=True, points="outliers", labels=labels, title=title)
    elif kind == "Funnel":
        funnel_df = plot_df.groupby(x, as_index=False)[y].sum().sort_values(y, ascending=False)
        fig = px.funnel(funnel_df, x=y, y=x, labels=labels, title=title)
    elif kind == "Waterfall":
        waterfall_df = plot_df.groupby(x, as_index=False)[y].sum()
        fig = go.Figure(go.Waterfall(
            x=waterfall_df[x].astype(str), y=waterfall_df[y],
            connector={"line": {"color": "rgba(120,130,150,.45)"}},
            increasing={"marker": {"color": "#E40000"}},
            decreasing={"marker": {"color": "#7B4DFF"}},
            totals={"marker": {"color": "#276EF1"}},
        ))
        fig.update_layout(title=title, xaxis_title=labels.get(x, x), yaxis_title=labels.get(y, y))
    else:
        fig = px.bar(plot_df, x=x, y=y, color=color, barmode="group", labels=labels, title=title)

    if kind == "Bar":
        fig.update_traces(marker_line_width=0)
    chart_frame(fig)

def region_filter(df, key):
    opts = ["All regions"] + sorted([str(v) for v in df["region"].dropna().unique()])
    choice = st.selectbox("Region", opts, key=f"{key}_region")
    return df if choice == "All regions" else df[df["region"] == choice]

def connection_filter(df, key):
    opts = ["All connections"] + sorted([str(v) for v in df["connection_type"].dropna().unique()])
    choice = st.selectbox("Connection", opts, key=f"{key}_connection")
    return df if choice == "All connections" else df[df["connection_type"] == choice]

if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}. Keep the database at data/raw/airtel.db and place this file inside the dashboard folder.")
    st.stop()

try:
    recharges, features = load_data(str(DB_PATH))
except Exception as exc:
    st.error("The dashboard UI loaded, but the database query failed.")
    st.exception(exc)
    st.info("Check that airtel.db has the tables and columns used by this dashboard.")
    st.stop()

if recharges.empty or features.empty:
    st.error("The Airtel database loaded, but the required tables contain no rows.")
    st.stop()


# ---------------------- Global sidebar -----------------------
with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
          <div class="side-logo">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-label="Airtel">
              <path d="M7.137 23.862c.79 0 1.708-.19 2.751-.554 1.55-.538 2.784-1.281 3.986-2.009l.316-.205a29.733 29.733 0 0 0 3.764-2.72 16.574 16.574 0 0 0 5.457-7.529c.395-1.138.949-3.384.268-5.487a7.117 7.117 0 0 0-2.862-3.749c-.158-.126-1.898-1.47-5.203-1.47-3.005 0-6.31 1.107-9.806 3.32l-.11.08-.317.205a20.133 20.133 0 0 0-2.309 1.693C1.585 6.813-.091 9.106.004 11.067c.031.79.427 1.534 1.075 2.008a3.472 3.472 0 0 0 2.214.68c1.803 0 3.765-.948 5.109-1.74l.253-.157.696-.443.237-.158c1.898-1.234 3.875-2.515 6.105-3.258a5.255 5.255 0 0 1 1.55-.285 3.163 3.163 0 0 1 .664.08 2.112 2.112 0 0 1 1.47 1.106c.523 1.012.396 2.61-.316 4.08a17.871 17.871 0 0 1-4.887 5.836 19.488 19.488 0 0 1-3.194 2.215l-.095.031a9.634 9.634 0 0 1-1.471.696l-.08.032-.41.158c-2.23.57-.87-1.329-.87-1.329.474-.537.98-1.028 1.518-1.502.316-.269.633-.554.933-.854l.064-.063c.395-.38.933-.902.901-1.645-.047-.98-1.075-1.582-2.056-1.613h-.063c-.95 0-1.819.522-2.404.98a7.27 7.27 0 0 0-1.598 1.74c-.6.901-1.85 3.226-.632 5.077.49.743 1.313 1.123 2.42 1.123z" fill="#E40000"/>
            </svg>
          </div>
          <div><div class="side-title">airtel analytics</div><div class="side-kicker">REVENUE CONTROL PANEL</div></div>
        </div>
        <div class="side-status"><span></span> DATABASE CONNECTED &nbsp; • &nbsp; JAN–JUN 2025</div>
        <div class="side-section">GLOBAL FILTERS</div>
        """,
        unsafe_allow_html=True,
    )
    region_options = ["All regions"] + sorted(features["region"].dropna().astype(str).unique().tolist())
    connection_options = ["All connections"] + sorted(features["connection_type"].dropna().astype(str).unique().tolist())
    plan_options = ["All plans"] + sorted(features["plan_type"].dropna().astype(str).unique().tolist())
    selected_region = st.selectbox("Operating region", region_options, key="sidebar_region")
    selected_connection = st.selectbox("Connection segment", connection_options, key="sidebar_connection")
    selected_plan = st.selectbox("Plan category", plan_options, key="sidebar_plan")
    st.markdown("---")
    st.markdown('<div class="side-section">QUICK INSIGHTS</div>', unsafe_allow_html=True)
    st.metric("Subscriber base", f"{features['customer_id'].nunique():,}")
    st.metric("Recharge records", f"{recharges['recharge_id'].nunique():,}")
    st.caption("Use the chart controls on each card to change its visualization independently.")
    if st.button("↻  Reset all filters", use_container_width=True):
        for key in ["sidebar_region", "sidebar_connection", "sidebar_plan"]:
            st.session_state.pop(key, None)
        st.rerun()

# Apply sidebar filters consistently to both tabs and headline KPIs.
if selected_region != "All regions":
    features = features[features["region"].astype(str) == selected_region].copy()
    recharges = recharges[recharges["region"].astype(str) == selected_region].copy()
if selected_connection != "All connections":
    features = features[features["connection_type"].astype(str) == selected_connection].copy()
    recharges = recharges[recharges["connection_type"].astype(str) == selected_connection].copy()
if selected_plan != "All plans":
    features = features[features["plan_type"].astype(str) == selected_plan].copy()
    recharges = recharges[recharges["plan_type"].astype(str) == selected_plan].copy()

# ------------------------- KPI row ---------------------------
received = float(recharges["amount_inr"].fillna(0).sum())
payments = int(recharges["recharge_id"].nunique())
subscribers = int(features["customer_id"].nunique())
postpaid = features[features["connection_type"].astype(str).str.lower() == "postpaid"]
prepaid = features[features["connection_type"].astype(str).str.lower() == "prepaid"]
revenue_total = float(features["actual_arpu_6m"].fillna(0).sum())
postpaid_share = (float(postpaid["actual_arpu_6m"].sum()) / revenue_total * 100) if revenue_total else 0
prepaid_share = (float(prepaid["actual_arpu_6m"].sum()) / revenue_total * 100) if revenue_total else 0

k = st.columns(4)
with k[0]: metric("Subscribers", f"{subscribers:,}", "Unique subscriber base")
with k[1]: metric("Received revenue", f"₹{received/1e7:.2f} Cr", "Jan–Jun 2025 recharge transactions")
with k[2]: metric("Recharge transactions", f"{payments:,}", "Jan–Jun 2025")
with k[3]: metric("Postpaid revenue share", f"{postpaid_share:.1f}%", f"Prepaid share: {prepaid_share:.1f}%")

st.markdown('<div class="section-label">REVENUE WORKSPACE</div>', unsafe_allow_html=True)
tab1, tab2 = st.tabs(["◈  Executive Overview", "▤  Revenue Deep Dive"])

# ======================== TAB 1 ==============================
with tab1:
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="chart-card"><div class="chart-heading">01 / Monthly received revenue</div><div class="chart-caption">Recharge value received by month • Jan–Jun 2025</div>', unsafe_allow_html=True)
        f = recharges.copy()
        a,b = st.columns(2)
        with a: kind = chart_type("monthly_rev", ("Bar","Line","Area","Scatter"))
        with b: channel = st.selectbox("Channel", ["All channels"] + sorted(f["channel"].dropna().astype(str).unique()), key="monthly_channel")
        if channel != "All channels": f = f[f["channel"].astype(str) == channel]
        monthly = f.groupby("month", as_index=False).agg(revenue=("amount_inr","sum"), transactions=("recharge_id","nunique"))
        make_chart(monthly, "month", "revenue", kind, labels={"month":"Month","revenue":"Received revenue (₹)"})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="chart-card"><div class="chart-heading">02 / Revenue by plan</div><div class="chart-caption">Actual monthly ARPU contribution by plan • customer-feature grain</div>', unsafe_allow_html=True)
        f = features.copy()
        a,b = st.columns(2)
        with a: kind = chart_type("plan_rev", ("Bar","Treemap","Scatter"))
        with b:
            plan_type = st.selectbox("Plan type", ["All plans"] + sorted(f["plan_type"].dropna().astype(str).unique()), key="plan_rev_filter")
        if plan_type != "All plans": f = f[f["plan_type"].astype(str) == plan_type]
        f = region_filter(f, "plan_rev")
        plan = f.groupby("plan_name", as_index=False).agg(revenue=("actual_arpu_6m","sum"), subscribers=("customer_id","nunique"))
        plan = plan.sort_values("revenue", ascending=False).head(12)
        make_chart(plan, "plan_name", "revenue", kind, labels={"plan_name":"Plan","revenue":"Actual ARPU total (₹)"})
        st.markdown('</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="chart-card"><div class="chart-heading">03 / Subscriber mix vs revenue mix</div><div class="chart-caption">How subscriber share compares with actual revenue share</div>', unsafe_allow_html=True)
        f = connection_filter(features.copy(), "mix")
        a,b = st.columns(2)
        with a: kind = chart_type("mix_chart", ("Bar","Line","Scatter","Area"))
        with b: metric_choice = st.selectbox("Segment", ["Connection type","Plan type","Region"], key="mix_segment")
        dim = {"Connection type":"connection_type","Plan type":"plan_type","Region":"region"}[metric_choice]
        mix = f.groupby(dim, as_index=False).agg(subscribers=("customer_id","nunique"), revenue=("actual_arpu_6m","sum"))
        mix["subscriber_share"] = mix["subscribers"] / max(mix["subscribers"].sum(),1) * 100
        mix["revenue_share"] = mix["revenue"] / max(mix["revenue"].sum(),1) * 100
        plot_mix = mix.melt(id_vars=dim, value_vars=["subscriber_share","revenue_share"], var_name="share_type", value_name="share")
        make_chart(plot_mix, dim, "share", kind, color="share_type", labels={dim:metric_choice,"share":"Share (%)","share_type":"Share"})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="chart-card"><div class="chart-heading">04 / Revenue concentration by decile</div><div class="chart-caption">Subscribers ranked by six-month recharge total • decile 1 is highest spend</div>', unsafe_allow_html=True)
        a,b = st.columns(2)
        with a: kind = chart_type("decile", ("Bar","Line","Area","Scatter"))
        with b: sort_choice = st.selectbox("Measure", ["Revenue share (%)","Recharge revenue (₹)"], key="decile_measure")
        dec = features[["customer_id","recharge_total_6m"]].copy()
        dec["recharge_total_6m"] = pd.to_numeric(dec["recharge_total_6m"], errors="coerce").fillna(0)
        dec["decile"] = pd.qcut(dec["recharge_total_6m"].rank(method="first", ascending=False), 10, labels=False) + 1
        dec = dec.groupby("decile", as_index=False).agg(revenue=("recharge_total_6m","sum"), subscribers=("customer_id","nunique"))
        dec["revenue_share"] = dec["revenue"] / max(dec["revenue"].sum(),1) * 100
        y = "revenue_share" if sort_choice == "Revenue share (%)" else "revenue"
        make_chart(dec, "decile", y, kind, labels={"decile":"Spend decile (1 = highest)","revenue_share":"Revenue share (%)","revenue":"Six-month recharge total (₹)"})
        st.markdown('</div>', unsafe_allow_html=True)

# ======================== TAB 2 ==============================
with tab2:
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="chart-card"><div class="chart-heading">05 / Actual vs stated ARPU</div><div class="chart-caption">Compare average ARPU values and the gap across plans</div>', unsafe_allow_html=True)
        f = features.copy()
        a,b = st.columns(2)
        with a: kind = chart_type("arpu_compare", ("Bar","Line","Scatter","Area"))
        with b: plan_type = st.selectbox("Plan category", ["All plans"] + sorted(f["plan_type"].dropna().astype(str).unique()), key="arpu_plan_filter")
        if plan_type != "All plans": f = f[f["plan_type"].astype(str) == plan_type]
        f = region_filter(f, "arpu")
        arpu = f.groupby("plan_name", as_index=False).agg(stated=("stated_arpu","mean"), actual=("actual_arpu_6m","mean"))
        arpu = arpu.sort_values("actual", ascending=False).head(12)
        arpu_plot = arpu.melt(id_vars="plan_name", value_vars=["stated","actual"], var_name="ARPU type", value_name="ARPU (₹)")
        make_chart(arpu_plot, "plan_name", "ARPU (₹)", kind, color="ARPU type", labels={"plan_name":"Plan"})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="chart-card"><div class="chart-heading">06 / Recharge channel performance</div><div class="chart-caption">Transaction value and payment count by recharge channel</div>', unsafe_allow_html=True)
        f = recharges.copy()
        a,b = st.columns(2)
        with a: kind = chart_type("channel_perf", ("Bar","Treemap","Scatter"))
        with b: measure = st.selectbox("Metric", ["Received revenue (₹)","Transactions"], key="channel_metric")
        channel_df = f.groupby("channel", as_index=False).agg(revenue=("amount_inr","sum"), transactions=("recharge_id","nunique"))
        y = "revenue" if measure == "Received revenue (₹)" else "transactions"
        make_chart(channel_df, "channel", y, kind, labels={"channel":"Channel","revenue":"Revenue (₹)","transactions":"Transactions"})
        st.markdown('</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="chart-card"><div class="chart-heading">07 / Transaction type analysis</div><div class="chart-caption">Recharge transaction mix by transaction type</div>', unsafe_allow_html=True)
        f = recharges.copy()
        a,b = st.columns(2)
        with a: kind = chart_type("txn_type", ("Bar","Treemap","Scatter"))
        with b: measure = st.selectbox("Metric", ["Revenue (₹)","Transaction count"], key="txn_metric")
        txn = f.groupby("txn_type", as_index=False).agg(revenue=("amount_inr","sum"), transactions=("recharge_id","nunique"))
        y = "revenue" if measure == "Revenue (₹)" else "transactions"
        make_chart(txn, "txn_type", y, kind, labels={"txn_type":"Transaction type","revenue":"Revenue (₹)","transactions":"Transactions"})
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="chart-card"><div class="chart-heading">08 / Regional revenue performance</div><div class="chart-caption">Actual ARPU contribution by Airtel region</div>', unsafe_allow_html=True)
        f = features.copy()
        a,b = st.columns(2)
        with a: kind = chart_type("region_perf", ("Bar","Treemap","Scatter"))
        with b: conn = st.selectbox("Connection type", ["All connections"] + sorted(f["connection_type"].dropna().astype(str).unique()), key="region_conn")
        if conn != "All connections": f = f[f["connection_type"].astype(str) == conn]
        reg = f.groupby("region", as_index=False).agg(revenue=("actual_arpu_6m","sum"), subscribers=("customer_id","nunique"))
        make_chart(reg, "region", "revenue", kind, labels={"region":"Region","revenue":"Actual ARPU total (₹)"})
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("View data quality and metric definitions"):
        st.markdown(
            """
            - **Received revenue:** sum of `recharges.amount_inr` for transactions dated 1 Jan–30 Jun 2025.
            - **Actual ARPU:** `customer_features.actual_arpu_6m`; kept separate from six-month recharge total.
            - **Stated ARPU:** `customer_features.stated_arpu`.
            - **Spend deciles:** subscribers ranked by `recharge_total_6m`; decile 1 is highest spend.
            - **Subscriber base:** unique `customer_id` values in `customer_features`.
            """
        )

st.markdown('<div class="footer">AIRTEL TELECOM ANALYTICS • FINANCE DASHBOARD • SOURCE: airtel.db</div>', unsafe_allow_html=True)
