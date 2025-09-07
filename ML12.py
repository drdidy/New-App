# app.py
# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 SPX PROPHET — SPX-only Enterprise App
# Tabs: 1) SPX Anchors  2) BC Forecast (EXACTLY 2 bounces, Entries & Exits)
#       3) Probability Board  4) Plan Card
#
# Core:
# - Anchor: previous session ≤ 3:00 PM CT SPX cash close
# - Fan slopes (per 30m): Top +0.312  •  Bottom −0.25  (overrideable)
# - Corrected bias + edge interaction logic (within-fan proximity + neutrality band)
# - ES→SPX offset ladder (1m → 5m → 30m → recent median)
# - Overnight detection with 1m/5m; 30m last-resort for robustness
# - Forms & slot pickers minimize disruptive reruns; ⭐ 8:30 highlight
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple

# ───────────────────────────────────────────────────────────────────────────────
# GLOBALS & CONFIG
# ───────────────────────────────────────────────────────────────────────────────
CT_TZ = pytz.timezone("America/Chicago")
RTH_START = "08:30"
RTH_END   = "14:30"

TOP_SLOPE_DEFAULT    = 0.312
BOTTOM_SLOPE_DEFAULT = 0.25

# Probability boosters (30m basis)
WEIGHTS_DEFAULT = {"ema":20, "volume":25, "wick":20, "atr":15, "tod":20, "div":0}
KEY_TOD = [(8,30), (10,0), (13,30)]
KEY_TOD_WINDOW_MIN = 7
WICK_MIN_RATIO = 0.6
ATR_LOOKBACK = 14
ATR_HIGH_PCTL = 70
ATR_LOW_PCTL  = 30
RSI_LEN = 14
RSI_WINDOW_MIN = 10

# ───────────────────────────────────────────────────────────────────────────────
# PAGE & THEME
# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🔮 SPX Prophet",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root { --brand:#2563eb; --brand-2:#10b981; --surface:#ffffff; --muted:#f8fafc;
        --text:#0f172a; --subtext:#475569; --border:#e2e8f0; --warn:#f59e0b; --danger:#ef4444; }
html, body, [class*="css"] { background: var(--muted); color: var(--text); }
.block-container { padding-top: 1.1rem; }
h1, h2, h3 { color: var(--text); }
.card, .metric-card {
  background: rgba(255,255,255,0.9); border: 1px solid var(--border); border-radius: 16px; padding: 16px;
  box-shadow: 0 12px 32px rgba(2,6,23,0.07); backdrop-filter: blur(8px);
}
.metric-title { font-size: .9rem; color: var(--subtext); margin: 0; }
.metric-value { font-size: 1.8rem; font-weight: 700; margin-top: 6px; }
.kicker { font-size: .8rem; color: var(--subtext); }
.badge-open { color:#065f46; background:#d1fae5; border:1px solid #99f6e4; padding:2px 8px; border-radius:999px; font-size:.8rem; font-weight:600; }
.badge-closed { color:#7c2d12; background:#ffedd5; border:1px solid #fed7aa; padding:2px 8px; border-radius:999px; font-size:.8rem; font-weight:600; }
.override-tag { font-size:.75rem; color:#334155; background:#e2e8f0; border:1px solid #cbd5e1; padding:2px 8px; border-radius:999px; display:inline-block; margin-top:6px; }
hr { border-top: 1px solid var(--border); }
.dataframe { background: var(--surface); border-radius: 12px; overflow: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ───────────────────────────────────────────────────────────────────────────────
def fmt_ct(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return CT_TZ.localize(dt)
    return dt.astimezone(CT_TZ)

def between_time(df: pd.DataFrame, start_str: str, end_str: str) -> pd.DataFrame:
    return df.between_time(start_str, end_str) if not df.empty else df

def rth_slots_ct(target_date: date) -> List[datetime]:
    start_dt = fmt_ct(datetime.combine(target_date, time(8,30)))
    end_dt   = fmt_ct(datetime.combine(target_date, time(14,30)))
    out, cur = [], start_dt
    while cur <= end_dt:
        out.append(cur)
        cur += timedelta(minutes=30)
    return out

def gen_slots(start_dt: datetime, end_dt: datetime, step_min: int = 30) -> List[datetime]:
    start_dt = fmt_ct(start_dt); end_dt = fmt_ct(end_dt)
    out, cur = [], start_dt
    while cur <= end_dt:
        out.append(cur); cur += timedelta(minutes=step_min)
    return out

def is_maintenance(dt: datetime) -> bool:
    return dt.hour == 16  # 4–5 PM CT maintenance hour

def in_weekend_gap(dt: datetime) -> bool:
    wd = dt.weekday()
    if wd == 5: return True
    if wd == 6 and dt.hour < 17: return True
    if wd == 4 and dt.hour >= 17: return True
    return False

def count_effective_blocks(anchor_time: datetime, target_time: datetime) -> float:
    if target_time <= anchor_time:
        return 0.0
    t = anchor_time
    blocks = 0
    while t < target_time:
        t_next = t + timedelta(minutes=30)
        if not is_maintenance(t_next) and not in_weekend_gap(t_next):
            blocks += 1
        t = t_next
    return float(blocks)

def ensure_ohlc_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns]
    for c in ["Open","High","Low","Close"]:
        if c not in df.columns:
            return pd.DataFrame()
    return df

def normalize_to_ct(df: pd.DataFrame, start_d: date, end_d: date) -> pd.DataFrame:
    if df.empty:
        return df
    df = ensure_ohlc_cols(df)
    if df.empty:
        return df
    if df.index.tz is None:
        df.index = df.index.tz_localize("US/Eastern")
    df.index = df.index.tz_convert(CT_TZ)
    sdt = fmt_ct(datetime.combine(start_d, time(0,0)))
    edt = fmt_ct(datetime.combine(end_d, time(23,59)))
    return df.loc[sdt:edt]

@st.cache_data(ttl=120, show_spinner=False)
def fetch_intraday(symbol: str, start_d: date, end_d: date, interval: str) -> pd.DataFrame:
    """
    Robust intraday fetch with correct CT normalization.
    - For 1m/2m/5m/15m: period-based (yfinance limitation), then slice.
    - For >=30m: use start/end windows.
    """
    try:
        t = yf.Ticker(symbol)
        if interval in ["1m","2m","5m","15m"]:
            days = max(1, min(7, (end_d - start_d).days + 2))
            df = t.history(period=f"{days}d", interval=interval, prepost=True,
                           auto_adjust=False, back_adjust=False)
            df = normalize_to_ct(df, start_d - timedelta(days=1), end_d + timedelta(days=1))
            sdt = fmt_ct(datetime.combine(start_d, time(0,0)))
            edt = fmt_ct(datetime.combine(end_d, time(23,59)))
            df = df.loc[sdt:edt]
        else:
            df = t.history(
                start=(start_d - timedelta(days=5)).strftime("%Y-%m-%d"),
                end=(end_d + timedelta(days=2)).strftime("%Y-%m-%d"),
                interval=interval, prepost=True, auto_adjust=False, back_adjust=False,
            )
            df = normalize_to_ct(df, start_d, end_d)
        return df
    except Exception:
        return pd.DataFrame()

def resample_to_30m_ct(min_df: pd.DataFrame) -> pd.DataFrame:
    """Safe 30m resample (handles missing Volume)."""
    if min_df.empty or not isinstance(min_df.index, pd.DatetimeIndex):
        return pd.DataFrame()
    df = min_df.sort_index()
    agg = {}
    if "Open"   in df.columns: agg["Open"]   = "first"
    if "High"   in df.columns: agg["High"]   = "max"
    if "Low"    in df.columns: agg["Low"]    = "min"
    if "Close"  in df.columns: agg["Close"]  = "last"
    if "Volume" in df.columns: agg["Volume"] = "sum"
    out = df.resample("30T", label="right", closed="right").agg(agg)
    out = out.dropna(subset=[c for c in ["Open","High","Low","Close"] if c in out.columns], how="any")
    return out

def get_prev_day_anchor_close_and_time(df_30m: pd.DataFrame, prev_day: date) -> Tuple[Optional[float], Optional[datetime]]:
    """Return last SPX bar ≤ 3:00 PM CT (close & its time) for prev_day."""
    if df_30m.empty:
        return None, None
    day_start = fmt_ct(datetime.combine(prev_day, time(0,0)))
    day_end   = fmt_ct(datetime.combine(prev_day, time(23,59)))
    d = df_30m.loc[day_start:day_end].copy()
    if d.empty:
        return None, None
    target = fmt_ct(datetime.combine(prev_day, time(15,0)))
    if target in d.index:
        return float(d.loc[target, "Close"]), target
    prior = d.loc[:target]
    if not prior.empty:
        return float(prior.iloc[-1]["Close"]), prior.index[-1]
    return None, None

def current_spx_slopes() -> Tuple[float, float]:
    top = float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT))
    bottom = float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT))
    return top, bottom

def project_fan_from_close(close_price: float, anchor_time: datetime, target_day: date) -> pd.DataFrame:
    top_slope, bottom_slope = current_spx_slopes()
    rows = []
    for slot in rth_slots_ct(target_day):
        blocks = count_effective_blocks(anchor_time, slot)
        top = close_price + top_slope * blocks
        bot = close_price - bottom_slope * blocks
        rows.append({"TimeDT": slot, "Time": slot.strftime("%H:%M"),
                     "Top": round(top,2), "Bottom": round(bot,2),
                     "Fan_Width": round(top-bot,2)})
    return pd.DataFrame(rows)

# ───────────────────────────────────────────────────────────────────────────────
# INDICATORS & SCORING
# ───────────────────────────────────────────────────────────────────────────────
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    roll_up = pd.Series(up, index=series.index).ewm(alpha=1/length, adjust=False).mean()
    roll_down = pd.Series(down, index=series.index).ewm(alpha=1/length, adjust=False).mean()
    rs = roll_up / (roll_down + 1e-12)
    return 100 - (100 / (1 + rs))

def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["Close"].shift(1)
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - prev_close).abs()
    tr3 = (df["Low"] - prev_close).abs()
    return pd.concat([tr1,tr2,tr3], axis=1).max(axis=1)

# ───────────────────────────────────────────────────────────────────────────────
# BIAS / EDGE LOGIC
# ───────────────────────────────────────────────────────────────────────────────
def compute_bias(price: float, top: float, bottom: float, tol_frac: float) -> str:
    """Within-fan proximity with neutrality band; outside → NO BIAS here."""
    if bottom <= price <= top:
        width = top - bottom
        center = (top + bottom)/2.0
        band = tol_frac * width
        if center - band <= price <= center + band:
            return "NO BIAS"
        dist_top = abs(top - price)
        dist_bottom = abs(price - bottom)
        return "UP" if dist_bottom < dist_top else "DOWN"
    return "NO BIAS"

def candle_class(open_, close_) -> str:
    if close_ > open_: return "Bullish"
    if close_ < open_: return "Bearish"
    return "Doji"

def touched_line(low, high, line) -> bool:
    return (low <= line <= high)

def classify_edge_touch(bar: pd.Series, top: float, bottom: float) -> Optional[Dict]:
    """
    Edge interaction rules:
    - Top touched + bearish close (inside/above) → different expectations
    - Bottom touched + bullish close (inside/below) → different expectations
    """
    o = float(bar.get("Open", np.nan))
    h = float(bar.get("High", np.nan))
    l = float(bar.get("Low",  np.nan))
    c = float(bar.get("Close",np.nan))
    cls = candle_class(o, c)

    inside = (bottom <= c <= top)
    above  = (c > top)
    below  = (c < bottom)

    # TOP
    if touched_line(l, h, top) and cls == "Bearish":
        if inside:
            return {"edge":"Top","case":"TopTouch_BearishClose_Inside",
                    "expected":"Breakdown to Bottom → plan to BUY from Bottom",
                    "direction_hint":"DownToBottomThenBuy"}
        if above:
            return {"edge":"Top","case":"TopTouch_BearishClose_Above",
                    "expected":"Top holds as support → market buys higher",
                    "direction_hint":"BuyHigherFromTop"}

    # BOTTOM
    if touched_line(l, h, bottom) and cls == "Bullish":
        if inside:
            return {"edge":"Bottom","case":"BottomTouch_BullishClose_Inside",
                    "expected":"Breakout to Top → plan to SELL from Top",
                    "direction_hint":"UpToTopThenSell"}
        if below:
            return {"edge":"Bottom","case":"BottomTouch_BullishClose_Below",
                    "expected":"Bottom fails → market drops further",
                    "direction_hint":"SellFurtherDown"}

    return None

# ───────────────────────────────────────────────────────────────────────────────
# PROBABILITY BOOSTERS
# ───────────────────────────────────────────────────────────────────────────────
def compute_boosters_score_30m(df_30m: pd.DataFrame, idx_30m: pd.Timestamp,
                               expected_hint: str, weights: Dict[str,int]) -> Tuple[int, Dict[str,int]]:
    comps = {k:0 for k in ["ema","volume","wick","atr","tod","div"]}
    if df_30m.empty or idx_30m not in df_30m.index:
        return 0, comps
    upto = df_30m.loc[:idx_30m].copy()
    if upto.shape[0] < 10:
        return 0, comps

    # EMA 8/21
    ema8 = ema(upto["Close"], 8)
    ema21 = ema(upto["Close"], 21)
    ema_state = "Bullish" if ema8.iloc[-1] > ema21.iloc[-1] else ("Bearish" if ema8.iloc[-1] < ema21.iloc[-1] else "None")
    expected_near_term = "Up" if expected_hint in ("BuyHigherFromTop","UpToTopThenSell") else "Down"
    if (expected_near_term == "Up" and ema_state == "Bullish") or (expected_near_term == "Down" and ema_state == "Bearish"):
        comps["ema"] = weights.get("ema",0)

    # Volume spike
    if "Volume" in upto.columns and upto["Volume"].notna().any():
        vma = upto["Volume"].rolling(20).mean()
        if vma.notna().any() and vma.iloc[-1]:
            if upto["Volume"].iloc[-1] > vma.iloc[-1] * 1.15:
                comps["volume"] = weights.get("volume",0)

    # Wick rejection
    bar = upto.iloc[-1]
    o,h,l,c = float(bar["Open"]), float(bar["High"]), float(bar["Low"]), float(bar["Close"])
    body = abs(c - o) + 1e-9
    upper_wick = max(0.0, h - max(o,c))
    lower_wick = max(0.0, min(o,c) - l)
    if expected_near_term == "Up":
        if lower_wick / body >= WICK_MIN_RATIO:
            comps["wick"] = weights.get("wick",0)
    else:
        if upper_wick / body >= WICK_MIN_RATIO:
            comps["wick"] = weights.get("wick",0)

    # ATR regime
    tr = true_range(upto)
    atr = tr.rolling(ATR_LOOKBACK).mean()
    if atr.notna().sum() >= ATR_LOOKBACK:
        pct = (atr.rank(pct=True).iloc[-1]) * 100.0
        if expected_hint in ("BuyHigherFromTop","UpToTopThenSell"):
            if pct <= ATR_LOW_PCTL:
                comps["atr"] = weights.get("atr",0)
        elif expected_hint in ("SellFurtherDown","DownToBottomThenBuy"):
            if pct >= ATR_HIGH_PCTL:
                comps["atr"] = weights.get("atr",0)

    # Time-of-day
    ts = fmt_ct(idx_30m.to_pydatetime())
    if any(abs((ts.hour*60 + ts.minute) - (hh*60+mm)) <= KEY_TOD_WINDOW_MIN for (hh,mm) in KEY_TOD):
        comps["tod"] = weights.get("tod",0)

    # Lightweight divergence (optional by weight)
    if weights.get("div",0) > 0:
        r = rsi(upto["Close"], RSI_LEN)
        if r.notna().sum() >= RSI_LEN + 2:
            window_bars = max(5, RSI_WINDOW_MIN)
            prior = upto.iloc[-window_bars:-1] if upto.shape[0] > window_bars else upto.iloc[:-1]
            if prior.shape[0] > 5:
                prior_low = prior["Close"].idxmin()
                prior_high = prior["Close"].idxmax()
                if expected_near_term == "Up":
                    if upto["Close"].iloc[-1] <= prior["Close"].min() and r.iloc[-1] > r.loc[prior_low]:
                        comps["div"] = weights.get("div",0)
                else:
                    if upto["Close"].iloc[-1] >= prior["Close"].max() and r.iloc[-1] < r.loc[prior_high]:
                        comps["div"] = weights.get("div",0)

    score = int(min(100, max(0, sum(comps.values()))))
    return score, comps

# ───────────────────────────────────────────────────────────────────────────────
# ES→SPX OFFSET & OVERNIGHT
# ───────────────────────────────────────────────────────────────────────────────
def _nearest_le_index(idx: pd.DatetimeIndex, ts: pd.Timestamp) -> Optional[pd.Timestamp]:
    s = idx[idx <= ts]
    return s[-1] if len(s) else None

def es_spx_offset_at_anchor(prev_day: date, spx_30m: pd.DataFrame) -> Optional[float]:
    """Δ = ES - SPX at ≤ 3:00 PM anchor; fallbacks ensure historical robustness."""
    spx_anchor_close, spx_anchor_time = get_prev_day_anchor_close_and_time(spx_30m, prev_day)
    if spx_anchor_close is None or spx_anchor_time is None:
        return None

    def try_sym_interval(sym: str, interval: str) -> Optional[float]:
        df = fetch_intraday(sym, prev_day, prev_day, interval)
        if df.empty or "Close" not in df.columns:
            return None
        lo = spx_anchor_time - timedelta(minutes=15)
        hi = spx_anchor_time
        window = df.loc[(df.index >= lo) & (df.index <= hi)]
        if not window.empty:
            es_close = float(window["Close"].iloc[-1])
            return es_close - spx_anchor_close
        idx = _nearest_le_index(df.index, spx_anchor_time)
        if idx is None:
            return None
        es_close = float(df.loc[idx, "Close"])
        return es_close - spx_anchor_close

    for interval in ["1m","5m"]:
        off = try_sym_interval("ES=F", interval)
        if off is not None:
            return float(off)

    es_30m = fetch_intraday("ES=F", prev_day, prev_day, "30m")
    if not es_30m.empty and "Close" in es_30m.columns:
        idx30 = _nearest_le_index(es_30m.index, spx_anchor_time)
        if idx30 is not None:
            return float(es_30m.loc[idx30, "Close"] - spx_anchor_close)

    # Median of the prior 5 trading days (5m)
    med_vals = []
    for i in range(1, 6):
        d = prev_day - timedelta(days=i)
        spx_d = fetch_intraday("^GSPC", d, d, "30m")
        if spx_d.empty:
            spx_d = fetch_intraday("SPY", d, d, "30m")
        s_close, s_time = get_prev_day_anchor_close_and_time(spx_d, d)
        if s_close is None or s_time is None:
            continue
        es5 = fetch_intraday("ES=F", d, d, "5m")
        if not es5.empty and "Close" in es5.columns:
            lo, hi = s_time - timedelta(minutes=15), s_time
            win = es5.loc[(es5.index >= lo) & (es5.index <= hi)]
            if not win.empty:
                med_vals.append(float(win["Close"].iloc[-1] - s_close))
            else:
                idxd = _nearest_le_index(es5.index, s_time)
                if idxd is not None:
                    med_vals.append(float(es5.loc[idxd, "Close"] - s_close))
    if med_vals:
        return float(np.median(med_vals))

    return None

def fetch_overnight_minute(prev_day: date, proj_day: date) -> Tuple[pd.DataFrame, str]:
    """Overnight window prev 17:00 → proj 08:30; return 1m or 5m or 30m last."""
    start = fmt_ct(datetime.combine(prev_day, time(17,0)))
    end   = fmt_ct(datetime.combine(proj_day, time(8,30)))
    es_1m = fetch_intraday("ES=F", prev_day, proj_day, "1m")
    if not es_1m.empty:
        return es_1m.loc[start:end].copy(), "1m"
    es_5m = fetch_intraday("ES=F", prev_day, proj_day, "5m")
    if not es_5m.empty:
        return es_5m.loc[start:end].copy(), "5m"
    es_30m = fetch_intraday("ES=F", prev_day, proj_day, "30m")
    if not es_30m.empty:
        return es_30m.loc[start:end].copy(), "30m"
    return pd.DataFrame(), "none"

def adjust_to_spx_frame(es_df: pd.DataFrame, offset: float) -> pd.DataFrame:
    df = es_df.copy()
    for col in ["Open","High","Low","Close"]:
        if col in df:
            df[col] = df[col] - offset
    return df

def nearest_30m_index(idx_30m: pd.DatetimeIndex, ts: pd.Timestamp) -> Optional[pd.Timestamp]:
    if idx_30m.empty:
        return None
    loc_df = idx_30m[idx_30m <= ts]
    return loc_df[-1] if len(loc_df) else None

# ───────────────────────────────────────────────────────────────────────────────
# DASHBOARD BUILDS
# ───────────────────────────────────────────────────────────────────────────────
def build_probability_dashboard(prev_day: date, proj_day: date,
                                anchor_close: float, anchor_time: datetime,
                                tol_frac: float, weights: Dict[str,int]) -> Tuple[pd.DataFrame, pd.DataFrame, float, str]:
    """Return: touches_df, fan_df, offset_used, used_interval"""
    fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)

    spx_prev_30m = fetch_intraday("^GSPC", prev_day, prev_day, "30m")
    if spx_prev_30m.empty:
        spx_prev_30m = fetch_intraday("SPY", prev_day, prev_day, "30m")

    off = es_spx_offset_at_anchor(prev_day, spx_prev_30m)
    if off is None:
        return pd.DataFrame(), fan_df, 0.0, "none"

    on_bars, used_interval = fetch_overnight_minute(prev_day, proj_day)
    if on_bars.empty:
        return pd.DataFrame(), fan_df, off, "none"

    on_adj = adjust_to_spx_frame(on_bars, off)
    on_adj_30m = resample_to_30m_ct(on_adj)
    detect_df = on_adj if used_interval in ("1m","5m") else on_adj_30m

    top_slope, bottom_slope = current_spx_slopes()
    rows = []
    for ts, bar in detect_df.iterrows():
        blocks = count_effective_blocks(anchor_time, ts)
        top = anchor_close + top_slope * blocks
        bottom = anchor_close - bottom_slope * blocks

        touch = classify_edge_touch(bar, top, bottom)
        if touch is None:
            continue

        idx_30m = nearest_30m_index(on_adj_30m.index, ts)
        if idx_30m is None:
            score, comps = 0, {k:0 for k in ["ema","volume","wick","atr","tod","div"]}
        else:
            score, comps = compute_boosters_score_30m(on_adj_30m, idx_30m, touch["direction_hint"], weights)

        price = float(bar["Close"])
        bias = compute_bias(price, top, bottom, tol_frac)

        rows.append({
            "TimeDT": ts, "Time": ts.strftime("%H:%M"),
            "Price": round(price,2), "Top": round(top,2), "Bottom": round(bottom,2),
            "Edge": touch["edge"], "Case": touch["case"],
            "Expectation": touch["expected"], "DirectionHint": touch["direction_hint"],
            "Bias": bias, "Score": score,
            "EMA_w": comps.get("ema",0), "Vol_w": comps.get("volume",0), "Wick_w": comps.get("wick",0),
            "ATR_w": comps.get("atr",0), "ToD_w": comps.get("tod",0), "Div_w": comps.get("div",0),
        })

    touches_df = pd.DataFrame(rows).sort_values("TimeDT").reset_index(drop=True)
    return touches_df, fan_df, off, used_interval

# ───────────────────────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS
# ───────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🔧 Controls")
today_ct = datetime.now(CT_TZ).date()
prev_day = st.sidebar.date_input("Previous Trading Day", value=today_ct - timedelta(days=1))
proj_day = st.sidebar.date_input("Projection Day", value=prev_day + timedelta(days=1))
st.sidebar.caption("Anchor uses the **last SPX bar ≤ 3:00 PM CT** on the previous session (manual override available).")

st.sidebar.markdown("---")
st.sidebar.subheader("✍️ Manual Anchor (optional)")
use_manual_close = st.sidebar.checkbox("Enter 3:00 PM CT Close Manually", value=False)
manual_close_val = st.sidebar.number_input("Manual 3:00 PM Close", value=6400.00, step=0.01, format="%.2f",
                                           disabled=not use_manual_close)

st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ Advanced (optional)", expanded=False):
    st.caption("Adjust **asymmetric** fan slopes and the within-fan neutrality band.")
    enable_slope = st.checkbox("Enable slope override",
                               value=("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state))
    top_slope_val = st.number_input("Top slope (+ per 30m)",
                                    value=float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT)),
                                    step=0.001, format="%.3f")
    bottom_slope_val = st.number_input("Bottom slope (− per 30m)",
                                       value=float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT)),
                                       step=0.001, format="%.3f")
    tol_frac = st.slider("Neutrality band (% of fan width)", 0, 40, 20, 1) / 100.0

    colA, colB = st.columns(2)
    with colA:
        if st.button("Apply slopes", use_container_width=True, key="apply_slope"):
            if enable_slope:
                st.session_state["top_slope_per_block"] = float(top_slope_val)
                st.session_state["bottom_slope_per_block"] = float(bottom_slope_val)
                st.success(f"Top=+{top_slope_val:.3f}  •  Bottom=−{bottom_slope_val:.3f}")
            else:
                for k in ("top_slope_per_block","bottom_slope_per_block"):
                    st.session_state.pop(k, None)
                st.info("Slope override disabled (using defaults).")
    with colB:
        if st.button("Reset slopes", use_container_width=True, key="reset_slope"):
            for k in ("top_slope_per_block","bottom_slope_per_block"):
                st.session_state.pop(k, None)
            st.success(f"Reset → Top=+{TOP_SLOPE_DEFAULT:.3f} • Bottom=−{BOTTOM_SLOPE_DEFAULT:.3f}")

st.sidebar.markdown("---")
btn_anchor = st.sidebar.button("🔮 Refresh SPX Anchors", type="primary", use_container_width=True, key="btn_anchor")
btn_prob   = st.sidebar.button("🧠 Refresh Probability Board", type="secondary", use_container_width=True, key="btn_prob")

# ───────────────────────────────────────────────────────────────────────────────
# HEADER METRICS
# ───────────────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
now = datetime.now(CT_TZ)
with c1:
    st.markdown(
        f"""
<div class="metric-card">
  <p class="metric-title">Current Time (CT)</p>
  <div class="metric-value">🕒 {now.strftime("%H:%M:%S")}</div>
  <div class="kicker">{now.strftime("%A, %B %d, %Y")}</div>
</div>
""", unsafe_allow_html=True)
with c2:
    is_wkday = now.weekday() < 5
    open_dt = now.replace(hour=8, minute=30, second=0, microsecond=0)
    close_dt = now.replace(hour=14, minute=30, second=0, microsecond=0)
    is_open = is_wkday and (open_dt <= now <= close_dt)
    badge = "badge-open" if is_open else "badge-closed"
    text = "Market Open" if is_open else "Closed"
    st.markdown(
        f"""
<div class="metric-card">
  <p class="metric-title">Market Status</p>
  <div class="metric-value">📊 <span class="{badge}">{text}</span></div>
  <div class="kicker">RTH: 08:30–14:30 CT • Mon–Fri</div>
</div>
""", unsafe_allow_html=True)
with c3:
    ts, bs = current_spx_slopes()
    st.markdown(
        f"""
<div class="metric-card">
  <p class="metric-title">SPX Slopes / 30m</p>
  <div class="metric-value">📐 Top=+{ts:.3f} • Bottom=−{bs:.3f}</div>
  <div class="kicker">Asymmetric fan</div>
  {"<div class='override-tag'>Override active</div>" if ("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state) else ""}
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ───────────────────────────────────────────────────────────────────────────────
# TABS
# ───────────────────────────────────────────────────────────────────────────────
tabAnchors, tabBC, tabProb, tabPlan = st.tabs(
    ["SPX Anchors", "BC Forecast", "Probability Board", "Plan Card"]
)

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 1: SPX ANCHORS                                                          ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabAnchors:
    st.subheader("SPX Anchors — Entries & Exits from Fan (⭐ 8:30 highlight)")

    if btn_anchor:
        with st.spinner("Building anchor fan & strategy…"):
            spx_prev = fetch_intraday("^GSPC", prev_day, prev_day, "30m")
            if spx_prev.empty:
                spx_prev = fetch_intraday("SPY", prev_day, prev_day, "30m")
            if spx_prev.empty:
                st.error("❌ Previous day data missing — can’t compute the anchor.")
                st.stop()

            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time  = fmt_ct(datetime.combine(prev_day, time(15,0)))
            else:
                anchor_close, anchor_time = get_prev_day_anchor_close_and_time(spx_prev, prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("Could not find a ≤3:00 PM CT close for the previous day.")
                    st.stop()

            fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)

            spx_proj = fetch_intraday("^GSPC", proj_day, proj_day, "30m")
            if spx_proj.empty:
                spx_proj = fetch_intraday("SPY", proj_day, proj_day, "30m")
            spx_proj_rth = between_time(spx_proj, RTH_START, RTH_END)

            tslope, bslope = current_spx_slopes()
            rows = []
            iter_index = (spx_proj_rth.index if not spx_proj_rth.empty
                          else pd.DatetimeIndex(rth_slots_ct(proj_day)))
            for dt in iter_index:
                blocks = count_effective_blocks(anchor_time, dt)
                top = anchor_close + tslope * blocks
                bottom = anchor_close - bslope * blocks
                if not spx_proj_rth.empty and dt in spx_proj_rth.index:
                    o = float(spx_proj_rth.loc[dt, "Open"]); c = float(spx_proj_rth.loc[dt, "Close"])
                    h = float(spx_proj_rth.loc[dt, "High"]); l = float(spx_proj_rth.loc[dt, "Low"])
                    price = c
                    bias = compute_bias(price, top, bottom, tol_frac)
                    touch = classify_edge_touch(spx_proj_rth.loc[dt], top, bottom)
                    note = touch["expected"] if touch else "—"
                else:
                    o=h=l=price=np.nan
                    bias = "NO DATA"; note = "Fan only"
                rows.append({
                    "Slot": "⭐ 8:30" if dt.strftime("%H:%M")=="08:30" else "",
                    "Time": dt.strftime("%H:%M"),
                    "Price": (round(price,2) if price==price else np.nan),
                    "Bias": bias, "Top": round(top,2), "Bottom": round(bottom,2),
                    "Fan_Width": round(top-bottom,2),
                    "Note": note
                })
            strat_df = pd.DataFrame(rows)

            st.session_state["anchors"] = {
                "fan_df": fan_df, "strat_df": strat_df,
                "anchor_close": anchor_close, "anchor_time": anchor_time,
                "prev_day": prev_day, "proj_day": proj_day, "tol_frac": tol_frac
            }

    if "anchors" in st.session_state:
        fan_df   = st.session_state["anchors"]["fan_df"]
        strat_df = st.session_state["anchors"]["strat_df"]

        st.markdown("### 🎯 Fan Lines (Top / Bottom @ 30-min)")
        st.dataframe(fan_df[["Time","Top","Bottom","Fan_Width"]], use_container_width=True, hide_index=True)

        st.markdown("### 📋 Strategy Table")
        st.caption("Bias uses within-fan proximity with neutrality band; entries/exits from fan-edge candle logic.")
        st.dataframe(
            strat_df[["Slot","Time","Price","Bias","Top","Bottom","Fan_Width","Note"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Use **Refresh SPX Anchors** in the sidebar.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 2: BC FORECAST  (EXACTLY 2 BOUNCES + ENTRY/EXIT LINES)                  ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabBC:
    st.subheader("BC Forecast — Bounce + Contract Forecast (Asia/Europe → NY 8:30–14:30)")
    st.caption("Requires **exactly 2 bounces** (times + SPX prices). For each contract, provide prices at both bounces and highs after each bounce (with times).")

    # Session window for slot pickers:
    asia_start = fmt_ct(datetime.combine(prev_day, time(19,0)))  # 7PM CT
    euro_end   = fmt_ct(datetime.combine(proj_day, time(7,0)))   # 7AM CT
    session_slots = gen_slots(asia_start, euro_end, 30)
    slot_labels = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]

    with st.form("bc_form_v2", clear_on_submit=False):
        st.markdown("**Underlying bounces (exactly two):**")
        c1, c2 = st.columns(2)
        with c1:
            b1_sel = st.selectbox("Bounce #1 Time (slot)", slot_labels, index=0, key="bc2_b1_sel")
            b1_spx = st.number_input("Bounce #1 SPX Price", value=6500.00, step=0.25, format="%.2f", key="bc2_b1_spx")
        with c2:
            b2_sel = st.selectbox("Bounce #2 Time (slot)", slot_labels, index=min(6, len(slot_labels)-1), key="bc2_b2_sel")
            b2_spx = st.number_input("Bounce #2 SPX Price", value=6512.00, step=0.25, format="%.2f", key="bc2_b2_spx")

        st.markdown("---")
        st.markdown("**Contract A (required)**")
        ca_sym = st.text_input("Contract A Label", value="6525c", key="bc2_ca_sym")
        ca_b1_price = st.number_input("A: Price at Bounce #1", value=10.00, step=0.05, format="%.2f", key="bc2_ca_b1_price")
        ca_b2_price = st.number_input("A: Price at Bounce #2", value=12.50, step=0.05, format="%.2f", key="bc2_ca_b2_price")
        ca_h1_time  = st.selectbox("A: High after Bounce #1 — Time", slot_labels, index=min(2, len(slot_labels)-1), key="bc2_ca_h1_time")
        ca_h1_price = st.number_input("A: High after Bounce #1 — Price", value=14.00, step=0.05, format="%.2f", key="bc2_ca_h1_price")
        ca_h2_time  = st.selectbox("A: High after Bounce #2 — Time", slot_labels, index=min(8, len(slot_labels)-1), key="bc2_ca_h2_time")
        ca_h2_price = st.number_input("A: High after Bounce #2 — Price", value=16.00, step=0.05, format="%.2f", key="bc2_ca_h2_price")

        st.markdown("---")
        st.markdown("**Contract B (optional)**")
        cb_enable = st.checkbox("Add Contract B", value=False, key="bc2_cb_enable")
        if cb_enable:
            cb_sym = st.text_input("Contract B Label", value="6515c", key="bc2_cb_sym")
            cb_b1_price = st.number_input("B: Price at Bounce #1", value=9.50, step=0.05, format="%.2f", key="bc2_cb_b1_price")
            cb_b2_price = st.number_input("B: Price at Bounce #2", value=11.80, step=0.05, format="%.2f", key="bc2_cb_b2_price")
            cb_h1_time  = st.selectbox("B: High after Bounce #1 — Time", slot_labels, index=min(3, len(slot_labels)-1), key="bc2_cb_h1_time")
            cb_h1_price = st.number_input("B: High after Bounce #1 — Price", value=13.30, step=0.05, format="%.2f", key="bc2_cb_h1_price")
            cb_h2_time  = st.selectbox("B: High after Bounce #2 — Time", slot_labels, index=min(9, len(slot_labels)-1), key="bc2_cb_h2_time")
            cb_h2_price = st.number_input("B: High after Bounce #2 — Price", value=15.10, step=0.05, format="%.2f", key="bc2_cb_h2_price")

        submit_bc = st.form_submit_button("📈 Project NY Session (8:30–14:30)")

    if submit_bc:
        try:
            b1_dt = fmt_ct(datetime.strptime(st.session_state["bc2_b1_sel"], "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(st.session_state["bc2_b2_sel"], "%Y-%m-%d %H:%M"))
            if b2_dt <= b1_dt:
                st.error("Bounce #2 must occur after Bounce #1.")
            else:
                # Underlying slope from bounces
                blocks_u = count_effective_blocks(b1_dt, b2_dt)
                u_slope = (float(b2_spx) - float(b1_spx)) / blocks_u if blocks_u > 0 else 0.0

                # Helpers: two-point line projection via 30m blocks
                def project_line(p1_dt, p1_price, p2_dt, p2_price, proj_day, label_proj: str):
                    blocks = count_effective_blocks(p1_dt, p2_dt)
                    slope = (p2_price - p1_price) / blocks if blocks > 0 else 0.0
                    rows = []
                    for slot in rth_slots_ct(proj_day):
                        b = count_effective_blocks(p1_dt, slot)
                        price = p1_price + slope * b
                        rows.append({"Time": slot.strftime("%H:%M"),
                                     label_proj: round(price, 2)})
                    return pd.DataFrame(rows), slope

                # SPX projection from bounces
                rows_u = []
                for slot in rth_slots_ct(proj_day):
                    b = count_effective_blocks(b1_dt, slot)
                    price = float(b1_spx) + u_slope * b
                    rows_u.append({"Time": slot.strftime("%H:%M"),
                                   "SPX_Projected": round(price,2)})
                spx_proj_df = pd.DataFrame(rows_u)
                spx_proj_df.insert(0, "Slot", spx_proj_df["Time"].apply(lambda x: "⭐ 8:30" if x=="08:30" else ""))

                # Contract A — entry line from bounce prices
                ca_entry_df, ca_entry_slope = project_line(
                    b1_dt, float(ca_b1_price), b2_dt, float(ca_b2_price), proj_day, f"{st.session_state['bc2_ca_sym']}_Entry"
                )
                # Contract A — exit line from high times/prices
                ca_h1_dt = fmt_ct(datetime.strptime(st.session_state["bc2_ca_h1_time"], "%Y-%m-%d %H:%M"))
                ca_h2_dt = fmt_ct(datetime.strptime(st.session_state["bc2_ca_h2_time"], "%Y-%m-%d %H:%M"))
                ca_exit_df, ca_exit_slope = project_line(
                    ca_h1_dt, float(ca_h1_price), ca_h2_dt, float(ca_h2_price), proj_day, f"{st.session_state['bc2_ca_sym']}_Exit"
                )

                # Contract B (optional)
                cb_entry_df = cb_exit_df = None
                cb_entry_slope = cb_exit_slope = 0.0
                if cb_enable:
                    cb_entry_df, cb_entry_slope = project_line(
                        b1_dt, float(cb_b1_price), b2_dt, float(cb_b2_price), proj_day, f"{st.session_state['bc2_cb_sym']}_Entry"
                    )
                    cb_h1_dt = fmt_ct(datetime.strptime(st.session_state["bc2_cb_h1_time"], "%Y-%m-%d %H:%M"))
                    cb_h2_dt = fmt_ct(datetime.strptime(st.session_state["bc2_cb_h2_time"], "%Y-%m-%d %H:%M"))
                    cb_exit_df, cb_exit_slope = project_line(
                        cb_h1_dt, float(cb_h1_price), cb_h2_dt, float(cb_h2_price), proj_day, f"{st.session_state['bc2_cb_sym']}_Exit"
                    )

                # Merge into one table
                out = spx_proj_df.merge(ca_entry_df, on="Time", how="left")
                out = out.merge(ca_exit_df, on="Time", how="left")
                # Spread for Contract A
                ca = st.session_state["bc2_ca_sym"]
                out[f"{ca}_Spread"] = out[f"{ca}_Exit"] - out[f"{ca}_Entry"]

                if cb_enable and cb_entry_df is not None and cb_exit_df is not None:
                    cb = st.session_state["bc2_cb_sym"]
                    out = out.merge(cb_entry_df, on="Time", how="left")
                    out = out.merge(cb_exit_df, on="Time", how="left")
                    out[f"{cb}_Spread"] = out[f"{cb}_Exit"] - out[f"{cb}_Entry"]

                # Expected Exit Time (median-duration method) per contract
                def expected_exit_chip(b1_dt, h1_dt, b2_dt, h2_dt):
                    d1 = count_effective_blocks(b1_dt, h1_dt)
                    d2 = count_effective_blocks(b2_dt, h2_dt)
                    durations = [d for d in [d1, d2] if d > 0]
                    if not durations:
                        return "n/a"
                    med_blocks = int(round(np.median(durations)))
                    # Expectation from the later of (b2_dt) into RTH:
                    candidate = b2_dt
                    for _ in range(med_blocks):
                        candidate += timedelta(minutes=30)
                        if is_maintenance(candidate) or in_weekend_gap(candidate):
                            continue
                    # Snap to first RTH slot ≥ candidate
                    for slot in rth_slots_ct(proj_day):
                        if slot >= candidate:
                            return slot.strftime("%H:%M")
                    return "n/a"

                ca_expected = expected_exit_chip(b1_dt, ca_h1_dt, b2_dt, ca_h2_dt)
                if cb_enable:
                    cb_expected = expected_exit_chip(b1_dt, cb_h1_dt, b2_dt, cb_h2_dt)
                else:
                    cb_expected = None

                # Metrics
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"<div class='metric-card'><p class='metric-title'>Underlying Slope /30m</p><div class='metric-value'>📐 {u_slope:+.3f}</div><div class='kicker'>From 2 bounces</div></div>", unsafe_allow_html=True)
                with m2: st.markdown(f"<div class='metric-card'><p class='metric-title'>{ca} Entry Slope /30m</p><div class='metric-value'>📈 {ca_entry_slope:+.3f}</div><div class='kicker'>Exit slope {ca_exit_slope:+.3f} • Expected exit ≈ {ca_expected}</div></div>", unsafe_allow_html=True)
                with m3:
                    if cb_enable:
                        cb = st.session_state["bc2_cb_sym"]
                        st.markdown(f"<div class='metric-card'><p class='metric-title'>{cb} Entry Slope /30m</p><div class='metric-value'>📈 {cb_entry_slope:+.3f}</div><div class='kicker'>Exit slope {cb_exit_slope:+.3f} • Expected exit ≈ {cb_expected}</div></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='metric-card'><p class='metric-title'>Contracts</p><div class='metric-value'>1</div></div>", unsafe_allow_html=True)
                with m4:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>BC Forecast</p><div class='metric-value'>⭐ 8:30 highlighted</div><div class='kicker'>Spread = Exit − Entry</div></div>", unsafe_allow_html=True)

                st.markdown("### 🔮 NY Session Projection (SPX + Contract Entry/Exit Lines)")
                st.dataframe(out, use_container_width=True, hide_index=True)

                st.session_state["bc_result"] = {
                    "table": out, "u_slope": u_slope,
                    "ca_sym": ca, "cb_sym": (st.session_state["bc2_cb_sym"] if cb_enable else None),
                    "ca_expected": ca_expected, "cb_expected": cb_expected
                }

        except Exception as e:
            st.error(f"BC Forecast error: {e}")

    if "bc_result" not in st.session_state:
        st.info("Fill the form and click **Project NY Session**.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 3: PROBABILITY BOARD                                                    ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabProb:
    st.subheader("Probability Board — Overnight Edge Confidence")

    left, right = st.columns(2)
    with left:
        enable_div = st.checkbox("Enable Oscillator Divergence (30m, lightweight)", value=False, key="prob_enable_div")
    with right:
        w_ema  = st.slider("Weight: EMA 8/21 (30m)", 0, 40, WEIGHTS_DEFAULT["ema"], 5, key="prob_w_ema")
        w_vol  = st.slider("Weight: Volume (30m)", 0, 40, WEIGHTS_DEFAULT["volume"], 5, key="prob_w_vol")
        w_wick = st.slider("Weight: Wick/Body (30m)", 0, 40, WEIGHTS_DEFAULT["wick"], 5, key="prob_w_wick")
        w_atr  = st.slider("Weight: ATR (30m)", 0, 40, WEIGHTS_DEFAULT["atr"], 5, key="prob_w_atr")
        w_tod  = st.slider("Weight: Time-of-Day", 0, 40, WEIGHTS_DEFAULT["tod"], 5, key="prob_w_tod")
        w_div  = st.slider("Weight: Divergence (if enabled)", 0, 40, 10 if enable_div else 0, 5,
                           disabled=not enable_div, key="prob_w_div")

    if btn_prob:
        with st.spinner("Scoring overnight edge interactions…"):
            spx_prev = fetch_intraday("^GSPC", prev_day, prev_day, "30m")
            if spx_prev.empty:
                spx_prev = fetch_intraday("SPY", prev_day, prev_day, "30m")
            if spx_prev.empty:
                st.error("Could not fetch previous day SPX data.")
                st.stop()

            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time  = fmt_ct(datetime.combine(prev_day, time(15,0)))
            else:
                anchor_close, anchor_time = get_prev_day_anchor_close_and_time(spx_prev, prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("Could not find a ≤3:00 PM CT close for the previous day.")
                    st.stop()

            custom_weights = {
                "ema": st.session_state["prob_w_ema"],
                "volume": st.session_state["prob_w_vol"],
                "wick": st.session_state["prob_w_wick"],
                "atr": st.session_state["prob_w_atr"],
                "tod": st.session_state["prob_w_tod"],
                "div": (st.session_state["prob_w_div"] if st.session_state["prob_enable_div"] else 0)
            }

            touches_df, fan_df, offset_used, used_interval = build_probability_dashboard(
                prev_day, proj_day, anchor_close, anchor_time, tol_frac, custom_weights
            )

            st.session_state["prob_result"] = {
                "touches_df": touches_df, "fan_df": fan_df,
                "offset_used": float(offset_used), "used_interval": used_interval,
                "anchor_close": anchor_close, "anchor_time": anchor_time,
                "prev_day": prev_day, "proj_day": proj_day,
                "weights": custom_weights, "tol_frac": tol_frac
            }

    if "prob_result" in st.session_state:
        pr = st.session_state["prob_result"]
        touches_df = pr["touches_df"]

        cA, cB, cC = st.columns(3)
        with cA:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Anchor Close (Prev ≤3:00 PM)</p><div class='metric-value'>💠 {pr['anchor_close']:.2f}</div></div>", unsafe_allow_html=True)
        with cB:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Overnight Edge Touches</p><div class='metric-value'>🧩 {len(touches_df)}</div></div>", unsafe_allow_html=True)
        with cC:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>ES→SPX Offset</p><div class='metric-value'>Δ {pr['offset_used']:+.2f}</div><div class='kicker'>Data: {pr['used_interval']}</div></div>", unsafe_allow_html=True)

        st.markdown("### 📡 Overnight Edge Interactions (Scored)")
        if pr["used_interval"] == "none":
            st.info("ES→SPX offset or overnight prints were unavailable even after fallbacks. Try a nearby date.")
        if touches_df.empty:
            st.info("No qualifying edge touches detected for this window.")
        else:
            view_cols = ["Time","Price","Top","Bottom","Bias","Edge","Case","Expectation","Score","EMA_w","Vol_w","Wick_w","ATR_w","ToD_w","Div_w"]
            st.dataframe(touches_df[view_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Use **Refresh Probability Board** in the sidebar.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 4: PLAN CARD                                                            ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabPlan:
    st.subheader("Plan Card — 8:25 Session Prep")

    ready = ("anchors" in st.session_state) and ("prob_result" in st.session_state)
    if not ready:
        st.info("Generate **SPX Anchors** and **Probability Board** first. (BC Forecast optional but recommended.)")
    else:
        an = st.session_state["anchors"]
        pr = st.session_state["prob_result"]
        bc = st.session_state.get("bc_result", None)

        # Headline metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='metric-card'><p class='metric-title'>Anchor Close</p><div class='metric-value'>💠 {an['anchor_close']:.2f}</div><div class='kicker'>Prev ≤ 3:00 PM CT</div></div>", unsafe_allow_html=True)
        with m2: 
            w830 = an['fan_df'].loc[an['fan_df']['Time']=='08:30','Fan_Width']
            fan_w = float(w830.iloc[0]) if not w830.empty else np.nan
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Fan Width @ 8:30</p><div class='metric-value'>🧭 {fan_w:.2f}</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-card'><p class='metric-title'>Offset</p><div class='metric-value'>Δ {pr['offset_used']:+.2f}</div><div class='kicker'>Overnight basis</div></div>", unsafe_allow_html=True)
        with m4:
            tdf = pr["touches_df"]
            readiness = int(np.mean(sorted(tdf["Score"].tolist(), reverse=True)[:3])) if not tdf.empty else 0
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Readiness</p><div class='metric-value'>🔥 {readiness}</div><div class='kicker'>0–100</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        colL, colR = st.columns(2)
        with colL:
            st.markdown("### 🎯 Primary Setup (from Anchors)")
            srow = an["strat_df"][an["strat_df"]["Time"]=="08:30"]
            if not srow.empty:
                srow = srow.iloc[0]
                st.write(f"- **8:30 Bias:** {srow['Bias']}")
                st.write(f"- **8:30 Fan:** Top {srow['Top']:.2f} / Bottom {srow['Bottom']:.2f} (width {srow['Fan_Width']:.2f})")
                st.write(f"- **Edge Note:** {srow['Note']}")
            else:
                st.write("- 8:30 row not available; see Strategy Table.")

            st.markdown("### 🧠 Probability Notes (overnight)")
            if not pr["touches_df"].empty:
                top_touch = pr["touches_df"].sort_values("Score", ascending=False).head(3)
                for _, r in top_touch.iterrows():
                    st.write(f"- {r['Time']}: **{r['Edge']}** {r['Case']} → *{r['Expectation']}* (Score {r['Score']})")
            else:
                st.write("- No scored touches for this date.")

        with colR:
            st.markdown("### 💼 Trade Plan (guide)")
            if bc and "table" in bc:
                t = bc["table"]
                row830 = t[t["Time"]=="08:30"].head(1)
                if not row830.empty:
                    st.write(f"- **SPX @ 8:30:** {float(row830['SPX_Projected']):.2f}")
                    ca = bc["ca_sym"]; cb = bc.get("cb_sym")
                    if f"{ca}_Entry" in row830:
                        st.write(f"- **{ca} Entry @ 8:30:** {float(row830[f'{ca}_Entry']):.2f}")
                    if f"{ca}_Exit" in row830:
                        st.write(f"- **{ca} ExitRef @ 8:30:** {float(row830[f'{ca}_Exit']):.2f}")
                    if cb:
                        if f"{cb}_Entry" in row830:
                            st.write(f"- **{cb} Entry @ 8:30:** {float(row830[f'{cb}_Entry']):.2f}")
                        if f"{cb}_Exit" in row830:
                            st.write(f"- **{cb} ExitRef @ 8:30:** {float(row830[f'{cb}_Exit']):.2f}")
                    # Expected exit time chips
                    if bc.get("ca_expected") and bc["ca_expected"] != "n/a":
                        st.write(f"- **{ca} expected exit ≈ {bc['ca_expected']}**")
                    if cb and bc.get("cb_expected") and bc["cb_expected"] != "n/a":
                        st.write(f"- **{cb} expected exit ≈ {bc['cb_expected']}**")
                else:
                    st.write("- BC Forecast 8:30 not available.")

            st.write("- **Invalidation:** Flip bias if candle close violates the opposite edge with confirming wick/body.")
            st.write("- **Targets:** Opposite fan edge; contract exit refs (from BC Forecast).")
            st.write("- **Sizing:** Scale with Readiness (e.g., 0–40 small, 40–70 medium, 70–100 full).")

# ───────────────────────────────────────────────────────────────────────────────
# FOOTER
# ───────────────────────────────────────────────────────────────────────────────
st.markdown("---")
colF1, colF2 = st.columns([1,2])
with colF1:
    if st.button("🔌 Test Data Connection"):
        td = fetch_intraday("^GSPC", today_ct - timedelta(days=3), today_ct, "30m")
        if td.empty:
            td = fetch_intraday("SPY", today_ct - timedelta(days=3), today_ct, "30m")
        if not td.empty:
            st.success(f"OK — received {len(td)} bars (30m).")
        else:
            st.error("Data fetch failed — try different dates.")
with colF2:
    st.caption("SPX Prophet • SPX-only • Fan Top +0.312 / Bottom −0.25 per 30m • ES→SPX offset ladder • ⭐ 8:30 focus")