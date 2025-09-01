# app.py
# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 SPX PROPHET — Full App (SPX Anchors • Stock Anchors • Signals & EMA • Contract Tool)
# - SPX: previous day's exact 3:00 PM CT close as anchor (manual override supported)
# - Fan: Top=+slope per 30m, Bottom=−slope per 30m (default ±0.260), skip 4–5 PM CT + Fri 5 PM → Sun 5 PM
# - Stocks: Mon/Tue swing high/low → two parallel anchor lines by your per-ticker slopes
# - Signals: fan touch + same-bar EMA 8/21 confirmation (1m if recent; otherwise 5m/30m fallback)
# - Contract Tool: two points (0–30 price) → slope → RTH projection
# - Clean light UI, icons, and compact tables
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

# Default slope per 30-minute block (Top +, Bottom −)
SLOPE_PER_BLOCK_DEFAULT = 0.260

# Per-ticker slope magnitudes (your latest set)
STOCK_SLOPES = {
    "TSLA": 0.0285, "NVDA": 0.0860, "AAPL": 0.0155, "MSFT": 0.0541,
    "AMZN": 0.0139, "GOOGL": 0.0122, "META": 0.0674, "NFLX": 0.0230,
}

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED PAGE & THEME CONFIGURATION
# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🔮 SPX Prophet Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enhanced Enterprise-Grade CSS with Glassmorphism
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
  /* Enhanced Color Palette */
  --primary: #3B82F6;           /* blue-500 */
  --primary-dark: #1D4ED8;      /* blue-700 */
  --primary-light: #DBEAFE;     /* blue-100 */
  --secondary: #10B981;         /* emerald-500 */
  --secondary-dark: #047857;    /* emerald-700 */
  --secondary-light: #D1FAE5;   /* emerald-100 */
  --accent: #8B5CF6;            /* violet-500 */
  --accent-light: #EDE9FE;      /* violet-100 */
  
  /* Surface Colors */
  --background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
  --surface: rgba(255, 255, 255, 0.95);
  --surface-elevated: rgba(255, 255, 255, 0.98);
  --surface-hover: rgba(255, 255, 255, 0.85);
  --glass: rgba(255, 255, 255, 0.25);
  --glass-border: rgba(255, 255, 255, 0.18);
  
  /* Text Colors */
  --text-primary: #0F172A;      /* slate-900 */
  --text-secondary: #475569;    /* slate-600 */
  --text-tertiary: #64748B;     /* slate-500 */
  --text-muted: #94A3B8;        /* slate-400 */
  
  /* Border & Shadow */
  --border: rgba(203, 213, 225, 0.4);  /* slate-300 with opacity */
  --border-light: rgba(226, 232, 240, 0.6);
  --shadow-sm: 0 2px 4px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 8px 24px rgba(15, 23, 42, 0.12);
  --shadow-xl: 0 16px 48px rgba(15, 23, 42, 0.16);
  --shadow-glass: 0 8px 32px rgba(15, 23, 42, 0.08);
  
  /* Status Colors */
  --success: #10B981;
  --success-bg: #ECFDF5;
  --success-border: #A7F3D0;
  --warning: #F59E0B;
  --warning-bg: #FFFBEB;
  --warning-border: #FDE68A;
  --error: #EF4444;
  --error-bg: #FEF2F2;
  --error-border: #FECACA;
  --info: #3B82F6;
  --info-bg: #EFF6FF;
  --info-border: #BFDBFE;
}

/* Base Styles */
* {
  box-sizing: border-box;
}

html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--background);
  color: var(--text-primary);
  line-height: 1.6;
}

/* Main Container */
.block-container {
  padding-top: 2rem;
  padding-bottom: 2rem;
  max-width: 1400px;
}

/* Typography Enhancements */
h1, h2, h3, h4, h5, h6 {
  color: var(--text-primary);
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.25;
}

h1 { font-size: 2.5rem; margin-bottom: 1rem; }
h2 { font-size: 2rem; margin-bottom: 0.875rem; }
h3 { font-size: 1.5rem; margin-bottom: 0.75rem; }

p, .stMarkdown p {
  color: var(--text-secondary);
  font-weight: 400;
  line-height: 1.7;
}

/* Enhanced Card System */
.card, .metric-card {
  background: var(--surface);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  padding: 1.5rem;
  box-shadow: var(--shadow-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.card::before, .metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
  opacity: 0.6;
}

.card:hover, .metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xl);
  border-color: rgba(59, 130, 246, 0.3);
}

/* Enhanced Metric Cards */
.metric-card {
  text-align: center;
  background: linear-gradient(135deg, var(--surface) 0%, rgba(255, 255, 255, 0.9) 100%);
  border: 1px solid var(--border-light);
}

.metric-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-tertiary);
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: 2rem;
  font-weight: 800;
  margin: 0.5rem 0;
  color: var(--text-primary);
  line-height: 1.1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.kicker {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
  margin-top: 0.25rem;
}

/* Enhanced Badge System */
.badge-open, .badge-closed {
  display: inline-flex;
  align-items: center;
  padding: 0.375rem 0.875rem;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.badge-open {
  color: var(--secondary-dark);
  background: linear-gradient(135deg, var(--secondary-light) 0%, #A7F3D0 100%);
  border: 1px solid var(--secondary);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.badge-closed {
  color: #92400E;
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  border: 1px solid var(--warning);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
}

/* Override Tag Enhancement */
.override-tag {
  font-size: 0.75rem;
  color: var(--accent);
  background: linear-gradient(135deg, var(--accent-light) 0%, #DDD6FE 100%);
  border: 1px solid var(--accent);
  padding: 0.25rem 0.75rem;
  border-radius: 50px;
  display: inline-block;
  margin-top: 0.5rem;
  font-weight: 600;
  box-shadow: var(--shadow-sm);
  animation: pulse-subtle 2s infinite;
}

@keyframes pulse-subtle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

/* Enhanced Dividers */
hr {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 2rem 0;
}

/* Enhanced Form Controls */
.stSelectbox > div > div,
.stNumberInput > div > div,
.stDateInput > div > div,
.stTimeInput > div > div,
.stTextInput > div > div {
  background: var(--surface-elevated);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.stSelectbox > div > div:focus-within,
.stNumberInput > div > div:focus-within,
.stDateInput > div > div:focus-within,
.stTimeInput > div > div:focus-within,
.stTextInput > div > div:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Enhanced Buttons */
.stButton > button {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.stButton > button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.stButton > button:hover::before {
  left: 100%;
}

/* Primary Button Enhancement */
.stButton > button[data-baseweb="button"][kind="primary"] {
  background: linear-gradient(135deg, var(--secondary) 0%, var(--secondary-dark) 100%);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
}

.stButton > button[data-baseweb="button"][kind="primary"]:hover {
  box-shadow: 0 12px 32px rgba(16, 185, 129, 0.4);
}
</style>
""",
    unsafe_allow_html=True,
)






# ───────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS (Unchanged functionality)
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
    """
    True for Fri >= 17:00 → Sun < 17:00 CT (no overnight session counted).
    """
    wd = dt.weekday()  # Mon=0 ... Sun=6
    if wd == 5:
        return True           # Saturday
    if wd == 6 and dt.hour < 17:
        return True           # Sunday before 5pm CT
    if wd == 4 and dt.hour >= 17:
        return True           # Friday from 5pm CT onward
    return False

def count_effective_blocks(anchor_time: datetime, target_time: datetime) -> float:
    """
    Count 30-min blocks from anchor_time → target_time,
    skipping maintenance (4–5 PM) and weekend gap.
    Count a block if the *end* time of that block is not in forbidden windows.
    """
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
        df.index = df.index.tz_localize("US/Eastern")
    df.index = df.index.tz_convert(CT_TZ)
    sdt = fmt_ct(datetime.combine(start_d, time(0, 0)))
    edt = fmt_ct(datetime.combine(end_d, time(23, 59)))
    return df.loc[sdt:edt]

@st.cache_data(ttl=120)
def fetch_intraday(symbol: str, start_d: date, end_d: date) -> pd.DataFrame:
    """
    Robust intraday fetch, 30m, CT index, auto_adjust=False for accurate closes.
    Falls back to period-based fetch if start/end returns empty.
    """
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
    """
    Interval-aware fetch. For 1m data, yfinance requires recent periods (<=7d).
    We automatically choose a period window for 1m/5m; otherwise use start/end.
    """
    try:
        t = yf.Ticker(symbol)
        if interval in ["1m", "2m", "5m", "15m"]:
            # choose a period window that safely covers [start_d, end_d]
            days = max(1, min(7, (end_d - start_d).days + 2))
            df = t.history(period=f"{days}d", interval=interval,
                           prepost=True, auto_adjust=False, back_adjust=False)
            # trim to the exact date range after tz normalization
            # pick a broad range for normalization
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

def get_prev_day_3pm_close(spx_prev: pd.DataFrame, prev_day: date) -> Optional[float]:
    """
    Get the **3:00 PM CT exact bar close** for prev_day.
    If exact 15:00 not present, use the last bar <= 15:00 within prev_day.
    """
    if spx_prev.empty:
        return None
    day_start = fmt_ct(datetime.combine(prev_day, time(0, 0)))
    day_end   = fmt_ct(datetime.combine(prev_day, time(23, 59)))
    d = spx_prev.loc[day_start:day_end].copy()
    if d.empty:
        return None
    target = fmt_ct(datetime.combine(prev_day, time(15, 0)))
    if target in d.index:
        return float(d.loc[target, "Close"])
    prior = d.loc[:target]
    if not prior.empty:
        return float(prior.iloc[-1]["Close"])
    return None

# ───── Slope state
def current_slope() -> float:
    return float(st.session_state.get("slope_per_block", SLOPE_PER_BLOCK_DEFAULT))

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED SIDEBAR DESIGN
# ───────────────────────────────────────────────────────────────────────────────

# Additional CSS for enhanced sidebar
st.markdown("""
<style>
/* Enhanced Sidebar Styling */
.css-1d391kg, .css-1lcbmhc {
    background: linear-gradient(180deg, var(--surface-elevated) 0%, var(--surface) 100%);
    border-right: 1px solid var(--border-light);
    box-shadow: var(--shadow-lg);
}

/* Sidebar Headers */
.css-1d391kg h1, .css-1lcbmhc h1,
.css-1d391kg h2, .css-1lcbmhc h2,
.css-1d391kg h3, .css-1lcbmhc h3 {
    color: var(--text-primary);
    font-weight: 700;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--primary-light);
}

/* Sidebar Input Groups */
.sidebar-group {
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(8px);
}

.sidebar-group h4 {
    color: var(--primary);
    font-size: 0.95rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Enhanced Dividers in Sidebar */
.css-1d391kg hr, .css-1lcbmhc hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.5rem 0;
}

/* Sidebar Captions */
.css-1d391kg .stCaption, .css-1lcbmhc .stCaption {
    color: var(--text-tertiary);
    font-size: 0.8rem;
    font-style: italic;
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: var(--info-bg);
    border-left: 3px solid var(--info);
    border-radius: 0 8px 8px 0;
}

/* Enhanced Expander in Sidebar */
.css-1d391kg .streamlit-expanderHeader, 
.css-1lcbmhc .streamlit-expanderHeader {
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 0.75rem;
    font-weight: 600;
    color: var(--text-primary);
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
}

.css-1d391kg .streamlit-expanderHeader:hover,
.css-1lcbmhc .streamlit-expanderHeader:hover {
    background: var(--surface-hover);
    transform: translateY(-1px);
}

.css-1d391kg .streamlit-expanderContent,
.css-1lcbmhc .streamlit-expanderContent {
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 1rem;
    box-shadow: var(--shadow-sm);
}

/* Success/Error Messages in Sidebar */
.css-1d391kg .stSuccess, .css-1lcbmhc .stSuccess {
    background: var(--success-bg);
    border: 1px solid var(--success-border);
    border-radius: 12px;
    padding: 0.75rem;
    color: var(--success);
}

.css-1d391kg .stError, .css-1lcbmhc .stError {
    background: var(--error-bg);
    border: 1px solid var(--error-border);
    border-radius: 12px;
    padding: 0.75rem;
    color: var(--error);
}

.css-1d391kg .stInfo, .css-1lcbmhc .stInfo {
    background: var(--info-bg);
    border: 1px solid var(--info-border);
    border-radius: 12px;
    padding: 0.75rem;
    color: var(--info);
}
</style>
""", unsafe_allow_html=True)

# Enhanced Sidebar with better organization
with st.sidebar:
    # Sidebar Header with icon and styling
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: var(--primary); font-size: 1.5rem; margin: 0;">
            🔧 Control Center
        </h1>
        <p style="color: var(--text-tertiary); font-size: 0.9rem; margin: 0.5rem 0 0 0;">
            Configure your analysis parameters
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Date Configuration Group
    st.markdown('<div class="sidebar-group">', unsafe_allow_html=True)
    st.markdown('<h4>📅 Date Configuration</h4>', unsafe_allow_html=True)
    
    today_ct = datetime.now(CT_TZ).date()
    prev_day = st.date_input(
        "Previous Trading Day", 
        value=today_ct - timedelta(days=1),
        help="The day from which to get the 3:00 PM CT anchor price"
    )
    proj_day = st.date_input(
        "Projection Day", 
        value=prev_day + timedelta(days=1),
        help="The day for which to generate projections"
    )
    
    st.caption("🎯 Anchor will be set at **3:00 PM CT** on the previous trading day.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Manual Override Group
    st.markdown('<div class="sidebar-group">', unsafe_allow_html=True)
    st.markdown('<h4>✍️ Manual Override</h4>', unsafe_allow_html=True)
    
    use_manual_close = st.checkbox(
        "Enter 3:00 PM CT Close Manually", 
        value=False,
        help="Override the fetched close price with a manual value"
    )
    manual_close_val = st.number_input(
        "Manual 3:00 PM Close",
        value=6400.00,
        step=0.01,
        format="%.2f",
        disabled=not use_manual_close,
        help="If enabled, this value overrides the fetched close for the SPX anchor."
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Advanced Settings Expander
    with st.expander("⚙️ Advanced Settings", expanded=False):
        st.markdown('<div class="sidebar-group" style="margin: 0; border: none; box-shadow: none; background: transparent;">', unsafe_allow_html=True)
        st.caption("🔧 Adjust per-30m slope (applies to SPX and stock projections).")
        
        enable_slope = st.checkbox(
            "Enable slope override", 
            value=("slope_per_block" in st.session_state),
            help="Override the default slope calculation"
        )
        slope_val = st.number_input(
            "Slope per 30m (Top +, Bottom −)",
            value=float(st.session_state.get("slope_per_block", SLOPE_PER_BLOCK_DEFAULT)),
            step=0.001, 
            format="%.3f",
            help="Example: 0.260 means Top = anchor + 0.260 per 30 minutes."
        )
        
        col_adv_a, col_adv_b = st.columns(2)
        with col_adv_a:
            if st.button("Apply slope", use_container_width=True, key="apply_slope"):
                if enable_slope:
                    st.session_state["slope_per_block"] = float(slope_val)
                    st.success(f"Slope set to ±{slope_val:.3f}")
                else:
                    if "slope_per_block" in st.session_state:
                        del st.session_state["slope_per_block"]
                    st.info("Slope override disabled (using default).")
        with col_adv_b:
            if st.button("Reset slope", use_container_width=True, key="reset_slope"):
                if "slope_per_block" in st.session_state:
                    del st.session_state["slope_per_block"]
                st.success(f"Reset slope to default ±{SLOPE_PER_BLOCK_DEFAULT:.3f}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Action Button
    st.markdown('<div style="margin-top: 2rem;">', unsafe_allow_html=True)
    go_spx = st.button("🔮 Generate SPX Fan & Strategy", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)






# ───────────────────────────────────────────────────────────────────────────────
# ANALYSIS FUNCTIONS (Unchanged functionality)
# ───────────────────────────────────────────────────────────────────────────────

# ───── SPX Fan Projection
def project_fan_from_close(close_price: float, anchor_time: datetime, target_day: date) -> pd.DataFrame:
    slope = current_slope()
    rows = []
    for slot in rth_slots_ct(target_day):
        blocks = count_effective_blocks(anchor_time, slot)
        top = close_price + slope * blocks
        bot = close_price - slope * blocks
        rows.append({"Time": slot.strftime("%H:%M"),
                     "Top": round(top, 2),
                     "Bottom": round(bot, 2),
                     "Fan_Width": round(top - bot, 2)})
    return pd.DataFrame(rows)

# ───── SPX Strategy
def build_spx_strategy(rth_prices: pd.DataFrame, fan_df: pd.DataFrame, anchor_close: float) -> pd.DataFrame:
    """
    - Bias: "UP" if price ≥ anchor_close; else "DOWN".
    - Within fan:
        - Bias UP → BUY bottom → TP1/TP2 at top
        - Bias DOWN → SELL top → TP1/TP2 at bottom
    - Above fan: SELL at top, TP2 = top - width
    - Below fan: SELL at bottom, TP2 = bottom - width
    """
    if rth_prices.empty or fan_df.empty:
        return pd.DataFrame()

    price_lu = {dt.strftime("%H:%M"): float(rth_prices.loc[dt, "Close"]) for dt in rth_prices.index}
    rows = []
    for _, row in fan_df.iterrows():
        t = row["Time"]
        if t not in price_lu:
            continue
        p = price_lu[t]
        top, bot, width = row["Top"], row["Bottom"], row["Fan_Width"]
        bias = "UP" if p >= anchor_close else "DOWN"

        if bot <= p <= top:
            if bias == "UP":
                direction = "BUY"; entry = bot; tp1 = top; tp2 = top; note = "Within fan; bias UP"
            else:
                direction = "SELL"; entry = top; tp1 = bot; tp2 = bot; note = "Within fan; bias DOWN"
        elif p > top:
            direction = "SELL"; entry = top; tp1 = np.nan; tp2 = top - width; note = "Above fan"
        else:  # p < bottom
            direction = "SELL"; entry = bot; tp1 = np.nan; tp2 = bot - width; note = "Below fan"

        rows.append({
            "Time": t, "Price": round(p, 2), "Bias": bias, "EntrySide": direction,
            "Entry": round(entry, 2), "TP1": (round(tp1, 2) if not pd.isna(tp1) else np.nan),
            "TP2": (round(tp2, 2) if not pd.isna(tp2) else np.nan),
            "Top": round(top, 2), "Bottom": round(bot, 2)
        })
    return pd.DataFrame(rows)

# ───── Stocks: swings & two-line projection
def detect_absolute_swings(df: pd.DataFrame) -> Tuple[Optional[Tuple[float, datetime]], Optional[Tuple[float, datetime]]]:
    """Return (highest_high, its_time), (lowest_low, its_time)"""
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
    """Ascending from swing high (+slope_mag) and descending from swing low (−slope_mag)."""
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

# ───── EMA utils
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def compute_ema_cross_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with EMA8/EMA21 and crossover label for same-bar check."""
    if df.empty or 'Close' not in df:
        return pd.DataFrame()
    out = df.copy()
    out['EMA8'] = ema(out['Close'], 8)
    out['EMA21'] = ema(out['Close'], 21)
    # same-bar "state"
    out['Crossover'] = np.where(out['EMA8'] > out['EMA21'], 'Bullish', np.where(out['EMA8'] < out['EMA21'], 'Bearish', 'None'))
    return out

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED HEADER METRICS SECTION
# ───────────────────────────────────────────────────────────────────────────────

# Additional CSS for enhanced metrics display
st.markdown("""
<style>
/* Enhanced Header Section */
.header-section {
    background: linear-gradient(135deg, var(--surface) 0%, rgba(255, 255, 255, 0.8) 100%);
    border: 1px solid var(--border-light);
    border-radius: 24px;
    padding: 2rem;
    margin: 2rem 0;
    box-shadow: var(--shadow-glass);
    backdrop-filter: blur(20px);
    position: relative;
    overflow: hidden;
}

.header-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, 
        rgba(59, 130, 246, 0.02) 0%, 
        rgba(16, 185, 129, 0.02) 50%, 
        rgba(139, 92, 246, 0.02) 100%);
    pointer-events: none;
}

/* Enhanced Metric Cards with Animation */
.metric-card-enhanced {
    background: linear-gradient(135deg, var(--surface-elevated) 0%, var(--surface) 100%);
    border: 1px solid var(--border-light);
    border-radius: 20px;
    padding: 2rem 1.5rem;
    box-shadow: var(--shadow-md);
    backdrop-filter: blur(12px);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    text-align: center;
    height: 160px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-card-enhanced::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent));
    opacity: 0.6;
    transition: opacity 0.3s ease;
}

.metric-card-enhanced:hover::before {
    opacity: 1;
}

.metric-card-enhanced:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: var(--shadow-xl);
    border-color: rgba(59, 130, 246, 0.3);
}

/* Time-specific styling */
.time-card {
    border-color: var(--primary-light);
    background: linear-gradient(135deg, var(--primary-light) 0%, var(--surface-elevated) 100%);
}

.time-card .metric-value {
    color: var(--primary);
}

/* Status-specific styling */
.status-card {
    border-color: var(--secondary-light);
    background: linear-gradient(135deg, var(--secondary-light) 0%, var(--surface-elevated) 100%);
}

.status-card.open {
    border-color: var(--success-border);
    background: linear-gradient(135deg, var(--success-bg) 0%, var(--surface-elevated) 100%);
}

.status-card.closed {
    border-color: var(--warning-border);
    background: linear-gradient(135deg, var(--warning-bg) 0%, var(--surface-elevated) 100%);
}

/* Slope-specific styling */
.slope-card {
    border-color: var(--accent-light);
    background: linear-gradient(135deg, var(--accent-light) 0%, var(--surface-elevated) 100%);
}

.slope-card .metric-value {
    color: var(--accent);
}

/* Enhanced metric text */
.metric-title-enhanced {
    font-size: 0.875rem;
    font-weight: 700;
    color: var(--text-tertiary);
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.metric-value-enhanced {
    font-size: 2.25rem;
    font-weight: 800;
    margin: 1rem 0;
    color: var(--text-primary);
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    flex: 1;
}

.metric-subtitle {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 500;
    margin: 0;
    line-height: 1.4;
}

/* Live time animation */
@keyframes pulse-glow {
    0%, 100% { 
        box-shadow: var(--shadow-md);
    }
    50% { 
        box-shadow: var(--shadow-lg), 0 0 20px rgba(59, 130, 246, 0.1);
    }
}

.time-card {
    animation: pulse-glow 3s ease-in-out infinite;
}

/* Market status badge enhancements */
.status-badge-enhanced {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 50px;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.025em;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    border: 2px solid;
}

.status-open {
    color: var(--secondary-dark);
    background: linear-gradient(135deg, var(--secondary-light) 0%, #A7F3D0 100%);
    border-color: var(--secondary);
    box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
}

.status-closed {
    color: #92400E;
    background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
    border-color: var(--warning);
    box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);
}

/* Icon styling */
.metric-icon {
    font-size: 1.5rem;
    opacity: 0.8;
}

/* Responsive design */
@media (max-width: 768px) {
    .metric-card-enhanced {
        height: 140px;
        padding: 1.5rem 1rem;
    }
    
    .metric-value-enhanced {
        font-size: 1.8rem;
    }
    
    .header-section {
        padding: 1.5rem;
        margin: 1rem 0;
    }
}
</style>
""", unsafe_allow_html=True)

# Enhanced Header Metrics Display
st.markdown('<div class="header-section">', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem; position: relative; z-index: 1;">
    <h1 style="color: var(--text-primary); font-size: 2.5rem; margin: 0; font-weight: 800;">
        📈 SPX Prophet Analytics
    </h1>
    <p style="color: var(--text-secondary); font-size: 1.1rem; margin: 0.5rem 0 0 0; font-weight: 500;">
        Real-time market analysis with advanced projections
    </p>
</div>
""", unsafe_allow_html=True)

# Enhanced metrics in a responsive grid
c1, c2, c3 = st.columns(3, gap="large")
now = datetime.now(CT_TZ)

with c1:
    st.markdown(
        f"""
<div class="metric-card-enhanced time-card">
    <div class="metric-title-enhanced">
        <span class="metric-icon">🕐</span>
        Current Time (CT)
    </div>
    <div class="metric-value-enhanced">
        {now.strftime("%H:%M:%S")}
    </div>
    <div class="metric-subtitle">
        {now.strftime("%A, %B %d, %Y")}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

with c2:
    is_wkday = now.weekday() < 5
    open_dt = now.replace(hour=8, minute=30, second=0, microsecond=0)
    close_dt = now.replace(hour=14, minute=30, second=0, microsecond=0)
    is_open = is_wkday and (open_dt <= now <= close_dt)
    
    status_class = "status-open" if is_open else "status-closed"
    card_class = "open" if is_open else "closed"
    status_text = "MARKET OPEN" if is_open else "MARKET CLOSED"
    status_icon = "🟢" if is_open else "🔴"
    
    st.markdown(
        f"""
<div class="metric-card-enhanced status-card {card_class}">
    <div class="metric-title-enhanced">
        <span class="metric-icon">📊</span>
        Market Status
    </div>
    <div class="metric-value-enhanced">
        <span class="status-badge-enhanced {status_class}">
            {status_icon} {status_text}
        </span>
    </div>
    <div class="metric-subtitle">
        RTH: 08:30–14:30 CT • Mon–Fri
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

with c3:
    slope_disp = current_slope()
    override_indicator = "🔧 OVERRIDE ACTIVE" if "slope_per_block" in st.session_state else "DEFAULT"
    override_class = "override-tag" if "slope_per_block" in st.session_state else "metric-subtitle"
    
    st.markdown(
        f"""
<div class="metric-card-enhanced slope-card">
    <div class="metric-title-enhanced">
        <span class="metric-icon">📐</span>
        Slope per 30min
    </div>
    <div class="metric-value-enhanced">
        ±{slope_disp:.3f}
    </div>
    <div class="{override_class}">
        {override_indicator if "slope_per_block" in st.session_state else "Top = +slope • Bottom = −slope"}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)

# Enhanced divider
st.markdown("""
<div style="margin: 3rem 0;">
    <hr style="border: none; height: 2px; background: linear-gradient(90deg, transparent, var(--primary) 20%, var(--secondary) 50%, var(--accent) 80%, transparent); opacity: 0.6;">
</div>
""", unsafe_allow_html=True)




# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED TABS SYSTEM WITH BEAUTIFUL STYLING
# ───────────────────────────────────────────────────────────────────────────────

# Additional CSS for enhanced tabs and content areas
st.markdown("""
<style>
/* Enhanced Tab System */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 0.5rem;
    box-shadow: var(--shadow-md);
    backdrop-filter: blur(12px);
    margin-bottom: 2rem;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    border-radius: 12px;
    padding: 1rem 2rem;
    font-weight: 600;
    font-size: 1rem;
    color: var(--text-secondary);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.stTabs [data-baseweb="tab"]:hover {
    background: var(--surface-hover);
    color: var(--primary);
    transform: translateY(-1px);
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: white;
    box-shadow: var(--shadow-md);
}

.stTabs [data-baseweb="tab"][aria-selected="true"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s;
}

.stTabs [data-baseweb="tab"][aria-selected="true"]:hover::before {
    left: 100%;
}

/* Enhanced Tab Content */
.stTabs [data-baseweb="tab-panel"] {
    background: var(--surface);
    border: 1px solid var(--border-light);
    border-radius: 20px;
    padding: 2rem;
    box-shadow: var(--shadow-glass);
    backdrop-filter: blur(16px);
    position: relative;
    overflow: hidden;
}

.stTabs [data-baseweb="tab-panel"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, 
        rgba(59, 130, 246, 0.01) 0%, 
        rgba(16, 185, 129, 0.01) 50%, 
        rgba(139, 92, 246, 0.01) 100%);
    pointer-events: none;
}

/* Section Headers in Tabs */
.tab-section-header {
    color: var(--text-primary);
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
    padding-bottom: 0.75rem;
    border-bottom: 3px solid;
    border-image: linear-gradient(90deg, var(--primary), var(--secondary)) 1;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.tab-subsection-header {
    color: var(--primary);
    font-size: 1.375rem;
    font-weight: 600;
    margin: 2rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    background: linear-gradient(135deg, var(--primary-light) 0%, rgba(59, 130, 246, 0.05) 100%);
    border: 1px solid var(--primary-light);
    border-radius: 12px;
}

/* Enhanced Form Controls in Tabs */
.tab-controls {
    background: var(--surface-elevated);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1.5rem 0;
    box-shadow: var(--shadow-sm);
}

.control-group {
    margin-bottom: 1rem;
}

.control-group:last-child {
    margin-bottom: 0;
}

/* Enhanced Info Messages */
.info-card {
    background: linear-gradient(135deg, var(--info-bg) 0%, rgba(59, 130, 246, 0.05) 100%);
    border: 1px solid var(--info-border);
    border-left: 4px solid var(--info);
    border-radius: 12px;
    padding: 1.5rem;
    color: var(--info);
    font-weight: 500;
    margin: 1.5rem 0;
    box-shadow: var(--shadow-sm);
}

.success-card {
    background: linear-gradient(135deg, var(--success-bg) 0%, rgba(16, 185, 129, 0.05) 100%);
    border: 1px solid var(--success-border);
    border-left: 4px solid var(--success);
    border-radius: 12px;
    padding: 1.5rem;
    color: var(--success);
    font-weight: 600;
    margin: 1.5rem 0;
    box-shadow: var(--shadow-sm);
}

.error-card {
    background: linear-gradient(135deg, var(--error-bg) 0%, rgba(239, 68, 68, 0.05) 100%);
    border: 1px solid var(--error-border);
    border-left: 4px solid var(--error);
    border-radius: 12px;
    padding: 1.5rem;
    color: var(--error);
    font-weight: 600;
    margin: 1.5rem 0;
    box-shadow: var(--shadow-sm);
}

/* Enhanced Data Tables */
.dataframe {
    background: var(--surface-elevated) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
}

.dataframe table {
    border-collapse: collapse !important;
}

.dataframe th {
    background: linear-gradient(135deg, var(--primary-light) 0%, rgba(59, 130, 246, 0.1) 100%) !important;
    color: var(--primary) !important;
    font-weight: 700 !important;
    padding: 1rem !important;
    border-bottom: 2px solid var(--primary-light) !important;
    text-align: center !important;
}

.dataframe td {
    padding: 0.875rem !important;
    border-bottom: 1px solid var(--border-light) !important;
    text-align: center !important;
    color: var(--text-primary) !important;
}

.dataframe tr:hover {
    background: var(--surface-hover) !important;
}

/* Loading Spinner Enhancement */
.stSpinner > div {
    border-color: var(--primary) !important;
}

/* Caption Styling */
.stCaption {
    background: var(--surface-elevated);
    border: 1px solid var(--border-light);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: var(--text-secondary);
    font-style: italic;
    margin: 1rem 0;
    box-shadow: var(--shadow-sm);
}

/* Two-column layout for stock swing info */
.swing-info {
    background: var(--surface-elevated);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: var(--shadow-sm);
    position: relative;
}

.swing-info::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--secondary), var(--primary));
    border-radius: 16px 16px 0 0;
}

.swing-high {
    border-left: 4px solid var(--secondary);
    padding-left: 1rem;
}

.swing-low {
    border-left: 4px solid var(--error);
    padding-left: 1rem;
}

.swing-price {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0.5rem 0;
}

.swing-time {
    font-size: 0.9rem;
    color: var(--text-secondary);
    font-family: 'Monaco', 'Menlo', monospace;
}
</style>
""", unsafe_allow_html=True)

# Enhanced Tabs System
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 SPX Anchors", 
    "📈 Stock Anchors", 
    "🔄 Signals & EMA", 
    "🧮 Contract Tool"
])

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 1: ENHANCED SPX ANCHORS                                                 ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab1:
    st.markdown('<h2 class="tab-section-header">🎯 SPX Close-Anchor Fan (3:00 PM CT)</h2>', unsafe_allow_html=True)
    
    if go_spx:
        with st.spinner("🔄 Building SPX fan & strategy analysis..."):
            # Fetch prev/proj for ^GSPC (fallback to SPY if ^GSPC empty)
            spx_prev = fetch_intraday("^GSPC", prev_day, prev_day)
            if spx_prev.empty:
                spx_prev = fetch_intraday("SPY", prev_day, prev_day)

            spx_proj = fetch_intraday("^GSPC", proj_day, proj_day)
            if spx_proj.empty:
                spx_proj = fetch_intraday("SPY", proj_day, proj_day)

            if spx_prev.empty or spx_proj.empty:
                st.markdown(
                    '<div class="error-card">❌ <strong>Market Data Error:</strong> Unable to fetch market data for the selected dates. Please try different dates or check your connection.</div>',
                    unsafe_allow_html=True
                )
            else:
                # Anchor close
                if use_manual_close:
                    anchor_close = float(manual_close_val)
                    anchor_time  = fmt_ct(datetime.combine(prev_day, time(15, 0)))
                    st.markdown(
                        f'<div class="success-card">✅ <strong>Manual Override Active:</strong> Using manual 3:00 PM CT close: <strong>{anchor_close:.2f}</strong></div>',
                        unsafe_allow_html=True
                    )
                else:
                    prev_3pm_close = get_prev_day_3pm_close(spx_prev, prev_day)
                    if prev_3pm_close is None:
                        st.markdown(
                            '<div class="error-card">❌ <strong>Data Error:</strong> Could not find a 3:00 PM CT close for the previous day. Try using manual override.</div>',
                            unsafe_allow_html=True
                        )
                        st.stop()
                    anchor_close = float(prev_3pm_close)
                    anchor_time  = fmt_ct(datetime.combine(prev_day, time(15, 0)))
                    st.markdown(
                        f'<div class="success-card">🎯 <strong>Anchor Established:</strong> Previous day 3:00 PM CT close: <strong>{anchor_close:.2f}</strong></div>',
                        unsafe_allow_html=True
                    )

                # Fan
                fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)

                # Strategy
                spx_proj_rth = between_time(spx_proj, RTH_START, RTH_END)
                if spx_proj_rth.empty:
                    st.markdown(
                        '<div class="error-card">❌ <strong>RTH Data Missing:</strong> No regular trading hours data available for the projection day.</div>',
                        unsafe_allow_html=True
                    )
                else:
                    strat_df = build_spx_strategy(spx_proj_rth, fan_df, anchor_close)

                    # Enhanced Fan Table Section
                    st.markdown('<h3 class="tab-subsection-header">🎯 Fan Lines (Top / Bottom @ 30-min intervals)</h3>', unsafe_allow_html=True)
                    st.markdown('<div class="tab-controls">', unsafe_allow_html=True)
                    st.dataframe(fan_df, use_container_width=True, hide_index=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Enhanced Strategy Table Section
                    st.markdown('<h3 class="tab-subsection-header">📋 Trading Strategy Analysis</h3>', unsafe_allow_html=True)
                    st.markdown(
                        '<div class="info-card">📊 <strong>Bias Logic:</strong> <strong>UP</strong> bias when current price ≥ 3:00 PM anchor close | <strong>DOWN</strong> bias when current price < anchor close</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown('<div class="tab-controls">', unsafe_allow_html=True)
                    st.dataframe(
                        strat_df[["Time","Price","Bias","EntrySide","Entry","TP1","TP2","Top","Bottom"]],
                        use_container_width=True, hide_index=True
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '''
<div class="info-card">
    <strong>🚀 Ready to Generate SPX Analysis</strong><br>
    Use the <strong>Control Center</strong> in the sidebar to:
    <ul style="margin: 1rem 0 0 1.5rem; color: var(--text-secondary);">
        <li>Select your previous trading day and projection day</li>
        <li>Optionally set a manual 3:00 PM CT close price</li>
        <li>Adjust slope parameters if needed</li>
        <li>Click <strong>"🔮 Generate SPX Fan & Strategy"</strong></li>
    </ul>
</div>
            ''',
            unsafe_allow_html=True
        )

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 2: ENHANCED STOCK ANCHORS                                               ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab2:
    st.markdown('<h2 class="tab-section-header">📈 Stock Anchor Lines (Mon/Tue swings → dual projections)</h2>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="info-card">📊 <strong>Analysis Method:</strong> We identify the highest swing high and lowest swing low from Monday + Tuesday combined data, then project an ascending line from the high and a descending line from the low using your per-ticker slope magnitude.</div>',
        unsafe_allow_html=True
    )

    # Enhanced Controls Section
    st.markdown('<div class="tab-controls">', unsafe_allow_html=True)
    
    core = list(STOCK_SLOPES.keys())
    cc1, cc2, cc3 = st.columns([1.4, 1, 1], gap="medium")
    
    with cc1:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        ticker = st.selectbox("📊 Select Ticker", core + ["Custom…"], index=0, key="stk_ticker", help="Choose from pre-configured tickers or enter a custom symbol")
        custom_ticker = ""
        if ticker == "Custom…":
            custom_ticker = st.text_input("Custom Symbol", value="", placeholder="e.g., AMD", help="Enter any valid ticker symbol")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with cc2:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        monday_date = st.date_input("📅 Monday Date", value=today_ct - timedelta(days=max(1, (today_ct.weekday()+6)%7 + 1)), help="The Monday for swing analysis")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with cc3:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        tuesday_date = st.date_input("📅 Tuesday Date", value=monday_date + timedelta(days=1), help="The Tuesday for swing analysis")
        st.markdown('</div>', unsafe_allow_html=True)

    # Slope and projection controls
    cc4, cc5 = st.columns([1.5, 1], gap="medium")
    
    with cc4:
        slope_mag_default = STOCK_SLOPES.get(ticker, 0.0150) if ticker != "Custom…" else 0.0150
        slope_mag = st.number_input("📐 Slope Magnitude (per 30min)", value=float(slope_mag_default), step=0.0001, format="%.4f", help=f"Default for {ticker}: {slope_mag_default:.4f}")
    
    with cc5:
        proj_day_stock = st.date_input("🎯 Projection Day", value=tuesday_date + timedelta(days=1), help="Day to project the anchor lines")

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Action Button
    run_stock = st.button("📈 Analyze Stock Anchors", type="primary", use_container_width=True)

    if run_stock:
        with st.spinner("🔄 Fetching data and computing projections..."):
            sym = custom_ticker.upper() if ticker == "Custom…" and custom_ticker else (ticker if ticker != "Custom…" else None)
            if not sym:
                st.markdown('<div class="error-card">❌ <strong>Input Error:</strong> Please enter a custom symbol.</div>', unsafe_allow_html=True)
                st.stop()

            mon = fetch_intraday(sym, monday_date, monday_date)
            tue = fetch_intraday(sym, tuesday_date, tuesday_date)
            if mon.empty and tue.empty:
                st.markdown(f'<div class="error-card">❌ <strong>Data Error:</strong> No data available for <strong>{sym}</strong> on the selected dates.</div>', unsafe_allow_html=True)
                st.stop()

            combined = mon if tue.empty else (tue if mon.empty else pd.concat([mon, tue]).sort_index())

            hi, lo = detect_absolute_swings(combined)
            if not hi or not lo:
                st.markdown('<div class="error-card">❌ <strong>Analysis Error:</strong> Could not detect swing highs and lows in the data.</div>', unsafe_allow_html=True)
                st.stop()

            (high_price, high_time) = hi
            (low_price,  low_time)  = lo
            high_time = fmt_ct(high_time); low_time = fmt_ct(low_time)

            proj_df = project_two_stock_lines(high_price, high_time, low_price, low_time, slope_mag, proj_day_stock)

            # Enhanced Results Display
            st.markdown('<h3 class="tab-subsection-header">📊 Swing Analysis Results</h3>', unsafe_allow_html=True)
            
            cA, cB = st.columns(2, gap="large")
            with cA:
                st.markdown(
                    f'''
<div class="swing-info swing-high">
    <h4 style="color: var(--secondary); margin: 0 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem;">
        📈 Swing High (Mon/Tue)
    </h4>
    <div class="swing-price">
        {sym} — High: <strong>{high_price:.2f}</strong>
    </div>
    <div class="swing-time">
        {high_time.strftime('%Y-%m-%d %H:%M CT')}
    </div>
</div>
                    ''',
                    unsafe_allow_html=True
                )
            with cB:
                st.markdown(
                    f'''
<div class="swing-info swing-low">
    <h4 style="color: var(--error); margin: 0 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem;">
        📉 Swing Low (Mon/Tue)
    </h4>
    <div class="swing-price">
        {sym} — Low: <strong>{low_price:.2f}</strong>
    </div>
    <div class="swing-time">
        {low_time.strftime('%Y-%m-%d %H:%M CT')}
    </div>
</div>
                    ''',
                    unsafe_allow_html=True
                )

            st.markdown('<h3 class="tab-subsection-header">🔧 RTH Projection Lines</h3>', unsafe_allow_html=True)
            st.markdown('<div class="tab-controls">', unsafe_allow_html=True)
            st.dataframe(proj_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)





# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 3: ENHANCED SIGNALS & EMA                                               ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab3:
    st.markdown('<h2 class="tab-section-header">🔄 Signals: Fan Touch + Same-Bar EMA 8/21 Confirmation</h2>', unsafe_allow_html=True)
    
    st.markdown(
        '''
<div class="info-card">
    <strong>🎯 Signal Detection Logic:</strong><br>
    We identify moments when price touches the fan lines (top or bottom) and simultaneously check for EMA 8/21 crossover confirmation within the same bar. This provides high-probability entry signals with technical confirmation.
</div>
        ''',
        unsafe_allow_html=True
    )

    # Enhanced Controls Section
    st.markdown('<div class="tab-controls">', unsafe_allow_html=True)
    
    colS1, colS2, colS3 = st.columns([1.2, 1, 1], gap="medium")
    
    with colS1:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        sig_symbol = st.selectbox(
            "📊 Analysis Symbol", 
            ["^GSPC", "SPY", "ES=F"], 
            index=0,
            help="Choose the symbol for signal analysis"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with colS2:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        sig_day = st.date_input(
            "📅 Analysis Day", 
            value=today_ct,
            help="Day to analyze for touch signals"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with colS3:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        interval_pref = st.selectbox(
            "⏱️ Time Interval", 
            ["1m", "5m", "30m"], 
            index=0, 
            help="1m requires recent dates (≤7 days). Falls back to 5m/30m if unavailable."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Enhanced Action Button
    run_sig = st.button("🔎 Analyze Touch Signals", type="primary", use_container_width=True)

    if run_sig:
        with st.spinner("🔄 Computing fan lines and analyzing signals..."):
            # Build fan for the day (needs previous day close at 3:00 PM CT)
            prev_day_sig = sig_day - timedelta(days=1)
            spx_prev = fetch_intraday("^GSPC", prev_day_sig, prev_day_sig)
            if spx_prev.empty and sig_symbol in ["^GSPC", "SPY"]:
                spx_prev = fetch_intraday("SPY", prev_day_sig, prev_day_sig)

            if spx_prev.empty:
                st.markdown(
                    '<div class="error-card">❌ <strong>Fan Generation Error:</strong> Could not build fan lines due to missing previous day data. Try a different date.</div>',
                    unsafe_allow_html=True
                )
                st.stop()

            prev_3pm_close = get_prev_day_3pm_close(spx_prev, prev_day_sig)
            if prev_3pm_close is None:
                st.markdown(
                    '<div class="error-card">❌ <strong>Anchor Error:</strong> Previous day 3:00 PM CT close not found. Fan lines cannot be generated.</div>',
                    unsafe_allow_html=True
                )
                st.stop()

            anchor_close = float(prev_3pm_close)
            anchor_time  = fmt_ct(datetime.combine(prev_day_sig, time(15, 0)))
            fan_df = project_fan_from_close(anchor_close, anchor_time, sig_day)

            # Display fan anchor info
            st.markdown(
                f'<div class="success-card">🎯 <strong>Fan Anchor:</strong> {prev_3pm_close:.2f} from {prev_day_sig.strftime("%Y-%m-%d")} 3:00 PM CT</div>',
                unsafe_allow_html=True
            )

            # Intraday data for signals: try requested interval, fallback gracefully
            intraday = fetch_intraday_interval(sig_symbol, sig_day, sig_day, interval_pref)
            fallback_interval = interval_pref
            
            if intraday.empty and interval_pref != "5m":
                intraday = fetch_intraday_interval(sig_symbol, sig_day, sig_day, "5m")
                fallback_interval = "5m"
            if intraday.empty and interval_pref != "30m":
                intraday = fetch_intraday_interval(sig_symbol, sig_day, sig_day, "30m")
                fallback_interval = "30m"

            if intraday.empty:
                st.markdown(
                    '<div class="error-card">❌ <strong>Data Error:</strong> No intraday data available for the analysis day. Try a different date or symbol.</div>',
                    unsafe_allow_html=True
                )
                st.stop()

            if fallback_interval != interval_pref:
                st.markdown(
                    f'<div class="info-card">ℹ️ <strong>Interval Fallback:</strong> Requested {interval_pref} not available, using {fallback_interval} interval instead.</div>',
                    unsafe_allow_html=True
                )

            # Map fan prices to nearest matching times by "HH:MM"
            fan_lu_top = {r['Time']: r['Top'] for _, r in fan_df.iterrows()}
            fan_lu_bot = {r['Time']: r['Bottom'] for _, r in fan_df.iterrows()}

            # Prepare EMA cross dataframe on same intraday interval
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

            st.markdown('<h3 class="tab-subsection-header">📡 Fan Touch + EMA Confirmation Analysis</h3>', unsafe_allow_html=True)
            
            if signals:
                st.markdown(
                    f'<div class="success-card">✅ <strong>Found {len(signals)} touch event(s)</strong> on {sig_day.strftime("%Y-%m-%d")} using {fallback_interval} interval</div>',
                    unsafe_allow_html=True
                )
                st.markdown('<div class="tab-controls">', unsafe_allow_html=True)
                signals_df = pd.DataFrame(signals)
                st.dataframe(signals_df, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="info-card">📊 <strong>No signals detected</strong> on {sig_day.strftime("%Y-%m-%d")} using {fallback_interval} interval. This could indicate a trending day with no fan touches or insufficient EMA confirmation moments.</div>',
                    unsafe_allow_html=True
                )

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 4: ENHANCED CONTRACT TOOL                                               ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tab4:
    st.markdown('<h2 class="tab-section-header">🧮 Contract Tool (Overnight → RTH Projection)</h2>', unsafe_allow_html=True)
    
    st.markdown(
        '''
<div class="info-card">
    <strong>📈 Contract Projection Method:</strong><br>
    Define two price points in time to establish a trend slope, then project that slope across Regular Trading Hours (RTH). Perfect for analyzing overnight contract movements and projecting into the trading session.
</div>
        ''',
        unsafe_allow_html=True
    )

    # Enhanced Two-Point Input Section
    st.markdown('<h3 class="tab-subsection-header">📍 Define Two Reference Points</h3>', unsafe_allow_html=True)
    
    st.markdown('<div class="tab-controls">', unsafe_allow_html=True)
    point_col1, point_col2 = st.columns(2, gap="large")
    
    with point_col1:
        st.markdown('<div style="background: var(--primary-light); border: 1px solid var(--primary); border-radius: 12px; padding: 1.5rem;">', unsafe_allow_html=True)
        st.markdown('<h4 style="color: var(--primary); margin: 0 0 1rem 0;">📍 Point 1 (Start)</h4>', unsafe_allow_html=True)
        
        p1_date = st.date_input("Date", value=today_ct - timedelta(days=1), key="p1_date", help="Starting reference date")
        p1_time = st.time_input("Time (CT)", value=time(20, 0), key="p1_time", help="Starting reference time in CT")
        p1_price = st.number_input(
            "Contract Price", 
            value=10.00, 
            min_value=0.01, 
            step=0.01, 
            format="%.2f", 
            key="p1_price",
            help="Contract price at this point"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with point_col2:
        st.markdown('<div style="background: var(--secondary-light); border: 1px solid var(--secondary); border-radius: 12px; padding: 1.5rem;">', unsafe_allow_html=True)
        st.markdown('<h4 style="color: var(--secondary); margin: 0 0 1rem 0;">📍 Point 2 (End)</h4>', unsafe_allow_html=True)
        
        p2_date = st.date_input("Date", value=today_ct, key="p2_date", help="Ending reference date")
        p2_time = st.time_input("Time (CT)", value=time(8, 0), key="p2_time", help="Ending reference time in CT")
        p2_price = st.number_input(
            "Contract Price", 
            value=12.00, 
            min_value=0.01, 
            step=0.01, 
            format="%.2f", 
            key="p2_price",
            help="Contract price at this point"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Projection Day Selection
    st.markdown('<div class="control-group" style="margin: 1.5rem 0;">', unsafe_allow_html=True)
    proj_day_ct = st.date_input(
        "🎯 RTH Projection Day", 
        value=p2_date,
        help="Day for which to generate RTH projections"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Enhanced Action Button
    run_ct = st.button("🧮 Generate Contract Projections", type="primary", use_container_width=True)

    if run_ct:
        with st.spinner("🔄 Computing contract slope and RTH projections..."):
            p1_dt = fmt_ct(datetime.combine(p1_date, p1_time))
            p2_dt = fmt_ct(datetime.combine(p2_date, p2_time))
            
            if p2_dt <= p1_dt:
                st.markdown(
                    '<div class="error-card">❌ <strong>Time Error:</strong> Point 2 must be chronologically after Point 1. Please adjust your dates and times.</div>',
                    unsafe_allow_html=True
                )
                st.stop()

            # slope per 30m blocks (skip maintenance & weekend)
            blocks = count_effective_blocks(p1_dt, p2_dt)
            slope_ct = (p2_price - p1_price) / blocks if blocks > 0 else 0.0

            # project across RTH
            rows = []
            for slot in rth_slots_ct(proj_day_ct):
                b = count_effective_blocks(p1_dt, slot)
                price = p1_price + slope_ct * b
                rows.append({
                    "Time": slot.strftime("%H:%M"),
                    "Contract_Price": round(price, 2),
                    "Blocks": round(b, 1)
                })
            proj_df = pd.DataFrame(rows)

            # Enhanced Analysis Summary
            st.markdown('<h3 class="tab-subsection-header">📊 Contract Analysis Summary</h3>', unsafe_allow_html=True)
            
            mc1, mc2, mc3, mc4 = st.columns(4, gap="medium")
            
            with mc1:
                st.markdown(
                    f'''
<div class="metric-card-enhanced">
    <div class="metric-title-enhanced">
        <span class="metric-icon">⏱️</span>
        Time Span
    </div>
    <div class="metric-value-enhanced">
        {(p2_dt-p1_dt).total_seconds()/3600:.1f}h
    </div>
    <div class="metric-subtitle">
        Total Duration
    </div>
</div>
                    ''',
                    unsafe_allow_html=True
                )
            
            with mc2:
                price_change = p2_price - p1_price
                change_color = "var(--secondary)" if price_change >= 0 else "var(--error)"
                change_icon = "📈" if price_change >= 0 else "📉"
                st.markdown(
                    f'''
<div class="metric-card-enhanced">
    <div class="metric-title-enhanced">
        <span class="metric-icon">{change_icon}</span>
        Price Change
    </div>
    <div class="metric-value-enhanced" style="color: {change_color};">
        {price_change:+.2f}
    </div>
    <div class="metric-subtitle">
        Point 1 → Point 2
    </div>
</div>
                    ''',
                    unsafe_allow_html=True
                )
            
            with mc3:
                st.markdown(
                    f'''
<div class="metric-card-enhanced">
    <div class="metric-title-enhanced">
        <span class="metric-icon">🧩</span>
        Effective Blocks
    </div>
    <div class="metric-value-enhanced">
        {blocks:.1f}
    </div>
    <div class="metric-subtitle">
        30-min periods
    </div>
</div>
                    ''',
                    unsafe_allow_html=True
                )
            
            with mc4:
                slope_color = "var(--secondary)" if slope_ct >= 0 else "var(--error)"
                slope_icon = "📐"
                st.markdown(
                    f'''
<div class="metric-card-enhanced">
    <div class="metric-title-enhanced">
        <span class="metric-icon">{slope_icon}</span>
        Slope / 30min
    </div>
    <div class="metric-value-enhanced" style="color: {slope_color};">
        {slope_ct:+.3f}
    </div>
    <div class="metric-subtitle">
        Rate of change
    </div>
</div>
                    ''',
                    unsafe_allow_html=True
                )

            # Enhanced RTH Projection Table
            st.markdown('<h3 class="tab-subsection-header">📊 RTH Contract Projections</h3>', unsafe_allow_html=True)
            
            st.markdown(
                f'''
<div class="success-card">
    📈 <strong>Projection Based On:</strong> {p1_dt.strftime("%Y-%m-%d %H:%M CT")} @ {p1_price:.2f} → {p2_dt.strftime("%Y-%m-%d %H:%M CT")} @ {p2_price:.2f}
</div>
                ''',
                unsafe_allow_html=True
            )
            
            st.markdown('<div class="tab-controls">', unsafe_allow_html=True)
            st.dataframe(proj_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# ENHANCED FOOTER UTILITIES
# ───────────────────────────────────────────────────────────────────────────────

# Enhanced Footer Section
st.markdown("""
<div style="margin: 4rem 0 2rem 0;">
    <hr style="border: none; height: 2px; background: linear-gradient(90deg, transparent, var(--primary) 20%, var(--secondary) 50%, var(--accent) 80%, transparent); opacity: 0.4;">
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="header-section" style="margin: 2rem 0;">', unsafe_allow_html=True)

st.markdown(
    '''
<div style="text-align: center; margin-bottom: 2rem; position: relative; z-index: 1;">
    <h3 style="color: var(--text-primary); margin: 0; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 0.75rem;">
        🔧 System Utilities
    </h3>
    <p style="color: var(--text-secondary); margin: 0.5rem 0 0 0; font-size: 1rem;">
        Test connections and verify system status
    </p>
</div>
    ''',
    unsafe_allow_html=True
)

colA, colB = st.columns([1, 2], gap="large")

with colA:
    st.markdown('<div class="tab-controls" style="text-align: center;">', unsafe_allow_html=True)
    if st.button("🔌 Test Data Connection", type="secondary", use_container_width=True):
        with st.spinner("🔄 Testing market data connection..."):
            td = fetch_intraday("^GSPC", today_ct - timedelta(days=3), today_ct)
            if td.empty:
                td = fetch_intraday("SPY", today_ct - timedelta(days=3), today_ct)
            if not td.empty:
                st.markdown(
                    f'<div class="success-card">✅ <strong>Connection Successful!</strong><br>Received {len(td)} data bars from the last 3 days.</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="error-card">❌ <strong>Connection Failed</strong><br>Unable to fetch market data. Please try different dates or check your internet connection.</div>',
                    unsafe_allow_html=True
                )
    st.markdown('</div>', unsafe_allow_html=True)

with colB:
    st.markdown(
        '''
<div class="info-card" style="margin: 0;">
    <strong>📋 System Information:</strong><br>
    <ul style="margin: 0.75rem 0 0 1.5rem; color: var(--text-secondary); line-height: 1.6;">
        <li><strong>Timezone:</strong> All times normalized to Central Time (CT)</li>
        <li><strong>SPX Anchor:</strong> Uses exact 3:00 PM CT close from previous day</li>
        <li><strong>Slope Application:</strong> Consistent slope methodology across all projections</li>
        <li><strong>Manual Override:</strong> Available for SPX close via sidebar controls</li>
        <li><strong>Data Source:</strong> Yahoo Finance via yfinance library</li>
    </ul>
</div>
        ''',
        unsafe_allow_html=True
    )

st.markdown('</div>', unsafe_allow_html=True)

# Final Enhanced Footer
st.markdown("""
<div style="text-align: center; margin: 3rem 0 2rem 0; padding: 2rem; background: var(--surface); border: 1px solid var(--border-light); border-radius: 20px; box-shadow: var(--shadow-sm);">
    <p style="color: var(--text-tertiary); font-size: 0.9rem; margin: 0; font-weight: 500;">
        🔮 <strong>SPX Prophet Analytics</strong> — Professional Market Analysis Platform<br>
        <span style="color: var(--text-muted); font-size: 0.8rem;">Built with precision • Designed for traders • Powered by advanced algorithms</span>
    </p>
</div>
""", unsafe_allow_html=True)
