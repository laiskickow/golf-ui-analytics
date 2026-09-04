"""
Export the Golf UI GA4 dashboard as a standalone HTML file.
Used by GitHub Actions to publish to GitHub Pages.

Env vars required:
  GA4_CLIENT_ID, GA4_CLIENT_SECRET, GA4_REFRESH_TOKEN
"""
import os
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric, OrderBy,
    FilterExpression, Filter,
)
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import re as _re

PROPERTY_ID = "533271514"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
IST_OFFSET = 1
DAYS = 30

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
    "nudge_player": ["golf_adjust_player_nudge"],
    "nudge_hole": ["golf_adjust_hole_nudge"],
    "nudge_modal": ["golf_modal_adjust_nudge"],
}

NEW_TRACKING_EVENTS = [
    ("golf_toggle_favourite", "Toggle Favourite"),
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

PAGE_COLORS = {
    "Rounds": "#60A5FA",
    "Course Management": "#4ADE80",
    "Leaderboard": "#FBBF24",
    "Participants": "#A78BFA",
    "Other": "#9CA3AF",
}

CHART_COLORS = ["#60A5FA", "#4ADE80", "#FBBF24", "#F87171", "#A78BFA", "#F472B6", "#38BDF8", "#9CA3AF"]

ROUND_COLORS = {"R1": "#60A5FA", "R2": "#4ADE80", "R3": "#FBBF24", "R4": "#F87171"}

T = {
    "bg": "#F3F4F6",
    "surface": "#FFFFFF",
    "border": "#D5DAE1",
    "text": "#111827",
    "text_secondary": "#374151",
    "text_muted": "#6B7280",
    "accent": "#1D4ED8",
    "accent_light": "#DBEAFE",
    "chart_grid": "#E5E7EB",
    "chart_text": "#374151",
}

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


def get_credentials():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GA4_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GA4_CLIENT_ID"],
        client_secret=os.environ["GA4_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def fetch(dims, mets, start="30daysAgo", end="today", filter_event=None):
    creds = get_credentials()
    client = BetaAnalyticsDataClient(credentials=creds)
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in mets],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name=dims[0]))] if dims else [],
        limit=10000,
    )
    if filter_event:
        req.dimension_filter = FilterExpression(filter=Filter(
            field_name="eventName",
            string_filter=Filter.StringFilter(value=filter_event, match_type=Filter.StringFilter.MatchType.EXACT),
        ))
    resp = client.run_report(req)
    rows = [[dv.value for dv in r.dimension_values] + [mv.value for mv in r.metric_values] for r in resp.rows]
    df = pd.DataFrame(rows, columns=dims + mets)
    for m in mets:
        df[m] = pd.to_numeric(df[m], errors="coerce")
    return df


def try_fetch(*args, **kwargs):
    try:
        return fetch(*args, **kwargs)
    except Exception as e:
        print(f"  fetch error: {e}")
        return pd.DataFrame()


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


def fmt_time(s):
    return f"{int(s) // 60}m {int(s) % 60:02d}s"


def delta(cur, prev):
    if prev == 0:
        return ""
    pct = round((cur - prev) / prev * 100)
    color = "#15803D" if pct >= 0 else "#B91C1C"
    arrow = "+" if pct >= 0 else ""
    return f'<span style="color:{color};font-size:0.75rem;">{arrow}{pct}%</span>'


def chart_layout(height=280):
    return dict(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color=T["chart_text"]),
    )


def main():
    print("Fetching GA4 data...")
    start = f"{DAYS}daysAgo"
    prev_start = f"{DAYS * 2}daysAgo"
    prev_end = f"{DAYS}daysAgo"

    overview = fetch(["date"], ["activeUsers", "sessions", "eventCount", "averageSessionDuration"], start)
    overview_prev = fetch(["date"], ["activeUsers", "sessions", "eventCount", "averageSessionDuration"], prev_start, prev_end)
    events = fetch(["eventName"], ["eventCount", "totalUsers"], start)
    events_prev = fetch(["eventName"], ["eventCount"], prev_start, prev_end)
    daily = fetch(["date", "eventName"], ["eventCount"], start)

    ec = dict(zip(events["eventName"], events["eventCount"].astype(int))) if not events.empty else {}
    ecp = dict(zip(events_prev["eventName"], events_prev["eventCount"].astype(int))) if not events_prev.empty else {}

    def esum(alias):
        return sum(ec.get(e, 0) for e in EVENT_ALIASES.get(alias, [alias]))

    # ── Overview metrics ──
    users_total = int(overview["activeUsers"].sum())
    users_prev = int(overview_prev["activeUsers"].sum())
    sessions_total = int(overview["sessions"].sum())
    sessions_prev = int(overview_prev["sessions"].sum())
    avg_dur = overview["averageSessionDuration"].mean()
    dur_prev = overview_prev["averageSessionDuration"].mean() if not overview_prev.empty else 0
    load_tournament = ec.get("golf_action_click_load_tournament", 0)
    load_prev = ecp.get("golf_action_click_load_tournament", 0)

    # ── Pages viewed ──
    print("Fetching page data...")
    nav_by_page = try_fetch(["eventName", "pageLocation"], ["eventCount"], start, filter_event="golf_nav_view")
    page_pie_html = ""
    if not nav_by_page.empty:
        nav_by_page["page"] = nav_by_page["pageLocation"].apply(extract_page)
        page_totals = nav_by_page.groupby("page")["eventCount"].sum().sort_values(ascending=False)
        total_nav = page_totals.sum()
        if total_nav > 0:
            fig = go.Figure(go.Pie(
                labels=page_totals.index.tolist(),
                values=page_totals.values.tolist(),
                hole=0.5,
                marker=dict(colors=[PAGE_COLORS.get(p, "#6B7280") for p in page_totals.index],
                            line=dict(color="#fff", width=2)),
                textinfo="label+percent",
                textfont=dict(size=11),
            ))
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                              paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            page_pie_html = fig.to_html(full_html=False, include_plotlyjs=False)

    # ── Round tabs ──
    url_data = try_fetch(["pageLocation"], ["eventCount"], start, filter_event="golf_select_round_tab")
    round_pie_html = ""
    if not url_data.empty:
        url_data["round"] = url_data["pageLocation"].apply(
            lambda u: _re.search(r'roundNumber=(\d)', str(u)).group(1) if _re.search(r'roundNumber=(\d)', str(u)) else None
        )
        url_clean = url_data[url_data["round"].notna()]
        if not url_clean.empty:
            by_round = url_clean.groupby("round")["eventCount"].sum().reset_index()
            by_round["label"] = by_round["round"].apply(lambda x: f"R{x}")
            by_round = by_round.sort_values("label")
            fig = go.Figure(go.Pie(
                labels=by_round["label"].tolist(),
                values=by_round["eventCount"].tolist(),
                hole=0.5,
                marker=dict(colors=[ROUND_COLORS.get(l, T["accent"]) for l in by_round["label"]],
                            line=dict(color="#fff", width=2)),
                textinfo="label+percent", textfont=dict(size=11),
            ))
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                              paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            round_pie_html = fig.to_html(full_html=False, include_plotlyjs=False)

    # ── Nudges ──
    player_nudge = ec.get("golf_adjust_player_nudge", 0)
    hole_nudge = ec.get("golf_adjust_hole_nudge", 0)
    modal_nudge = ec.get("golf_modal_adjust_nudge", 0)
    modal_prev = ecp.get("golf_modal_adjust_nudge", 0)
    sidebar_open = ec.get("golf_open_hole_configure", 0)
    sidebar_open_prev = ecp.get("golf_open_hole_configure", 0)

    # ── Kill switch ──
    ks_total = esum("kill_switch")

    # ── Course management nudges ──
    rough = ec.get("golf_course_adjust_rough", 0)
    morning = ec.get("golf_course_adjust_morning_wave", 0)
    afternoon = ec.get("golf_course_adjust_afternoon_wave", 0)
    early_hd = ec.get("golf_course_adjust_hole_early_hd", 0)
    early_par = ec.get("golf_course_adjust_hole_early_par", 0)
    late_hd = ec.get("golf_course_adjust_hole_late_hd", 0)
    late_par = ec.get("golf_course_adjust_hole_late_par", 0)

    # ── Additional tracking bar chart ──
    print("Building charts...")
    new_items = [(lbl, ec.get(ev, 0)) for ev, lbl in NEW_TRACKING_EVENTS if ec.get(ev, 0) > 0]
    tracking_bar_html = ""
    if new_items:
        ndf = pd.DataFrame(new_items, columns=["Event", "Count"]).sort_values("Count", ascending=True)
        fig = go.Figure(go.Bar(
            x=ndf["Count"], y=ndf["Event"], orientation="h",
            marker_color=T["accent"],
            text=[f"{v:,}" for v in ndf["Count"]],
            textposition="auto",
            textfont=dict(color="#FFFFFF", size=11),
        ))
        fig.update_layout(
            **chart_layout(height=max(200, len(ndf) * 36)),
            xaxis=dict(visible=False),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=11, color=T["text_secondary"])),
            showlegend=False,
        )
        tracking_bar_html = fig.to_html(full_html=False, include_plotlyjs=False)

    # ── Demographics ──
    geo = try_fetch(["country", "city"], ["activeUsers"], start)
    devices = try_fetch(["deviceCategory"], ["activeUsers"], start)
    browsers = try_fetch(["browser"], ["activeUsers"], start)
    hourly = try_fetch(["hour"], ["activeUsers", "sessions"], start)

    geo_html = ""
    if not geo.empty:
        for _, r in geo.sort_values("activeUsers", ascending=False).head(8).iterrows():
            city = r["city"] if r["city"] != "(not set)" else ""
            loc = f"{city}, {r['country']}" if city else r["country"]
            geo_html += f'<div class="text-item">{loc}: {int(r["activeUsers"]):,}</div>'

    device_html = ""
    if not devices.empty:
        for _, r in devices.sort_values("activeUsers", ascending=False).iterrows():
            device_html += f'<div class="text-item">{r["deviceCategory"].title()}: {int(r["activeUsers"]):,}</div>'
    if not browsers.empty:
        device_html += '<div style="border-top:1px solid #E5E7EB;margin:0.5rem 0;"></div>'
        for _, r in browsers.sort_values("activeUsers", ascending=False).head(5).iterrows():
            device_html += f'<div class="text-item">{r["browser"]}: {int(r["activeUsers"]):,}</div>'

    hourly_chart_html = ""
    if not hourly.empty:
        hr = hourly.copy()
        hr["hour"] = (hr["hour"].astype(int) + IST_OFFSET) % 24
        hr = hr.sort_values("hour")
        hr["lbl"] = hr["hour"].apply(lambda h: f"{h:02d}")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=hr["lbl"], y=hr["activeUsers"], name="Users", marker_color=T["accent"]))
        fig.add_trace(go.Bar(x=hr["lbl"], y=hr["sessions"], name="Sessions", marker_color=T["accent_light"]))
        fig.update_layout(
            **chart_layout(200), barmode="group", showlegend=True,
            legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor=T["chart_grid"], title="Hour", tickangle=-45, title_font=dict(size=10)),
            yaxis=dict(gridcolor=T["chart_grid"], title="Count", title_font=dict(size=10)),
        )
        hourly_chart_html = fig.to_html(full_html=False, include_plotlyjs=False)

    # ── Errors & Performance ──
    js_err = ec.get("golf_error_fail_js_error", 0)
    js_prev = ecp.get("golf_error_fail_js_error", 0)
    perf = ec.get("golf_perf_load_page_timing", 0)
    err_rate = round(js_err / max(sessions_total, 1) * 100, 1)

    load_time_custom = try_fetch(["customEvent:load_time_ms"], ["eventCount"], start, filter_event="golf_perf_load_page_timing")
    avg_load_ms = 0
    if not load_time_custom.empty and "customEvent:load_time_ms" in load_time_custom.columns:
        vals = pd.to_numeric(load_time_custom["customEvent:load_time_ms"], errors="coerce").dropna()
        if not vals.empty:
            avg_load_ms = round(vals.mean())

    # ── Event trends ──
    trends_html = ""
    if not daily.empty:
        de = daily.copy()
        de["date"] = pd.to_datetime(de["date"], format="%Y%m%d")
        today = pd.Timestamp.now().normalize()
        de = de[de["date"] < today]
        fig = go.Figure()
        for i, (name, evts) in enumerate(TREND_GROUPS.items()):
            sub = de[de["eventName"].isin(evts)].groupby("date")["eventCount"].sum().reset_index().sort_values("date")
            if not sub.empty:
                total = int(sub["eventCount"].sum())
                fig.add_trace(go.Scatter(
                    x=sub["date"], y=sub["eventCount"],
                    name=f"{name} ({total:,})",
                    line=dict(width=2, color=CHART_COLORS[i % len(CHART_COLORS)]),
                ))
        fig.update_layout(
            **chart_layout(320), showlegend=True,
            legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor=T["chart_grid"], tickformat="%b %d",
                       dtick="D1" if DAYS <= 30 else "D7",
                       tickfont=dict(size=10, color=T["text_secondary"])),
            yaxis=dict(gridcolor=T["chart_grid"], title="Events", title_font=dict(size=10)),
        )
        trends_html = fig.to_html(full_html=False, include_plotlyjs=False)

    # ── Build HTML ──
    print("Building HTML...")
    now = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
    load_label = f"{avg_load_ms:,} ms" if 0 < avg_load_ms < 10000 else (f"{avg_load_ms / 1000:.1f} s" if avg_load_ms >= 10000 else "—")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Golf UI Analytics</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: {T["bg"]}; color: {T["text"]}; font-family: 'Inter', sans-serif; padding: 2rem; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  .card {{ background: {T["surface"]}; border: 1px solid {T["border"]}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.25rem; }}
  .grid {{ display: grid; gap: 1rem; }}
  .grid-2 {{ grid-template-columns: 1fr 1fr; }}
  .grid-3 {{ grid-template-columns: 1fr 1fr 1fr; }}
  .grid-4 {{ grid-template-columns: 1fr 1fr 1fr 1fr; }}
  .metric {{ background: {T["surface"]}; border: 1px solid {T["border"]}; border-radius: 10px; padding: 0.85rem 1rem; }}
  .metric-label {{ color: {T["text_muted"]}; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }}
  .metric-value {{ color: {T["text"]}; font-size: 1.5rem; font-weight: 600; margin-top: 0.25rem; }}
  .metric-delta {{ font-size: 0.75rem; margin-top: 0.15rem; }}
  h1 {{ font-size: 1.68rem; font-weight: 700; }}
  h2 {{ font-size: 1.05rem; font-weight: 600; margin-bottom: 0.75rem; }}
  .subtitle {{ color: {T["text_muted"]}; font-size: 0.82rem; }}
  .section-num {{ display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 7px; background: {T["accent"]}; color: #fff; font-size: 0.72rem; font-weight: 700; margin-right: 0.6rem; }}
  .section-header {{ display: flex; align-items: center; margin-bottom: 1rem; }}
  .disclaimer {{ color: #B91C1C; font-size: 0.82rem; margin-top: 0.5rem; }}
  .caption {{ color: {T["text_muted"]}; font-size: 0.78rem; margin-top: 0.5rem; }}
  .text-item {{ font-size: 0.85rem; padding: 0.2rem 0; color: {T["text_secondary"]}; }}
  .sub-card {{ background: {T["surface"]}; border: 1px solid {T["border"]}; border-radius: 8px; padding: 1rem; }}
  .updated {{ color: {T["text_muted"]}; font-size: 0.75rem; text-align: right; padding: 1rem 0; }}
  @media (max-width: 768px) {{
    .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }}
    body {{ padding: 1rem; }}
  }}
</style>
</head>
<body>
<div class="container">

<!-- Header -->
<div class="card">
  <h1>Golf UI Analytics</h1>
  <p class="subtitle">GA4 analytics for the Golf trading UI &middot; Last {DAYS} days vs previous {DAYS} days</p>
  <p class="disclaimer">&#9888; Some tracking tags were added recently and may not have as much data as older ones.</p>
</div>

<!-- 1. Overview -->
<div class="card">
  <div class="section-header"><span class="section-num">1</span><h2>Overview</h2></div>
  <div class="grid grid-4">
    <div class="metric">
      <div class="metric-label">Unique users</div>
      <div class="metric-value">{users_total:,}</div>
      <div class="metric-delta">{delta(users_total, users_prev)}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Sessions</div>
      <div class="metric-value">{sessions_total:,}</div>
      <div class="metric-delta">{delta(sessions_total, sessions_prev)}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Load tournament</div>
      <div class="metric-value">{load_tournament:,}</div>
      <div class="metric-delta">{delta(load_tournament, load_prev)}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Avg session</div>
      <div class="metric-value">{fmt_time(avg_dur)}</div>
      <div class="metric-delta">{delta(avg_dur, dur_prev)}</div>
    </div>
  </div>
</div>

<!-- 2. Pages viewed -->
<div class="card">
  <div class="section-header"><span class="section-num">2</span><h2>Pages viewed</h2></div>
  <div class="grid grid-2">
    <div>
      <h2 style="font-size:0.9rem;">Page distribution</h2>
      {page_pie_html if page_pie_html else '<p class="caption">No page data</p>'}
    </div>
    <div>
      <h2 style="font-size:0.9rem;">Rounds — clicks per round</h2>
      {round_pie_html if round_pie_html else '<p class="caption">No round tab data</p>'}
    </div>
  </div>
</div>

<!-- 3. Trader Actions -->
<div class="card">
  <div class="section-header"><span class="section-num">3</span><h2>Trader actions</h2></div>

  <h2 style="font-size:0.9rem;">Nudge — Rounds</h2>
  <p class="caption" style="margin-top:-0.5rem;margin-bottom:0.75rem;">Nudge adjustments on the Rounds page and sidebar panel</p>
  <div class="grid grid-4">
    <div class="metric">
      <div class="metric-label">Player Nudge</div>
      <div class="metric-value">{player_nudge:,}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Hole Nudge</div>
      <div class="metric-value">{hole_nudge:,}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Nudge sidebar Open</div>
      <div class="metric-value">{sidebar_open:,}</div>
      <div class="metric-delta">{delta(sidebar_open, sidebar_open_prev)}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Sidebar nudge clicks</div>
      <div class="metric-value">{modal_nudge:,}</div>
      <div class="metric-delta">{delta(modal_nudge, modal_prev)}</div>
    </div>
  </div>

  <div class="grid grid-2" style="margin-top:1rem;">
    <div class="sub-card">
      <h2 style="font-size:0.9rem;">Kill switch</h2>
      <div class="metric" style="border:none;padding:0.5rem 0;">
        <div class="metric-label">Total toggles</div>
        <div class="metric-value">{ks_total:,}</div>
      </div>
    </div>
    <div class="sub-card">
      <h2 style="font-size:0.9rem;">Nudge — Course Mgmt</h2>
      <div class="grid grid-3" style="margin-top:0.5rem;">
        <div><div class="metric-label">Rough</div><div class="metric-value" style="font-size:1.1rem;">{rough:,}</div></div>
        <div><div class="metric-label">Morning</div><div class="metric-value" style="font-size:1.1rem;">{morning:,}</div></div>
        <div><div class="metric-label">Afternoon</div><div class="metric-value" style="font-size:1.1rem;">{afternoon:,}</div></div>
      </div>
      <div class="grid grid-4" style="margin-top:0.5rem;">
        <div><div class="metric-label">Early HD</div><div style="font-weight:600;">{early_hd:,}</div></div>
        <div><div class="metric-label">Early Par</div><div style="font-weight:600;">{early_par:,}</div></div>
        <div><div class="metric-label">Late HD</div><div style="font-weight:600;">{late_hd:,}</div></div>
        <div><div class="metric-label">Late Par</div><div style="font-weight:600;">{late_par:,}</div></div>
      </div>
    </div>
  </div>

  <h2 style="font-size:0.9rem;margin-top:1.25rem;">Additional tracking tags</h2>
  {tracking_bar_html if tracking_bar_html else '<p class="caption">No tracking data</p>'}
</div>

<!-- 4. Demographics -->
<div class="card">
  <div class="section-header"><span class="section-num">4</span><h2>Demographics</h2></div>
  <div class="grid grid-3">
    <div>
      <h2 style="font-size:0.9rem;">Location</h2>
      {geo_html if geo_html else '<p class="caption">No location data</p>'}
    </div>
    <div>
      <h2 style="font-size:0.9rem;">Device &amp; browser</h2>
      {device_html if device_html else '<p class="caption">No device data</p>'}
    </div>
    <div>
      <h2 style="font-size:0.9rem;">Activity by hour</h2>
      {hourly_chart_html if hourly_chart_html else '<p class="caption">No hourly data</p>'}
    </div>
  </div>
</div>

<!-- 5. Errors & Performance -->
<div class="card">
  <div class="section-header"><span class="section-num">5</span><h2>Errors &amp; performance</h2></div>
  <div class="grid grid-4">
    <div class="metric">
      <div class="metric-label">JS errors</div>
      <div class="metric-value">{js_err:,}</div>
      <div class="metric-delta">{delta(js_err, js_prev)}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Error rate</div>
      <div class="metric-value">{err_rate}%</div>
    </div>
    <div class="metric">
      <div class="metric-label">Page timing events</div>
      <div class="metric-value">{perf:,}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Avg load time</div>
      <div class="metric-value">{load_label}</div>
    </div>
  </div>
</div>

<!-- 6. Event trends -->
<div class="card">
  <div class="section-header"><span class="section-num">6</span><h2>Event trends</h2></div>
  <p class="caption" style="margin-top:-0.5rem;margin-bottom:0.75rem;">Sessions, tournament loads, nudges, and kill switches — daily counts (excluding today)</p>
  {trends_html if trends_html else '<p class="caption">No trend data</p>'}
</div>

<div class="updated">Last updated: {now} &middot; Auto-refreshes every hour via GitHub Actions</div>

</div>
</body>
</html>"""

    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w") as f:
        f.write(html)
    print(f"Exported to public/index.html ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
