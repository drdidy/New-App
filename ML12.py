# app.py
# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 SPX PROPHET — Enterprise App
# (SPX Fan Anchors • Probability Dashboard • Stock Anchors • Signals • Contract Tool)
# - Anchor: exact 3:00 PM CT previous-day SPX close (manual override supported)
# - SPX fan uses ASYMMETRIC slopes per 30m: Top +0.31, Bottom −0.25 (overrideable)
# - Block counter skips 4–5 PM CT maintenance & Fri 5 PM → Sun 5 PM weekend gap
# - Probability Dashboard uses overnight data (offset-aligned) to score edge tests
# - Bias logic uses descending anchor (Bottom line) + within-fan proximity tolerance
# - Contract projections integrated from Probability Dashboard touch rows
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple

# ───────────────────────────────────────────────────────────────────────────────
# CORE CONFIG
# ───────────────────────────────────────────────────────────────────────────────
CT_TZ = pytz.timezone("America/Chicago")
RTH_START = "08:30"
RTH_END   = "14:30"

# Default per-30m slopes (SPX fan)
TOP_SLOPE_DEFAULT    = 0.31   # Top line +0.31 per 30m
BOTTOM_SLOPE_DEFAULT = 0.25   # Bottom line −0.25 per 30m

# Per-ticker slope magnitudes (for Stock Anchors tab)
STOCK_SLOPES = {
    "TSLA": 0.0285, "NVDA": 0.0860, "AAPL": 0.0155, "MSFT": 0.0541,
    "AMZN": 0.0139, "GOOGL": 0.0122, "META": 0.0674, "NFLX": 0.0230,
}

# Probability weights (sum may reach 100)
WEIGHTS = {
    "ema": 20,          # EMA(8/21) on 1-min alignment with expected move
    "volume": 25,       # Volume spike confirming rejection/break
    "wick": 20,         # Wick/Body rejection geometry
    "atr": 15,          # ATR context (low=hold, high=break)
    "tod": 20,          # Time-of-day weighting (8:30, 10:00, 13:30)
    "div": 0,           # Optional oscillator divergence (kept default 0; user can enable)
}

# Time-of-day anchor minutes for weighting (±window minutes)
KEY_TOD = [(8,30), (10,0), (13,30)]
KEY_TOD_WINDOW_MIN = 7

# Wick sensitivity
WICK_MIN_RATIO = 0.6  # wick length vs body length in "rejection" direction

# ATR config
ATR_LOOKBACK = 14     # periods (on 1-min)
ATR_HIGH_PCTL = 70    # above this percentile → "high ATR"
ATR_LOW_PCTL  = 30    # below this percentile → "low ATR"

# RSI config for lightweight divergence
RSI_LEN = 14
RSI_WINDOW_MIN = 30  # lookback minutes for a prior swing

# ───────────────────────────────────────────────────────────────────────────────
# PAGE & THEME (light, enterprise vibe with glassy cards)
# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🔮 SPX Prophet Analytics (Enterprise)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
  --brand: #2563eb;      /* blue-600 */
  --brand-2: #10b981;    /* emerald-500 */
  --surface: #ffffff;
  --muted: #f8fafc;      /* slate-50 */
  --text: #0f172a;       /* slate-900 */
  --subtext: #475569;    /* slate-600 */
  --border: #e2e8f0;     /* slate-200 */
  --warn: #f59e0b;       /* amber-500 */
  --danger: #ef4444;     /* red-500 */
}

html, body, [class*="css"]  { background: var(--muted); color: var(--text); }
.block-container { padding-top: 1.1rem; }
h1, h2, h3 { color: var(--text); }

.card, .metric-card {
  background: rgba(255,255,255,0.9);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 12px 32px rgba(2,6,23,0.07);
  backdrop-filter: blur(8px);
}
.metric-title { font-size: 0.9rem; color: var(--subtext); margin: 0; }
.metric-value { font-size: 1.8rem; font-weight: 700; margin-top: 6px; }
.kicker { font-size: 0.8rem; color: var(--subtext); }

.badge-open {
  color: #065f46; background: #d1fae5; border: 1px solid #99f6e4;
  padding: 2px 8px; border-radius: 999px; font-size: 0.8rem; font-weight: 600;
}
.badge-closed {
  color: #7c2d12; background: #ffedd5; border: 1px solid #fed7aa;
  padding: 2px 8px; border-radius: 999px; font-size: 0.8rem; font-weight: 600;
}

hr { border-top: 1px solid var(--border); }
.dataframe { background: var(--surface); border-radius: 12px; overflow: hidden; }
.small-note { color: var(--subtext); font-size: 0.85rem; }

.override-tag {
  font-size: 0.75rem; color: #334155; background: #e2e8f0; border: 1px solid #cbd5e1;
  padding: 2px 8px; border-radius: 999px; display:inline-block; margin-top:6px;
}
.badge-slot {
  color:#1f2937; background:#e2e8f0; border:1px solid #cbd5e1;
  padding:2px 8px; border-radius:999px; font-size:0.75rem; font-weight:600;
}
</style>
""",
    unsafe_allow_html=True,
)

# ───────────────────────────────────────────────────────────────────────────────
# HELPERS
# ───────────────────────────────────────────────────────────────────────────────
def fmt_ct(dt: datetime) -> datetime:
    """Ensure timezone-aware CT."""
    if dt.tzinfo is None:
        return CT_TZ.localize(dt)
    return dt.astimezone(CT_TZ)

def between_time(df: pd.DataFrame, start_str: str, end_str: str) -> pd.DataFrame:
    return df.between_time(start_str, end_str) if not df.empty else df

def rth_slots_ct(target_date: date) -> List[datetime]:
    start_dt = fmt_ct(datetime.combine(target_date, time(8, 30)))
    end_dt   = fmt_ct(datetime.combine(target_date, time(14, 30)))
    slots = []
    cur = start_dt
    while cur <= end_dt:
        slots.append(cur)
        cur += timedelta(minutes=30)
    return slots

def is_maintenance(dt: datetime) -> bool:
    """True for 4–5 PM CT maintenance hour."""
    return dt.hour == 16

def in_weekend_gap(dt: datetime) -> bool:
    """True for Fri >= 17:00 → Sun < 17:00 CT (no overnight session counted)."""
    wd = dt.weekday()  # Mon=0 ... Sun=6
    if wd == 5: return True                         # Saturday
    if wd == 6 and dt.hour < 17: return True        # Sunday before 5pm CT
    if wd == 4 and dt.hour >= 17: return True       # Friday from 5pm CT onward
    return False

def count_effective_blocks(anchor_time: datetime, target_time: datetime) -> float:
    """Count 30-min blocks from anchor_time → target_time skipping maintenance/weekend."""
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
    required = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in df.columns for c in required):
        return pd.DataFrame()
    return df

def normalize_to_ct(df: pd.DataFrame, start_d: date, end_d: date) -> pd.DataFrame:
    if df.empty:
        return df
    df = ensure_ohlc_cols(df)
    if df.empty:
        return df
    if df.index.tz is None:
        # yfinance usually returns US/Eastern
        df.index = df.index.tz_localize("US/Eastern")
    df.index = df.index.tz_convert(CT_TZ)
    sdt = fmt_ct(datetime.combine(start_d, time(0, 0)))
    edt = fmt_ct(datetime.combine(end_d, time(23, 59)))
    return df.loc[sdt:edt]

@st.cache_data(ttl=120)
def fetch_intraday(symbol: str, start_d: date, end_d: date) -> pd.DataFrame:
    """Robust intraday fetch, 30m, CT index, pre/post ON; fall back to period-based."""
    try:
        t = yf.Ticker(symbol)
        df = t.history(
            start=(start_d - timedelta(days=5)).strftime("%Y-%m-%d"),
            end=(end_d + timedelta(days=2)).strftime("%Y-%m-%d"),
            interval="30m", prepost=True, auto_adjust=False, back_adjust=False,
        )
        df = normalize_to_ct(df, start_d, end_d)
        if df.empty:
            days = max(7, (end_d - start_d).days + 7)
            df2 = t.history(
                period=f"{days}d", interval="30m",
                prepost=True, auto_adjust=False, back_adjust=False,
            )
            df = normalize_to_ct(df2, start_d, end_d)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=120)
def fetch_intraday_interval(symbol: str, start_d: date, end_d: date, interval: str) -> pd.DataFrame:
    """Interval-aware fetch. 1m/5m need period windows per yfinance limits."""
    try:
        t = yf.Ticker(symbol)
        if interval in ["1m", "2m", "5m", "15m"]:
            days = max(1, min(7, (end_d - start_d).days + 2))
            df = t.history(period=f"{days}d", interval=interval,
                           prepost=True, auto_adjust=False, back_adjust=False)
            df = normalize_to_ct(df, start_d - timedelta(days=1), end_d + timedelta(days=1))
            sdt = fmt_ct(datetime.combine(start_d, time(0, 0)))
            edt = fmt_ct(datetime.combine(end_d, time(23, 59)))
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

def get_prev_day_3pm_close(df_30m: pd.DataFrame, prev_day: date) -> Optional[float]:
    """Get the 3:00 PM CT bar close for prev_day; else last bar ≤ 15:00."""
    if df_30m.empty:
        return None
    day_start = fmt_ct(datetime.combine(prev_day, time(0, 0)))
    day_end   = fmt_ct(datetime.combine(prev_day, time(23, 59)))
    d = df_30m.loc[day_start:day_end].copy()
    if d.empty:
        return None
    target = fmt_ct(datetime.combine(prev_day, time(15, 0)))
    if target in d.index:
        return float(d.loc[target, "Close"])
    prior = d.loc[:target]
    if not prior.empty:
        return float(prior.iloc[-1]["Close"])
    return None

# ───── Slopes state (SPX fan only; top and bottom may differ)
def current_spx_slopes() -> Tuple[float, float]:
    top = float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT))
    bottom = float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT))
    return top, bottom

# ───── SPX Fan Projection (asymmetric slopes)
def project_fan_from_close(close_price: float, anchor_time: datetime, target_day: date) -> pd.DataFrame:
    top_slope, bottom_slope = current_spx_slopes()
    rows = []
    for slot in rth_slots_ct(target_day):
        blocks = count_effective_blocks(anchor_time, slot)
        top = close_price + top_slope * blocks
        bot = close_price - bottom_slope * blocks
        rows.append({"TimeDT": slot, "Time": slot.strftime("%H:%M"),
                     "Top": round(top, 2), "Bottom": round(bot, 2),
                     "Fan_Width": round(top - bot, 2)})
    return pd.DataFrame(rows)

# ───── EMA / RSI utils
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def compute_ema_cross_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Close" not in df:
        return pd.DataFrame()
    out = df.copy()
    out["EMA8"] = ema(out["Close"], 8)
    out["EMA21"] = ema(out["Close"], 21)
    out["Crossover"] = np.where(out["EMA8"] > out["EMA21"], "Bullish",
                         np.where(out["EMA8"] < out["EMA21"], "Bearish", "None"))
    return out

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
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

# ───────────────────────────────────────────────────────────────────────────────
# BIAS / EDGE LOGIC
# ───────────────────────────────────────────────────────────────────────────────
def compute_bias(price: float, top: float, bottom: float, tol_frac: float) -> str:
    """
    Dynamic bias:
    - If inside fan:
        - Nearer Bottom (descending anchor) → UP
        - Nearer Top (ascending anchor) → DOWN
        - Within center band (±tol_frac*width) → NO BIAS
    - If outside fan → no bias here (edge logic decides action)
    """
    if bottom <= price <= top:
        width = top - bottom
        center = (top + bottom) / 2.0
        band = tol_frac * width
        if price >= center - band and price <= center + band:
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
    Return dict when bar touches an edge; else None.
    Implements the user's decision tree:
    - TOP:
        a) Bearish candle touches Top and closes bearish inside → expect breakdown to Bottom (then buy from Bottom)
        b) Bearish candle touches Top but closes above fan → Top holds as support → buy higher from Top
    - BOTTOM:
        c) Bullish candle touches Bottom and closes bullish inside → expect breakout to Top (then sell from Top)
        d) Bullish candle touches Bottom but closes below fan → Bottom fails → sell further down
    """
    o = float(bar.get("Open", np.nan))
    h = float(bar.get("High", np.nan))
    l = float(bar.get("Low", np.nan))
    c = float(bar.get("Close", np.nan))
    cls = candle_class(o, c)

    inside = (bottom <= c <= top)
    above  = (c > top)
    below  = (c < bottom)

    # Touch Top?
    if touched_line(l, h, top) and cls == "Bearish":
        if inside:
            return {"edge":"Top","case":"TopTouch_BearishClose_Inside",
                    "expected":"Breakdown to Bottom → plan to BUY from Bottom",
                    "direction_hint":"DownToBottomThenBuy"}
        if above:
            return {"edge":"Top","case":"TopTouch_BearishClose_Above",
                    "expected":"Top holds as support → market buys higher",
                    "direction_hint":"BuyHigherFromTop"}

    # Touch Bottom?
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
def compute_boosters_score(df_1m: pd.DataFrame,
                           idx: pd.Timestamp,
                           expected_hint: str,
                           weights: Dict[str,int]) -> Tuple[int, Dict[str,int]]:
    """
    Evaluate booster signals at 'idx' (bar index) and return (score, components).
    - EMA(8/21): alignment with expected move
    - Volume spike: volume > rolling mean (x%)
    - Wick/Body rejection: long wick in expected direction
    - ATR context: low ATR → hold; high ATR → break
    - Time-of-day: within window of key times
    - Divergence (lightweight): optional (0 weight default)
    """
    comps = {k:0 for k in ["ema","volume","wick","atr","tod","div"]}

    if idx not in df_1m.index:  # safety
        return 0, comps

    # Slice up to idx for rolling stats
    upto = df_1m.loc[:idx].copy()
    if upto.shape[0] < 20:
        return 0, comps

    # EMA
    ema8 = ema(upto["Close"], 8)
    ema21 = ema(upto["Close"], 21)
    ema_state = "Bullish" if ema8.iloc[-1] > ema21.iloc[-1] else ("Bearish" if ema8.iloc[-1] < ema21.iloc[-1] else "None")
    # Map expected direction hint to needed EMA
    # Hints: DownToBottomThenBuy (near-term down), BuyHigherFromTop (up), UpToTopThenSell (up), SellFurtherDown (down)
    expected_near_term = "Up" if expected_hint in ("BuyHigherFromTop","UpToTopThenSell") else "Down"
    if (expected_near_term == "Up" and ema_state == "Bullish") or (expected_near_term == "Down" and ema_state == "Bearish"):
        comps["ema"] = weights.get("ema",0)

    # Volume spike vs rolling mean(20)
    vol = upto["Volume"]
    if vol.notna().all() and vol.iloc[-1] > vol.rolling(20).mean().iloc[-1] * 1.15:
        comps["volume"] = weights.get("volume",0)

    # Wick/Body rejection
    bar = upto.iloc[-1]
    o,h,l,c = float(bar["Open"]), float(bar["High"]), float(bar["Low"]), float(bar["Close"])
    body = abs(c - o) + 1e-9
    upper_wick = max(0.0, h - max(o,c))
    lower_wick = max(0.0, min(o,c) - l)
    if expected_near_term == "Up":
        if lower_wick / body >= WICK_MIN_RATIO:
            comps["wick"] = weights.get("wick",0)
    else:  # Down
        if upper_wick / body >= WICK_MIN_RATIO:
            comps["wick"] = weights.get("wick",0)

    # ATR context
    tr = true_range(upto)
    atr = tr.rolling(ATR_LOOKBACK).mean()
    if atr.notna().sum() >= ATR_LOOKBACK:
        last_atr = float(atr.iloc[-1])
        pct = (atr.rank(pct=True).iloc[-1]) * 100.0
        # Interpret: low ATR → edges hold; high ATR → breaks succeed
        if expected_hint in ("BuyHigherFromTop","UpToTopThenSell"):  # "hold then move" flavor
            if pct <= ATR_LOW_PCTL:
                comps["atr"] = weights.get("atr",0)
        elif expected_hint in ("SellFurtherDown","DownToBottomThenBuy"):
            # If near-term is down or break lower, high ATR helps continuation
            if pct >= ATR_HIGH_PCTL:
                comps["atr"] = weights.get("atr",0)

    # Time-of-day
    ts = fmt_ct(idx.to_pydatetime())
    if any(abs((ts.hour*60 + ts.minute) - (hh*60+mm)) <= KEY_TOD_WINDOW_MIN for (hh,mm) in KEY_TOD):
        comps["tod"] = weights.get("tod",0)

    # Oscillator divergence (lightweight proxy)
    if weights.get("div",0) > 0:
        r = rsi(upto["Close"], RSI_LEN)
        if r.notna().sum() >= RSI_LEN + 2:
            # compare to approx prior swing in last RSI_WINDOW_MIN
            window_bars = max(5, RSI_WINDOW_MIN)  # on 1m
            prior = upto.iloc[-window_bars:-1] if upto.shape[0] > window_bars else upto.iloc[:-1]
            if prior.shape[0] > 5:
                prior_low = prior["Close"].idxmin()
                prior_high = prior["Close"].idxmax()
                if expected_near_term == "Up":
                    # bullish divergence: price <= prior low but RSI higher
                    if upto["Close"].iloc[-1] <= prior["Close"].min() and r.iloc[-1] > r.loc[prior_low]:
                        comps["div"] = weights.get("div",0)
                else:
                    # bearish divergence: price >= prior high but RSI lower
                    if upto["Close"].iloc[-1] >= prior["Close"].max() and r.iloc[-1] < r.loc[prior_high]:
                        comps["div"] = weights.get("div",0)

    score = sum(comps.values())
    score = int(min(100, max(0, score)))
    return score, comps

# ───────────────────────────────────────────────────────────────────────────────
# PROBABILITY DASHBOARD (overnight analysis)
# ───────────────────────────────────────────────────────────────────────────────
def es_spx_offset_at_3pm(prev_day: date, spx_30m: pd.DataFrame) -> Optional[float]:
    """
    Compute ES–SPX offset at 3:00 PM CT (same timestamp),
    using ES=F 1m around 3 PM to find a close.
    """
    # SPX 3 PM
    spx_close = get_prev_day_3pm_close(spx_30m, prev_day)
    if spx_close is None:
        return None
    # ES around 3 PM (1m)
    es_1m = fetch_intraday_interval("ES=F", prev_day, prev_day, "1m")
    if es_1m.empty:
        return None
    t3 = fmt_ct(datetime.combine(prev_day, time(15,0)))
    if t3 in es_1m.index:
        es_close = float(es_1m.loc[t3, "Close"])
    else:
        # nearest <= 3:00
        es_close = float(es_1m.loc[:t3]["Close"].iloc[-1])
    return float(es_close - spx_close)

def fetch_overnight_1m(prev_day: date, proj_day: date) -> pd.DataFrame:
    """
    1-minute data covering the overnight window (roughly 17:00 prev → 08:30 proj).
    """
    es_1m = fetch_intraday_interval("ES=F", prev_day, proj_day, "1m")
    if es_1m.empty:
        return pd.DataFrame()
    # Overnight window (skip weekend/maintenance implicitly by yfinance trading hours)
    start = fmt_ct(datetime.combine(prev_day, time(17, 0)))
    end   = fmt_ct(datetime.combine(proj_day, time(8, 30)))
    return es_1m.loc[start:end].copy()

def adjust_to_spx_frame(es_df: pd.DataFrame, offset: float) -> pd.DataFrame:
    """
    Adjust ES prices by subtracting the 3 PM offset so they can be compared to SPX fan.
    We keep the label generic (no UI mention), just using adjusted prices internally.
    """
    df = es_df.copy()
    for col in ["Open","High","Low","Close"]:
        if col in df:
            df[col] = df[col] - offset
    return df

def build_probability_dashboard(prev_day: date,
                                proj_day: date,
                                anchor_close: float,
                                anchor_time: datetime,
                                tol_frac: float,
                                weights: Dict[str,int]) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Returns:
      touches_df: detailed per-touch scoring rows
      fan_df:     SPX fan for proj day (for 8:30 highlight and reference)
      offset:     ES–SPX offset used
    """
    # Fan for proj day (RTH)
    fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)

    # Build offset from prev day 3 PM
    spx_prev_30m = fetch_intraday("^GSPC", prev_day, prev_day)
    if spx_prev_30m.empty:
        spx_prev_30m = fetch_intraday("SPY", prev_day, prev_day)
    off = es_spx_offset_at_3pm(prev_day, spx_prev_30m)
    if off is None:
        return pd.DataFrame(), fan_df, 0.0

    # Overnight 1m (adjusted to SPX frame)
    on_1m = fetch_overnight_1m(prev_day, proj_day)
    if on_1m.empty:
        return pd.DataFrame(), fan_df, off
    on_adj = adjust_to_spx_frame(on_1m, off)

    # For each 1m bar, compute matching fan lines based on blocks since anchor
    # Note: anchor_time is prev_day 15:00 CT exact
    top_slope, bottom_slope = current_spx_slopes()
    rows = []
    # Precompute rolling for boosters
    on_adj_booster = on_adj.copy()

    for ts, bar in on_adj.iterrows():
        blocks = count_effective_blocks(anchor_time, ts)
        top = anchor_close + top_slope * blocks
        bottom = anchor_close - bottom_slope * blocks

        # Edge touch classification per our tree
        touch = classify_edge_touch(bar, top, bottom)
        if touch is None:
            continue

        # Probability boosters & score
        score, comps = compute_boosters_score(on_adj_booster, ts, touch["direction_hint"], weights)

        # Bias at that minute (within-fan rule using tolerance)
        price = float(bar["Close"])
        bias = compute_bias(price, top, bottom, tol_frac)

        rows.append({
            "TimeDT": ts, "Time": ts.strftime("%H:%M"),
            "Price": round(price,2), "Top": round(top,2), "Bottom": round(bottom,2),
            "Edge": touch["edge"], "Case": touch["case"],
            "Expectation": touch["expected"],
            "DirectionHint": touch["direction_hint"],
            "Bias": bias,
            "Score": score,
            "EMA_w": comps["ema"], "Vol_w": comps["volume"], "Wick_w": comps["wick"],
            "ATR_w": comps["atr"], "ToD_w": comps["tod"], "Div_w": comps["div"],
        })

    touches_df = pd.DataFrame(rows).sort_values("TimeDT").reset_index(drop=True)
    return touches_df, fan_df, off

# ───────────────────────────────────────────────────────────────────────────────
# STOCK ANCHORS (existing)
# ───────────────────────────────────────────────────────────────────────────────
def detect_absolute_swings(df: pd.DataFrame) -> Tuple[Optional[Tuple[float, datetime]], Optional[Tuple[float, datetime]]]:
    if df.empty:
        return None, None
    hi = df['High'].idxmax() if 'High' in df else None
    lo = df['Low'].idxmin() if 'Low' in df else None
    high = (float(df.loc[hi, 'High']), hi) if hi is not None else None
    low  = (float(df.loc[lo, 'Low']),  lo) if lo is not None else None
    return high, low

def project_two_stock_lines(high_price: float, high_time: datetime,
                            low_price: float, low_time: datetime,
                            slope_mag: float, target_day: date) -> pd.DataFrame:
    rows = []
    for slot in rth_slots_ct(target_day):
        b_high = count_effective_blocks(high_time, slot)
        b_low  = count_effective_blocks(low_time,  slot)
        high_asc = high_price + slope_mag * b_high
        low_desc = low_price  - slope_mag * b_low
        rows.append({"Time": slot.strftime("%H:%M"),
                     "High_Asc": round(high_asc, 2),
                     "Low_Desc": round(low_desc, 2)})
    return pd.DataFrame(rows)

# ───────────────────────────────────────────────────────────────────────────────
# CONTRACT PROJECTIONS (Two-Point and Δ+Θ)
# ───────────────────────────────────────────────────────────────────────────────
def project_contract_two_point(p1_dt: datetime, p1_price: float,
                               p2_dt: Optional[datetime], p2_price: Optional[float],
                               proj_day: date) -> Tuple[pd.DataFrame, float, float]:
    """
    Two-point slope (fallback to single point → flat if no p2).
    """
    if p2_dt is not None and p2_price is not None and p2_dt > p1_dt:
        blocks = count_effective_blocks(p1_dt, p2_dt)
        slope = (p2_price - p1_price) / blocks if blocks > 0 else 0.0
    else:
        slope = 0.0
    rows = []
    for slot in rth_slots_ct(proj_day):
        b = count_effective_blocks(p1_dt, slot)
        price = p1_price + slope * b
        rows.append({"Time": slot.strftime("%H:%M"),
                     "Contract_Price": round(price, 2),
                     "Blocks": round(b, 1)})
    return pd.DataFrame(rows), slope, float(count_effective_blocks(p1_dt, fmt_ct(datetime.combine(proj_day, time(8,30)))))

def project_contract_delta_theta(p1_dt: datetime, p1_price: float,
                                 underlying_slope_per_30m: float,
                                 delta: float, theta_per_day: float,
                                 proj_day: date) -> Tuple[pd.DataFrame, float]:
    """
    Δ+Θ model:
    Contract slope per 30m ≈ Δ * underlying_slope_per_30m + Θ_per_30m
    Θ_per_30m ≈ theta_per_day / ( (6 hours RTH = 12 blocks) or 48 blocks/day ) → we’ll use 48 blocks/day for simplicity.
    """
    theta_per_30m = theta_per_day / 48.0
    contract_slope = delta * underlying_slope_per_30m + theta_per_30m
    rows = []
    for slot in rth_slots_ct(proj_day):
        b = count_effective_blocks(p1_dt, slot)
        price = p1_price + contract_slope * b
        rows.append({"Time": slot.strftime("%H:%M"),
                     "Contract_Price": round(price, 2),
                     "Blocks": round(b, 1)})
    return pd.DataFrame(rows), contract_slope

# ───────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Global controls (SPX panel)
# ───────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🔧 Controls")

today_ct = datetime.now(CT_TZ).date()
prev_day = st.sidebar.date_input("Previous Trading Day", value=today_ct - timedelta(days=1))
proj_day = st.sidebar.date_input("Projection Day", value=prev_day + timedelta(days=1))
st.sidebar.caption("Anchor at **3:00 PM CT** on the previous trading day.")

st.sidebar.markdown("---")
st.sidebar.subheader("✍️ Manual Close (optional)")
use_manual_close = st.sidebar.checkbox("Enter 3:00 PM CT Close Manually", value=False)
manual_close_val = st.sidebar.number_input(
    "Manual 3:00 PM Close",
    value=6400.00,
    step=0.01,
    format="%.2f",
    disabled=not use_manual_close,
    help="If enabled, this overrides the fetched SPX anchor close."
)

st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ Advanced (optional)", expanded=False):
    st.caption("Adjust **asymmetric** per-30m slopes and proximity tolerance for bias within fan.")
    enable_slope = st.checkbox("Enable slope override", value=("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state))
    top_slope_val = st.number_input("Top slope (+ per 30m)", value=float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT)), step=0.001, format="%.3f")
    bottom_slope_val = st.number_input("Bottom slope (− per 30m)", value=float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT)), step=0.001, format="%.3f")
    tol_frac = st.slider("Within-fan neutrality band (% of fan width)", min_value=0, max_value=40, value=20, step=1) / 100.0

    col_adv_a, col_adv_b = st.columns(2)
    with col_adv_a:
        if st.button("Apply slopes", use_container_width=True, key="apply_slope"):
            if enable_slope:
                st.session_state["top_slope_per_block"] = float(top_slope_val)
                st.session_state["bottom_slope_per_block"] = float(bottom_slope_val)
                st.success(f"Top=+{top_slope_val:.3f}  •  Bottom=−{bottom_slope_val:.3f}")
            else:
                for k in ("top_slope_per_block", "bottom_slope_per_block"):
                    if k in st.session_state: del st.session_state[k]
                st.info("Slope override disabled (using defaults).")
    with col_adv_b:
        if st.button("Reset slopes", use_container_width=True, key="reset_slope"):
            for k in ("top_slope_per_block", "bottom_slope_per_block"):
                if k in st.session_state: del st.session_state[k]
            st.success(f"Reset to defaults: Top=+{TOP_SLOPE_DEFAULT:.3f} • Bottom=−{BOTTOM_SLOPE_DEFAULT:.3f}")

st.sidebar.markdown("---")
go_spx = st.sidebar.button("🔮 Generate SPX Fan & Strategy", type="primary", use_container_width=True)

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
""",
        unsafe_allow_html=True,
    )
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
""",
        unsafe_allow_html=True,
    )
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
""",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ───────────────────────────────────────────────────────────────────────────────
# TABS
# ───────────────────────────────────────────────────────────────────────────────
tab1, tabProb, tab2, tab3, tab4 = st.tabs(["SPX Anchors", "Probability Dashboard", "Stock Anchors", "Signals & EMA", "Contract Tool"])

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 1: SPX ANCHORS                                                          ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab1:
    st.subheader("SPX Close-Anchor Fan (3:00 PM CT) — with 8:30 AM Highlight & Correct Bias")

    if go_spx:
        with st.spinner("Building SPX fan & strategy…"):
            # Fetch prev/proj for ^GSPC (fallback to SPY if empty)
            spx_prev = fetch_intraday("^GSPC", prev_day, prev_day)
            if spx_prev.empty:
                spx_prev = fetch_intraday("SPY", prev_day, prev_day)

            spx_proj = fetch_intraday("^GSPC", proj_day, proj_day)
            if spx_proj.empty:
                spx_proj = fetch_intraday("SPY", proj_day, proj_day)

            if spx_prev.empty or spx_proj.empty:
                st.error("❌ Market data connection failed for the selected dates.")
            else:
                # Anchor close
                if use_manual_close:
                    anchor_close = float(manual_close_val)
                    anchor_time  = fmt_ct(datetime.combine(prev_day, time(15, 0)))
                    st.success(f"Using manual 3:00 PM CT close: **{anchor_close:.2f}**")
                else:
                    prev_3pm_close = get_prev_day_3pm_close(spx_prev, prev_day)
                    if prev_3pm_close is None:
                        st.error("Could not find a 3:00 PM CT close for the previous day.")
                        st.stop()
                    anchor_close = float(prev_3pm_close)
                    anchor_time  = fmt_ct(datetime.combine(prev_day, time(15, 0)))
                    st.success(f"Anchor (Prev Day 3:00 PM CT) Close: **{anchor_close:.2f}**")

                # Fan
                fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)

                # Strategy table with corrected bias definition
                spx_proj_rth = between_time(spx_proj, RTH_START, RTH_END)
                if spx_proj_rth.empty:
                    st.error("No RTH data available for the projection day.")
                else:
                    # Build per-slot strategy view
                    top_slope, bottom_slope = current_spx_slopes()
                    rows = []
                    for dt, bar in spx_proj_rth.iterrows():
                        blocks = count_effective_blocks(anchor_time, dt)
                        top = anchor_close + top_slope * blocks
                        bottom = anchor_close - bottom_slope * blocks
                        price = float(bar["Close"])

                        bias = compute_bias(price, top, bottom, tol_frac)

                        # Decision notes (position only; full path logic is in Probability tab)
                        if bottom <= price <= top:
                            note = "Within fan"
                        elif price > top:
                            note = "Above fan"
                        else:
                            note = "Below fan"

                        rows.append({
                            "Time": dt.strftime("%H:%M"),
                            "Price": round(price,2),
                            "Bias": bias,
                            "Top": round(top,2),
                            "Bottom": round(bottom,2),
                            "Fan_Width": round(top-bottom,2),
                            "Slot": "⭐ 8:30" if dt.strftime("%H:%M")=="08:30" else "",
                            "Note": note
                        })
                    strat_df = pd.DataFrame(rows)

                    st.markdown("### 🎯 Fan Lines (Top / Bottom @ 30-min)")
                    st.dataframe(fan_df[["Time","Top","Bottom","Fan_Width"]], use_container_width=True, hide_index=True)

                    st.markdown("### 📋 Strategy Table (Corrected Bias)")
                    st.caption("Bias uses **descending anchor line** & within-fan proximity tolerance. 8:30 AM row is marked with ⭐.")
                    st.dataframe(
                        strat_df[["Slot","Time","Price","Bias","Top","Bottom","Fan_Width","Note"]],
                        use_container_width=True, hide_index=True
                    )
    else:
        st.info("Use the **sidebar** to pick dates (and optional manual close), then click **Generate SPX Fan & Strategy**.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB PROB: PROBABILITY DASHBOARD                                             ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabProb:
    st.subheader("Probability Dashboard (Overnight Edge Interactions → RTH Readiness)")
    st.caption("Overnight analysis is aligned to the SPX fan frame and scored with EMA/Volume/Wick/ATR/Time-of-Day (+ optional Divergence).")

    colp1, colp2 = st.columns([1,1])
    with colp1:
        enable_div = st.checkbox("Enable Oscillator Divergence (lightweight)", value=False)
    with colp2:
        w_ema  = st.slider("Weight: EMA 8/21 (1-min)", 0, 40, WEIGHTS["ema"], 5)
        w_vol  = st.slider("Weight: Volume Confirmation", 0, 40, WEIGHTS["volume"], 5)
        w_wick = st.slider("Weight: Wick/Body Rejection", 0, 40, WEIGHTS["wick"], 5)
        w_atr  = st.slider("Weight: ATR Context", 0, 40, WEIGHTS["atr"], 5)
        w_tod  = st.slider("Weight: Time-of-Day", 0, 40, WEIGHTS["tod"], 5)
        w_div  = st.slider("Weight: Divergence (if enabled)", 0, 40, 10 if enable_div else 0, 5, disabled=not enable_div)

    custom_weights = {"ema":w_ema,"volume":w_vol,"wick":w_wick,"atr":w_atr,"tod":w_tod,"div":(w_div if enable_div else 0)}

    run_prob = st.button("🧠 Analyze Overnight & Build Probability Scores", type="primary")

    if run_prob:
        with st.spinner("Scoring overnight edge interactions…"):
            # Build anchor (as in Tab 1)
            spx_prev = fetch_intraday("^GSPC", prev_day, prev_day)
            if spx_prev.empty:
                spx_prev = fetch_intraday("SPY", prev_day, prev_day)
            if spx_prev.empty:
                st.error("Could not fetch previous day SPX data.")
                st.stop()

            if use_manual_close:
                anchor_close = float(manual_close_val)
            else:
                prev_3pm_close = get_prev_day_3pm_close(spx_prev, prev_day)
                if prev_3pm_close is None:
                    st.error("Could not find a 3:00 PM CT close for the previous day.")
                    st.stop()
                anchor_close = float(prev_3pm_close)
            anchor_time  = fmt_ct(datetime.combine(prev_day, time(15, 0)))

            touches_df, fan_df, offset_used = build_probability_dashboard(
                prev_day, proj_day, anchor_close, anchor_time, tol_frac, custom_weights
            )

            if touches_df.empty:
                st.info("No qualifying overnight edge touches detected for the window.")
            else:
                cA, cB, cC = st.columns(3)
                with cA:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>Anchor Close (Prev 3:00 PM CT)</p><div class='metric-value'>💠 {anchor_close:.2f}</div></div>", unsafe_allow_html=True)
                with cB:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>Overnight Touches Scored</p><div class='metric-value'>🧩 {len(touches_df)}</div></div>", unsafe_allow_html=True)
                with cC:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>Overnight Readiness</p><div class='metric-value'>⭐ Focus 08:30</div><div class='kicker'>First RTH decision point</div></div>", unsafe_allow_html=True)

                st.markdown("### 📡 Overnight Edge Interactions (Scored)")
                view_cols = ["Time","Price","Top","Bottom","Bias","Edge","Case","Expectation","Score","EMA_w","Vol_w","Wick_w","ATR_w","ToD_w","Div_w"]
                st.dataframe(touches_df[view_cols], use_container_width=True, hide_index=True)

                # ── Contract projection launcher
                st.markdown("### 🧮 Contract Projection from a Selected Touch")
                if not touches_df.empty:
                    # select a touch time
                    all_times = [f"{i} — {row['Time']} • {row['Edge']} • Score {row['Score']}" for i,row in touches_df.iterrows()]
                    sel = st.selectbox("Pick an overnight touch to seed the contract projection:", options=all_times, index=len(all_times)-1)
                    idx = int(sel.split(" — ")[0])
                    touch_row = touches_df.iloc[idx]
                    touch_dt = touch_row["TimeDT"]

                    # Enter contract inputs
                    st.caption("Enter contract price at the selected touch time. Optionally provide a second pre-open quote for a two-point slope.")
                    colc1, colc2, colc3 = st.columns([1,1,1])
                    with colc1:
                        p1_price = st.number_input("Contract Price @ Touch (P1)", min_value=0.01, value=10.00, step=0.01, format="%.2f")
                    with colc2:
                        provide_p2 = st.checkbox("Add a second price (P2) to refine slope", value=False)
                        if provide_p2:
                            p2_time = st.time_input("P2 Time (CT, pre-open OK)", value=time(8, 0))
                            p2_price = st.number_input("Contract Price @ P2", min_value=0.01, value=12.00, step=0.01, format="%.2f")
                        else:
                            p2_time = None; p2_price = None
                    with colc3:
                        mode = st.selectbox("Projection Mode", ["Two-Point Slope","Δ + Θ (model-aware)"], index=0)

                    # Underlying slope estimate for Δ+Θ
                    # Use sign based on expected near-term direction:
                    top_slope, bottom_slope = current_spx_slopes()
                    expected_hint = touch_row["DirectionHint"]
                    near_term_up = expected_hint in ("BuyHigherFromTop","UpToTopThenSell")
                    underlying_slope = (top_slope if near_term_up else -bottom_slope)

                    if st.button("📤 Project 8:30 → 14:30", type="secondary"):
                        with st.spinner("Projecting contract path across RTH…"):
                            p1_dt = fmt_ct(touch_dt.to_pydatetime())

                            if mode == "Two-Point Slope":
                                p2_dt = (fmt_ct(datetime.combine(proj_day, p2_time)) if provide_p2 and p2_time else None)
                                proj_df, slope_used, blocks_to_open = project_contract_two_point(p1_dt, float(p1_price), p2_dt, (float(p2_price) if provide_p2 else None), proj_day)
                                st.markdown("#### Projection (Two-Point Slope)")
                                mc1, mc2, mc3, mc4 = st.columns(4)
                                with mc1: st.markdown(f"<div class='metric-card'><p class='metric-title'>Seed Time</p><div class='metric-value'>⏱ {p1_dt.strftime('%Y-%m-%d %H:%M')}</div></div>", unsafe_allow_html=True)
                                with mc2: st.markdown(f"<div class='metric-card'><p class='metric-title'>Blocks to 8:30</p><div class='metric-value'>🧩 {blocks_to_open:.1f}</div></div>", unsafe_allow_html=True)
                                with mc3: st.markdown(f"<div class='metric-card'><p class='metric-title'>Slope / 30m</p><div class='metric-value'>📐 {slope_used:+.3f}</div></div>", unsafe_allow_html=True)
                                with mc4: st.markdown(f"<div class='metric-card'><p class='metric-title'>Touch Score</p><div class='metric-value'>⭐ {int(touch_row['Score'])}</div></div>", unsafe_allow_html=True)
                                # Mark 8:30 row
                                proj_df.insert(0, "Slot", proj_df["Time"].apply(lambda x: "⭐ 8:30" if x=="08:30" else ""))
                                st.dataframe(proj_df, use_container_width=True, hide_index=True)

                            else:
                                # Δ + Θ path
                                colg1, colg2 = st.columns(2)
                                with colg1:
                                    delta = st.number_input("Δ (Delta, e.g., 0.35)", value=0.35, step=0.01, format="%.2f")
                                with colg2:
                                    theta_day = st.number_input("Θ per day (negative, e.g., -20.00)", value=-20.00, step=0.5, format="%.2f")
                                proj_df, c_slope = project_contract_delta_theta(p1_dt, float(p1_price), float(underlying_slope), float(delta), float(theta_day), proj_day)
                                st.markdown("#### Projection (Δ + Θ Model)")
                                mc1, mc2, mc3, mc4 = st.columns(4)
                                with mc1: st.markdown(f"<div class='metric-card'><p class='metric-title'>Seed Time</p><div class='metric-value'>⏱ {p1_dt.strftime('%Y-%m-%d %H:%M')}</div></div>", unsafe_allow_html=True)
                                with mc2: st.markdown(f"<div class='metric-card'><p class='metric-title'>Δ</p><div class='metric-value'>Δ {delta:.2f}</div></div>", unsafe_allow_html=True)
                                with mc3: st.markdown(f"<div class='metric-card'><p class='metric-title'>Θ / 30m</p><div class='metric-value'>θ {theta_day/48.0:+.3f}</div></div>", unsafe_allow_html=True)
                                with mc4: st.markdown(f"<div class='metric-card'><p class='metric-title'>Contract Slope / 30m</p><div class='metric-value'>📐 {c_slope:+.3f}</div></div>", unsafe_allow_html=True)
                                proj_df.insert(0, "Slot", proj_df["Time"].apply(lambda x: "⭐ 8:30" if x=="08:30" else ""))
                                st.dataframe(proj_df, use_container_width=True, hide_index=True)

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 2: STOCK ANCHORS                                                        ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab2:
    st.subheader("Stock Anchor Lines (Mon/Tue swings → two lines)")
    st.caption("Projects an ascending line from the highest swing high and a descending line from the lowest swing low (Mon+Tue combined), using your per-ticker slope.")

    # Controls
    core = list(STOCK_SLOPES.keys())
    cc1, cc2, cc3 = st.columns([1.4,1,1])
    with cc1:
        ticker = st.selectbox("Ticker", core + ["Custom…"], index=0, key="stk_ticker")
        custom_ticker = ""
        if ticker == "Custom…":
            custom_ticker = st.text_input("Custom Symbol", value="", placeholder="e.g., AMD")
    with cc2:
        # Monday default: "most recent Monday"
        monday_default = today_ct - timedelta(days=((today_ct.weekday() - 0) % 7 or 7))
        monday_date = st.date_input("Monday Date", value=monday_default)
    with cc3:
        tuesday_date = st.date_input("Tuesday Date", value=monday_date + timedelta(days=1))

    # Slope picker
    slope_mag_default = STOCK_SLOPES.get(ticker, 0.0150) if ticker != "Custom…" else 0.0150
    slope_mag = st.number_input("Slope Magnitude (per 30m)", value=float(slope_mag_default), step=0.0001, format="%.4f")

    proj_day_stock = st.date_input("Projection Day", value=tuesday_date + timedelta(days=1))
    run_stock = st.button("📈 Analyze Stock Anchors", type="primary")

    if run_stock:
        with st.spinner("Fetching and projecting…"):
            sym = custom_ticker.upper() if ticker == "Custom…" and custom_ticker else (ticker if ticker != "Custom…" else None)
            if not sym:
                st.error("Please enter a custom symbol.")
                st.stop()

            mon = fetch_intraday(sym, monday_date, monday_date)
            tue = fetch_intraday(sym, tuesday_date, tuesday_date)
            if mon.empty and tue.empty:
                st.error("No data for selected dates.")
                st.stop()

            combined = mon if tue.empty else (tue if mon.empty else pd.concat([mon, tue]).sort_index())

            hi, lo = detect_absolute_swings(combined)
            if not hi or not lo:
                st.error("Could not detect swings.")
                st.stop()

            (high_price, high_time) = hi
            (low_price,  low_time)  = lo
            high_time = fmt_ct(high_time); low_time = fmt_ct(low_time)

            proj_df = project_two_stock_lines(high_price, high_time, low_price, low_time, slope_mag, proj_day_stock)

            cA, cB = st.columns(2)
            with cA:
                st.markdown("**Swing High (Mon/Tue):**")
                st.write(f"📈 {sym} — High: **{high_price:.2f}** at {high_time.strftime('%Y-%m-%d %H:%M CT')}")
            with cB:
                st.markdown("**Swing Low (Mon/Tue):**")
                st.write(f"📉 {sym} — Low: **{low_price:.2f}** at {low_time.strftime('%Y-%m-%d %H:%M CT')}")

            st.markdown("### 🔧 Projection (RTH)")
            st.dataframe(proj_df, use_container_width=True, hide_index=True)

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 3: SIGNALS & EMA                                                        ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab3:
    st.subheader("Signals: Fan Touch + Same-Bar EMA 8/21 Confirmation")

    colS1, colS2, colS3 = st.columns([1.2,1,1])
    with colS1:
        sig_symbol = st.selectbox("Symbol", ["^GSPC", "SPY", "ES=F"], index=0)
    with colS2:
        sig_day = st.date_input("Analysis Day", value=today_ct)
    with colS3:
        interval_pref = st.selectbox("Interval preference", ["1m", "5m", "30m"], index=0, help="1m requires recent dates (≤7 days)")

    run_sig = st.button("🔎 Analyze Signals", type="primary")

    if run_sig:
        with st.spinner("Computing signals…"):
            prev_day_sig = sig_day - timedelta(days=1)
            spx_prev = fetch_intraday("^GSPC", prev_day_sig, prev_day_sig)
            if spx_prev.empty and sig_symbol in ["^GSPC", "SPY"]:
                spx_prev = fetch_intraday("SPY", prev_day_sig, prev_day_sig)

            if spx_prev.empty:
                st.error("Could not build fan (prev day data missing).")
                st.stop()

            prev_3pm_close = get_prev_day_3pm_close(spx_prev, prev_day_sig)
            if prev_3pm_close is None:
                st.error("Prev day 3:00 PM close not found.")
                st.stop()

            anchor_close = float(prev_3pm_close)
            anchor_time  = fmt_ct(datetime.combine(prev_day_sig, time(15, 0)))
            fan_df = project_fan_from_close(anchor_close, anchor_time, sig_day)

            intraday = fetch_intraday_interval(sig_symbol, sig_day, sig_day, interval_pref)
            if intraday.empty and interval_pref != "5m":
                intraday = fetch_intraday_interval(sig_symbol, sig_day, sig_day, "5m")
            if intraday.empty and interval_pref != "30m":
                intraday = fetch_intraday_interval(sig_symbol, sig_day, sig_day, "30m")

            if intraday.empty:
                st.error("No intraday data available for the analysis day.")
                st.stop()

            fan_lu_top = {r['Time']: r['Top'] for _, r in fan_df.iterrows()}
            fan_lu_bot = {r['Time']: r['Bottom'] for _, r in fan_df.iterrows()}

            ema_df = compute_ema_cross_df(intraday)

            signals = []
            for ts, bar in ema_df.iterrows():
                tstr = ts.strftime("%H:%M")
                if tstr not in fan_lu_top or tstr not in fan_lu_bot:
                    continue
                top = fan_lu_top[tstr]; bot = fan_lu_bot[tstr]
                low, high, close, open_ = bar.get('Low', np.nan), bar.get('High', np.nan), bar.get('Close', np.nan), bar.get('Open', np.nan)

                touched_bottom = (not pd.isna(low) and not pd.isna(high) and (low <= bot <= high))
                touched_top    = (not pd.isna(low) and not pd.isna(high) and (low <= top <= high))
                confirmation = bar['Crossover']  # 'Bullish' / 'Bearish' / 'None'
                action = ""
                rationale = ""

                if touched_bottom:
                    if confirmation == 'Bullish':
                        action = "BUY → target Top"
                        rationale = "Touched Bottom & same-bar EMA8>EMA21"
                    elif confirmation == 'Bearish':
                        action = "SELL → potential breakdown"
                        rationale = "Touched Bottom & same-bar EMA8<EMA21"
                elif touched_top:
                    if confirmation == 'Bearish':
                        action = "SELL → target Bottom"
                        rationale = "Touched Top & same-bar EMA8<EMA21"
                    elif confirmation == 'Bullish':
                        action = "BUY → potential breakout"
                        rationale = "Touched Top & same-bar EMA8>EMA21"

                if touched_bottom or touched_top:
                    signals.append({
                        "Time": tstr,
                        "Open": round(open_,2), "High": round(high,2), "Low": round(low,2), "Close": round(close,2),
                        "Top": round(top,2), "Bottom": round(bot,2),
                        "EMA8": round(bar['EMA8'],2), "EMA21": round(bar['EMA21'],2),
                        "Cross": confirmation,
                        "Signal": action if action else "Touch w/o confirm",
                        "Note": rationale if rationale else "Confirmation not aligned"
                    })

            st.markdown("### 📡 Fan Touch + EMA Confirmation")
            if signals:
                st.dataframe(pd.DataFrame(signals), use_container_width=True, hide_index=True)
            else:
                st.info("No touch+confirmation signals found for that day/interval.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 4: CONTRACT TOOL (standalone)                                           ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab4:
    st.subheader("Contract Tool (Point-to-Point or Δ+Θ)")

    point_col1, point_col2 = st.columns(2)
    with point_col1:
        p1_date = st.date_input("Point 1 Date", value=today_ct - timedelta(days=1))
        p1_time = st.time_input("Point 1 Time (CT)", value=time(20, 0))
        p1_price = st.number_input("Point 1 Contract Price", value=10.00, min_value=0.01, step=0.01, format="%.2f")
    with point_col2:
        p2_date = st.date_input("Point 2 Date", value=today_ct)
        p2_time = st.time_input("Point 2 Time (CT)", value=time(8, 0))
        p2_price = st.number_input("Point 2 Contract Price", value=12.00, min_value=0.01, step=0.01, format="%.2f")

    proj_day_ct = st.date_input("RTH Projection Day", value=p2_date)
    mode_ct = st.selectbox("Mode", ["Two-Point Slope","Δ + Θ (model-aware)"], index=0)
    run_ct = st.button("🧮 Analyze Contract Projections", type="primary")

    if run_ct:
        p1_dt = fmt_ct(datetime.combine(p1_date, p1_time))
        p2_dt = fmt_ct(datetime.combine(p2_date, p2_time))
        if p2_dt <= p1_dt and mode_ct == "Two-Point Slope":
            st.error("Point 2 must be after Point 1 for Two-Point mode.")
            st.stop()

        if mode_ct == "Two-Point Slope":
            proj_df, slope_ct, blocks = project_contract_two_point(p1_dt, float(p1_price), p2_dt, float(p2_price), proj_day_ct)
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1: st.markdown(f"<div class='metric-card'><p class='metric-title'>Time Span</p><div class='metric-value'>⏱ {(p2_dt-p1_dt).total_seconds()/3600:.1f}h</div></div>", unsafe_allow_html=True)
            with mc2: st.markdown(f"<div class='metric-card'><p class='metric-title'>Δ Price</p><div class='metric-value'>↕ {p2_price - p1_price:+.2f}</div></div>", unsafe_allow_html=True)
            with mc3: st.markdown(f"<div class='metric-card'><p class='metric-title'>Blocks Counted</p><div class='metric-value'>🧩 {blocks:.1f}</div></div>", unsafe_allow_html=True)
            with mc4: st.markdown(f"<div class='metric-card'><p class='metric-title'>Slope / 30m</p><div class='metric-value'>📐 {slope_ct:+.3f}</div></div>", unsafe_allow_html=True)
            proj_df.insert(0, "Slot", proj_df["Time"].apply(lambda x: "⭐ 8:30" if x=="08:30" else ""))
            st.markdown("### 📊 RTH Projection")
            st.dataframe(proj_df, use_container_width=True, hide_index=True)

        else:
            colg1, colg2, colg3 = st.columns(3)
            with colg1:
                underlying_slope = st.number_input("Underlying slope / 30m (±)", value=0.10, step=0.01, format="%.2f",
                                                   help="Approx expected SPX move per 30m (+ for up, − for down).")
            with colg2:
                delta = st.number_input("Δ (Delta)", value=0.35, step=0.01, format="%.2f")
            with colg3:
                theta_day = st.number_input("Θ per day (negative)", value=-20.00, step=0.5, format="%.2f")
            proj_df, c_slope = project_contract_delta_theta(p1_dt, float(p1_price), float(underlying_slope), float(delta), float(theta_day), proj_day_ct)
            mc1, mc2, mc3 = st.columns(3)
            with mc1: st.markdown(f"<div class='metric-card'><p class='metric-title'>Seed Time</p><div class='metric-value'>⏱ {p1_dt.strftime('%Y-%m-%d %H:%M')}</div></div>", unsafe_allow_html=True)
            with mc2: st.markdown(f"<div class='metric-card'><p class='metric-title'>Contract Slope / 30m</p><div class='metric-value'>📐 {c_slope:+.3f}</div></div>", unsafe_allow_html=True)
            with mc3: st.markdown(f"<div class='metric-card'><p class='metric-title'>Θ / 30m</p><div class='metric-value'>θ {theta_day/48.0:+.3f}</div></div>", unsafe_allow_html=True)
            proj_df.insert(0, "Slot", proj_df["Time"].apply(lambda x: "⭐ 8:30" if x=="08:30" else ""))
            st.markdown("### 📊 RTH Projection")
            st.dataframe(proj_df, use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────────────────────────────────────
# FOOTER UTILITIES
# ───────────────────────────────────────────────────────────────────────────────
st.markdown("---")
colA, colB = st.columns([1, 2])
with colA:
    if st.button("🔌 Test Data Connection"):
        td = fetch_intraday("^GSPC", today_ct - timedelta(days=3), today_ct)
        if td.empty:
            td = fetch_intraday("SPY", today_ct - timedelta(days=3), today_ct)
        if not td.empty:
            st.success(f"OK — received {len(td)} bars.")
        else:
            st.error("Data fetch failed — try different dates later.")
with colB:
    st.caption("Times normalized to **CT**. Fan anchor uses **Prev Day 3:00 PM CT SPX close**. Overnight analysis is internally aligned to the SPX frame. 8:30 AM is highlighted in all tables.")
