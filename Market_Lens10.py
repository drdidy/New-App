# MarketLens Pro v5 — End-User Edition (no Plotly)
# Clean glassmorphism UI • All times in CT • Swing CLOSE-only logic
# Run:
#   pip install -r requirements.txt
#   streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, time as dtime, date
import pytz
import io
import zipfile
from typing import List, Tuple, Optional

APP_NAME = "MarketLens Pro v5 — Max Pointe Consulting"

# ===============================
# THEMING (Glassmorphism Dark/Light)
# ===============================

def theme_css(mode: str):
    dark = {
        "bg": "#0a0f1c",
        "panel": "rgba(16,22,39,0.6)",
        "panelSolid": "#0f1627",
        "text": "#E9EEF7",
        "muted": "#AAB4C8",
        "accent": "#7cc8ff",
        "accent2": "#7cf6c5",
        "success": "#29b37a",
        "warn": "#f0b847",
        "danger": "#ff5b6a",
        "border": "rgba(255,255,255,0.12)",
        "shadow": "0 20px 60px rgba(0,0,0,0.55)",
        "glow": "0 0 90px rgba(124,200,255,0.10), 0 0 130px rgba(124,246,197,0.06)"
    }
    light = {
        "bg": "#f5f8ff",
        "panel": "rgba(255,255,255,0.75)",
        "panelSolid": "#ffffff",
        "text": "#0b1020",
        "muted": "#5d6474",
        "accent": "#0b6cff",
        "accent2": "#0f9d58",
        "success": "#188a5b",
        "warn": "#c07b00",
        "danger": "#cc0f2f",
        "border": "rgba(9,16,32,0.12)",
        "shadow": "0 16px 48px rgba(6,11,20,0.12)",
        "glow": "0 0 80px rgba(11,108,255,0.10), 0 0 120px rgba(15,157,88,0.06)"
    }
    p = dark if mode == "Dark" else light
    grad = (
        "radial-gradient(1100px 700px at 15% 5%, rgba(124,200,255,0.10), transparent 55%),"
        "radial-gradient(900px 600px at 85% 15%, rgba(124,246,197,0.10), transparent 60%),"
        f"linear-gradient(160deg, {p['bg']} 0%, {p['bg']} 100%)"
    )
    particles = (
        "radial-gradient(3px 3px at 30% 25%, rgba(255,255,255,0.06), transparent 60%),"
        "radial-gradient(2px 2px at 65% 35%, rgba(255,255,255,0.05), transparent 60%)"
    )
    return f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
      background: {grad}, {particles};
      background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{
      background: {p['panel']};
      border-right: 1px solid {p['border']};
      backdrop-filter: blur(12px);
    }}
    .ml-card {{
      background: {p['panel']};
      border: 1px solid {p['border']};
      border-radius: 20px;
      box-shadow: {p['shadow']};
      padding: 18px 20px;
      transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
      backdrop-filter: blur(10px);
    }}
    .ml-card:hover {{ transform: translateY(-2px); border-color: {p['accent']}; box-shadow: {p['glow']}; }}
    .ml-pill {{
      display:inline-flex; align-items:center; gap:.45rem; padding: 4px 12px; border-radius: 999px;
      border: 1px solid {p['border']}; background: {p['panelSolid']}; font-weight: 700; font-size: .85rem; color: {p['text']};
    }}
    .ml-sub {{ color: {p['muted']}; font-size: .95rem; }}
    .ml-metrics {{ display:flex; gap:12px; flex-wrap:wrap; }}
    .ml-metric {{ padding:14px; border-radius:14px; border:1px solid {p['border']}; background:{p['panelSolid']}; min-width:160px; }}
    .ml-metric .k {{ font-size:.82rem; color:{p['muted']}; }}
    .ml-metric .v {{ font-size:1.45rem; font-weight:800; letter-spacing:.2px; color:{p['text']}; }}
    .ml-row {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:16px; }}
    h1,h2,h3,h4,h5,h6,label,p,span,div {{ color:{p['text']}; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto; }}
    .stDataFrame div[data-testid="StyledTable"] {{ font-variant-numeric: tabular-nums; }}
    .stDownloadButton button, .stButton>button {{
      background: linear-gradient(90deg, {p['accent']}, {p['accent2']});
      color: {'#071222' if mode=='Dark' else '#ffffff'}; border: 0; border-radius: 14px; padding: 10px 16px; font-weight: 800;
      box-shadow: {p['shadow']};
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{ filter:brightness(1.05); transform: translateY(-1px); }}
    .muted {{ color:{p['muted']}; }}
    </style>
    """

def inject_theme(mode: str):
    st.markdown(theme_css(mode), unsafe_allow_html=True)

# ===============================
# TIMEZONES / HELPERS (CT-centric)
# ===============================

CT = pytz.timezone("America/Chicago")
ET = pytz.timezone("America/New_York")
UTC = pytz.UTC

def as_ct(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        ts = UTC.localize(ts)
    return ts.astimezone(CT)

def format_ct(ts: datetime, with_date=True) -> str:
    ts_ct = as_ct(ts)
    return ts_ct.strftime("%Y-%m-%d %H:%M CT" if with_date else "%H:%M")

def rth_slots_ct_dt(proj_date: date, start="08:30", end="14:30") -> List[datetime]:
    h1, m1 = map(int, start.split(":"))
    h2, m2 = map(int, end.split(":"))
    start_dt = CT.localize(datetime.combine(proj_date, dtime(h1, m1)))
    end_dt   = CT.localize(datetime.combine(proj_date, dtime(h2, m2)))
    idx = pd.date_range(start=start_dt, end=end_dt, freq="30min", tz=CT)
    return list(idx.to_pydatetime())

# ===============================
# SLOPES (per 30-min block)
# ===============================
SLOPES = {
    "SPX": {"Skyline": +0.268, "Baseline": -0.235},
    "AAPL": 0.0155, "MSFT": 0.0541, "NVDA": 0.0086, "AMZN": 0.0139, "GOOGL": 0.0122, "TSLA": 0.0285, "META": 0.0674
}

# ===============================
# DATA NORMALIZATION (MultiIndex safety)
# ===============================

def _flatten_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        maybe_fields = set([c[0] for c in df.columns])
        if {"Open","High","Low","Close","Adj Close","Volume"}.issubset(maybe_fields):
            df = df.copy(); df.columns = [c[0] for c in df.columns]
        else:
            df = df.copy(); df.columns = ["|".join([str(x) for x in c if x is not None]) for c in df.columns]
    return df

def _coerce_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    df = _flatten_ohlcv(df)
    cols = list(df.columns)
    out = {}
    for target in ["Open","High","Low","Close","Volume"]:
        if target in df.columns:
            out[target] = pd.to_numeric(df[target], errors="coerce")
        else:
            cand = [c for c in cols if isinstance(c, str) and c.endswith(target)]
            out[target] = pd.to_numeric(df[cand[0]], errors="coerce") if cand else pd.Series(index=df.index, dtype=float)
    if "Adj Close" in df.columns:
        out["Adj Close"] = pd.to_numeric(df["Adj Close"], errors="coerce")
    return pd.DataFrame(out, index=df.index)

# ===============================
# DATA FETCH (yfinance) + CACHE
# ===============================

@st.cache_data(ttl=60)
def fetch_live(symbol: str, start_utc: datetime, end_utc: datetime, interval="30m") -> pd.DataFrame:
    df = yf.download(symbol, start=start_utc, end=end_utc, interval=interval, auto_adjust=False, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    if getattr(df.index, "tz", None) is None:
        df.index = df.index.tz_localize(UTC)
    return _coerce_ohlcv(df)

def price_range_ok(df: pd.DataFrame) -> bool:
    if df.empty or "Close" not in df.columns: 
        return False
    lo, hi = float(df["Close"].min(skipna=True)), float(df["Close"].max(skipna=True))
    return (lo > 0) and (hi/lo < 5.0)

# ===============================
# SWINGS (CLOSE-only, NumPy-safe)
# ===============================

def mark_swings(df: pd.DataFrame, col: str = "Close", k: int = 1) -> pd.DataFrame:
    out = df.copy()
    series = df[col].squeeze()
    if isinstance(series, pd.DataFrame): series = series.iloc[:,0]
    s = pd.to_numeric(series, errors="coerce")
    n = len(s)
    if n == 0:
        out["swing_high"] = False; out["swing_low"] = False; return out
    cond_high = np.ones(n, dtype=bool)
    cond_low  = np.ones(n, dtype=bool)
    for j in range(1, k + 1):
        prev = s.shift(j); nxt = s.shift(-j)
        cond_high &= (s > prev.fillna(-np.inf)).to_numpy() & (s > nxt.fillna(-np.inf)).to_numpy()
        cond_low  &= (s < prev.fillna( np.inf)).to_numpy() & (s < nxt.fillna( np.inf)).to_numpy()
    out["swing_high"] = cond_high; out["swing_low"] = cond_low
    return out

def pick_anchor_from_swings(df_sw: pd.DataFrame, kind: str) -> Optional[Tuple[float, pd.Timestamp]]:
    if kind == "skyline":
        sub = df_sw[df_sw["swing_high"]]
        if sub.empty: return None
        row = sub.sort_values(["Close","Volume"], ascending=[False, False]).iloc[0]
    else:
        sub = df_sw[df_sw["swing_low"]]
        if sub.empty: return None
        row = sub.sort_values(["Close","Volume"], ascending=[True, False]).iloc[0]
    return float(row["Close"]), row.name

# ===============================
# ANCHORS (SPX via ES=F) & (Stocks Mon/Tue)
# ===============================

def detect_spx_anchors_from_es(previous_day: date, k: int = 1):
    # ES=F window: 17:00–19:30 CT (fetch slightly wider to keep edges)
    start_ct = CT.localize(datetime.combine(previous_day, dtime(16,59)))
    end_ct   = CT.localize(datetime.combine(previous_day, dtime(20,1)))
    es = fetch_live("ES=F", start_ct.astimezone(UTC), end_ct.astimezone(UTC))
    if es.empty or not price_range_ok(es):
        return None, None, None
    es_ct = es.copy(); es_ct.index = es_ct.index.tz_convert(CT)
    win = es_ct.between_time("17:00", "19:30")[["Open","High","Low","Close","Volume"]].copy()
    if win.empty: return None, None, None
    sw = mark_swings(win, "Close", k=k)
    sky = pick_anchor_from_swings(sw, "skyline")
    base = pick_anchor_from_swings(sw, "baseline")
    # ES→SPX offset suggestion using previous RTH (14:30–15:30 CT)
    rth_prev_start = CT.localize(datetime.combine(previous_day, dtime(14,30)))
    rth_prev_end   = CT.localize(datetime.combine(previous_day, dtime(15,30)))
    spx_prev = fetch_live("^GSPC", rth_prev_start.astimezone(UTC), rth_prev_end.astimezone(UTC))
    es_prev  = fetch_live("ES=F",  rth_prev_start.astimezone(UTC), rth_prev_end.astimezone(UTC))
    offset = None
    if not spx_prev.empty and not es_prev.empty:
        offset = float(spx_prev["Close"].iloc[-1]) - float(es_prev["Close"].iloc[-1])
    return sky, base, offset

def detect_stock_anchors_two_day(symbol: str, mon_date: date, tue_date: date, k: int = 1):
    # ET sessions 09:30–16:00 across Mon & Tue, outputs converted to CT
    start_et = ET.localize(datetime.combine(mon_date, dtime(9,30)))
    end_et   = ET.localize(datetime.combine(tue_date, dtime(16,0)))
    df = fetch_live(symbol, start_et.astimezone(UTC), end_et.astimezone(UTC))
    if df.empty or not price_range_ok(df): return None, None
    df_et = df.copy(); df_et.index = df_et.index.tz_convert(ET)
    df_et = df_et.between_time("09:30","16:00")[["Open","High","Low","Close","Volume"]].copy()
    if df_et.empty: return None, None
    sw = mark_swings(df_et, "Close", k=k)
    sky = pick_anchor_from_swings(sw, "skyline")
    base = pick_anchor_from_swings(sw, "baseline")
    if (sky is None) or (base is None): return None, None
    sky_p, sky_t = sky; base_p, base_t = base
    return (sky_p, sky_t.astimezone(CT)), (base_p, base_t.astimezone(CT))

# ===============================
# PROJECTIONS & SIGNALS
# ===============================

def project_line(anchor_price: float, anchor_time_ct: datetime, slope_per_block: float, rth_slots_ct: List[datetime]) -> pd.DataFrame:
    minute = 0 if anchor_time_ct.minute < 30 else 30
    anchor_aligned = anchor_time_ct.replace(minute=minute, second=0, microsecond=0)
    def blocks_to(slot_dt: datetime) -> int:
        return int(round((slot_dt - anchor_aligned).total_seconds() / 1800.0))
    rows = []
    for dt in rth_slots_ct:
        b = blocks_to(dt)
        rows.append({"Time (CT)": dt.strftime("%H:%M"), "Price": round(anchor_price + slope_per_block * b, 4)})
    return pd.DataFrame(rows)

def detect_signals(rth_ohlc_ct: pd.DataFrame, line_df: pd.DataFrame, mode="BUY") -> pd.DataFrame:
    if rth_ohlc_ct.empty: return pd.DataFrame([])
    line_map = dict(zip(line_df["Time (CT)"], line_df["Price"]))
    rows = []
    for i, ts in enumerate(rth_ohlc_ct.index):
        tstr = ts.astimezone(CT).strftime("%H:%M")
        if tstr not in line_map: continue
        line = float(line_map[tstr])
        o,h,l,c = (float(rth_ohlc_ct.iloc[i][k]) for k in ["Open","High","Low","Close"])
        is_bull, is_bear = (c > o), (c < o)
        touched = (l <= line <= h)
        if mode=="BUY"  and touched and is_bear and (c > line) and (o > line):
            rows.append({"Time (CT)": tstr, "Line": round(line,4), "Close": round(c,4), "Type": "BUY"})
        if mode=="SELL" and touched and is_bull and (c < line) and (o < line):
            rows.append({"Time (CT)": tstr, "Line": round(line,4), "Close": round(c,4), "Type": "SELL"})
    return pd.DataFrame(rows)

def ema(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()

def ema_crossovers(rth_close_ct: pd.Series):
    e8 = ema(rth_close_ct, 8); e21 = ema(rth_close_ct, 21)
    diff = e8 - e21; sign = np.sign(diff)
    cross_idx = np.where(np.diff(sign) != 0)[0] + 1
    rows = []
    for i in cross_idx:
        rows.append({
            "Time (CT)": rth_close_ct.index[i].astimezone(CT).strftime("%Y-%m-%d %H:%M"),
            "EMA8": round(float(e8.iloc[i]),4),
            "EMA21": round(float(e21.iloc[i]),4),
            "Direction": "Bullish ↑" if diff.iloc[i] > 0 else "Bearish ↓"
        })
    return pd.DataFrame(rows), e8, e21

# ===============================
# COMPLEMENTARY TOOLS (Profitability helpers)
# ===============================

def position_size_planner():
    st.markdown("#### Position Size & R:R Planner")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        eq = st.number_input("Account Equity ($)", value=25000.0, step=100.0, min_value=0.0)
    with c2:
        risk_pct = st.number_input("Risk % per Trade", value=1.0, step=0.1, min_value=0.0, max_value=10.0)
    with c3:
        entry = st.number_input("Entry Price", value=100.0, step=0.1, min_value=0.0)
    with c4:
        stop = st.number_input("Stop Price", value=98.0, step=0.1, min_value=0.0)
    tgt1 = st.number_input("Target 1", value=102.0, step=0.1, min_value=0.0)
    tgt2 = st.number_input("Target 2", value=104.0, step=0.1, min_value=0.0)

    risk_dollars = eq * (risk_pct/100.0)
    per_share_risk = abs(entry - stop) if entry and stop else 0.0
    size = int(risk_dollars / per_share_risk) if per_share_risk > 0 else 0
    rr1 = (tgt1 - entry) / (entry - stop) if per_share_risk > 0 else 0.0
    rr2 = (tgt2 - entry) / (entry - stop) if per_share_risk > 0 else 0.0

    st.markdown("<div class='ml-metrics'>", unsafe_allow_html=True)
    st.markdown(f"<div class='ml-metric'><div class='k'>Risk ($)</div><div class='v'>${risk_dollars:,.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='ml-metric'><div class='k'>Position Size</div><div class='v'>{size:,} shares</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='ml-metric'><div class='k'>R:R @ T1</div><div class='v'>{rr1:.2f}:1</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='ml-metric'><div class='k'>R:R @ T2</div><div class='v'>{rr2:.2f}:1</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def session_checklist():
    st.markdown("#### Session Checklist")
    a,b,c = st.columns(3)
    with a:
        st.checkbox("Exit levels are exits — never entries", value=True)
        st.checkbox("Anchors are magnets, not timing", value=True)
    with b:
        st.checkbox("When in doubt, stay out", value=True)
        st.checkbox("Respect maintenance (SPX 16:00–17:00 CT)", value=True)
    with c:
        st.checkbox("No revenge trading; cap daily loss", value=True)
        st.checkbox("Trade only 30m signals", value=True)

def best_days_panel():
    st.markdown("#### Best Trading Days Cheat Sheet")
    cheat = {
        "NVDA": "Tue / Thu — peak vol mid-week",
        "META": "Tue / Thu — newsflow cadence",
        "TSLA": "Mon / Wed — gamma squeeze + momentum",
        "AAPL": "Mon / Wed — earnings drift & supply chain",
        "AMZN": "Wed / Thu — marketplace volume & OPEX flow",
        "GOOGL":"Thu / Fri — ad spend updates tilt",
        "NFLX": "Tue / Fri — sub metrics / positioning unwind",
    }
    cols = st.columns(3)
    i = 0
    for k,v in cheat.items():
        with cols[i%3]:
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>{k}</div><div style='height:8px'></div><div>{v}</div></div>", unsafe_allow_html=True)
        i+=1

def export_all_button(named_tables: dict):
    # named_tables: {filename:str -> DataFrame}
    if not named_tables: return
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, df in named_tables.items():
            zf.writestr(fname, df.to_csv(index=False))
    st.download_button("⬇️ Export All (ZIP)", data=buf.getvalue(), file_name="marketlens_exports.zip", mime="application/zip", use_container_width=True)

# ===============================
# CONTRACT TOOL (CT)
# ===============================

def contract_projection_tool():
    st.markdown("### Contract Projection Tool")
    c1, c2 = st.columns(2)
    with c1:
        t1 = st.time_input("Point 1 Time (CT)", value=dtime(20,0), step=1800)
        p1 = st.number_input("Point 1 Price", value=10.0, step=0.1)
    with c2:
        t2 = st.time_input("Point 2 Time (CT)", value=dtime(3,30), step=1800)
        p2 = st.number_input("Point 2 Price", value=12.0, step=0.1)
    proj_day = st.date_input("Projection Day (CT)", value=datetime.now(CT).date())

    prev_day = proj_day - timedelta(days=1)
    dt1 = CT.localize(datetime.combine(prev_day if t1.hour >= 20 else proj_day, t1))
    dt2 = CT.localize(datetime.combine(prev_day if t2.hour >= 20 else proj_day, t2))

    blocks_signed = int(round((dt2 - dt1).total_seconds() / 1800.0))
    slope = 0.0 if blocks_signed == 0 else (p2 - p1) / blocks_signed

    slots_dt = rth_slots_ct_dt(proj_day, "08:30", "14:30")
    rows = []
    for slot in slots_dt:
        b = int(round((slot - dt1).total_seconds() / 1800.0))
        rows.append({"Time (CT)": slot.strftime("%H:%M"), "Price": round(p1 + slope*b, 4)})
    df = pd.DataFrame(rows)

    st.markdown("<div class='ml-row'>", unsafe_allow_html=True)
    st.markdown(f"<div class='ml-card'><div class='ml-pill'>Slope</div><div class='ml-sub'>Per 30-min block</div><div style='height:8px'></div><div style='font-weight:800;font-size:1.4rem'>{slope:.4f}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download Contract Projection CSV", df.to_csv(index=False).encode(), "contract_projection.csv", "text/csv", use_container_width=True)
    return df

# ===============================
# UI PRIMITIVES
# ===============================

def card(title, sub=None, body_fn=None, badge=None):
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    if badge:
        st.markdown(f"<div class='ml-pill'>{badge}</div>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='margin:6px 0 2px 0'>{title}</h4>", unsafe_allow_html=True)
    if sub: st.markdown(f"<div class='ml-sub'>{sub}</div>", unsafe_allow_html=True)
    if body_fn:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        body_fn()
    st.markdown("</div>", unsafe_allow_html=True)

def metrics(pairs):
    st.markdown("<div class='ml-metrics'>", unsafe_allow_html=True)
    for k,v in pairs:
        st.markdown(f"<div class='ml-metric'><div class='k'>{k}</div><div class='v'>{v}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ===============================
# MAIN
# ===============================

def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

    with st.sidebar:
        st.markdown("## ⚙️ Display")
        mode = st.radio("Theme", ["Dark", "Light"], index=0)
        inject_theme(mode)

        st.markdown("### 🧮 Slopes (per 30-min)")
        spx_sky  = st.number_input("SPX Skyline (+)", value=SLOPES["SPX"]["Skyline"], step=0.001, format="%.3f")
        spx_base = st.number_input("SPX Baseline (−)", value=SLOPES["SPX"]["Baseline"], step=0.001, format="%.3f")
        st.caption("Stocks use ± magnitudes (e.g., AAPL 0.0155 → Skyline +0.0155 / Baseline −0.0155).")

        st.markdown("### 🧰 Tools")
        st.caption("Use the tabs to compute anchors, projections, signals, and size your trades.")

    st.markdown(f"## {APP_NAME}")
    st.caption("All timestamps in **Central Time (CT)**. Close-only swing logic. Premium glass UI.")

    tab_dash, tab_spx, tab_stk, tab_sig, tab_contract = st.tabs([
        "🧭 Dashboard", "📈 SPX Anchors", "📚 Stock Anchors", "✅ Signals & EMA", "🧮 Contract Tool"
    ])

    exports = {}  # for Export All

    # ============ DASHBOARD ============
    with tab_dash:
        def body():
            metrics([("Mode", "Dark" if mode=="Dark" else "Light"),
                     ("SPX + Slope", f"{spx_sky:+.3f}/blk"),
                     ("SPX − Slope", f"{spx_base:+.3f}/blk")])
            st.markdown("<div class='ml-row'>", unsafe_allow_html=True)
            with st.container():
                position_size_planner()
            with st.container():
                session_checklist()
            with st.container():
                best_days_panel()
            st.markdown("</div>", unsafe_allow_html=True)
        card("Trading Control Center", "Plan risk, confirm rules, and review day tendencies.", body_fn=body, badge="Dashboard")

    # ============ SPX ============
    with tab_spx:
        def body():
            yesterday_ct = (datetime.now(CT) - timedelta(days=1)).date()
            prev_day = st.date_input("Previous trading day (CT)", value=yesterday_ct, key="spx_prev_day")
            k_spx = st.slider("Swing selectivity (bars each side)", 1, 3, 1, key="spx_k")
            sky, base, offset = detect_spx_anchors_from_es(prev_day, k=k_spx)
            if (sky is None) or (base is None):
                st.error("No valid swings found in 17:00–19:30 CT. Try a different date or reduce selectivity.")
                return
            sky_p, sky_t = sky; base_p, base_t = base
            conf = {1:"Moderate",2:"High",3:"Very High"}[k_spx]
            st.markdown("<div class='ml-row'>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>Skyline</div><div class='ml-sub'>Swing-high close</div><div style='height:6px'></div><div class='ml-metric'><div class='k'>Price</div><div class='v'>{sky_p:.2f}</div></div><div class='ml-sub'>@ {format_ct(sky_t)}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>Baseline</div><div class='ml-sub'>Swing-low close</div><div style='height:6px'></div><div class='ml-metric'><div class='k'>Price</div><div class='v'>{base_p:.2f}</div></div><div class='ml-sub'>@ {format_ct(base_t)}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>Confidence</div><div class='ml-sub'>Based on swing selectivity</div><div style='height:6px'></div><div class='ml-metric'><div class='k'>Level</div><div class='v'>{conf}</div></div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # ES→SPX offset (editable)
            suggested_offset = float(offset) if isinstance(offset,(int,float)) else 0.0
            es_spx_offset = st.number_input("ES → SPX offset (adds to ES close to estimate SPX)", value=suggested_offset, step=0.5, key="spx_off")
            sky_spx = sky_p + es_spx_offset; base_spx = base_p + es_spx_offset

            proj_day = st.date_input("Projection Day (CT)", value=prev_day + timedelta(days=1), key="spx_proj")
            slots = rth_slots_ct_dt(proj_day, "08:30", "14:30")
            df_sky = project_line(sky_spx, sky_t, spx_sky, slots)
            df_base = project_line(base_spx, base_t, spx_base, slots)

            st.markdown("#### SPX Projections (08:30–14:30 CT)")
            c1, c2 = st.columns(2)
            with c1:
                st.write("Skyline (+0.268/blk)")
                st.dataframe(df_sky, use_container_width=True, hide_index=True)
                st.download_button("Download Skyline CSV", df_sky.to_csv(index=False).encode(), "spx_skyline.csv", "text/csv")
                exports["spx_skyline.csv"] = df_sky
            with c2:
                st.write("Baseline (−0.235/blk)")
                st.dataframe(df_base, use_container_width=True, hide_index=True)
                st.download_button("Download Baseline CSV", df_base.to_csv(index=False).encode(), "spx_baseline.csv", "text/csv")
                exports["spx_baseline.csv"] = df_base
        card("SPX Anchors → Projection", "Asian session (17:00–19:30 CT) close-only swings → project via SPX slopes.", body_fn=body, badge="SPX")

    # ============ STOCKS ============
    with tab_stk:
        def body():
            sym = st.text_input("Stock Symbol", value="AAPL").upper()
            today_et = datetime.now(ET).date()
            weekday = today_et.weekday()
            last_mon = today_et - timedelta(days=(weekday - 0) % 7 or 7)
            last_tue = last_mon + timedelta(days=1)
            c1, c2 = st.columns(2)
            with c1: mon_date = st.date_input("Monday (ET session)", value=last_mon, key="mon")
            with c2: tue_date = st.date_input("Tuesday (ET session)", value=last_tue, key="tue")
            k_stk = st.slider("Swing selectivity (bars each side)", 1, 3, 1, key="stk_k")
            sky, base = detect_stock_anchors_two_day(sym, mon_date, tue_date, k=k_stk)
            if (sky is None) or (base is None):
                st.error("No valid swings across Mon/Tue sessions. Try different dates or reduce selectivity.")
                return
            sky_p, sky_t = sky; base_p, base_t = base
            slope_mag = SLOPES.get(sym, SLOPES.get(sym.capitalize(), 0.015))
            conf = {1:"Moderate",2:"High",3:"Very High"}[k_stk]

            st.markdown("<div class='ml-row'>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>{sym} Skyline</div><div class='ml-sub'>Swing-high close</div><div style='height:6px'></div><div class='ml-metric'><div class='k'>Price</div><div class='v'>{sky_p:.2f}</div></div><div class='ml-sub'>@ {format_ct(sky_t)}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>{sym} Baseline</div><div class='ml-sub'>Swing-low close</div><div style='height:6px'></div><div class='ml-metric'><div class='k'>Price</div><div class='v'>{base_p:.2f}</div></div><div class='ml-sub'>@ {format_ct(base_t)}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>Confidence</div><div class='ml-sub'>Based on swing selectivity</div><div style='height:6px'></div><div class='ml-metric'><div class='k'>Level</div><div class='v'>{conf}</div></div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Default projection day: first Wednesday after Tue
            days_ahead = (2 - tue_date.weekday()) % 7
            if days_ahead == 0: days_ahead = 7
            first_wed = tue_date + timedelta(days=days_ahead)
            proj_day = st.date_input("Projection Day (CT)", value=first_wed, key=f"{sym}_proj")
            slots = rth_slots_ct_dt(proj_day, "08:30", "14:30")
            df_sky = project_line(sky_p, sky_t, +slope_mag, slots)
            df_base = project_line(base_p, base_t, -slope_mag, slots)

            st.markdown(f"#### {sym} Projections (08:30–14:30 CT)")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"Skyline (+{slope_mag:.4f}/blk)")
                st.dataframe(df_sky, use_container_width=True, hide_index=True)
                st.download_button(f"Download {sym} Skyline CSV", df_sky.to_csv(index=False).encode(), f"{sym}_skyline.csv", "text/csv")
                exports[f"{sym}_skyline.csv"] = df_sky
            with c2:
                st.write(f"Baseline (−{slope_mag:.4f}/blk)")
                st.dataframe(df_base, use_container_width=True, hide_index=True)
                st.download_button(f"Download {sym} Baseline CSV", df_base.to_csv(index=False).encode(), f"{sym}_baseline.csv", "text/csv")
                exports[f"{sym}_baseline.csv"] = df_base
        card("Stock Anchors → Projection", "Mon/Tue close-only swings → project via stock slopes.", body_fn=body, badge="Stocks")

    # ============ SIGNALS & EMA ============
    with tab_sig:
        def body():
            sym2 = st.text_input("Symbol", value="^GSPC").upper()
            day = st.date_input("Day (CT)", value=datetime.now(CT).date(), key="sig_day")
            rth_start = CT.localize(datetime.combine(day, dtime(8,30)))
            rth_end   = CT.localize(datetime.combine(day, dtime(14,30)))
            df = fetch_live(sym2, rth_start.astimezone(UTC), rth_end.astimezone(UTC))
            df_ct = df.copy()
            if not df_ct.empty:
                df_ct.index = df_ct.index.tz_convert(CT)
                df_ct = df_ct.between_time("08:30","14:30")

            st.markdown("##### Reference Line")
            c1,c2,c3 = st.columns(3)
            with c1: ref_price = st.number_input("Anchor Price", value=5000.0, step=1.0)
            with c2: ref_time  = st.time_input("Anchor Time (CT)", value=dtime(17,0), step=1800)
            with c3: ref_slope = st.number_input("Slope per 30m (+/−)", value=0.268, step=0.001, format="%.3f")
            slots = rth_slots_ct_dt(day, "08:30", "14:30")
            line_df = project_line(ref_price, CT.localize(datetime.combine(day, ref_time)), ref_slope, slots)

            if not df_ct.empty:
                buys = detect_signals(df_ct, line_df, "BUY")
                sells = detect_signals(df_ct, line_df, "SELL")
                # Summary metrics
                latest_buy = buys["Time (CT)"].iloc[-1] if not buys.empty else "—"
                latest_sell = sells["Time (CT)"].iloc[-1] if not sells.empty else "—"
                metrics([("Buys", len(buys)), ("Sells", len(sells)), ("Last Buy", latest_buy), ("Last Sell", latest_sell)])
                st.write("Reference Line Table")
                st.dataframe(line_df, use_container_width=True, hide_index=True)
                st.write("Buy Signals")
                st.dataframe(buys, use_container_width=True, hide_index=True)
                st.write("Sell Signals")
                st.dataframe(sells, use_container_width=True, hide_index=True)

                # EMA Crossovers
                st.markdown("##### EMA(8/21) Crossovers")
                ema_df, _, _ = ema_crossovers(df_ct["Close"])
                st.dataframe(ema_df, use_container_width=True, hide_index=True)

                # Exports
                exports["reference_line.csv"] = line_df
                exports[f"{sym2}_buys.csv"] = buys
                exports[f"{sym2}_sells.csv"] = sells
                exports[f"{sym2}_ema_crossovers.csv"] = ema_df
            else:
                st.info("No 30-minute RTH data available for that day/symbol yet.")
        card("Signals & EMA", "Line-touch entries on 30-min bars + EMA8/21 crossovers.", body_fn=body, badge="Signals")

    # ============ CONTRACT TOOL ============
    with tab_contract:
        def body():
            df = contract_projection_tool()
            exports["contract_projection.csv"] = df
        card("Contract Projection", "Two points (20:00 prev → 10:00 today) → slope → 08:30–14:30 CT forecast.", body_fn=body, badge="Contracts")

    # Export all tables
    export_all_button(exports)

    st.markdown("<div class='muted' style='margin-top:12px'>© 2025 MarketLens Pro • Streamlit • All computations per your rules</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
