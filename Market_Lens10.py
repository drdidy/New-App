# MarketLens Pro v5 by Max Pointe Consulting — Streamlit-only (no Plotly)
# All timestamps displayed in Central Time (CT).
# Run:
#   pip install -r requirements.txt
#   streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, time as dtime, date
import pytz
from typing import Iterable, List, Tuple, Optional

APP_NAME = "MarketLens Pro v5 by Max Pointe Consulting"

# ===============================
# THEME / COSMIC BACKGROUND (Dark + Light)
# ===============================

def theme_css(mode: str):
    dark = {
        "bg": "#0a0f1c",
        "panel": "rgba(16, 22, 39, 0.75)",
        "panelSolid": "#0f1627",
        "text": "#E9EEF7",
        "muted": "#AAB4C8",
        "accent": "#7cc8ff",
        "accent2": "#7cf6c5",
        "success": "#29b37a",
        "warn": "#f0b847",
        "danger": "#ff5b6a",
        "border": "rgba(255,255,255,0.12)",
        "shadow": "0 10px 34px rgba(0,0,0,0.45)",
        "glow": "0 0 80px rgba(124,200,255,0.12), 0 0 120px rgba(124,246,197,0.06)"
    }
    light = {
        "bg": "#f6f9ff",
        "panel": "rgba(255,255,255,0.8)",
        "panelSolid": "#ffffff",
        "text": "#0b1020",
        "muted": "#5d6474",
        "accent": "#0b6cff",
        "accent2": "#0f9d58",
        "success": "#188a5b",
        "warn": "#c07b00",
        "danger": "#cc0f2f",
        "border": "rgba(9,16,32,0.12)",
        "shadow": "0 10px 34px rgba(6,11,20,0.08)",
        "glow": "0 0 80px rgba(11,108,255,0.08), 0 0 120px rgba(15,157,88,0.05)"
    }
    p = dark if mode == "Dark" else light
    grad = (
        "radial-gradient(900px 600px at 20% 10%, rgba(124,200,255,0.08), transparent 60%),"
        "radial-gradient(700px 500px at 80% 20%, rgba(124,246,197,0.08), transparent 60%),"
        f"linear-gradient(160deg, {p['bg']} 0%, {p['bg']} 100%)"
    )
    particles = (
        "radial-gradient(3px 3px at 30% 20%, rgba(255,255,255,0.05), transparent 60%),"
        "radial-gradient(2px 2px at 70% 35%, rgba(255,255,255,0.04), transparent 60%)"
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
      backdrop-filter: blur(10px);
    }}
    .ml-card {{
      background: {p['panel']};
      border: 1px solid {p['border']};
      border-radius: 16px;
      box-shadow: {p['shadow']};
      padding: 16px 18px;
      transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
    }}
    .ml-card:hover {{ transform: translateY(-2px); border-color: {p['accent']}; box-shadow: {p['glow']}; }}
    .ml-pill {{
      display:inline-flex; align-items:center; gap:.4rem; padding: 2px 10px; border-radius: 999px;
      border: 1px solid {p['border']}; background: {p['panelSolid']}; font-weight: 600; font-size: .85rem; color: {p['text']};
    }}
    .ml-sub {{ color: {p['muted']}; font-size: .92rem; }}
    .ml-metrics {{ display:flex; gap:12px; flex-wrap:wrap; }}
    .ml-metric {{ padding:12px 14px; border-radius:12px; border:1px solid {p['border']}; background:{p['panelSolid']}; min-width:150px; }}
    .ml-metric .k {{ font-size:.82rem; color:{p['muted']}; }}
    .ml-metric .v {{ font-size:1.35rem; font-weight:800; letter-spacing:.2px; color:{p['text']}; }}
    h1,h2,h3,h4,h5,h6,label,p,span,div {{ color:{p['text']}; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; }}
    .stDataFrame div[data-testid="StyledTable"] {{ font-variant-numeric: tabular-nums; }}
    .stDownloadButton button, .stButton>button {{
      background: linear-gradient(90deg, {p['accent']}, {p['accent2']});
      color: {'#071222' if mode=='Dark' else '#ffffff'}; border: 0; border-radius: 12px; padding: 8px 14px; font-weight: 700;
      box-shadow: {p['shadow']};
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{ filter:brightness(1.05); transform: translateY(-1px); }}
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
# DATA NORMALIZATION (handle MultiIndex columns)
# ===============================

ESSENTIALS = ["Open","High","Low","Close","Volume","Adj Close"]

def _flatten_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure single-level OHLCV columns even if yfinance returns MultiIndex."""
    if isinstance(df.columns, pd.MultiIndex):
        # If top level looks like fields and second level like tickers:
        maybe_fields = set([c[0] for c in df.columns])
        if {"Open","High","Low","Close","Adj Close","Volume"}.issubset(maybe_fields):
            # Keep first level only
            df = df.copy()
            df.columns = [c[0] for c in df.columns]
        else:
            # Fallback: join all levels
            df = df.copy()
            df.columns = ["|".join([str(x) for x in c if x is not None]) for c in df.columns]
    return df

def _coerce_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce/rename columns so df has standard OHLCV single-level columns.
    If exact names are missing, try suffix matches (e.g., 'AAPL Close').
    """
    df = _flatten_ohlcv(df)
    cols = list(df.columns)
    out = {}
    for target in ["Open","High","Low","Close","Volume"]:
        if target in df.columns:
            out[target] = pd.to_numeric(df[target], errors="coerce")
        else:
            # try suffix match
            cand = [c for c in cols if isinstance(c, str) and c.endswith(target)]
            if cand:
                out[target] = pd.to_numeric(df[cand[0]], errors="coerce")
            else:
                out[target] = pd.Series(index=df.index, dtype=float)
    out_df = pd.DataFrame(out, index=df.index)
    # Retain Adj Close if present
    if "Adj Close" in df.columns:
        out_df["Adj Close"] = pd.to_numeric(df["Adj Close"], errors="coerce")
    return out_df

# ===============================
# DATA FETCHING (yfinance) + CACHING
# ===============================

@st.cache_data(ttl=60)
def fetch_live(symbol: str, start_utc: datetime, end_utc: datetime, interval="30m") -> pd.DataFrame:
    df = yf.download(symbol, start=start_utc, end=end_utc, interval=interval, auto_adjust=False, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    if getattr(df.index, "tz", None) is None:
        df.index = df.index.tz_localize(UTC)
    df = _coerce_ohlcv(df)
    return df

@st.cache_data(ttl=300)
def fetch_hist(symbol: str, period="5d", interval="30m") -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    if getattr(df.index, "tz", None) is None:
        df.index = df.index.tz_localize(UTC)
    df = _coerce_ohlcv(df)
    return df

def price_range_ok(df: pd.DataFrame) -> bool:
    if df.empty or "Close" not in df.columns: 
        return False
    lo, hi = float(df["Close"].min(skipna=True)), float(df["Close"].max(skipna=True))
    return (lo > 0) and (hi/lo < 5.0)

# ===============================
# SWING DETECTION (CLOSE-only, NumPy-safe)
# ===============================

def mark_swings(df: pd.DataFrame, col: str = "Close", k: int = 1) -> pd.DataFrame:
    """
    Local swings using CLOSE-only.
    swing_high: CLOSE > CLOSE of previous k bars AND next k bars.
    swing_low : CLOSE < CLOSE of previous k bars AND next k bars.
    Robust to MultiIndex/duplicate columns; guarantees Series via .squeeze().
    """
    out = df.copy()
    series = df[col]
    # Guarantee 1-D
    series = series.squeeze()
    if isinstance(series, pd.DataFrame):
        # Shouldn't happen after squeeze; extra guard
        series = series.iloc[:, 0]
    s = pd.to_numeric(series, errors="coerce")
    n = len(s)
    if n == 0:
        out["swing_high"] = False
        out["swing_low"] = False
        return out

    cond_high = np.ones(n, dtype=bool)
    cond_low  = np.ones(n, dtype=bool)

    for j in range(1, k + 1):
        prev = s.shift(j)
        nxt  = s.shift(-j)
        cond_high &= (s > prev.fillna(-np.inf)).to_numpy() & (s > nxt.fillna(-np.inf)).to_numpy()
        cond_low  &= (s < prev.fillna( np.inf)).to_numpy() & (s < nxt.fillna( np.inf)).to_numpy()

    out["swing_high"] = cond_high
    out["swing_low"]  = cond_low
    return out

def pick_anchor_from_swings(df_sw: pd.DataFrame, kind: str) -> Optional[Tuple[float, pd.Timestamp]]:
    """
    kind == "skyline": among swing_high rows → highest CLOSE (tie: highest VOLUME)
    kind == "baseline": among swing_low rows → lowest CLOSE (tie: highest VOLUME)
    """
    if kind == "skyline":
        sub = df_sw[df_sw["swing_high"]]
        if sub.empty: return None
        row = sub.sort_values(["Close", "Volume"], ascending=[False, False]).iloc[0]
    else:
        sub = df_sw[df_sw["swing_low"]]
        if sub.empty: return None
        row = sub.sort_values(["Close", "Volume"], ascending=[True, False]).iloc[0]
    return float(row["Close"]), row.name

# ===============================
# ANCHOR DETECTION
# ===============================

def detect_spx_anchors_from_es(previous_day: date, k: int = 1):
    """
    ES=F window (CT): 17:00–19:30 on previous day for CLOSE-only swings.
    Fetch 16:59–20:01 CT to avoid boundary loss, then filter.
    Returns: (sky_tuple, base_tuple, suggested_offset, raw_ct_df, swings_ct_df)
    """
    start_ct = CT.localize(datetime.combine(previous_day, dtime(16,59)))
    end_ct   = CT.localize(datetime.combine(previous_day, dtime(20,1)))
    es = fetch_live("ES=F", start_ct.astimezone(UTC), end_ct.astimezone(UTC))
    if es.empty or not price_range_ok(es):
        return None, None, None, pd.DataFrame(), pd.DataFrame()

    es_ct = es.copy()
    es_ct.index = es_ct.index.tz_convert(CT)

    raw_ct = es_ct.between_time("17:00", "20:00")[["Open","High","Low","Close","Volume"]].copy()
    win = es_ct.between_time("17:00", "19:30")[["Open","High","Low","Close","Volume"]].copy()
    if win.empty:
        return None, None, None, raw_ct, pd.DataFrame()

    sw = mark_swings(win, col="Close", k=k)
    sky = pick_anchor_from_swings(sw, "skyline")
    base = pick_anchor_from_swings(sw, "baseline")

    # Suggest ES→SPX offset from previous RTH (14:30–15:30 CT)
    rth_prev_start = CT.localize(datetime.combine(previous_day, dtime(14,30)))
    rth_prev_end   = CT.localize(datetime.combine(previous_day, dtime(15,30)))
    spx_prev = fetch_live("^GSPC", rth_prev_start.astimezone(UTC), rth_prev_end.astimezone(UTC))
    es_prev  = fetch_live("ES=F",  rth_prev_start.astimezone(UTC), rth_prev_end.astimezone(UTC))
    offset = None
    if not spx_prev.empty and not es_prev.empty:
        spx_last = float(spx_prev["Close"].iloc[-1])
        es_last  = float(es_prev["Close"].iloc[-1])
        offset = spx_last - es_last

    return sky, base, offset, raw_ct, sw

def detect_stock_anchors_two_day(symbol: str, mon_date: date, tue_date: date, k: int = 1):
    """
    Stocks Mon/Tue (ET): 09:30–16:00 combined, CLOSE-only swings.
    Output audit tables and anchor timestamps converted to CT.
    Returns: (sky_tuple_ct, base_tuple_ct, raw_ct_df, swings_ct_df)
    """
    start_et = ET.localize(datetime.combine(mon_date, dtime(9,30)))
    end_et   = ET.localize(datetime.combine(tue_date, dtime(16,0)))
    df = fetch_live(symbol, start_et.astimezone(UTC), end_et.astimezone(UTC))
    if df.empty or not price_range_ok(df):
        return None, None, pd.DataFrame(), pd.DataFrame()

    df_et = df.copy()
    df_et.index = df_et.index.tz_convert(ET)
    df_et = df_et.between_time("09:30","16:00")[["Open","High","Low","Close","Volume"]].copy()
    if df_et.empty:
        return None, None, pd.DataFrame(), pd.DataFrame()

    sw_et = mark_swings(df_et, col="Close", k=k)
    sky_et = pick_anchor_from_swings(sw_et, "skyline")
    base_et = pick_anchor_from_swings(sw_et, "baseline")
    if (sky_et is None) or (base_et is None):
        return None, None, pd.DataFrame(), pd.DataFrame()

    sky_p, sky_t_et = sky_et
    base_p, base_t_et = base_et

    raw_ct = df_et.copy(); raw_ct.index = raw_ct.index.tz_convert(CT)
    sw_ct  = sw_et.copy();  sw_ct.index  = sw_ct.index.tz_convert(CT)

    sky_ct = (sky_p, sky_t_et.astimezone(CT))
    base_ct = (base_p, base_t_et.astimezone(CT))
    return sky_ct, base_ct, raw_ct, sw_ct

# ===============================
# PROJECTIONS & SIGNALS
# ===============================

def project_line(anchor_price: float, anchor_time_ct: datetime, slope_per_block: float, rth_slots_ct: List[datetime]) -> pd.DataFrame:
    """
    Project a line from an anchor (CT datetime) using slope per 30-min block.
    Uses signed block deltas across days, aligning anchor down to nearest 30m.
    """
    minute = 0 if anchor_time_ct.minute < 30 else 30
    anchor_aligned = anchor_time_ct.replace(minute=minute, second=0, microsecond=0)

    def blocks_to(slot_dt: datetime) -> int:
        return int(round((slot_dt - anchor_aligned).total_seconds() / 1800.0))

    prices, times = [], []
    for dt in rth_slots_ct:
        b = blocks_to(dt)
        prices.append(round(anchor_price + slope_per_block * b, 4))
        times.append(dt.strftime("%H:%M"))
    return pd.DataFrame({"Time (CT)": times, "Price": prices})

def detect_signals(rth_ohlc_ct: pd.DataFrame, line_df: pd.DataFrame, mode="BUY") -> pd.DataFrame:
    """
    BUY: bearish candle touches line from above & closes ABOVE.
    SELL: bullish candle touches line from below & closes BELOW.
    """
    if rth_ohlc_ct.empty:
        return pd.DataFrame([])
    line_map = dict(zip(line_df["Time (CT)"], line_df["Price"]))
    rows = []
    for i, ts in enumerate(rth_ohlc_ct.index):
        tstr = ts.astimezone(CT).strftime("%H:%M")
        if tstr not in line_map:
            continue
        line = float(line_map[tstr])
        o,h,l,c = (float(rth_ohlc_ct.iloc[i][k]) for k in ["Open","High","Low","Close"])
        is_bull, is_bear = (c > o), (c < o)
        touched = (l <= line <= h)
        if mode=="BUY"  and touched and is_bear and (c > line) and (o > line):
            rows.append({"Time (CT)": tstr, "Line": round(line,4), "Close": round(c,4), "Type": "BUY",  "Note": "Bearish; touched from above; closed above"})
        if mode=="SELL" and touched and is_bull and (c < line) and (o < line):
            rows.append({"Time (CT)": tstr, "Line": round(line,4), "Close": round(c,4), "Type": "SELL", "Note": "Bullish; touched from below; closed below"})
    return pd.DataFrame(rows)

def ema(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()

def ema_crossovers(rth_close_ct: pd.Series):
    e8 = ema(rth_close_ct, 8)
    e21 = ema(rth_close_ct, 21)
    diff = e8 - e21
    sign = np.sign(diff)
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
# CONTRACT PROJECTION TOOL (CT)
# ===============================
def contract_projection_tool():
    st.markdown("### Contract Projection Tool")
    st.caption("Times are **Central Time**. Enter two points from **8:00 PM (prev day)** to **10:00 AM (current)**. Forecast outputs for **08:30–14:30 CT**.")
    col1, col2 = st.columns(2)
    with col1:
        t1 = st.time_input("Point 1 Time (CT)", value=dtime(20,0), step=1800)
        p1 = st.number_input("Point 1 Price", value=10.0, step=0.1)
    with col2:
        t2 = st.time_input("Point 2 Time (CT)", value=dtime(3,30), step=1800)
        p2 = st.number_input("Point 2 Price", value=12.0, step=0.1)

    proj_day = st.date_input("Projection day (CT)", value=datetime.now(CT).date())

    prev_day = proj_day - timedelta(days=1)
    dt1 = CT.localize(datetime.combine(prev_day if t1.hour >= 20 else proj_day, t1))
    dt2 = CT.localize(datetime.combine(prev_day if t2.hour >= 20 else proj_day, t2))

    blocks_signed = int(round((dt2 - dt1).total_seconds() / 1800.0))
    slope = 0.0 if blocks_signed == 0 else (p2 - p1) / blocks_signed
    st.info(f"Slope per 30-min block: **{slope:.4f}**  |  Blocks between points: {blocks_signed}")

    slots_dt = rth_slots_ct_dt(proj_day, "08:30", "14:30")

    def blocks_from_dt1(slot_dt):
        return int(round((slot_dt - dt1).total_seconds() / 1800.0))

    rows = []
    for slot in slots_dt:
        b = blocks_from_dt1(slot)
        price = round(p1 + slope * b, 4)
        rows.append({"Time (CT)": slot.strftime("%H:%M"), "Price": price})
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download Contract Projection CSV", df.to_csv(index=False).encode(), "contract_projection.csv", "text/csv", use_container_width=True)
    return df

# ===============================
# UI HELPERS
# ===============================
def card(title, sub=None, body_fn=None, badge=None):
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    if badge:
        st.markdown(f"<div class='ml-pill'>{badge}</div>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='margin:6px 0 2px 0'>{title}</h4>", unsafe_allow_html=True)
    if sub: st.markdown(f"<div class='ml-sub'>{sub}</div>", unsafe_allow_html=True)
    if body_fn:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        body_fn()
    st.markdown("</div>", unsafe_allow_html=True)

# ===============================
# MAIN APP
# ===============================
def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        mode = st.radio("Theme", ["Dark", "Light"], index=0)
        inject_theme(mode)

        st.markdown("### 🧮 Slopes (per 30-min block)")
        st.caption("SPX uses +0.268 (Skyline) / −0.235 (Baseline); stocks use ± magnitudes shown.")
        spx_sky  = st.number_input("SPX Skyline (+)", value=SLOPES["SPX"]["Skyline"], step=0.001, format="%.3f")
        spx_base = st.number_input("SPX Baseline (−)", value=SLOPES["SPX"]["Baseline"], step=0.001, format="%.3f")

    st.markdown(f"## {APP_NAME}")
    st.caption("All timestamps are shown in **Central Time (CT)**.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "SPX (Asian Session Anchors)",
        "Stocks (Mon/Tue Anchors)",
        "Signals & EMA",
        "Contract Tool"
    ])

    # ======== TAB 1: SPX (ES=F) ========
    with tab1:
        st.markdown("### SPX via ES=F (Asian Session, CLOSE-only swings)")
        yesterday_ct = (datetime.now(CT) - timedelta(days=1)).date()
        prev_day = st.date_input("Previous trading day (CT)", value=yesterday_ct)
        k_spx = st.slider("Swing width (bars each side)", 1, 3, 1, help="k=1 = 3-bar swing; higher k requires a more pronounced swing.")

        sky, base, offset, es_raw_ct, es_sw = detect_spx_anchors_from_es(prev_day, k=k_spx)

        def body_spx():
            if (sky is None) or (base is None):
                st.error("No swing highs/lows found in 17:00–19:30 CT window. Try a different date or reduce k.")
                return

            sky_price_es, sky_time_ct = sky
            base_price_es, base_time_ct = base

            st.write(f"**ES Skyline (swing-high close)**: {sky_price_es} @ {format_ct(sky_time_ct)}")
            st.write(f"**ES Baseline (swing-low close)**: {base_price_es} @ {format_ct(base_time_ct)}")

            with st.expander("Audit: ES=F raw 30-min bars (17:00–20:00 CT)"):
                raw_show = es_raw_ct.copy()
                raw_show["Time (CT)"] = raw_show.index.map(lambda x: format_ct(x))
                st.dataframe(raw_show.reset_index(drop=True), use_container_width=True, hide_index=True)

            with st.expander("Audit: Swing-marked window (17:00–19:30 CT)"):
                sw_show = es_sw.copy()
                sw_show["Time (CT)"] = sw_show.index.map(lambda x: format_ct(x))
                st.dataframe(sw_show.reset_index(drop=True), use_container_width=True, hide_index=True)

            suggested_offset = float(offset) if isinstance(offset, (int, float)) else 0.0
            es_spx_offset = st.number_input("ES → SPX offset (add to ES close to estimate SPX)", value=suggested_offset, step=0.5)
            sky_spx  = sky_price_es  + es_spx_offset
            base_spx = base_price_es + es_spx_offset

            proj_day = st.date_input("Projection day (CT)", value=prev_day + timedelta(days=1), key="spx_proj_day")
            slots_dt = rth_slots_ct_dt(proj_day, "08:30", "14:30")
            df_sky = project_line(sky_spx, sky_time_ct, spx_sky, slots_dt)
            df_base = project_line(base_spx, base_time_ct, spx_base, slots_dt)

            c1, c2 = st.columns(2)
            with c1:
                st.write("SPX Skyline (+0.268 per 30m)")
                st.dataframe(df_sky, use_container_width=True, hide_index=True)
                st.download_button("Download SPX Skyline CSV", df_sky.to_csv(index=False).encode(), "spx_skyline.csv", "text/csv")
            with c2:
                st.write("SPX Baseline (−0.235 per 30m)")
                st.dataframe(df_base, use_container_width=True, hide_index=True)
                st.download_button("Download SPX Baseline CSV", df_base.to_csv(index=False).encode(), "spx_baseline.csv", "text/csv")

        card("Anchors → Projection", sub="ES Asian session (17:00–19:30 CT) CLOSE-only swings → SPX via offset → project through next-day RTH.", body_fn=body_spx, badge="SPX")

    # ======== TAB 2: STOCKS (Mon/Tue) ========
    with tab2:
        st.markdown("### Individual Stocks (Mon/Tue, CLOSE-only swings)")
        sym = st.text_input("Stock symbol", value="AAPL").upper()

        today_et = datetime.now(ET).date()
        weekday = today_et.weekday()  # Mon=0
        last_mon = today_et - timedelta(days=(weekday - 0) % 7 or 7)
        last_tue = last_mon + timedelta(days=1)

        c1, c2 = st.columns(2)
        with c1:
            mon_date = st.date_input("Monday (ET session date)", value=last_mon, key="mon_et")
        with c2:
            tue_date = st.date_input("Tuesday (ET session date)", value=last_tue, key="tue_et")

        k_stk = st.slider("Swing width (bars each side)", 1, 3, 1, key="k_stock", help="k=1 = 3-bar swing; higher k = stricter swings.")

        sky_ct, base_ct, raw_ct, sw_ct = detect_stock_anchors_two_day(sym, mon_date, tue_date, k=k_stk)

        def body_stk():
            if (sky_ct is None) or (base_ct is None):
                st.error("No swing highs/lows found across Mon/Tue. Try other dates, symbol, or reduce k.")
                return

            sky_p, sky_t = sky_ct
            base_p, base_t = base_ct
            st.write(f"**{sym} Skyline (swing-high close)**: {sky_p} @ {format_ct(sky_t)}")
            st.write(f"**{sym} Baseline (swing-low close)**: {base_p} @ {format_ct(base_t)}")

            with st.expander("Audit: Mon/Tue 30-min bars (displayed in CT)"):
                df_show = raw_ct.copy()
                df_show["Time (CT)"] = df_show.index.map(lambda x: format_ct(x))
                st.dataframe(df_show.reset_index(drop=True), use_container_width=True, hide_index=True)

            with st.expander("Audit: Swing-marked bars (CT)"):
                df_sw = sw_ct.copy()
                df_sw["Time (CT)"] = df_sw.index.map(lambda x: format_ct(x))
                st.dataframe(df_sw.reset_index(drop=True), use_container_width=True, hide_index=True)

            slope_mag = SLOPES.get(sym, SLOPES.get(sym.capitalize(), 0.015))
            # Next Wednesday after Tuesday
            days_ahead = (2 - tue_date.weekday()) % 7
            if days_ahead == 0: days_ahead = 7
            first_wed = tue_date + timedelta(days=days_ahead)

            proj_day = st.date_input("Projection day (CT)", value=first_wed, key=f"{sym}_proj_day")
            slots_dt = rth_slots_ct_dt(proj_day, "08:30", "14:30")
            df_sky = project_line(sky_p, sky_t, +slope_mag, slots_dt)
            df_base = project_line(base_p, base_t, -slope_mag, slots_dt)

            c1, c2 = st.columns(2)
            with c1:
                st.write(f"{sym} Skyline (+{slope_mag:.4f} per 30m)")
                st.dataframe(df_sky, use_container_width=True, hide_index=True)
                st.download_button(f"Download {sym} Skyline CSV", df_sky.to_csv(index=False).encode(), f"{sym}_skyline.csv", "text/csv")
            with c2:
                st.write(f"{sym} Baseline (−{slope_mag:.4f} per 30m)")
                st.dataframe(df_base, use_container_width=True, hide_index=True)
                st.download_button(f"Download {sym} Baseline CSV", df_base.to_csv(index=False).encode(), f"{sym}_baseline.csv", "text/csv")

        card("Anchors → Projection", sub="Mon/Tue ET sessions, CLOSE-only swings (displayed in CT) → project through chosen RTH day.", body_fn=body_stk, badge=sym)

    # ======== TAB 3: SIGNALS & EMA (CT) ========
    with tab3:
        st.markdown("### Signal Detection (30m) + EMA(8/21) — All in CT")
        sym2 = st.text_input("Symbol for signals/EMA", value="^GSPC").upper()
        proj_day = st.date_input("Day (CT)", value=datetime.now(CT).date(), key="sig_day")
        rth_start = CT.localize(datetime.combine(proj_day, dtime(8,30)))
        rth_end   = CT.localize(datetime.combine(proj_day, dtime(14,30)))
        df_rth = fetch_live(sym2, rth_start.astimezone(UTC), rth_end.astimezone(UTC))
        df_rth_ct = df_rth.copy()
        if not df_rth_ct.empty:
            df_rth_ct.index = df_rth_ct.index.tz_convert(CT)
            df_rth_ct = df_rth_ct.between_time("08:30", "14:30")

        st.markdown("#### Reference Line (for signals)")
        ref_price = st.number_input("Anchor price", value=5000.0, step=1.0)
        ref_time  = st.time_input("Anchor time (CT)", value=dtime(17,0), step=1800)
        ref_slope = st.number_input("Slope per 30m (+ or −)", value=0.268, step=0.001, format="%.3f")
        slots_dt = rth_slots_ct_dt(proj_day, "08:30", "14:30")
        ref_df = project_line(ref_price, CT.localize(datetime.combine(proj_day, ref_time)), ref_slope, slots_dt)

        c1, c2 = st.columns(2)
        with c1:
            st.write("Reference Line Table")
            st.dataframe(ref_df, use_container_width=True, hide_index=True)
        with c2:
            st.download_button("Download Reference Line CSV", ref_df.to_csv(index=False).encode(), "reference_line.csv", "text/csv")

        if not df_rth_ct.empty:
            st.markdown("#### Signals (CT)")
            buys = detect_signals(df_rth_ct, ref_df, mode="BUY")
            sells = detect_signals(df_rth_ct, ref_df, mode="SELL")
            st.write("**Buy Signals**")
            st.dataframe(buys, use_container_width=True, hide_index=True)
            st.write("**Sell Signals**")
            st.dataframe(sells, use_container_width=True, hide_index=True)

            st.markdown("#### EMA(8/21) Crossovers (CT)")
            ema_df, _, _ = ema_crossovers(df_rth_ct["Close"])
            st.dataframe(ema_df, use_container_width=True, hide_index=True)
        else:
            st.info("No 30m RTH data available for this day/symbol yet.")

    # ======== TAB 4: CONTRACT TOOL ========
    with tab4:
        contract_projection_tool()

    st.markdown("<div style='opacity:.7; font-size:.85rem; margin-top:8px'>© 2025 MarketLens Pro • Built with Streamlit (all times in CT)</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
