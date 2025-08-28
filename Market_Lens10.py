# app.py
# MarketLens Pro v5 by Max Pointe Consulting
# Streamlit single-file app (no Plotly). Run:
#   pip install -r requirements.txt
#   streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, time as dtime, date
import pytz


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
    idx = pd.date_range(start=start_ct, end=end_ct, freq=freq, tz=CT)
    return idx

def rth_slots_ct(start="08:30", end="14:30"):
    start_dt = datetime.combine(datetime.now(CT).date(), datetime.strptime(start, "%H:%M").time()).replace(tzinfo=CT)
    end_dt   = datetime.combine(datetime.now(CT).date(), datetime.strptime(end, "%H:%M").time()).replace(tzinfo=CT)
    rng = dt_range_ct(start_dt, end_dt, "30min")
    return [t.astimezone(CT).strftime("%H:%M") for t in rng]

# ===============================
# SLOPES (per 30-min block)
# ===============================
SLOPES = {
    "SPX": {"Skyline": +0.268, "Baseline": -0.235},
    "AAPL": 0.0155, "MSFT": 0.0541, "NVDA": 0.0086, "AMZN": 0.0139, "GOOGL": 0.0122, "TSLA": 0.0285, "META": 0.0674
}

# ===============================
# DATA FETCHING (yfinance) + CACHING
# ===============================

@st.cache_data(ttl=60)
def fetch_live(symbol: str, start_utc: datetime, end_utc: datetime, interval="30m"):
    df = yf.download(symbol, start=start_utc, end=end_utc, interval=interval, auto_adjust=False, progress=False)
    if not df.empty:
        if df.index.tz is None:
            df.index = df.index.tz_localize(UTC)
    return df

@st.cache_data(ttl=300)
def fetch_hist(symbol: str, period="5d", interval="30m"):
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
    if not df.empty:
        if df.index.tz is None:
            df.index = df.index.tz_localize(UTC)
    return df

def price_range_ok(df: pd.DataFrame) -> bool:
    if df.empty: return False
    lo, hi = float(df["Close"].min()), float(df["Close"].max())
    return (lo > 0) and (hi/lo < 5.0)  # crude sanity

# ===============================
# ANCHOR DETECTION
# ===============================

def detect_spx_anchors_from_es(previous_day: date):
    # Window: 5:00 PM - 7:30 PM CT on previous trading day
    start_ct = CT.localize(datetime.combine(previous_day, dtime(17,0)))
    end_ct   = CT.localize(datetime.combine(previous_day, dtime(19,30)))
    start_utc, end_utc = start_ct.astimezone(UTC), end_ct.astimezone(UTC)

    es = fetch_live("ES=F", start_utc, end_utc)  # 30m bars
    if es.empty or not price_range_ok(es):
        return None, None, None

    es_ct = es.copy()
    es_ct.index = es_ct.index.tz_convert(CT)
    es_ct = es_ct.between_time("17:00","20:00")
    if es_ct.empty:
        return None, None, None

    # Skyline: highest CLOSE, tie-breaker highest VOLUME
    skyline_idx = es_ct.sort_values(["Close","Volume"], ascending=[False, False]).index[0]
    skyline_price_es = float(es_ct.loc[skyline_idx, "Close"])
    skyline_time_ct = skyline_idx

    # Baseline: lowest CLOSE, tie-breaker highest VOLUME
    baseline_idx = es_ct.sort_values(["Close","Volume"], ascending=[True, False]).index[0]
    baseline_price_es = float(es_ct.loc[baseline_idx, "Close"])
    baseline_time_ct = baseline_idx

    # Dynamic ES→SPX offset suggestion: (prev RTH close SPX - prev RTH close ES)
    rth_prev_start = CT.localize(datetime.combine(previous_day, dtime(14,30)))
    rth_prev_end   = CT.localize(datetime.combine(previous_day, dtime(15,30)))
    spx_prev = fetch_live("^GSPC", rth_prev_start.astimezone(UTC), rth_prev_end.astimezone(UTC))
    es_prev  = fetch_live("ES=F",  rth_prev_start.astimezone(UTC), rth_prev_end.astimezone(UTC))
    offset = None
    if not spx_prev.empty and not es_prev.empty:
        spx_last = float(spx_prev["Close"].iloc[-1])
        es_last  = float(es_prev["Close"].iloc[-1])
        offset = spx_last - es_last

    return (skyline_price_es, skyline_time_ct), (baseline_price_es, baseline_time_ct), offset

def detect_stock_anchors_two_day(symbol: str, mon_date: date, tue_date: date):
    # Fetch two full sessions in ET: 09:30-16:00
    start_et = ET.localize(datetime.combine(mon_date, dtime(9,30)))
    end_et   = ET.localize(datetime.combine(tue_date, dtime(16,0)))
    df = fetch_live(symbol, start_et.astimezone(UTC), end_et.astimezone(UTC))
    if df.empty or not price_range_ok(df):
        return None, None, df
    df_et = df.copy()
    df_et.index = df_et.index.tz_convert(ET)
    df_et = df_et.between_time("09:30","16:00")
    if df_et.empty:
        return None, None, df_et
    # CLOSE-only anchors, volume tie-breakers
    skyline_idx = df_et.sort_values(["Close","Volume"], ascending=[False, False]).index[0]
    baseline_idx = df_et.sort_values(["Close","Volume"], ascending=[True, False]).index[0]
    skyline = (float(df_et.loc[skyline_idx, "Close"]), skyline_idx)
    baseline = (float(df_et.loc[baseline_idx, "Close"]), baseline_idx)
    return skyline, baseline, df_et

# ===============================
# PROJECTION + SIGNALS
# ===============================

def project_line(anchor_price: float, anchor_time_ct: datetime, slope_per_block: float, rth_times_ct):
    # Align anchor time to nearest 30m grid (down)
    anchor_time_ct = anchor_time_ct.astimezone(CT)
    minute = 0 if anchor_time_ct.minute < 30 else 30
    anchor_aligned = anchor_time_ct.replace(minute=minute, second=0, microsecond=0)

    def blocks_to(tstr):
        hh, mm = map(int, tstr.split(":"))
        # Use the anchor's date to create a comparable slot timestamp
        t_ct = anchor_aligned.replace(hour=hh, minute=mm, second=0, microsecond=0)
        delta = int(round(((t_ct - anchor_aligned).total_seconds()) / 1800.0))
        return delta

    prices = []
    for t in rth_times_ct:
        b = blocks_to(t)
        prices.append(round(anchor_price + slope_per_block * b, 4))
    return pd.DataFrame({"Time": rth_times_ct, "Price": prices})

def detect_signals(rth_ohlc_ct: pd.DataFrame, line_df: pd.DataFrame, mode="BUY"):
    if rth_ohlc_ct.empty: 
        return pd.DataFrame([])
    idx_times = [ts.astimezone(CT).strftime("%H:%M") for ts in rth_ohlc_ct.index]
    line_map = dict(zip(line_df["Time"], line_df["Price"]))
    rows = []
    for i, ts in enumerate(rth_ohlc_ct.index):
        tstr = idx_times[i]
        if tstr not in line_map: 
            continue
        line = line_map[tstr]
        o,h,l,c = (float(rth_ohlc_ct.iloc[i][k]) for k in ["Open","High","Low","Close"])
        is_bull = c > o
        is_bear = c < o
        touched = (l <= line <= h)
        # BUY: bearish candle touching from above + close ABOVE line (entry on close)
        if mode=="BUY" and touched and is_bear and (c > line) and (o > line):
            rows.append({"Time": tstr, "Line": round(line,4), "Close": round(c,4), "Type": "BUY", "Note": "Bearish, touched from above, closed above"})
        # SELL: bullish candle touching from below + close BELOW line (entry on close)
        if mode=="SELL" and touched and is_bull and (c < line) and (o < line):
            rows.append({"Time": tstr, "Line": round(line,4), "Close": round(c,4), "Type": "SELL", "Note": "Bullish, touched from below, closed below"})
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
            "Time": rth_close_ct.index[i].astimezone(CT).strftime("%Y-%m-%d %H:%M"),
            "EMA8": round(float(e8.iloc[i]),4),
            "EMA21": round(float(e21.iloc[i]),4),
            "Direction": "Bullish ↑" if diff.iloc[i] > 0 else "Bearish ↓"
        })
    df = pd.DataFrame(rows)
    return df, e8, e21

# ===============================
# CONTRACT PROJECTION TOOL
# ===============================
def contract_projection_tool():
    st.markdown("### Contract Projection Tool")
    st.caption("Enter two contract points (time + price). Times can range from **8:00 PM (prev day)** to **10:00 AM (current day)**. Forecasts output for **08:30–14:30 CT**.")
    col1, col2 = st.columns(2)
    with col1:
        t1 = st.time_input("Point 1 Time (CT)", value=dtime(20,0), step=1800)
        p1 = st.number_input("Point 1 Price", value=10.0, step=0.1)
    with col2:
        t2 = st.time_input("Point 2 Time (CT)", value=dtime(3,30), step=1800)
        p2 = st.number_input("Point 2 Price", value=12.0, step=0.1)

    rth_times = rth_slots_ct("08:30","14:30")
    today_ct = datetime.now(CT).date()
    prev_ct = today_ct - timedelta(days=1)

    def to_dt(t):
        return CT.localize(datetime.combine(prev_ct if t.hour>=20 else today_ct, t))

    dt1 = to_dt(t1)
    dt2 = to_dt(t2)

    def blocks_between_dt(a, b):
        return int(round(((b - a).total_seconds())/1800.0))

    blocks = abs(blocks_between_dt(dt1, dt2))
    slope = 0.0 if blocks==0 else (p2 - p1)/blocks

    st.info(f"Slope per 30-min block: **{slope:.4f}** (blocks between points: {blocks})")

    proj_rows = []
    for t in rth_times:
        h,m = map(int, t.split(":"))
        slot_dt = CT.localize(datetime.combine(today_ct, dtime(h,m)))
        db = abs(blocks_between_dt(dt1, slot_dt))
        price = round(p1 + slope * db, 4)
        proj_rows.append({"Time": t, "Price": price})
    df = pd.DataFrame(proj_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Download Contract Projection CSV", df.to_csv(index=False).encode(), "contract_projection.csv", "text/csv", use_container_width=True)
    return df

# ===============================
# UI HELPERS
# ===============================
def card(title, sub=None, body_fn=None, badge=None):
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    head = f"<div class='ml-pill'>{badge}</div>" if badge else ""
    st.markdown(f"{head}<h4 style='margin:6px 0 2px 0'>{title}</h4>", unsafe_allow_html=True)
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
# MAIN APP
# ===============================
def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        mode = st.radio("Theme", ["Dark", "Light"], index=0)
        inject_theme(mode)

        st.markdown("### 📈 Tickers")
        st.caption("Use ^GSPC for SPX, ES=F for S&P futures, and standard Yahoo tickers for stocks.")
        default_ticker = "^GSPC"
        spx_ticker = st.text_input("SPX Index Symbol", value=default_ticker)
        st.markdown("---")
        st.markdown("### 🧮 Slopes (per 30-min block)")
        spx_sky = st.number_input("SPX Skyline (+)", value=SLOPES["SPX"]["Skyline"], step=0.001, format="%.3f")
        spx_base = st.number_input("SPX Baseline (−)", value=SLOPES["SPX"]["Baseline"], step=0.001, format="%.3f")
        st.caption("Stocks use ± of the same magnitude (e.g., AAPL 0.0155 → Skyline +0.0155 / Baseline −0.0155).")

        st.markdown("### ⏱️ RTH Window")
        st.caption("Projection window is fixed at 8:30 AM – 2:30 PM CT (30-min blocks).")

    st.markdown(f"## {APP_NAME}")
    st.caption("Dark glassmorphism • Cosmic gradient • Professional, verifiable math-first pipeline")

    tab1, tab2, tab3, tab4 = st.tabs(["SPX (Asian Session Anchors)", "Stocks (Mon/Tue Anchors)", "Signals & EMA", "Contract Tool"])

    # ======== TAB 1: SPX ========
    with tab1:
        st.markdown("### SPX Asian Session Analysis (via ES=F)")
        yesterday_ct = (datetime.now(CT) - timedelta(days=1)).date()
        prev_day = st.date_input("Previous trading day (CT)", value=yesterday_ct)
        sky, base, offset = detect_spx_anchors_from_es(prev_day)

        def body():
            if sky is None or base is None:
                st.error("Could not detect anchors from ES=F in 17:00–19:30 CT window. Try another date.")
                return
            sky_price_es, sky_time = sky
            base_price_es, base_time = base
            st.write(f"**ES Skyline**: {sky_price_es} @ {sky_time.strftime('%Y-%m-%d %H:%M CT')}")
            st.write(f"**ES Baseline**: {base_price_es} @ {base_time.strftime('%Y-%m-%d %H:%M CT')}")

            suggested_offset = float(offset) if isinstance(offset,(int,float)) else 0.0
            es_spx_offset = st.number_input("ES → SPX dynamic offset", value=suggested_offset, step=0.5, help="Suggested: SPX_prev_close - ES_prev_close. You can override.")
            sky_spx = sky_price_es + es_spx_offset
            base_spx = base_price_es + es_spx_offset

            st.markdown("---")
            st.markdown("#### Projected Lines (SPX RTH 08:30–14:30 CT)")
            rth = rth_slots_ct("08:30","14:30")
            df_sky = project_line(sky_spx, sky_time, spx_sky, rth)
            df_base = project_line(base_spx, base_time, spx_base, rth)
            c1, c2 = st.columns(2)
            with c1:
                st.write("Skyline (+ slope)")
                st.dataframe(df_sky, use_container_width=True, hide_index=True)
            with c2:
                st.write("Baseline (− slope)")
                st.dataframe(df_base, use_container_width=True, hide_index=True)
            st.download_button("Download SPX Skyline CSV", df_sky.to_csv(index=False).encode(), "spx_skyline.csv", "text/csv")
            st.download_button("Download SPX Baseline CSV", df_base.to_csv(index=False).encode(), "spx_baseline.csv", "text/csv")

        card("Anchors → Projection", sub="ES Asian session (17:00–19:30 CT) CLOSE-only anchors, converted to SPX, projected through RTH.", body_fn=body, badge="SPX")

    # ======== TAB 2: STOCKS ========
    with tab2:
        st.markdown("### Individual Stock Anchor System (Mon/Tue)")
        sym = st.text_input("Stock symbol", value="AAPL")
        today = datetime.now(ET).date()
        weekday = today.weekday()  # Mon=0
        last_mon = today - timedelta(days=(weekday - 0) % 7 or 7)
        last_tue = last_mon + timedelta(days=1)
        c1, c2 = st.columns(2)
        with c1:
            mon_date = st.date_input("Monday (ET)", value=last_mon, key="mon")
        with c2:
            tue_date = st.date_input("Tuesday (ET)", value=last_tue, key="tue")

        skyline, baseline, df_et = detect_stock_anchors_two_day(sym, mon_date, tue_date)

        def body():
            if skyline is None or baseline is None:
                st.error("Could not detect anchors from Mon/Tue 09:30–16:00 ET data. Try different dates or symbol.")
                return
            sky_p, sky_t = skyline
            base_p, base_t = baseline
            st.write(f"**Skyline (max CLOSE)**: {sky_p} @ {sky_t.strftime('%Y-%m-%d %H:%M ET')}")
            st.write(f"**Baseline (min CLOSE)**: {base_p} @ {base_t.strftime('%Y-%m-%d %H:%M ET')}")

            slope_mag = SLOPES.get(sym.upper(), SLOPES.get(sym.capitalize(), 0.015))  # fallback
            rth = rth_slots_ct("08:30","14:30")
            df_sky = project_line(sky_p, sky_t.astimezone(CT), +slope_mag, rth)
            df_base = project_line(base_p, base_t.astimezone(CT), -slope_mag, rth)

            c1, c2 = st.columns(2)
            with c1:
                st.write("Skyline (+ slope)")
                st.dataframe(df_sky, use_container_width=True, hide_index=True)
            with c2:
                st.write("Baseline (− slope)")
                st.dataframe(df_base, use_container_width=True, hide_index=True)
            st.download_button(f"Download {sym} Skyline CSV", df_sky.to_csv(index=False).encode(), f"{sym}_skyline.csv", "text/csv")
            st.download_button(f"Download {sym} Baseline CSV", df_base.to_csv(index=False).encode(), f"{sym}_baseline.csv", "text/csv")

        card("Anchors → Projection", sub="Mon/Tue CLOSE-only anchors across both days (absolute extremes). Project to Wed/Thu RTH using stock slopes.", body_fn=body, badge=sym.upper())

    # ======== TAB 3: SIGNALS & EMA ========
    with tab3:
        st.markdown("### Signal Detection (30m candles) + EMA(8/21)")
        sym2 = st.text_input("Symbol for signals/EMA", value="^GSPC")
        proj_day = st.date_input("Projection day (CT)", value=datetime.now(CT).date())
        rth_start = CT.localize(datetime.combine(proj_day, dtime(8,30)))
        rth_end   = CT.localize(datetime.combine(proj_day, dtime(14,30)))
        df_rth = fetch_live(sym2, rth_start.astimezone(UTC), rth_end.astimezone(UTC))
        df_rth_ct = df_rth.copy()
        if not df_rth_ct.empty:
            df_rth_ct.index = df_rth_ct.index.tz_convert(CT)
            df_rth_ct = df_rth_ct.between_time("08:30","14:30")

        st.markdown("#### Reference Line")
        ref_price = st.number_input("Anchor price (SPX or stock)", value=5000.0, step=1.0)
        ref_time = st.time_input("Anchor time (CT)", value=dtime(17,0), step=1800)
        ref_slope = st.number_input("Slope per 30m (+ or −)", value=0.268, step=0.001, format="%.3f")
        rth = rth_slots_ct("08:30","14:30")
        ref_df = project_line(ref_price, CT.localize(datetime.combine(proj_day, ref_time)), ref_slope, rth)
        c1, c2 = st.columns(2)
        with c1:
            st.write("Reference Line Table")
            st.dataframe(ref_df, use_container_width=True, hide_index=True)
        with c2:
            st.download_button("Download Reference Line CSV", ref_df.to_csv(index=False).encode(), "reference_line.csv", "text/csv")

        if not df_rth_ct.empty:
            st.markdown("#### Signals")
            buys = detect_signals(df_rth_ct, ref_df, mode="BUY")
            sells = detect_signals(df_rth_ct, ref_df, mode="SELL")
            st.write("**Buy Signals**")
            st.dataframe(buys, use_container_width=True, hide_index=True)
            st.write("**Sell Signals**")
            st.dataframe(sells, use_container_width=True, hide_index=True)

            st.markdown("#### EMA(8/21) Crossovers")
            ema_df, e8, e21 = ema_crossovers(df_rth_ct["Close"])
            st.dataframe(ema_df, use_container_width=True, hide_index=True)
        else:
            st.info("No 30m RTH data available for the selected day/symbol yet.")

    # ======== TAB 4: CONTRACT TOOL ========
    with tab4:
        contract_projection_tool()

    st.markdown("<div style='opacity:.7; font-size:.85rem; margin-top:8px'>© 2025 MarketLens Pro • Built with Streamlit (no external JS/Plotly)</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
