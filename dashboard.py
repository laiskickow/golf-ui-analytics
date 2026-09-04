import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from io import BytesIO
from datetime import datetime
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric, OrderBy,
    FilterExpression, Filter,
)
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

PROPERTY_ID = "533271514"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
DIR = Path(__file__).parent
IST_OFFSET = 1

LABELS = {
    "golf_nav_view": "Page Navigation",
    "golf_toggle_kill_switch": "Kill-Switch Toggle",
    "golf_adjust_player_nudge": "Player Nudge",
    "golf_adjust_hole_nudge": "Hole Nudge",
    "golf_toggle_view_mode": "View Mode Toggle",
    "golf_select_round_tab": "Round Tab Select",
    "golf_open_player_view": "Open Player View",
    "golf_toggle_player": "Toggle Player",
    "golf_pre_round_prices_expand": "Pre-Round Prices",
    "golf_search_player": "Player Search",
    "golf_click_setup": "Setup Button",
    "golf_leaderboard_switch_view": "View Switch (LB)",
    "golf_click_button_group": "View Switch (LB)",
    "golf_adjust_nudge": "Course Nudge (removed)",
    "golf_course_adjust_rough": "Rough Difficulty",
    "golf_course_adjust_morning_wave": "Morning Wave",
    "golf_course_adjust_afternoon_wave": "Afternoon Wave",
    "golf_course_adjust_hole_early_hd": "Hole Early HD",
    "golf_course_adjust_hole_early_par": "Hole Early Par",
    "golf_course_adjust_hole_late_hd": "Hole Late HD",
    "golf_course_adjust_hole_late_par": "Hole Late Par",
    "golf_toggle_favourite": "Toggle Favourite",
    "golf_toggle_group_expand": "Expand Group",
    "golf_open_hole_insights": "Hole Insights",
    "golf_open_hole_configure": "Hole Configure",
    "golf_modal_adjust_nudge": "Sidebar Nudge",
    "golf_click_tournament_selector": "Tournament Selector",
    "golf_action_click_load_tournament": "Load Tournament",
    "golf_perf_load_page_timing": "Page Load Time",
    "golf_error_fail_js_error": "JS Error",
    "golf_scroll_depth": "Scroll Depth",
    "golf_scroll_horizontal": "Horizontal Scroll (Rounds)",
    "page_view": "Page View",
    "session_start": "Session Start",
    "first_visit": "First Visit",
    "user_engagement": "Active Focus",
}

EVENT_ALIASES = {
    "kill_switch": ["golf_toggle_kill_switch"],
    "nudge_all": [
        "golf_adjust_player_nudge", "golf_adjust_hole_nudge", "golf_adjust_nudge", "golf_modal_adjust_nudge",
        "golf_course_adjust_rough", "golf_course_adjust_morning_wave", "golf_course_adjust_afternoon_wave",
        "golf_course_adjust_hole_early_hd", "golf_course_adjust_hole_early_par",
        "golf_course_adjust_hole_late_hd", "golf_course_adjust_hole_late_par",
    ],
    "nudge_player": ["golf_adjust_player_nudge"],
    "nudge_hole": ["golf_adjust_hole_nudge"],
    "nudge_course": ["golf_adjust_nudge"],
    "nudge_course_rough": ["golf_course_adjust_rough"],
    "nudge_course_morning": ["golf_course_adjust_morning_wave"],
    "nudge_course_afternoon": ["golf_course_adjust_afternoon_wave"],
    "nudge_course_level": [
        "golf_course_adjust_rough", "golf_course_adjust_morning_wave", "golf_course_adjust_afternoon_wave",
    ],
    "nudge_hole_early_hd": ["golf_course_adjust_hole_early_hd"],
    "nudge_hole_early_par": ["golf_course_adjust_hole_early_par"],
    "nudge_hole_late_hd": ["golf_course_adjust_hole_late_hd"],
    "nudge_hole_late_par": ["golf_course_adjust_hole_late_par"],
    "nudge_hole_course": [
        "golf_course_adjust_hole_early_hd", "golf_course_adjust_hole_early_par",
        "golf_course_adjust_hole_late_hd", "golf_course_adjust_hole_late_par",
    ],
    "nudge_modal": ["golf_modal_adjust_nudge"],
    "preround": ["golf_pre_round_prices_expand"],
    "search": ["golf_search_player"],
    "round_tab": ["golf_select_round_tab"],
    "favourite": ["golf_toggle_favourite"],
    "group_expand": ["golf_toggle_group_expand"],
    "player_view": ["golf_open_player_view"],
    "player_toggle": ["golf_toggle_player"],
    "hole_insights": ["golf_open_hole_insights"],
    "hole_configure": ["golf_open_hole_configure"],
    "setup": ["golf_click_setup"],
}

NEW_TRACKING_EVENTS = [
    ("golf_toggle_favourite", "Toggle Favourite (Participants & Rounds)"),
    ("golf_open_player_view", "Open Player View"),
    ("golf_toggle_player", "Toggle Player"),
    ("golf_toggle_group_expand", "Expand Group"),
    ("golf_open_hole_insights", "Hole Insights"),
    ("golf_click_setup", "Setup Button"),
    ("golf_scroll_depth", "Scroll Depth"),
    ("golf_scroll_horizontal", "Horizontal Scroll"),
    ("golf_leaderboard_switch_view", "View Switch (LB)"),
    ("golf_toggle_view_mode", "All vs Enabled Toggle"),
    ("golf_pre_round_prices_expand", "Pre-round Expand"),
]

SECTIONS = [
    "Overview",
    "Pages Viewed",
    "Trader Actions",
    "Demographics",
    "Errors & Performance",
    "Event Trends",
]

# ── Light-only palette with strong contrast ─────────────────────
T = {
    "bg": "#F3F4F6",
    "surface": "#FFFFFF",
    "surface_alt": "#FFFFFF",
    "border": "#D5DAE1",
    "border_strong": "#B0B8C4",
    "text": "#111827",
    "text_secondary": "#374151",
    "text_muted": "#6B7280",
    "accent": "#1D4ED8",
    "accent_light": "#DBEAFE",
    "success": "#15803D",
    "success_light": "#DCFCE7",
    "warning": "#A16207",
    "warning_light": "#FEF9C3",
    "danger": "#B91C1C",
    "danger_light": "#FEE2E2",
    "chart_grid": "#E5E7EB",
    "chart_text": "#374151",
}

PAGE_COLORS = {
    "Rounds": "#60A5FA",
    "Course Management": "#4ADE80",
    "Leaderboard": "#FBBF24",
    "Participants": "#A78BFA",
    "Other": "#9CA3AF",
}

CHART_COLORS = ["#60A5FA", "#4ADE80", "#FBBF24", "#F87171", "#A78BFA", "#F472B6", "#38BDF8", "#9CA3AF"]

ROUND_COLORS = {
    "R1": "#60A5FA",
    "R2": "#4ADE80",
    "R3": "#FBBF24",
    "R4": "#F87171",
}


def label(ev):
    return LABELS.get(ev, ev.replace("_", " ").replace("-", " ").title())


def esum(alias, counts=None):
    counts = counts or {}
    return sum(counts.get(e, 0) for e in EVENT_ALIASES.get(alias, [alias]))


def get_credentials():
    if "ga4" in st.secrets:
        creds = Credentials(
            token=None,
            refresh_token=st.secrets["ga4"]["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=st.secrets["ga4"]["client_id"],
            client_secret=st.secrets["ga4"]["client_secret"],
            scopes=SCOPES,
        )
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        return creds

    token_file = DIR / "token.json"
    client_secret_file = DIR / "client_secret.json"
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), SCOPES)
            creds = flow.run_local_server(port=8085)
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return creds


@st.cache_data(ttl=600)
def fetch(dims, mets, start="30daysAgo", end="today", filter_event=None, filter_match="EXACT", limit=10000, user_email=None):
    creds = get_credentials()
    client = BetaAnalyticsDataClient(credentials=creds)
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in mets],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name=dims[0]))] if dims else [],
        limit=limit,
    )
    filters = []
    if filter_event:
        mt = Filter.StringFilter.MatchType.EXACT if filter_match == "EXACT" else Filter.StringFilter.MatchType.BEGINS_WITH
        filters.append(FilterExpression(filter=Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(value=filter_event, match_type=mt),
        )))
    if user_email:
        filters.append(FilterExpression(filter=Filter(
            field_name="customUser:user_email",
            string_filter=Filter.StringFilter(value=user_email, match_type=Filter.StringFilter.MatchType.EXACT),
        )))
    if len(filters) == 1:
        req.dimension_filter = filters[0]
    elif len(filters) > 1:
        req.dimension_filter = FilterExpression(
            and_group=FilterExpression.AndGroup(expressions=filters)
        )
    resp = client.run_report(req)
    rows = [[dv.value for dv in r.dimension_values] + [mv.value for mv in r.metric_values] for r in resp.rows]
    df = pd.DataFrame(rows, columns=dims + mets)
    for m in mets:
        df[m] = pd.to_numeric(df[m], errors="coerce")
    return df


def try_fetch(dims, mets, *args, **kwargs):
    try:
        if "user_email" not in kwargs and "active_email_filter" in globals() and active_email_filter:
            kwargs["user_email"] = active_email_filter
        return fetch(dims, mets, *args, **kwargs)
    except Exception:
        return pd.DataFrame(columns=dims + mets)


def delta(cur, prev):
    if prev == 0:
        return None
    pct = round((cur - prev) / prev * 100)
    return f"{pct}%" if pct >= 0 else f"{pct}%"


def fmt_time(s):
    return f"{int(s) // 60}m {int(s) % 60:02d}s"


def extract_page(path):
    p = str(path).lower()
    if "course-management" in p:
        return "Course Management"
    if "participants" in p:
        return "Participants"
    if "leaderboard" in p:
        return "Leaderboard"
    if "rounds" in p or "hole" in p or "group" in p or "player" in p:
        return "Rounds"
    return "Other"


def cl(height=280, show_legend=False, legend_top=False):
    layout = dict(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color=T["chart_text"]),
        showlegend=show_legend,
    )
    if legend_top and show_legend:
        layout["legend"] = dict(
            orientation="h", y=1.12, x=0,
            font=dict(size=11, color=T["text_secondary"]),
            bgcolor="rgba(0,0,0,0)",
        )
    return layout


# ── PAGE CONFIG ──────────────────────────────────────────────────
st.set_page_config(page_title="Golf UI Analytics", layout="wide", initial_sidebar_state="collapsed")

if "ga4" not in st.secrets and not (DIR / "client_secret.json").exists():
    st.error("Missing credentials — add client_secret.json locally or configure st.secrets for cloud deployment.")
    st.stop()

# ── CSS ──────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {{
        background-color: {T["bg"]};
        color: {T["text"]};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    .stApp header {{
        background-color: {T["bg"]} !important;
    }}

    div[data-testid="stMetric"] {{
        background: #FFFFFF !important;
        border: 1px solid {T["border"]};
        border-radius: 10px;
        padding: 0.85rem 1rem;
        min-height: 100%;
        height: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    div[data-testid="stMetric"] label {{
        color: {T["text_muted"]} !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {T["text"]} !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }}
    [data-testid="stMetricDelta"] > div {{
        font-size: 0.7rem;
    }}

    /* White background on border containers (st.container(border=True)) */
    div[data-testid="stVerticalBlock"].st-emotion-cache-1ne20ew {{
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
    }}
    /* Main content wrapper must be transparent so grey page bg shows through */
    .stMainBlockContainer {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    /* Columns and non-card blocks: transparent */
    .stColumn,
    div[data-testid="stVerticalBlock"]:not(.st-emotion-cache-1ne20ew) {{
        background: transparent !important;
        background-color: transparent !important;
    }}

    /* Gap spacers must stay transparent */
    .section-gap,
    .section-gap * {{
        background: transparent !important;
        background-color: transparent !important;
    }}

    /* Spacing between top-level section cards */
    .section-gap {{
        height: 20px;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
    }}

    /* Equal-height columns */
    div[data-testid="stHorizontalBlock"] {{
        align-items: stretch !important;
    }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
        display: flex;
        flex-direction: column;
    }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div {{
        flex: 1;
    }}

    section[data-testid="stSidebar"] > div {{
        padding-top: 1rem;
        background-color: {T["surface"]};
    }}

    .dash-section {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.6rem 0;
        margin-bottom: 0.5rem;
    }}
    .dash-section .num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 7px;
        background: {T["accent"]};
        color: #FFFFFF;
        font-size: 0.72rem;
        font-weight: 700;
        flex-shrink: 0;
    }}
    .dash-section h2 {{
        margin: 0;
        font-size: 1.05rem;
        font-weight: 600;
        color: {T["text"]};
    }}
    .dash-section .subtitle {{
        font-size: 0.78rem;
        color: {T["text_muted"]};
        margin-left: auto;
    }}

    .top-bar {{
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem 0 1rem 0;
        margin-bottom: 0.5rem;
    }}
    .top-bar h1 {{
        margin: 0;
        font-size: 1.68rem;
        font-weight: 700;
        color: {T["text"]};
        flex: 1;
    }}
    .top-bar-sub {{
        font-size: 0.82rem;
        color: {T["text_muted"]};
        margin: -0.4rem 0 0.5rem 0;
        line-height: 1.4;
    }}

    hr {{
        border-color: {T["border"]} !important;
    }}

    .stCaption, [data-testid="stCaptionContainer"] {{
        color: {T["text_muted"]} !important;
    }}

    .tag-ref {{
        font-size: 0.78rem;
    }}
    .tag-ref td {{
        padding: 0.3rem 0.5rem;
        border-bottom: 1px solid {T["border"]};
        color: {T["text"]};
    }}
    .tag-ref .ev {{
        font-family: 'SF Mono', 'Fira Code', monospace;
        font-size: 0.7rem;
        color: {T["text_secondary"]};
    }}
    .tag-ref .cnt {{
        text-align: right;
        color: {T["text_muted"]};
        font-size: 0.72rem;
    }}

    .stSelectbox label, .stMultiSelect label {{
        color: {T["text_secondary"]} !important;
    }}
    .stRadio label {{
        color: {T["text_secondary"]} !important;
    }}

    [data-testid="stPopover"] {{
        background: {T["surface"]} !important;
    }}

    /* Round tab detail cards */
    .round-card {{
        background: {T["surface_alt"]};
        border: 1px solid {T["border"]};
        border-radius: 8px;
        padding: 0.65rem 0.85rem;
        margin-bottom: 0.35rem;
    }}
    .round-card .round-label {{
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.2rem;
    }}
    .round-card .round-val {{
        font-size: 1.15rem;
        font-weight: 600;
        color: {T["text"]};
    }}
    .round-card .round-time {{
        font-size: 0.75rem;
        color: {T["text_muted"]};
    }}
</style>
""", unsafe_allow_html=True)


# ── HEADER + FILTERS CARD ────────────────────────────────────────
all_users_df = try_fetch(["customUser:user_email"], ["activeUsers"], "30daysAgo")
email_options = []
if not all_users_df.empty:
    clean_emails = all_users_df[~all_users_df["customUser:user_email"].isin(["(not set)", ""])]
    if not clean_emails.empty:
        email_options = sorted(clean_emails["customUser:user_email"].tolist())

with st.container(border=True):
    st.markdown('<div class="top-bar"><h1>Golf UI Analytics</h1></div>', unsafe_allow_html=True)
    st.markdown('<p class="top-bar-sub">GA4 analytics for the Golf trading UI. Data is pulled from Google Analytics and may have up to 24–48 h delay for some metrics.</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#B91C1C;font-size:0.82rem;margin:0 0 0.5rem 0;">⚠ Some tracking tags were added recently and may not have as much data as older ones.</p>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4, fc_spacer = st.columns([2, 3, 1, 1, 2], gap="small")
    with fc1:
        period = st.segmented_control("Period", ["3d", "7d", "30d", "90d"], default="30d", label_visibility="collapsed")
    with fc2:
        selected_email = st.selectbox(
            "Filter by user",
            options=["All users"] + email_options,
            index=0,
            label_visibility="collapsed",
            key="email_filter",
        )
    with fc3:
        show_docs = st.popover("Tags")
    with fc4:
        show_export = st.popover("Export")

days = {"3d": 3, "7d": 7, "30d": 30, "90d": 90}[period]
start = f"{days}daysAgo"
prev_start = f"{days * 2}daysAgo"
prev_end = f"{days}daysAgo"

active_email_filter = selected_email if selected_email != "All users" else None

if active_email_filter:
    st.caption(f"Showing data for **{active_email_filter}**")

# ── FETCH ─────────────────────────────────────────────────────────
_uf = {"user_email": active_email_filter} if active_email_filter else {}
overview = fetch(["date"], ["activeUsers", "sessions", "eventCount", "averageSessionDuration"], start, **_uf)
overview_prev = fetch(["date"], ["activeUsers", "sessions", "eventCount", "averageSessionDuration"], prev_start, prev_end, **_uf)
events = fetch(["eventName"], ["eventCount", "totalUsers"], start, **_uf)
events_prev = fetch(["eventName"], ["eventCount"], prev_start, prev_end, **_uf)
daily = fetch(["date", "eventName"], ["eventCount"], start, **_uf)

ec = dict(zip(events["eventName"], events["eventCount"].astype(int))) if not events.empty else {}
ecp = dict(zip(events_prev["eventName"], events_prev["eventCount"].astype(int))) if not events_prev.empty else {}
eu = dict(zip(events["eventName"], events["totalUsers"].astype(int))) if not events.empty else {}


def section_header(num, title, subtitle=""):
    sub = f'<span class="subtitle">{subtitle}</span>' if subtitle else ""
    st.markdown(f'<div class="dash-section"><span class="num">{num}</span><h2>{title}</h2>{sub}</div>', unsafe_allow_html=True)


# ── TAG REFERENCE POPOVER ────────────────────────────────────────
with show_docs:
    st.markdown("#### Tag reference")
    st.caption("GA4 event names and counts")
    doc_view = st.radio("Show", ["Golf tags", "GA4 automatic", "All"], label_visibility="collapsed", key="doc_view")
    st.divider()
    golf_tags = {k: v for k, v in LABELS.items() if k.startswith("golf_")}
    auto_tags = {k: v for k, v in LABELS.items() if not k.startswith("golf_")}

    if doc_view in ("Golf tags", "All"):
        rows = ""
        for ev, lbl in sorted(golf_tags.items(), key=lambda x: ec.get(x[0], 0), reverse=True):
            count = ec.get(ev, 0)
            rows += f'<tr><td>{lbl}</td><td class="ev">{ev}</td><td class="cnt">{count:,}</td></tr>'
        st.markdown(f'<table class="tag-ref">{rows}</table>', unsafe_allow_html=True)
    if doc_view in ("GA4 automatic", "All"):
        if doc_view == "All":
            st.divider()
        rows = ""
        for ev, lbl in auto_tags.items():
            count = ec.get(ev, 0)
            if count > 0:
                rows += f'<tr><td>{lbl}</td><td class="ev">{ev}</td><td class="cnt">{count:,}</td></tr>'
        if rows:
            st.markdown(f'<table class="tag-ref">{rows}</table>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# 1. OVERVIEW
# ══════════════════════════════════════════════════════════════════
users_total = int(overview["activeUsers"].sum())
users_prev = int(overview_prev["activeUsers"].sum())
sessions_total = int(overview["sessions"].sum())
sessions_prev = int(overview_prev["sessions"].sum())
avg_dur = overview["averageSessionDuration"].mean()
dur_prev = overview_prev["averageSessionDuration"].mean() if not overview_prev.empty else 0
load_tournament = ec.get("golf_action_click_load_tournament", 0)
load_prev = ecp.get("golf_action_click_load_tournament", 0)

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_header("1", "Overview", f"Last {days} days vs previous {days} days")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Unique users", f"{users_total:,}", delta=delta(users_total, users_prev),
              help="Distinct users who opened the Golf UI app in the selected period")
    c2.metric("Sessions", f"{sessions_total:,}", delta=delta(sessions_total, sessions_prev),
              help="Total GA4 sessions — each time a user opens the app counts as one session")
    c3.metric("Load tournament", f"{load_tournament:,}", delta=delta(load_tournament, load_prev),
              help="Number of times a tournament was loaded from the selector")
    c4.metric("Avg session", fmt_time(avg_dur), delta=delta(avg_dur, dur_prev),
              help="Average time a user spends per session in the app")



# ══════════════════════════════════════════════════════════════════
# 2. PAGES VIEWED
# ══════════════════════════════════════════════════════════════════
import re as _re

def _extract_round_from_url(url):
    m = _re.search(r'roundNumber=(\d)', str(url))
    return m.group(1) if m else None

def round_label_fn(x):
    s = str(x).strip()
    if s.isdigit():
        return f"R{s}"
    if s.lower().startswith("round "):
        return f"R{s[6:].strip()}"
    return s

nav_by_page = try_fetch(
    ["eventName", "pageLocation"], ["eventCount"], start,
    filter_event="golf_nav_view",
)

nav_by_page_parsed = pd.DataFrame()
if not nav_by_page.empty:
    nav_by_page["page"] = nav_by_page["pageLocation"].apply(extract_page)
    nav_by_page_parsed = nav_by_page

rt_total = esum("round_tab", ec)
round_dim = None
rd_data = pd.DataFrame()

url_data = try_fetch(
    ["pageLocation"], ["eventCount"], start,
    filter_event="golf_select_round_tab",
)
if not url_data.empty:
    url_data["page"] = url_data["pageLocation"].apply(extract_page)
    url_data["round_from_url"] = url_data["pageLocation"].apply(_extract_round_from_url)
    url_clean = url_data[url_data["round_from_url"].notna()]
    if not url_clean.empty:
        rd_data = url_clean
        round_dim = "round_from_url"

if rd_data.empty or not round_dim:
    for dim_name in [
        "customEvent:click_text",
        "customEvent:active_round",
        "customEvent:round_number",
        "customEvent:tab_label",
    ]:
        candidate = try_fetch(
            [dim_name, "pageLocation"], ["eventCount"], start,
            filter_event="golf_select_round_tab",
        )
        if not candidate.empty and dim_name in candidate.columns:
            clean = candidate[~candidate[dim_name].isin(["(not set)", "", "unknown"])]
            if not clean.empty:
                rd_data = clean
                round_dim = dim_name
                break

if not rd_data.empty and round_dim and "page" not in rd_data.columns:
    rd_data["page"] = rd_data["pageLocation"].apply(extract_page)

cm_nav = try_fetch(
    ["pageLocation"], ["eventCount"], start,
    filter_event="golf_nav_view",
)
cm_round_data = pd.DataFrame()
if not cm_nav.empty:
    cm_nav["page"] = cm_nav["pageLocation"].apply(extract_page)
    cm_nav = cm_nav[cm_nav["page"] == "Course Management"]
    cm_nav["round_from_url"] = cm_nav["pageLocation"].apply(_extract_round_from_url)
    cm_round_data = cm_nav[cm_nav["round_from_url"].notna()]

def _render_round_pie(page_data, use_dim, page_name, total_page_nav):
    if not page_data.empty and use_dim:
        by_round = page_data.groupby(use_dim)["eventCount"].sum().reset_index()
        by_round.columns = ["round", "count"]
        by_round["label"] = by_round["round"].apply(round_label_fn)
        by_round = by_round.sort_values("label")
        colors = [ROUND_COLORS.get(lbl, T["accent"]) for lbl in by_round["label"]]
        fig_rt = go.Figure(go.Pie(
            labels=by_round["label"].tolist(),
            values=by_round["count"].tolist(),
            hole=0.5,
            marker=dict(colors=colors, line=dict(color=T["surface"], width=2)),
            textinfo="label+percent",
            textfont=dict(size=11, color=T["text_secondary"]),
            hovertemplate="%{label}: %{value:,} clicks (%{percent})<extra></extra>",
        ))
        fig_rt.update_layout(
            height=240, margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
        )
        st.plotly_chart(fig_rt, use_container_width=True)
        tab_clicks = int(page_data["eventCount"].sum())
        st.caption(f"**{tab_clicks:,}** tab switches · **{total_page_nav:,}** page views")
    else:
        st.info("No round tab data yet")

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_header("2", "Pages viewed", "Navigation patterns between tabs")

    if not nav_by_page_parsed.empty:
        page_totals = nav_by_page_parsed.groupby("page")["eventCount"].sum().sort_values(ascending=False)
        total_nav = page_totals.sum()
        rounds_nav_total = int(page_totals.get("Rounds", 0))
        cm_nav_total = int(page_totals.get("Course Management", 0))

        pcol1, pcol2, pcol3 = st.columns(3)

        with pcol1:
            st.markdown("**Page distribution**")
            if total_nav > 0:
                fig_pie = go.Figure(go.Pie(
                    labels=page_totals.index.tolist(),
                    values=page_totals.values.tolist(),
                    hole=0.5,
                    marker=dict(
                        colors=[PAGE_COLORS.get(p, "#6B7280") for p in page_totals.index],
                        line=dict(color=T["surface"], width=2),
                    ),
                    textinfo="label+percent",
                    textfont=dict(size=11, color=T["text_secondary"]),
                    hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>",
                ))
                fig_pie.update_layout(
                    height=260, margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                st.caption(f"**{int(total_nav):,}** total page views")

        with pcol2:
            st.markdown("**Rounds — clicks p/ round**")
            if not rd_data.empty and round_dim:
                rounds_page_data = rd_data[rd_data["page"] == "Rounds"] if "page" in rd_data.columns else rd_data
                _render_round_pie(rounds_page_data, round_dim, "Rounds", rounds_nav_total)
            else:
                st.info("No round tab data yet")

        with pcol3:
            st.markdown("**Course mgmt — clicks p/ round**")
            if not cm_round_data.empty:
                _render_round_pie(cm_round_data, "round_from_url", "Course Management", cm_nav_total)
            elif not rd_data.empty and round_dim and "page" in rd_data.columns:
                cm_page_data = rd_data[rd_data["page"] == "Course Management"]
                if not cm_page_data.empty:
                    _render_round_pie(cm_page_data, round_dim, "Course Management", cm_nav_total)
                else:
                    st.info("No round tab data yet")
            else:
                st.info("No round tab data yet")
    else:
        st.info("No navigation data in this period")


# ══════════════════════════════════════════════════════════════════
# 3. TRADER ACTIONS (merged: core actions + new tracking tags)
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
_trader_card = st.container(border=True)
with _trader_card:
    section_header("3", "Trader actions", "Core trading workflows and additional tracking")

# ── Nudge — Rounds (Player, Hole, Sidebar in one row) ──
player_nudge = ec.get("golf_adjust_player_nudge", 0)
hole_nudge = ec.get("golf_adjust_hole_nudge", 0)
modal_nudge = ec.get("golf_modal_adjust_nudge", 0)
modal_prev = ecp.get("golf_modal_adjust_nudge", 0)
sidebar_open = ec.get("golf_open_hole_configure", 0)
sidebar_open_prev = ecp.get("golf_open_hole_configure", 0)

with _trader_card:
    st.markdown("**Nudge — Rounds**")
    st.caption("Nudge adjustments on the Rounds page and sidebar panel")

    nd1, nd2, nd3, nd4 = st.columns(4)
    with nd1:
        st.metric("Player Nudge", f"{player_nudge:,}",
                  help="Clicks on player-level nudge +/- buttons on the Rounds page")
    with nd2:
        st.metric("Hole Nudge", f"{hole_nudge:,}",
                  help="Clicks on hole-level nudge +/- buttons on the Rounds page")
    with nd3:
        st.metric("Nudge sidebar Open", f"{sidebar_open:,}", delta=delta(sidebar_open, sidebar_open_prev),
                  help="Times the hole configure sidebar was opened")
    with nd4:
        st.metric("Sidebar nudge clicks", f"{modal_nudge:,}", delta=delta(modal_nudge, modal_prev),
                  help="Nudge adjustments made inside the sidebar panel")

# ── Kill Switch + Nudge Course Mgmt side by side ──
with _trader_card:
    ta1, ta2 = st.columns(2)

with ta1:
    with st.container(border=True):
        st.markdown("**Kill switch**")
        st.caption("Kill switch toggle clicks broken down by page")

        ks_total_count = esum("kill_switch", ec)
        if ks_total_count > 0:
            ks_frames = []
            for ev in EVENT_ALIASES["kill_switch"]:
                if ec.get(ev, 0) > 0:
                    df_ks = try_fetch(
                        ["eventName", "pageLocation"], ["eventCount", "totalUsers"], start,
                        filter_event=ev,
                    )
                    if not df_ks.empty:
                        ks_frames.append(df_ks)

            if ks_frames:
                ks_data = pd.concat(ks_frames, ignore_index=True)
                ks_data["page"] = ks_data["pageLocation"].apply(extract_page)
                ks_by_page = ks_data.groupby("page")["eventCount"].sum()
                ks_users = int(ks_data["totalUsers"].sum())

                fig_ks = go.Figure(go.Pie(
                    labels=ks_by_page.index.tolist(),
                    values=ks_by_page.values.tolist(),
                    hole=0.45,
                    marker=dict(
                        colors=[PAGE_COLORS.get(p, "#6B7280") for p in ks_by_page.index],
                        line=dict(color=T["surface"], width=2),
                    ),
                    textinfo="label+percent",
                    textfont=dict(size=10, color=T["text_secondary"]),
                ))
                fig_ks.update_layout(
                    height=200, margin=dict(l=5, r=5, t=5, b=5),
                    paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                )
                st.plotly_chart(fig_ks, use_container_width=True)

                st.metric("Total toggles", f"{ks_total_count:,}")
                if ks_users > 0:
                    st.metric("Avg per trader", f"{round(ks_total_count / ks_users, 1)}")

                ks_state = try_fetch(
                    ["customEvent:kill_switch_state"], ["eventCount"], start,
                    filter_event="golf_toggle_kill_switch",
                )
                if not ks_state.empty and "customEvent:kill_switch_state" in ks_state.columns:
                    state_dict = dict(zip(ks_state["customEvent:kill_switch_state"], ks_state["eventCount"].astype(int)))
                    active = state_dict.get("Active", 0)
                    suspended = state_dict.get("Suspended", 0)
                    if active > 0 or suspended > 0:
                        st.caption(f"Active: {active:,} · Suspended: {suspended:,}")
            else:
                st.info("No kill switch data")
        else:
            st.info("No kill switch data")

with ta2:
    with st.container(border=True):
        st.markdown("**Nudge — Course Mgmt**")
        st.caption("Granular nudge clicks on the Course Management page")

        rough = ec.get("golf_course_adjust_rough", 0)
        morning = ec.get("golf_course_adjust_morning_wave", 0)
        afternoon = ec.get("golf_course_adjust_afternoon_wave", 0)
        course_level_total = rough + morning + afternoon

        early_hd = ec.get("golf_course_adjust_hole_early_hd", 0)
        early_par = ec.get("golf_course_adjust_hole_early_par", 0)
        late_hd = ec.get("golf_course_adjust_hole_late_hd", 0)
        late_par = ec.get("golf_course_adjust_hole_late_par", 0)
        hole_course_total = early_hd + early_par + late_hd + late_par

        legacy_course = ec.get("golf_adjust_nudge", 0)
        course_total = course_level_total + hole_course_total + legacy_course

        if course_total > 0:
            st.caption("Course-level adjustments")
            cl1, cl2, cl3 = st.columns(3)
            cl1.metric("Rough Difficulty", f"{rough:,}",
                        help="Clicks adjusting rough difficulty nudge on Course Management")
            cl2.metric("Morning Wave", f"{morning:,}",
                        help="Clicks adjusting morning wave nudge")
            cl3.metric("Afternoon Wave", f"{afternoon:,}",
                        help="Clicks adjusting afternoon wave nudge")

            st.caption("Per-hole nudges")
            hl1, hl2, hl3, hl4 = st.columns(4)
            hl1.metric("Early HD", f"{early_hd:,}",
                        help="Early wave handicap nudge clicks per hole")
            hl2.metric("Early Par", f"{early_par:,}",
                        help="Early wave par nudge clicks per hole")
            hl3.metric("Late HD", f"{late_hd:,}",
                        help="Late wave handicap nudge clicks per hole")
            hl4.metric("Late Par", f"{late_par:,}",
                        help="Late wave par nudge clicks per hole")

            if legacy_course > 0:
                st.caption(f"Legacy course nudge (untyped): {legacy_course:,}")
        else:
            st.caption("No course management nudge data")

# ── Search (separate card) ──
with _trader_card:
    with st.container(border=True):
        st.markdown("**Player search**")
        st.caption("How often traders use the search feature to find players")

        search_data = try_fetch(
            ["eventName", "pageLocation"], ["eventCount"], start,
            filter_event="golf_search_player",
        )

        if not search_data.empty:
            search_data["page"] = search_data["pageLocation"].apply(extract_page)
            search_by_page = search_data.groupby("page")["eventCount"].sum()
            sr_cols = st.columns(len(search_by_page))
            for i, page_name in enumerate(["Participants", "Leaderboard"]):
                count = int(search_by_page.get(page_name, 0))
                if count > 0 and i < len(sr_cols):
                    sr_cols[i].metric(f"Search ({page_name})", f"{count:,}",
                                      help=f"Player search uses on the {page_name} page")
        else:
            st.info("No search data")

# ── Additional tracking tags ──
TRACKING_TOOLTIPS = {
    "Toggle Favourite": "Clicks to favourite/unfavourite a player",
    "Open Player View": "Clicks to open the detailed player view panel",
    "Toggle Player": "Clicks to enable/disable a player in the round",
    "Expand Group": "Clicks to expand/collapse a player group row",
    "Hole Insights": "Clicks to open the hole insights panel",
    "Hole Configure": "Clicks to open the hole configuration panel",
    "Setup Button": "Clicks on the setup button on the Participants page",
    "Sidebar Nudge": "Nudge adjustments made through the sidebar panel",
    "Scroll Depth": "Tracks how far down the page users scroll",
    "Horizontal Scroll": "Horizontal scroll events on the Rounds table",
    "View Switch (LB)": "Clicks switching Leaderboard view mode",
    "Rough Difficulty": "Course-level rough difficulty nudge clicks",
    "Morning Wave": "Course-level morning wave nudge clicks",
    "Afternoon Wave": "Course-level afternoon wave nudge clicks",
    "Hole Early HD": "Per-hole early wave handicap nudge clicks",
    "Hole Early Par": "Per-hole early wave par nudge clicks",
    "Hole Late HD": "Per-hole late wave handicap nudge clicks",
    "Hole Late Par": "Per-hole late wave par nudge clicks",
}

_tracking_page_data = try_fetch(
    ["eventName", "pageLocation"], ["eventCount"], start,
)
_ev_page_map = {}
if not _tracking_page_data.empty:
    _tracking_page_data["page"] = _tracking_page_data["pageLocation"].apply(extract_page)
    _page_by_ev = _tracking_page_data.groupby("eventName")["page"].apply(
        lambda pages: pages.mode().iloc[0] if not pages.mode().empty else ""
    )
    _ev_page_map = _page_by_ev.to_dict()

new_items = []
for ev_name, lbl in NEW_TRACKING_EVENTS:
    count = ec.get(ev_name, 0)
    if count > 0:
        new_items.append((lbl, count, TRACKING_TOOLTIPS.get(lbl, "")))

with _trader_card:
    st.markdown("**Additional tracking tags**")
    st.caption("All tracked interaction events and their counts for the selected period")

    if new_items:
        ndf = pd.DataFrame(new_items, columns=["Event", "Count", "Tooltip"]).sort_values("Count", ascending=True)
        fig_new = go.Figure(go.Bar(
            x=ndf["Count"], y=ndf["Event"], orientation="h",
            marker_color=T["accent"],
            text=[f"{v:,}" for v in ndf["Count"]],
            textposition="auto",
            textfont=dict(color="#FFFFFF", size=11),
            marker_line_width=0,
            hovertemplate=[f"<b>{row['Event']}</b><br>{row['Count']:,} clicks<br><i>{row['Tooltip']}</i><extra></extra>" for _, row in ndf.iterrows()],
        ))
        fig_new.update_layout(
            **cl(height=max(200, len(ndf) * 36)),
            xaxis=dict(visible=False),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=11, color=T["text_secondary"])),
        )
        st.plotly_chart(fig_new, use_container_width=True)
    else:
        st.info("No new tracking events recorded in this period")


# ══════════════════════════════════════════════════════════════════
# 4. DEMOGRAPHICS
# ══════════════════════════════════════════════════════════════════
geo = try_fetch(["country", "city"], ["activeUsers"], start)
devices = try_fetch(["deviceCategory"], ["activeUsers"], start)
browsers = try_fetch(["browser"], ["activeUsers"], start)
hourly = try_fetch(["hour"], ["activeUsers", "sessions"], start)
st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_header("4", "Demographics", "Locations, devices, and usage patterns")

    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.markdown("**Users**")
        st.caption("Active users in this period")
        if not all_users_df.empty:
            col_email = "customUser:user_email"
            clean_users = all_users_df[~all_users_df[col_email].isin(["(not set)", ""])]
            if not clean_users.empty:
                for _, r in clean_users.sort_values("activeUsers", ascending=False).iterrows():
                    email = r[col_email]
                    name = email.split("@")[0].replace(".", " ").title()
                    st.text(f"{name}")
            else:
                st.caption("No identified users — user_email custom dimension may not be set")
        else:
            st.caption("No identified users — user_email custom dimension may not be set")

    with d2:
        st.markdown("**Location**")
        st.caption("Where users are accessing the app from")
        if not geo.empty:
            geo_sorted = geo.sort_values("activeUsers", ascending=False).head(10)
            for _, r in geo_sorted.iterrows():
                city = r["city"] if r["city"] != "(not set)" else ""
                loc = f"{city}, {r['country']}" if city else r["country"]
                st.text(f"{loc}: {int(r['activeUsers']):,}")
        else:
            st.info("No location data")

    with d3:
        st.markdown("**Device & browser**")
        st.caption("Device types and browsers used")
        if not devices.empty:
            for _, r in devices.sort_values("activeUsers", ascending=False).iterrows():
                st.text(f"{r['deviceCategory'].title()}: {int(r['activeUsers']):,}")
        st.markdown("---")
        if not browsers.empty:
            for _, r in browsers.sort_values("activeUsers", ascending=False).head(5).iterrows():
                st.text(f"{r['browser']}: {int(r['activeUsers']):,}")

    with d4:
        st.markdown("**Activity by hour**")
        st.caption("Users and sessions by hour (Irish time, UTC+1)")
        if not hourly.empty:
            hr = hourly.copy()
            hr["hour"] = (hr["hour"].astype(int) + IST_OFFSET) % 24
            hr = hr.sort_values("hour")
            hr["lbl"] = hr["hour"].apply(lambda h: f"{h:02d}")

            fig_hr = go.Figure()
            fig_hr.add_trace(go.Bar(
                x=hr["lbl"], y=hr["activeUsers"], name="Users",
                marker_color=T["accent"],
                marker_line_width=0,
            ))
            fig_hr.add_trace(go.Bar(
                x=hr["lbl"], y=hr["sessions"], name="Sessions",
                marker_color=T["accent_light"],
                marker_line_width=0,
            ))
            fig_hr.update_layout(
                **cl(height=200, show_legend=True),
                barmode="group",
                xaxis=dict(gridcolor=T["chart_grid"], title="Hour", tickangle=-45, title_font=dict(size=10)),
                yaxis=dict(gridcolor=T["chart_grid"], title="Count", title_font=dict(size=10)),
            )
            st.plotly_chart(fig_hr, use_container_width=True)
        else:
            st.info("No hourly data")


# ══════════════════════════════════════════════════════════════════
# 5. ERRORS & PERFORMANCE
# ══════════════════════════════════════════════════════════════════
js_err = ec.get("golf_error_fail_js_error", 0)
perf = ec.get("golf_perf_load_page_timing", 0)

load_time_data = try_fetch(
    ["eventName"], ["eventCount", "eventValue"], start,
    filter_event="golf_perf_load_page_timing",
)
avg_load_ms = 0
if not load_time_data.empty and "eventValue" in load_time_data.columns:
    total_val = load_time_data["eventValue"].sum()
    total_cnt = load_time_data["eventCount"].sum()
    if total_cnt > 0:
        avg_load_ms = round(total_val / total_cnt)

load_time_custom = try_fetch(
    ["customEvent:load_time_ms"], ["eventCount"], start,
    filter_event="golf_perf_load_page_timing",
)
if not load_time_custom.empty and "customEvent:load_time_ms" in load_time_custom.columns:
    vals = pd.to_numeric(load_time_custom["customEvent:load_time_ms"], errors="coerce").dropna()
    if not vals.empty:
        avg_load_ms = round(vals.mean())

if js_err > 0 or perf > 0:
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        section_header("5", "Errors & performance", "JavaScript errors and page load metrics")

        js_prev = ecp.get("golf_error_fail_js_error", 0)
        err_rate = round(js_err / max(sessions_total, 1) * 100, 1)

        ep1, ep2, ep3, ep4 = st.columns(4)
        ep1.metric("JS errors", f"{js_err:,}", delta=delta(js_err, js_prev), delta_color="inverse",
                   help="Total JS errors caught by the GTM error tracking tag")
        ep2.metric("Error rate", f"{err_rate}%",
                   help="JS errors as a percentage of total sessions — above 5% is a concern")
        ep3.metric("Page timing events", f"{perf:,}",
                   help="DOMReady performance pings — counts how many times a page load measurement fired")
        if avg_load_ms > 0:
            load_label = f"{avg_load_ms:,} ms" if avg_load_ms < 10000 else f"{avg_load_ms / 1000:.1f} s"
            ep4.metric("Avg load time", load_label,
                       help="Average DOMContentLoaded time from the cjs_page_load_time variable (ms)")
        else:
            ep4.metric("Avg load time", "—",
                       help="No load_time_ms data yet — the custom dimension was just added, data will appear after page loads are recorded")
        if err_rate > 5:
            st.error(f"Error rate {err_rate}% — above 5% threshold")


# ══════════════════════════════════════════════════════════════════
# 6. EVENT TRENDS
# ══════════════════════════════════════════════════════════════════
TREND_GROUPS = {
    "Session Start": ["session_start"],
    "Load Tournament": ["golf_action_click_load_tournament"],
    "All Nudges": [
        "golf_adjust_player_nudge", "golf_adjust_hole_nudge",
        "golf_modal_adjust_nudge", "golf_course_adjust_rough",
        "golf_course_adjust_afternoon_wave",
        "golf_course_adjust_hole_early_hd", "golf_course_adjust_hole_early_par",
        "golf_course_adjust_hole_late_hd", "golf_course_adjust_hole_late_par",
    ],
    "All Kill Switches": ["golf_toggle_kill_switch"],
}

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
with st.container(border=True):
    section_header("6", "Event trends", f"Daily volume over the last {days} days")
    st.caption("Sessions, tournament loads, nudges, and kill switches — daily counts")
    if not daily.empty:
        de = daily.copy()
        de["date"] = pd.to_datetime(de["date"], format="%Y%m%d")
        today = pd.Timestamp.now().normalize()
        de = de[de["date"] < today]

        available_groups = {
            name: evts for name, evts in TREND_GROUPS.items()
            if any(ev in de["eventName"].unique() for ev in evts)
        }

        if available_groups:
            trend_filter = st.multiselect(
                "Event groups", list(available_groups.keys()),
                default=list(available_groups.keys()),
                label_visibility="collapsed",
                key="trend_filter",
            )
            if trend_filter:
                fig_trends = go.Figure()
                for i, group_name in enumerate(trend_filter):
                    evts = available_groups[group_name]
                    sub = de[de["eventName"].isin(evts)].groupby("date")["eventCount"].sum().reset_index()
                    sub = sub.sort_values("date")
                    total = int(sub["eventCount"].sum())
                    fig_trends.add_trace(go.Scatter(
                        x=sub["date"], y=sub["eventCount"],
                        name=f"{group_name} ({total:,})",
                        line=dict(width=2, color=CHART_COLORS[i % len(CHART_COLORS)]),
                        hovertemplate="%{x|%b %d}: %{y:,}<extra>" + group_name + "</extra>",
                    ))
                fig_trends.update_layout(
                    **cl(height=320, show_legend=True, legend_top=True),
                    xaxis=dict(
                        gridcolor=T["chart_grid"],
                        showticklabels=True,
                        tickformat="%b %d",
                        dtick="D1" if days <= 30 else "D7",
                        tickfont=dict(size=10, color=T["text_secondary"]),
                        range=[
                            de["date"].min().normalize(),
                            de["date"].max().normalize() + pd.Timedelta(days=1),
                        ],
                    ),
                    yaxis=dict(gridcolor=T["chart_grid"], title="Events", title_font=dict(size=10)),
                )
                st.plotly_chart(fig_trends, use_container_width=True)
            else:
                st.info("Select event groups to show trends")
        else:
            st.info("No trend events in daily data")
    else:
        st.info("No daily data for this period")


# ── EXPORT POPOVER ───────────────────────────────────────────────
with show_export:
    st.markdown("#### Export PDF")
    st.caption("Select sections to include")
    export_sections = st.multiselect(
        "Sections", SECTIONS, default=SECTIONS,
        label_visibility="collapsed", key="export_sections",
    )
    if st.button("Generate PDF", type="primary", use_container_width=True):
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 12, "Golf UI Analytics", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 6, f"Period: {period}  |  Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(6)

            def sh(title):
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_fill_color(245, 247, 250)
                pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", fill=True)
                pdf.ln(2)

            def kv(key, value):
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(60, 6, key, new_x="RIGHT")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")

            if "Overview" in export_sections:
                sh("Overview")
                kv("Unique users", f"{users_total:,}")
                kv("Sessions", f"{sessions_total:,}")
                kv("Load tournament", f"{load_tournament:,}")
                kv("Avg session", fmt_time(avg_dur))
                kv("Total events", f"{int(overview['eventCount'].sum()):,}")
                pdf.ln(4)

            if "Trader Actions" in export_sections:
                sh("Trader Actions")
                kv("Kill-Switch toggles", f"{esum('kill_switch', ec):,}")
                kv("Player Nudge", f"{esum('nudge_player', ec):,}")
                kv("Hole Nudge", f"{esum('nudge_hole', ec):,}")
                kv("Course Nudge (legacy)", f"{esum('nudge_course', ec):,}")
                kv("Sidebar Nudge", f"{esum('nudge_modal', ec):,}")
                pdf.ln(2)
                sh("Course Mgmt — Granular")
                kv("Rough Difficulty", f"{esum('nudge_course_rough', ec):,}")
                kv("Morning Wave", f"{esum('nudge_course_morning', ec):,}")
                kv("Afternoon Wave", f"{esum('nudge_course_afternoon', ec):,}")
                kv("Hole Early HD", f"{esum('nudge_hole_early_hd', ec):,}")
                kv("Hole Early Par", f"{esum('nudge_hole_early_par', ec):,}")
                kv("Hole Late HD", f"{esum('nudge_hole_late_hd', ec):,}")
                kv("Hole Late Par", f"{esum('nudge_hole_late_par', ec):,}")
                kv("Search", f"{esum('search', ec):,}")
                pdf.ln(2)
                sh("Additional Tracking Tags")
                for ev_name, lbl in NEW_TRACKING_EVENTS:
                    kv(lbl, f"{ec.get(ev_name, 0):,}")
                pdf.ln(4)

            if "Errors & Performance" in export_sections:
                sh("Errors & Performance")
                kv("JS Errors", f"{js_err:,}")
                pdf_err_rate = round(js_err / max(sessions_total, 1) * 100, 1)
                kv("Error rate", f"{pdf_err_rate}%")
                kv("Page timing events", f"{perf:,}")
                kv("Avg session duration", fmt_time(avg_dur))
                pdf.ln(4)

            buf = BytesIO()
            pdf.output(buf)
            buf.seek(0)
            st.download_button(
                "Download PDF", data=buf,
                file_name=f"golf_analytics_{period}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf", use_container_width=True,
            )
        except ImportError:
            st.error("Missing packages: `pip install fpdf2 kaleido`")
        except Exception as e:
            st.error(f"Export failed: {e}")
