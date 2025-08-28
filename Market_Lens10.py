# app.py
# MarketLens Pro v5 — Analytics Edition (Streamlit-only, no Plotly)
# Focus: actionable analytics for entries/exits on 30m bars (CLOSE-only), all times in CT.
# Run:
#   pip install -r requirements.txt
#   streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, time as dtime, date
import pytz
from typing import List, Tuple, Optional, Dict

APP_NAME = "MarketLens Pro v5 — Max Pointe Consulting (Analytics)"

# ===============================
# THEME — Glassmorphism (Dark/Light)
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
        "glow": "0 0 90px rgba(124,200,255,0.12), 0 0 130px rgba(124,246,197,0.08)"
    }
    light = {
        "bg": "#f5f8ff",
        "panel": "rgba(255,255,255,0.78)",
        "panelSolid": "#ffffff",
        "text": "#0b1020",
        "muted": "#5d6474",
        "accent": "#0b6cff",
        "accent2": "#0f9d58",
        "success": "#188a5b",
        "warn": "#c07b00",
        "danger": "#cc0f2f",
        "border": "rgba(9,16,32,0.12)",
        "shadow": "0 16px 48px rgba(6,11,20,0.14)",
        "glow": "0 0 80px rgba(11,108,255,0.10), 0 0 120px rgba(15,157,88,0.08)"
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
# DATA NORMALIZATION / FETCH
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

@st.cache_data(ttl=60)
def fetch_live(symbol: str, start_utc: datetime, end_utc: datetime, interval="30m") -> pd.DataFrame:
    df = yf.download(symbol, start=start_utc, end=end_utc, interval=interval, auto_adjust=False, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    if getattr(df.index, "tz", None) is None:
        df.index = df.index.tz_localize(UTC)
    return _coerce_ohlcv(df)

@st.cache_data(ttl=300)
def fetch_hist_period(symbol: str, period="60d", interval="30m") -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
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
# SWINGS (CLOSE-only)
# ===============================

def mark_swings(df: pd.DataFrame, col: str = "Close", k: int = 1) -> pd.DataFrame:
    out = df.copy()
    series = df[col].squeeze()
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:,0]
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
# PROJECTIONS, SIGNALS, VWAP, ATR, EMA
# ===============================

def project_line(anchor_price: float, anchor_time_ct: datetime, slope_per_block: float, rth_slots_ct: List[datetime]) -> pd.DataFrame:
    minute = 0 if anchor_time_ct.minute < 30 else 30
    anchor_aligned = anchor_time_ct.replace(minute=minute, second=0, microsecond=0)
    rows = []
    for dt in rth_slots_ct:
        blocks = int(round((dt - anchor_aligned).total_seconds() / 1800.0))
        rows.append({"Time (CT)": dt.strftime("%H:%M"), "Price": round(anchor_price + slope_per_block * blocks, 4)})
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

def intraday_vwap(df_ct: pd.DataFrame) -> pd.Series:
    if df_ct.empty: return pd.Series(dtype=float)
    d = df_ct.copy()
    d.index = d.index.tz_convert(CT)
    d["typ"] = (d["High"] + d["Low"] + d["Close"]) / 3.0
    day = d.index.date
    cum_pv = d["typ"] * d["Volume"]
    vwap = (cum_pv.groupby(day).cumsum()) / (d["Volume"].groupby(day).cumsum()).replace(0, np.nan)
    vwap.index = d.index
    return vwap

def atr_30m(df_ct: pd.DataFrame, n: int = 14) -> pd.Series:
    if df_ct.empty: return pd.Series(dtype=float)
    d = df_ct.copy()
    d.index = d.index.tz_convert(CT)
    prev_close = d["Close"].shift(1)
    tr = pd.concat([
        (d["High"] - d["Low"]),
        (d["High"] - prev_close).abs(),
        (d["Low"] - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def ema_series(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()

# ===============================
# ANALYTICS / BACKTEST
# ===============================

def generate_line_for_day(anchor_price: float, anchor_time_ct: datetime, slope_per_block: float, day_ct: date) -> pd.DataFrame:
    slots = rth_slots_ct_dt(day_ct, "08:30","14:30")
    return project_line(anchor_price, anchor_time_ct, slope_per_block, slots)

def simulate_day(df_day: pd.DataFrame, line_df: pd.DataFrame, mode: str, atr: pd.Series,
                 rr_target: float, atr_multiple_stop: float,
                 vwap: pd.Series, use_vwap: bool, ema8: pd.Series, ema21: pd.Series, use_ema: bool) -> Tuple[pd.DataFrame, Dict]:
    trades = detect_signals(df_day, line_df, mode=mode)
    if trades.empty:
        return trades, {"trades":0,"wins":0,"losses":0,"avg_R":0.0,"expectancy":0.0}

    df = df_day.copy()
    df["Time (CT)"] = df.index.strftime("%H:%M")
    merged = trades.merge(df.reset_index()[["Time (CT)","Open","High","Low","Close"]], on="Time (CT)", how="left")

    if use_vwap:
        vwmap = vwap.reindex(df.index).astype(float)
        merged["vw"] = merged["Time (CT)"].map(dict(zip(df["Time (CT)"], vwmap)))
        if mode=="BUY":
            merged = merged[merged["Close"] > merged["vw"]]
        else:
            merged = merged[merged["Close"] < merged["vw"]]
    if use_ema:
        e8 = ema8.reindex(df.index).astype(float)
        e21 = ema21.reindex(df.index).astype(float)
        merged["e8"] = merged["Time (CT)"].map(dict(zip(df["Time (CT)"], e8)))
        merged["e21"]= merged["Time (CT)"].map(dict(zip(df["Time (CT)"], e21)))
        if mode=="BUY":
            merged = merged[merged["e8"] > merged["e21"]]
        else:
            merged = merged[merged["e8"] < merged["e21"]]

    if merged.empty:
        return merged, {"trades":0,"wins":0,"losses":0,"avg_R":0.0,"expectancy":0.0}

    atr_map = atr.reindex(df.index).astype(float)
    merged["atr"] = merged["Time (CT)"].map(dict(zip(df["Time (CT)"], atr_map)))
    merged["R_stop"] = atr_multiple_stop * merged["atr"]

    if mode=="BUY":
        merged["Entry"]  = merged["Close"]
        merged["Stop"]   = merged["Entry"] - merged["R_stop"]
        merged["Target"] = merged["Entry"] + rr_target * merged["R_stop"]
        merged["Outcome (R)"] = np.where(merged["High"] >= merged["Target"], rr_target,
                                  np.where(merged["Low"]  <= merged["Stop"], -1.0, 0.0))
    else:
        merged["Entry"]  = merged["Close"]
        merged["Stop"]   = merged["Entry"] + merged["R_stop"]
        merged["Target"] = merged["Entry"] - rr_target * merged["R_stop"]
        merged["Outcome (R)"] = np.where(merged["Low"]  <= merged["Target"], rr_target,
                                  np.where(merged["High"] >= merged["Stop"], -1.0, 0.0))

    wins = int((merged["Outcome (R)"] > 0).sum())
    losses = int((merged["Outcome (R)"] < 0).sum())
    trades_n = int(len(merged))
    avg_R = float(merged["Outcome (R)"].replace(0.0, np.nan).mean(skipna=True)) if trades_n else 0.0
    expectancy = float(merged["Outcome (R)"].mean()) if trades_n else 0.0

    merged = merged[["Time (CT)","Type","Entry","Stop","Target","Outcome (R)"]].rename(columns={"Type":"Signal"})
    merged["Entry"] = merged["Entry"].round(4)
    merged["Stop"] = merged["Stop"].round(4)
    merged["Target"] = merged["Target"].round(4)
    merged["Outcome (R)"] = merged["Outcome (R)"].round(2)

    return merged, {"trades":trades_n,"wins":wins,"losses":losses,"avg_R":round(avg_R,2),"expectancy":round(expectancy,2)}

def confluence_table(df_ct: pd.DataFrame, line_df: pd.DataFrame, ema8: pd.Series, ema21: pd.Series, vwap: pd.Series) -> pd.DataFrame:
    if df_ct.empty: return pd.DataFrame()
    df = df_ct.copy()
    df["Time (CT)"] = df.index.strftime("%H:%M")
    line_map = dict(zip(line_df["Time (CT)"], line_df["Price"]))
    df["line"] = df["Time (CT)"].map(line_map)
    df = df.dropna(subset=["line"])
    tr = (df["High"] - df["Low"]).ewm(span=14, adjust=False).mean()
    proximity = (df["Close"] - df["line"]).abs() / tr.replace(0,np.nan)
    e8 = ema_series(df_ct["Close"], 8).reindex(df.index)
    e21 = ema_series(df_ct["Close"], 21).reindex(df.index)
    regime = np.where(e8 > e21, 1, -1)
    vw = vwap.reindex(df.index)
    vreg = np.where(df["Close"] > vw, 1, -1)
    score = (1 / (1 + proximity.fillna(9.9))) + 0.5*(regime) + 0.5*(vreg)
    out = pd.DataFrame({
        "Time (CT)": df["Time (CT)"],
        "Line": df["line"].round(4),
        "Close": df["Close"].round(4),
        "Proximity": proximity.round(3),
        "EMA Regime": np.where(regime>0, "Bull", "Bear"),
        "VWAP Regime": np.where(vreg>0, "Above", "Below"),
        "Confluence Score": score.round(2)
    })
    return out.reset_index(drop=True)

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

# ===============================
# MAIN APP
# ===============================

def main():
    st.set_page_config(page_title=APP_NAME, page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")

    with st.sidebar:
        st.markdown("## ⚙️ Display")
        mode = st.radio("Theme", ["Dark", "Light"], index=0, key="ui_theme")
        inject_theme(mode)
        st.markdown("### 🧮 Slopes (per 30-min)")
        spx_sky  = st.number_input("SPX Skyline (+)", value=SLOPES["SPX"]["Skyline"], step=0.001, format="%.3f", key="sb_spx_sky")
        spx_base = st.number_input("SPX Baseline (−)", value=SLOPES["SPX"]["Baseline"], step=0.001, format="%.3f", key="sb_spx_base")
        st.caption("Stocks use ± magnitudes (e.g., AAPL 0.0155 → Skyline +0.0155 / Baseline −0.0155).")

    st.markdown(f"## {APP_NAME}")
    st.caption("All timestamps in **Central Time (CT)**. Line-chart logic uses **CLOSE only**.")

    tab_spx, tab_stk, tab_sig, tab_analytics, tab_contract = st.tabs([
        "📈 SPX Anchors", "📚 Stock Anchors", "✅ Signals & EMA", "📊 Analytics / Backtest", "🧮 Contract Tool"
    ])

    # ======== SPX Anchors (ES Asian Session) ========
    with tab_spx:
        def body():
            yesterday_ct = (datetime.now(CT) - timedelta(days=1)).date()
            prev_day = st.date_input("Previous trading day (CT)", value=yesterday_ct, key="spx_prev_day")
            k_spx = st.slider("Swing selectivity (bars each side)", 1, 3, 1, key="spx_k")
            sky, base, offset = detect_spx_anchors_from_es(prev_day, k=k_spx)
            if (sky is None) or (base is None):
                st.error("No valid CLOSE-only swings in 17:00–19:30 CT. Try another date or reduce selectivity.")
                return
            sky_p, sky_t = sky; base_p, base_t = base
            st.markdown("<div class='ml-row'>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>Skyline</div><div class='ml-sub'>Swing-high close</div><div style='height:6px'></div><div style='font-weight:800;font-size:1.3rem'>{sky_p:.2f}</div><div class='ml-sub'>@ {format_ct(sky_t)}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>Baseline</div><div class='ml-sub'>Swing-low close</div><div style='height:6px'></div><div style='font-weight:800;font-size:1.3rem'>{base_p:.2f}</div><div class='ml-sub'>@ {format_ct(base_t)}</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            suggested_offset = float(offset) if isinstance(offset,(int,float)) else 0.0
            es_spx_offset = st.number_input("ES → SPX offset (add to ES close to estimate SPX)", value=suggested_offset, step=0.5, key="spx_off")
            sky_spx = sky_p + es_spx_offset; base_spx = base_p + es_spx_offset

            proj_day = st.date_input("Projection Day (CT)", value=prev_day + timedelta(days=1), key="spx_proj")
            slots = rth_slots_ct_dt(proj_day, "08:30","14:30")
            df_sky = project_line(sky_spx, sky_t, spx_sky, slots)
            df_base = project_line(base_spx, base_t, spx_base, slots)

            c1, c2 = st.columns(2)
            with c1:
                st.write("SPX Skyline (+0.268/blk)")
                st.dataframe(df_sky, use_container_width=True, hide_index=True)
                st.download_button("Download Skyline CSV", df_sky.to_csv(index=False).encode(), "spx_skyline.csv", "text/csv", key="dl_spx_sky")
            with c2:
                st.write("SPX Baseline (−0.235/blk)")
                st.dataframe(df_base, use_container_width=True, hide_index=True)
                st.download_button("Download Baseline CSV", df_base.to_csv(index=False).encode(), "spx_baseline.csv", "text/csv", key="dl_spx_base")
        card("SPX Anchors → Projection", "ES Asian session (17:00–19:30 CT) CLOSE-only swings → SPX via offset → RTH projections.", body_fn=body, badge="SPX")

    # ======== Stock Anchors (Mon/Tue) ========
    with tab_stk:
        def body():
            sym = st.text_input("Stock Symbol", value="AAPL", key="stk_sym").upper()
            today_et = datetime.now(ET).date()
            weekday = today_et.weekday()
            last_mon = today_et - timedelta(days=(weekday - 0) % 7 or 7)
            last_tue = last_mon + timedelta(days=1)
            c1, c2 = st.columns(2)
            with c1: mon_date = st.date_input("Monday (ET session)", value=last_mon, key="stk_mon")
            with c2: tue_date = st.date_input("Tuesday (ET session)", value=last_tue, key="stk_tue")
            k_stk = st.slider("Swing selectivity (bars each side)", 1, 3, 1, key="stk_k")
            sky, base = detect_stock_anchors_two_day(sym, mon_date, tue_date, k=k_stk)
            if (sky is None) or (base is None):
                st.error("No valid CLOSE-only swings across Mon/Tue. Adjust dates or selectivity.")
                return
            sky_p, sky_t = sky; base_p, base_t = base
            slope_mag = SLOPES.get(sym, SLOPES.get(sym.capitalize(), 0.015))

            st.markdown("<div class='ml-row'>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>{sym} Skyline</div><div class='ml-sub'>Swing-high close</div><div style='height:6px'></div><div style='font-weight:800;font-size:1.3rem'>{sky_p:.2f}</div><div class='ml-sub'>@ {format_ct(sky_t)}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='ml-card'><div class='ml-pill'>{sym} Baseline</div><div class='ml-sub'>Swing-low close</div><div style='height:6px'></div><div style='font-weight:800;font-size:1.3rem'>{base_p:.2f}</div><div class='ml-sub'>@ {format_ct(base_t)}</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Default projection day: first Wednesday after Tue
            days_ahead = (2 - tue_date.weekday()) % 7
            if days_ahead == 0: days_ahead = 7
            first_wed = tue_date + timedelta(days=days_ahead)
            proj_day = st.date_input("Projection Day (CT)", value=first_wed, key=f"{sym}_proj")
            slots = rth_slots_ct_dt(proj_day, "08:30","14:30")
            df_sky = project_line(sky_p, sky_t, +slope_mag, slots)
            df_base = project_line(base_p, base_t, -slope_mag, slots)

            c1, c2 = st.columns(2)
            with c1:
                st.write(f"{sym} Skyline (+{slope_mag:.4f}/blk)")
                st.dataframe(df_sky, use_container_width=True, hide_index=True)
                st.download_button(f"Download {sym} Skyline CSV", df_sky.to_csv(index=False).encode(), f"{sym}_skyline.csv", "text/csv", key=f"dl_{sym}_sky")
            with c2:
                st.write(f"{sym} Baseline (−{slope_mag:.4f}/blk)")
                st.dataframe(df_base, use_container_width=True, hide_index=True)
                st.download_button(f"Download {sym} Baseline CSV", df_base.to_csv(index=False).encode(), f"{sym}_baseline.csv", "text/csv", key=f"dl_{sym}_base")
        card("Stock Anchors → Projection", "Mon/Tue CLOSE-only swings → stock-specific slopes → RTH projections.", body_fn=body, badge="Stocks")

    # ======== Signals & EMA (single-day utility) ========
    with tab_sig:
        def body():
            sym2 = st.text_input("Symbol", value="^GSPC", key="sig_sym").upper()
            day = st.date_input("Day (CT)", value=datetime.now(CT).date(), key="sig_day")
            rth_start = CT.localize(datetime.combine(day, dtime(8,30)))
            rth_end   = CT.localize(datetime.combine(day, dtime(14,30)))
            df_ct = fetch_live(sym2, rth_start.astimezone(UTC), rth_end.astimezone(UTC))
            if not df_ct.empty:
                df_ct.index = df_ct.index.tz_convert(CT)
                df_ct = df_ct.between_time("08:30","14:30")

            st.markdown("##### Reference Line")
            c1,c2,c3 = st.columns(3)
            with c1: ref_price = st.number_input("Anchor Price", value=5000.0, step=1.0, key="sig_anchor_price")
            with c2: ref_time  = st.time_input("Anchor Time (CT)", value=dtime(17,0), step=1800, key="sig_anchor_time")
            with c3: ref_slope = st.number_input("Slope per 30m (+/−)", value=0.268, step=0.001, format="%.3f", key="sig_ref_slope")

            line_df = project_line(ref_price, CT.localize(datetime.combine(day, ref_time)), ref_slope, rth_slots_ct_dt(day, "08:30","14:30"))
            if not df_ct.empty:
                buys = detect_signals(df_ct, line_df, "BUY")
                sells = detect_signals(df_ct, line_df, "SELL")
                st.write("Reference Line")
                st.dataframe(line_df, use_container_width=True, hide_index=True)
                st.write("Buy Signals")
                st.dataframe(buys, use_container_width=True, hide_index=True)
                st.write("Sell Signals")
                st.dataframe(sells, use_container_width=True, hide_index=True)

                e8 = ema_series(df_ct["Close"], 8)
                e21= ema_series(df_ct["Close"], 21)
                crosses = []
                sign = np.sign(e8 - e21)
                idx = np.where(np.diff(sign) != 0)[0] + 1
                for i in idx:
                    crosses.append({
                        "Time (CT)": df_ct.index[i].strftime("%Y-%m-%d %H:%M"),
                        "EMA8": round(float(e8.iloc[i]),4),
                        "EMA21": round(float(e21.iloc[i]),4),
                        "Direction": "Bullish ↑" if (e8.iloc[i] - e21.iloc[i])>0 else "Bearish ↓"
                    })
                st.write("EMA(8/21) Crossovers")
                st.dataframe(pd.DataFrame(crosses), use_container_width=True, hide_index=True)
            else:
                st.info("No 30-minute RTH data available for that day/symbol yet.")
        card("Signals & EMA", "Line-touch entries on 30-minute bars + EMA8/21 crossovers.", body_fn=body, badge="Signals")

    # ======== Analytics / Backtest ========
    with tab_analytics:
        def body():
            st.markdown("##### Configure Reference Line (used for simulation across many days)")
            sym = st.text_input("Symbol", value="^GSPC", key="bt_sym").upper()
            lookback_days = st.slider("Lookback (trading days, ≤60 for 30m data)", 5, 60, 20, key="bt_lookback")
            mode = st.selectbox("Signal Mode", ["BUY","SELL"], index=0, key="bt_mode")

            c1,c2,c3 = st.columns(3)
            with c1: anchor_price = st.number_input("Anchor Price", value=5000.0, step=1.0, key="bt_anchor_price")
            with c2: anchor_time  = st.time_input("Anchor Time (CT)", value=dtime(17,0), step=1800, key="bt_anchor_time")
            with c3: slope        = st.number_input("Slope per 30m (+/−)", value=0.268, step=0.001, format="%.3f", key="bt_slope")

            c4,c5,c6 = st.columns(3)
            with c4: rr_target = st.number_input("Target (R)", value=1.5, step=0.1, min_value=0.5, key="bt_rr")
            with c5: atr_stop  = st.number_input("Stop (ATR multiples)", value=1.0, step=0.1, min_value=0.2, key="bt_atr_stop")
            with c6: use_vwap  = st.checkbox("Require VWAP alignment", value=True, key="bt_use_vwap")

            c7,c8 = st.columns(2)
            with c7: use_ema = st.checkbox("Require EMA8/21 regime", value=False, key="bt_use_ema")
            with c8: st.caption("If checked: BUY requires EMA8>EMA21, SELL requires EMA8<EMA21")

            end_ct = datetime.now(CT)
            start_ct = end_ct - timedelta(days=lookback_days*2)  # pad for weekends/holidays
            hist = fetch_hist_period(sym, period="60d", interval="30m")
            if hist.empty:
                st.error("No historical 30-minute data returned.")
                return
            hist = hist.copy(); hist.index = hist.index.tz_convert(CT)
            hist = hist.between_time("08:30","14:30")
            hist = hist[(hist.index >= start_ct) & (hist.index <= end_ct)]
            if hist.empty:
                st.error("No RTH bars in selected window.")
                return

            # Indicators
            atr = atr_30m(hist, 14)
            vwap = intraday_vwap(hist)
            e8 = ema_series(hist["Close"], 8)
            e21= ema_series(hist["Close"], 21)

            # Simulate per day
            days = sorted(list(set(hist.index.date)))
            day_stats = []
            all_trades = []
            time_perf: Dict[str, list] = {}

            for d in days:
                df_day = hist[hist.index.date == d]
                if df_day.empty: continue
                line_df = generate_line_for_day(anchor_price, CT.localize(datetime.combine(d, anchor_time)), slope, d)
                trades, stats = simulate_day(df_day, line_df, mode, atr, rr_target, atr_stop, vwap, use_vwap, e8, e21, use_ema)
                if not trades.empty:
                    trades = trades.copy()
                    trades.insert(0, "Date", d.strftime("%Y-%m-%d"))
                    all_trades.append(trades)
                    for _, r in trades.iterrows():
                        time_perf.setdefault(r["Time (CT)"], []).append(r["Outcome (R)"])
                stats["date"] = d.strftime("%Y-%m-%d")
                day_stats.append(stats)

            if all_trades:
                trade_log = pd.concat(all_trades, ignore_index=True)
                st.write("**Trade Log**")
                st.dataframe(trade_log, use_container_width=True, hide_index=True)

                wins = int((trade_log["Outcome (R)"] > 0).sum())
                losses = int((trade_log["Outcome (R)"] < 0).sum())
                total = len(trade_log)
                avg_R = float(trade_log["Outcome (R)"].replace(0.0, np.nan).mean(skipna=True)) if total else 0.0
                expectancy = float(trade_log["Outcome (R)"].mean()) if total else 0.0

                st.markdown("<div class='ml-row'>", unsafe_allow_html=True)
                st.markdown(f"<div class='ml-card'><div class='ml-pill'>Outcome</div><div class='ml-sub'>Across {total} signals</div><div style='height:6px'></div><div style='font-weight:800;font-size:1.3rem'>Win {wins} • Loss {losses}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='ml-card'><div class='ml-pill'>Avg R</div><div class='ml-sub'>Ignoring 0R</div><div style='height:6px'></div><div style='font-weight:800;font-size:1.3rem'>{avg_R:.2f}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='ml-card'><div class='ml-pill'>Expectancy</div><div class='ml-sub'>Mean R per trade</div><div style='height:6px'></div><div style='font-weight:800;font-size:1.3rem'>{expectancy:.2f}</div></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                perf_rows = []
                for t, arr in sorted(time_perf.items()):
                    r = pd.Series(arr)
                    perf_rows.append({"Time (CT)": t, "Trades": len(r), "Win%": round(100*(r>0).mean(),1), "Avg R": round(r.mean(),2)})
                perf_df = pd.DataFrame(perf_rows).sort_values(["Trades","Avg R"], ascending=[False, False])
                st.write("**Time-of-Day Edge (historical)**")
                st.dataframe(perf_df, use_container_width=True, hide_index=True)

                last_day = days[-1]
                df_last = hist[hist.index.date == last_day]
                line_last = generate_line_for_day(anchor_price, CT.localize(datetime.combine(last_day, anchor_time)), slope, last_day)
                conf = confluence_table(df_last, line_last, e8, e21, vwap)
                st.write(f"**Confluence Score — {last_day}** (higher = better alignment)")
                st.dataframe(conf, use_container_width=True, hide_index=True)
            else:
                st.info("No qualifying signals in the selected window with current filters/line settings.")
        card("Analytics / Backtest", "Simulate your line-touch rules across many days with ATR/VWAP/EMA filters. Find best windows & expectancy.", body_fn=body, badge="Analytics")

    # ======== Contract Tool ========
    with tab_contract:
        def body():
            c1, c2 = st.columns(2)
            with c1:
                t1 = st.time_input("Point 1 Time (CT)", value=dtime(20,0), step=1800, key="ct_p1_time")
                p1 = st.number_input("Point 1 Price", value=10.0, step=0.1, key="ct_p1_price")
            with c2:
                t2 = st.time_input("Point 2 Time (CT)", value=dtime(3,30), step=1800, key="ct_p2_time")
                p2 = st.number_input("Point 2 Price", value=12.0, step=0.1, key="ct_p2_price")
            proj_day = st.date_input("Projection Day (CT)", value=datetime.now(CT).date(), key="ct_proj_day")
            prev_day = proj_day - timedelta(days=1)
            dt1 = CT.localize(datetime.combine(prev_day if t1.hour >= 20 else proj_day, t1))
            dt2 = CT.localize(datetime.combine(prev_day if t2.hour >= 20 else proj_day, t2))
            blocks_signed = int(round((dt2 - dt1).total_seconds() / 1800.0))
            slope = 0.0 if blocks_signed == 0 else (p2 - p1) / blocks_signed
            slots = rth_slots_ct_dt(proj_day, "08:30","14:30")
            rows = []
            for slot in slots:
                b = int(round((slot - dt1).total_seconds() / 1800.0))
                rows.append({"Time (CT)": slot.strftime("%H:%M"), "Price": round(p1 + slope*b, 4)})
            df = pd.DataFrame(rows)
            st.write(f"Slope per 30-min block: **{slope:.4f}**")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Download Contract Projection CSV", df.to_csv(index=False).encode(), "contract_projection.csv", "text/csv", key="dl_contract")
        card("Contract Projection", "Two points (20:00 prev → 10:00 today) → slope → 08:30–14:30 CT forecast.", body_fn=body, badge="Contracts")

    st.markdown("<div class='muted' style='margin-top:12px'>© 2025 MarketLens Pro • All analytics on 30-minute bars (CT). CLOSE-only swing logic.</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
