from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    :root { --bg:#0B0F14; --surface:#12161C; --line:#232A33; --accent:#3E92CC; --text:#E6EDF3; --muted:#93A1B0; }
    .stApp, [data-testid="stAppViewContainer"] { background:var(--bg); color:var(--text); font-family:'IBM Plex Sans',sans-serif; }
    [data-testid="stSidebar"] { background:#0D1218; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] [data-baseweb="radio"] { border-radius:0!important; padding:5px 8px; border-left:2px solid transparent; }
    [data-testid="stSidebar"] [data-baseweb="radio"]:has(input:checked) { border-left-color:var(--accent); color:var(--accent); }
    h1,h2,h3 { font-family:'IBM Plex Sans',sans-serif!important; color:var(--text)!important; letter-spacing:-.015em; }
    h1 { font-size:1.65rem!important; font-weight:600!important; } h2 { font-size:1.2rem!important; } h3 { font-size:1rem!important; }
    .screen-heading { font:600 1.55rem 'IBM Plex Sans',sans-serif; color:var(--text); padding:0 0 10px; margin:0 0 20px; border-bottom:1px solid var(--line); }
    .instrument-panel { background:var(--surface); border:1px solid var(--line); border-radius:2px; padding:14px; margin:0 0 16px; box-shadow:none; }
    .muted { color:var(--muted); }
    .mono, .mono *, code, pre { font-family:'IBM Plex Mono',ui-monospace,monospace!important; font-variant-numeric:tabular-nums; }
    .measurement { width:100%; border-collapse:collapse; font-size:.83rem; }
    .measurement td { padding:8px 0; border-bottom:1px solid var(--line); } .measurement tr:last-child td { border-bottom:0; }
    .measurement .label { color:var(--muted); } .measurement .value { text-align:right; color:var(--text); font-family:'IBM Plex Mono',monospace; font-variant-numeric:tabular-nums; }
    .measurement .unavailable { color:var(--muted); }
    .hypothesis { border-top:1px solid var(--line); padding:13px 0 3px; margin-top:15px; }
    .hypothesis.dim { opacity:.48; } .hypothesis-title { color:var(--text); font-weight:600; } .hypothesis-meta { color:var(--muted); font-size:.83rem; }
    .status { display:inline-block; min-width:76px; text-align:center; border:1px solid currentColor; border-radius:2px; padding:2px 6px; font:600 .72rem 'IBM Plex Mono',monospace; }
    .status-pass { color:#34C759; } .status-fail { color:#FF453A; } .status-in-progress { color:#FFB020; }
    .correlation-value { color:var(--accent); font:600 clamp(3rem,8vw,6.5rem) 'IBM Plex Mono',monospace; letter-spacing:-.08em; line-height:1; font-variant-numeric:tabular-nums; }
    .bitstream { font:400 .84rem/1.55 'IBM Plex Mono',monospace; word-break:break-all; border:1px solid var(--line); border-radius:2px; overflow:hidden; }
    .bit-header { background:rgba(62,146,204,.16); padding:12px; } .bit-payload { background:var(--surface); padding:12px; border-top:1px solid var(--line); }
    .stButton > button, .stDownloadButton > button { border-radius:2px!important; box-shadow:none!important; font-family:'IBM Plex Sans',sans-serif!important; }
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] { background:var(--accent)!important; border-color:var(--accent)!important; color:#06111A!important; }
    [data-testid="stAlert"] { background:var(--surface)!important; border:1px solid var(--line); border-left:2px solid var(--accent); border-radius:2px!important; box-shadow:none!important; }
    [data-testid="stAlert"] > div, [data-testid="stAlert"] [data-testid="stAlertContainer"], [data-testid="stAlert"] [data-testid="stAlertIcon"] { background:transparent!important; border-radius:2px!important; }
    [data-testid="stAlert"] p, [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p, [data-testid="stAlert"] span { color:var(--text)!important; font-size:.85rem; }
    [data-testid="stAlert"] [data-testid="stAlertIcon"] svg, [data-testid="stAlert"] [data-testid="stAlertIcon"] path { fill:var(--accent)!important; }
    [data-testid="stCode"] { background:var(--surface)!important; border:1px solid var(--line); border-radius:2px!important; }
    [data-testid="stCode"] pre, [data-testid="stCode"] code, [data-testid="stCode"] [data-testid="stCodeBlock"], [data-testid="stCode"] > div { background:transparent!important; border-radius:2px!important; }
    [data-testid="stCode"] pre, [data-testid="stCode"] code { font-family:'IBM Plex Mono',monospace!important; font-variant-numeric:tabular-nums; }
    </style>
    """, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    classes = {"PASS": "status-pass", "FAIL": "status-fail", "IN PROGRESS": "status-in-progress"}
    return f"<span class='status {classes.get(status, '')}'>{status}</span>"
