# app.py
# MarketLens Pro v5 — SPX (tables only, no charts)
# Run:
#   pip install -r requirements.txt
#   streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dtime, date
import pytz

# --- optional safe import for yfinance ---
try:
    import yfinance as yf
    YF_AVAILABLE = True
except Exception:
    YF_AVAILABLE = False
    yf = None

APP_NAME = "MarketLens Pro v5 — SPX by Max Pointe Consulting"

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
        "panel": "rgba(255,255,255,0.86)",
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
# TIMEZONES / HELPERS
# ===============================
CT = pytz.timezone("America/Chicago")
ET = pytz.timezone("America/New_York")
UTC = pytz.UTC

def to_ct(ts):
    if ts.tzinfo is None:
        ts = UTC.localize(ts)
    return ts.astimezone(CT)

def dt_range_ct(start_ct, end_ct, freq="30min"):
    return pd.date_range(start=start_ct, end=end_ct, freq=freq, tz=CT)

def rth_times_list():
    # fixed RTH times for table alignment (HH:MM strings)
    start_dt = CT.localize(datetime.combine(datetime.now(CT).date(), dtime(8,30)))
    end_dt   = CT.localize(datetime.combine(datetime.now(CT).date(), dtime(14,30)))
    rng = dt_range_ct(start_dt, end_dt, "30min")
    return [t.strftime("%H:%M") for t in rng]

# ===============================
# SLOPES (per 30-min block)
# ===============================
SPX_SLOPE_SKY = +0.268   # Skyline
SPX_SLOPE_BASE = -0.235  # Baseline

# ===============================
# Robust yfinance normalizer
# ===============================
def normalize_ohlcv(df: pd.DataFrame, symbol: str | None = None) -> pd.DataFrame:
    """
    Make a yfinance DataFrame predictable:
    - If MultiIndex columns, slice by symbol when possible or flatten.
    - Drop duplicate columns.
    - Ensure standard title-cased column names.
    """
    if df is None or df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        if symbol is not None:
            try:
                df = df.xs(symbol, axis=1, level=-1)
            except Exception:
                df.columns = df.columns.get_level_values(0)
        else:
            df.columns = df.columns.get_level_values(0)

    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    # Standardize title-case names
    rename_map = {c: str(c).strip().title() for c in df.columns}
    df = df.rename(columns=rename_map)
    return df

# ===============================
# DATA FETCHING (yfinance) + CACHING
# ===============================
@st.cache_data(ttl=60)
def fetch_live(symbol: str, start_utc: datetime, end_utc: datetime, interval="30m"):
    if not YF_AVAILABLE:
        return pd.DataFrame()
    df = yf.download(symbol, start=start_utc, end=end_utc, interval=interval, auto_adjust=False, progress=False)
    if not df.empty:
        if df.index.tz is None:
            df.index = df.index.tz_localize(UTC)
        df = normalize_ohlcv(df, symbol)
    return df

@st.cache_data(ttl=300)
def fetch_hist(symbol: str, period="5d", interval="30m"):
    if not YF_AVAILABLE:
        return pd.DataFrame()
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
    if not df.empty:
        if df.index.tz is None:
            df.index = df.index.tz_localize(UTC)
        df = normalize_ohlcv(df, symbol)
    return df

def price_range_ok(df: pd.DataFrame) -> bool:
    if df.empty: return False
    if "Close" not in df.columns: return False
    lo, hi = float(df["Close"].min()), float(df["Close"].max())
    return (lo > 0) and (hi/lo < 10.0)

# ===============================
# ANCHOR DETECTION (ES → SPX)
# ===============================
def detect_spx_anchors_from_es(prev_day_ct: date):
    """
    ES Asian session window: 17:00–19:30 CT (previous day)
    Skyline: highest CLOSE (tie-break by highest VOLUME)
    Baseline: lowest CLOSE (tie-break by highest VOLUME)
    Dynamic ES→SPX offset suggestion: (prev RTH close SPX - prev RTH close ES)
    """
    start_ct = CT.localize(datetime.combine(prev_day_ct, dtime(17,0)))
    end_ct   = CT.localize(datetime.combine(prev_day_ct, dtime(19,30)))
    start_utc, end_utc = start_ct.astimezone(UTC), end_ct.astimezone(UTC)

    es = fetch_live("ES=F", start_utc, end_utc)  # 30m bars
    if es.empty or not price_range_ok(es):
        return None, None, None, es

    es_ct = es.copy()
    es_ct.index = es_ct.index.tz_convert(CT)
    es_ct = es_ct.between_time("17:00","20:00")

    required = {"Close"}
    if not required.issubset(set(es_ct.columns)) or es_ct.empty:
        return None, None, None, es_ct

    have_volume = "Volume" in es_ct.columns
    if have_volume:
        skyline_idx = es_ct.sort_values(by=["Close","Volume"], ascending=[False, False]).index[0]
        baseline_idx = es_ct.sort_values(by=["Close","Volume"], ascending=[True,  False]).index[0]
    else:
        skyline_idx = es_ct["Close"].idxmax()
        baseline_idx = es_ct["Close"].idxmin()

    sky_es_price = float(es_ct.loc[skyline_idx, "Close"])
    base_es_price = float(es_ct.loc[baseline_idx, "Close"])
    sky_time_ct = skyline_idx
    base_time_ct = baseline_idx

    # ES→SPX offset suggestion using previous RTH (14:30–15:30 CT) closes
    rth_prev_start = CT.localize(datetime.combine(prev_day_ct, dtime(14,30)))
    rth_prev_end   = CT.localize(datetime.combine(prev_day_ct, dtime(15,30)))
    spx_prev = fetch_live("^GSPC", rth_prev_start.astimezone(UTC), rth_prev_end.astimezone(UTC))
    es_prev  = fetch_live("ES=F",  rth_prev_start.astimezone(UTC), rth_prev_end.astimezone(UTC))
    offset = None
    if not spx_prev.empty and not es_prev.empty and "Close" in spx_prev.columns and "Close" in es_prev.columns:
        spx_last = float(spx_prev["Close"].iloc[-1])
        es_last  = float(es_prev["Close"].iloc[-1])
        offset = spx_last - es_last

    return (sky_es_price, sky_time_ct), (base_es_price, base_time_ct), offset, es_ct

# ===============================
# PROJECTION + SIGNALS
# ===============================
def project_line(anchor_price: float, anchor_time_ct: datetime, slope_per_block: float, rth_times: list[str], proj_day_ct: date):
    """
    anchor_time_ct: timezone-aware CT datetime (can be previous day 17:00–19:30)
    rth_times: list of 'HH:MM' strings for RTH (08:30..14:30)
    proj_day_ct: date of the RTH session we’re projecting into (usually next day)
    """
    anchor_time_ct = anchor_time_ct.astimezone(CT)
    minute = 0 if anchor_time_ct.minute < 30 else 30
    anchor_aligned = anchor_time_ct.replace(minute=minute, second=0, microsecond=0)

    def blocks_to(tstr):
        hh, mm = map(int, tstr.split(":"))
        slot_dt = CT.localize(datetime.combine(proj_day_ct, dtime(hh, mm)))
        delta = int(round(((slot_dt - anchor_aligned).total_seconds()) / 1800.0))
        return delta

    prices = []
    for t in rth_times:
        b = blocks_to(t)
        prices.append(round(anchor_price + slope_per_block * b, 4))
    return pd.DataFrame({"Time": rth_times, "Price": prices})

def detect_signals_from_rules(rth_ohlc_ct: pd.DataFrame, line_df: pd.DataFrame, mode: str, tol: float = 0.0):
    """
    Rules (30-min candles):
    BUY: bearish candle touches line from above & closes ABOVE the line (entry on close)
         (o > c, low - tol <= line <= high + tol, o > line, c > line)
    SELL: bullish candle touches line from below & closes BELOW the line (entry on close)
         (c > o, low - tol <= line <= high + tol, o < line, c < line)
    """
    if rth_ohlc_ct.empty or "Close" not in rth_ohlc_ct.columns:
        return pd.DataFrame([])
    idx_times = [ts.tz_convert(CT).strftime("%H:%M") for ts in rth_ohlc_ct.index]
    line_map = dict(zip(line_df["Time"], line_df["Price"]))
    rows = []
    for i, ts in enumerate(rth_ohlc_ct.index):
        tstr = idx_times[i]
        if tstr not in line_map:
            continue
        line = float(line_map[tstr])
        row = rth_ohlc_ct.iloc[i]
        o, h, l, c = float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"])
        touched = (l - tol <= line <= h + tol)
        is_bull = c > o
        is_bear = c < o
        if mode == "BUY" and touched and is_bear and (o > line) and (c > line):
            rows.append({"Time": tstr, "Line": round(line, 4), "Entry": round(c, 4), "Type": "BUY"})
        if mode == "SELL" and touched and is_bull and (o < line) and (c < line):
            rows.append({"Time": tstr, "Line": round(line, 4), "Entry": round(c, 4), "Type": "SELL"})
    return pd.DataFrame(rows)

def compute_exits(rth_ohlc_ct: pd.DataFrame, line_df: pd.DataFrame, signals_df: pd.DataFrame):
    """
    Exit heuristic aligned with anchor-bounce concept:
    - For BUY: exit at the first future candle that CLOSES back BELOW the line.
    - For SELL: exit at the first future candle that CLOSES back ABOVE the line.
    - If no exit found, exit at 14:30 close.
    Returns signals with ExitTime, Exit, PnL (points).
    """
    if signals_df.empty:
        return signals_df

    idx_times = [ts.tz_convert(CT).strftime("%H:%M") for ts in rth_ohlc_ct.index]
    time_to_idx = {t: i for i, t in enumerate(idx_times)}
    line_map = dict(zip(line_df["Time"], line_df["Price"]))

    out_rows = []
    for _, sig in signals_df.iterrows():
        tstr = sig["Time"]; entry = float(sig["Entry"]); typ = sig["Type"]
        start_i = time_to_idx.get(tstr, None)
        if start_i is None:
            continue
        exit_price = None
        exit_time = idx_times[-1]
        # iterate forward
        for j in range(start_i + 1, len(idx_times)):
            tj = idx_times[j]
            if tj not in line_map:
                continue
            line = float(line_map[tj])
            close = float(rth_ohlc_ct.iloc[j]["Close"])
            if typ == "BUY" and close < line:
                exit_price = close; exit_time = tj; break
            if typ == "SELL" and close > line:
                exit_price = close; exit_time = tj; break
        if exit_price is None:
            # use final close
            exit_price = float(rth_ohlc_ct.iloc[-1]["Close"])
        pnl = round(exit_price - entry, 4) if typ == "BUY" else round(entry - exit_price, 4)
        out = dict(sig)
        out.update({"ExitTime": exit_time, "Exit": round(exit_price, 4), "PnL": pnl})
        out_rows.append(out)
    return pd.DataFrame(out_rows)

# ===============================
# CONTRACT PROJECTION (under SPX)
# ===============================
def contract_projection_under_spx(proj_day_ct: date):
    st.markdown("#### Contract Projection (SPX) — two-point slope")
    st.caption("Times allowed: **8:00 PM (previous day)** → **10:00 AM (current day)**. Output window: **08:30–14:30 CT**.")

    col1, col2 = st.columns(2)
    with col1:
        t1 = st.time_input("Point 1 Time (CT)", value=dtime(20,0), step=1800, key="cp_t1")
        p1 = st.number_input("Point 1 Price", value=10.0, step=0.1, key="cp_p1")
    with col2:
        t2 = st.time_input("Point 2 Time (CT)", value=dtime(3,30), step=1800, key="cp_t2")
        p2 = st.number_input("Point 2 Price", value=12.0, step=0.1, key="cp_p2")

    today_ct = proj_day_ct
    prev_ct = today_ct - timedelta(days=1)

    def to_dt(t):
        return CT.localize(datetime.combine(prev_ct if t.hour >= 20 else today_ct, t))
    dt1 = to_dt(t1); dt2 = to_dt(t2)

    def blocks_between_dt(a, b):
        return int(round(((b - a).total_seconds())/1800.0))

    blocks = abs(blocks_between_dt(dt1, dt2))
    slope = 0.0 if blocks == 0 else (p2 - p1) / blocks
    st.info(f"Slope per 30-min block: **{slope:.4f}**  •  Blocks between points: **{blocks}**")

    rth = [t.strftime("%H:%M") for t in dt_range_ct(CT.localize(datetime.combine(today_ct, dtime(8,30))),
                                                    CT.localize(datetime.combine(today_ct, dtime(14,30))),
                                                    "30min")]
    rows = []
    for t in rth:
        hh, mm = map(int, t.split(":"))
        slot_dt = CT.localize(datetime.combine(today_ct, dtime(hh, mm)))
        db = abs(blocks_between_dt(dt1, slot_dt))
        price = round(p1 + slope * db, 4)
        rows.append({"Time": t, "Price": price})
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download Contract Projection CSV", df.to_csv(index=False).encode(),
                       "spx_contract_projection.csv", "text/csv", use_container_width=True)
    return df

# ===============================
# QUALITY & FALLBACKS
# ===============================
def data_quality_summary(df: pd.DataFrame, window_label: str) -> str:
    if df.empty:
        return f"{window_label}: no data"
    cols = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
    n = len(df)
    zvol = int((df["Volume"] == 0).sum()) if "Volume" in df.columns else 0
    return f"{window_label}: {n} bars • columns={','.join(cols)} • zero-vol bars={zvol}"

def upload_csv_ui(help_text: str) -> pd.DataFrame:
    f = st.file_uploader(help_text, type=["csv"])
    if not f:
        return pd.DataFrame()
    try:
        df = pd.read_csv(f)
        # try to parse a datetime index if present
        for col in ["Datetime","Date","Time","Timestamp","datetime","date"]:
            if col in df.columns:
                try:
                    df.index = pd.to_datetime(df[col])
                    df.drop(columns=[col], inplace=True)
                    break
                except Exception:
                    pass
        # standardize columns
        rename = {c: c.strip().title() for c in df.columns}
        df.rename(columns=rename, inplace=True)
        return df
    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
        return pd.DataFrame()

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

def metric_grid(pairs):
    st.markdown("<div class='ml-metrics'>", unsafe_allow_html=True)
    for k,v in pairs:
        st.markdown(f"<div class='ml-metric'><div class='k'>{k}</div><div class='v'>{v}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ===============================
# MAIN (SPX ONLY)
# ===============================
def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        mode = st.radio("Theme", ["Dark", "Light"], index=0)
        inject_theme(mode)

        st.markdown("### 🧮 SPX Slopes (per 30m)")
        spx_sky = st.number_input("Skyline (+)", value=SPX_SLOPE_SKY, step=0.001, format="%.3f")
        spx_base = st.number_input("Baseline (−)", value=SPX_SLOPE_BASE, step=0.001, format="%.3f")

        st.markdown("### 🎯 Signal Sensitivity")
        tol = st.number_input("Touch tolerance (points)", value=0.0, step=0.25,
                              help="Allows a small wiggle room for 'touch'. 0 = strict line touch.")

        st.markdown("### ⏱️ Windows")
        st.caption("Anchors: previous day 17:00–19:30 CT (from ES). Projections & signals: chosen RTH day 08:30–14:30 CT.")

    st.markdown(f"## SPX — Asian Session Anchors → RTH Projections (Tables Only)")

    # Controls
    c1, c2 = st.columns(2)
    with c1:
        yesterday_ct = (datetime.now(CT) - timedelta(days=1)).date()
        prev_day = st.date_input("Previous trading day (CT) for Asian session", value=yesterday_ct)
    with c2:
        proj_day = st.date_input("Projection day (CT) for SPX RTH", value=datetime.now(CT).date())

    # ---------- Anchors card ----------
    def anchors_body():
        if YF_AVAILABLE:
            sky, base, offset, es_ct = detect_spx_anchors_from_es(prev_day)
        else:
            st.warning("`yfinance` not installed. Upload ES=F 30m CSV for 17:00–19:30 CT window.")
            es_ct = upload_csv_ui("Upload ES=F 30m CSV for previous day Asian window (17:00–19:30 CT)")
            if not es_ct.empty:
                es_ct.index = es_ct.index.tz_localize(UTC) if es_ct.index.tz is None else es_ct.index
                es_ct.index = es_ct.index.tz_convert(CT)
                es_ct = es_ct.between_time("17:00","20:00")
            if es_ct.empty or "Close" not in es_ct.columns:
                st.stop()
            have_volume = "Volume" in es_ct.columns
            if have_volume:
                skyline_idx = es_ct.sort_values(by=["Close","Volume"], ascending=[False, False]).index[0]
                baseline_idx = es_ct.sort_values(by=["Close","Volume"], ascending=[True,  False]).index[0]
            else:
                skyline_idx = es_ct["Close"].idxmax()
                baseline_idx = es_ct["Close"].idxmin()
            sky = (float(es_ct.loc[skyline_idx, "Close"]), skyline_idx)
            base = (float(es_ct.loc[baseline_idx, "Close"]), baseline_idx)
            offset = 0.0

        if sky is None or base is None:
            st.error("Could not detect anchors from ES=F in 17:00–19:30 CT window. Try another date or upload CSV.")
            st.stop()

        sky_es, sky_time = sky
        base_es, base_time = base

        st.markdown("**Detected ES Anchors (used to derive SPX):**")
        metric_grid([
            ("ES Skyline (Close)", f"{sky_es:.2f} @ {to_ct(sky_time).strftime('%Y-%m-%d %H:%M CT')}"),
            ("ES Baseline (Close)", f"{base_es:.2f} @ {to_ct(base_time).strftime('%Y-%m-%d %H:%M CT')}"),
        ])

        suggested_offset = float(offset) if isinstance(offset,(int,float)) else 0.0
        es_spx_offset = st.number_input("ES → SPX dynamic offset", value=suggested_offset, step=0.5,
                                        help="Suggested: SPX_prev_close - ES_prev_close. Override as needed.")

        # Convert to SPX anchors (this is what we project from)
        sky_spx = sky_es + es_spx_offset
        base_spx = base_es + es_spx_offset

        st.markdown("**SPX Anchors (used for projection):**")
        metric_grid([
            ("SPX Skyline", f"{sky_spx:.2f} (from ES Skyline)"),
            ("SPX Baseline", f"{base_spx:.2f} (from ES Baseline)"),
        ])

        # Project lines for SPX RTH
        rth_times = [t.strftime("%H:%M") for t in dt_range_ct(CT.localize(datetime.combine(proj_day, dtime(8,30))),
                                                             CT.localize(datetime.combine(proj_day, dtime(14,30))),
                                                             "30min")]
        df_sky = project_line(sky_spx, to_ct(sky_time), spx_sky, rth_times, proj_day)
        df_base = project_line(base_spx, to_ct(base_time), spx_base, rth_times, proj_day)

        cta1, cta2 = st.columns(2)
        with cta1:
            st.write("**SPX Skyline Projection (08:30–14:30 CT)**")
            st.dataframe(df_sky, use_container_width=True, hide_index=True)
            st.download_button("Download Skyline CSV", df_sky.to_csv(index=False).encode(),
                               "spx_skyline_projection.csv", "text/csv", use_container_width=True)
        with cta2:
            st.write("**SPX Baseline Projection (08:30–14:30 CT)**")
            st.dataframe(df_base, use_container_width=True, hide_index=True)
            st.download_button("Download Baseline CSV", df_base.to_csv(index=False).encode(),
                               "spx_baseline_projection.csv", "text/csv", use_container_width=True)

        # ---------- Entries & Exits ----------
        st.markdown("---")
        st.markdown("### Entries & Exits (30-min rules) — SPX RTH")

        # Get SPX RTH OHLC for projection day (or upload)
        if YF_AVAILABLE:
            rth_start = CT.localize(datetime.combine(proj_day, dtime(8,30)))
            rth_end   = CT.localize(datetime.combine(proj_day, dtime(14,30)))
            spx_rth = fetch_live("^GSPC", rth_start.astimezone(UTC), rth_end.astimezone(UTC))
        else:
            spx_rth = pd.DataFrame()

        if spx_rth.empty:
            st.warning("Live SPX data not available. Upload SPX 30m OHLC CSV for the projection day (08:30–14:30 CT).")
            spx_rth = upload_csv_ui("Upload SPX 30m OHLC CSV (08:30–14:30 CT)")
            if not spx_rth.empty:
                # assume the uploaded times are the RTH window
                spx_rth.index = spx_rth.index.tz_localize(UTC) if spx_rth.index.tz is None else spx_rth.index
                spx_rth.index = spx_rth.index.tz_convert(CT)
        else:
            spx_rth = spx_rth.copy()
            spx_rth.index = spx_rth.index.tz_convert(CT)
            spx_rth = spx_rth.between_time("08:30","14:30")

        # quality badge
        st.caption(data_quality_summary(spx_rth, "SPX RTH"))

        if not spx_rth.empty and "Close" in spx_rth.columns:
            # Scan Skyline and Baseline separately, then merge
            buy_sky = detect_signals_from_rules(spx_rth, df_sky, "BUY", tol)
            sell_sky = detect_signals_from_rules(spx_rth, df_sky, "SELL", tol)
            buy_sky["LineType"] = "Skyline"
            sell_sky["LineType"] = "Skyline"

            buy_base = detect_signals_from_rules(spx_rth, df_base, "BUY", tol)
            sell_base = detect_signals_from_rules(spx_rth, df_base, "SELL", tol)
            buy_base["LineType"] = "Baseline"
            sell_base["LineType"] = "Baseline"

            entries = pd.concat([buy_sky, sell_sky, buy_base, sell_base], ignore_index=True)
            entries = entries.sort_values(by="Time", ascending=True)

            st.write("**Entry Signals**")
            st.dataframe(entries, use_container_width=True, hide_index=True)
            st.download_button("Download Entry Signals CSV", entries.to_csv(index=False).encode(),
                               "spx_entry_signals.csv", "text/csv", use_container_width=True)

            # Compute exits & PnL (based on line cross-backs)
            # We must compute exits against the same line each signal came from:
            # split by LineType to apply correct line
            exit_blocks = []
            for line_type, group in entries.groupby("LineType"):
                line_df = df_sky if line_type == "Skyline" else df_base
                exit_blocks.append(compute_exits(spx_rth, line_df, group))
            exits = pd.concat(exit_blocks, ignore_index=True) if exit_blocks else pd.DataFrame()

            # Sort by entry time
            if not exits.empty:
                exits = exits.sort_values(by="Time", ascending=True)
                st.write("**Suggested Exits & PnL (points)**")
                st.dataframe(exits, use_container_width=True, hide_index=True)
                st.download_button("Download Exits & PnL CSV", exits.to_csv(index=False).encode(),
                                   "spx_exits_pnl.csv", "text/csv", use_container_width=True)
        else:
            st.info("Provide SPX RTH data to scan for entries/exits.")

        st.markdown("---")
        # ---------- Contract Projection (under SPX) ----------
        contract_projection_under_spx(proj_day)

    card(
        "SPX: ES Asian Anchors → Projection → Entries/Exits",
        sub="All calculations in 30-minute blocks. ES used for anchors; SPX displayed throughout.",
        body_fn=anchors_body,
        badge="SPX"
    )

    st.markdown("<div style='opacity:.7; font-size:.85rem; margin-top:8px'>© 2025 MarketLens Pro • Tables only • Built with Streamlit</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
