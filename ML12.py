# app.py - SPX Prophet Complete Application with Overnight ES Analysis
# Enterprise Trading Analytics Platform
# SPX Anchors | BC Forecast | Plan Card

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

CT_TZ = pytz.timezone("America/Chicago")
RTH_START = "08:30"
RTH_END = "14:30"

# Fan slopes (asymmetric)
TOP_SLOPE_DEFAULT = 0.312
BOTTOM_SLOPE_DEFAULT = 0.25
NEUTRAL_BAND_DEFAULT = 0.20

# Volume analysis parameters
VOLUME_LOOKBACK = 20
VOLUME_SPIKE_THRESHOLD = 1.25
SESSION_VOLUME_WINDOWS = {
    "ASIA": [(19, 0), (1, 0)],      # 7PM-1AM CT
    "LONDON": [(1, 0), (7, 0)],     # 1AM-7AM CT  
    "PREMARKET": [(7, 0), (8, 30)]  # 7AM-8:30AM CT
}

# Time-based scoring parameters
TIME_DECAY_HOURS = 6
SESSION_MOMENTUM_LOOKBACK = 4

# Overnight analysis parameters
OVERNIGHT_START_HOUR = 17  # 5 PM CT
OVERNIGHT_END_HOUR = 8     # 8 AM CT (before RTH)
FAN_TOUCH_TOLERANCE = 2.0  # Points for considering a "touch"

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION & STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SPX Prophet - Enterprise Trading Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Complete Enterprise UI System - Fixed Typography
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --primary-50: #eff6ff;
    --primary-500: #3b82f6;
    --primary-600: #2563eb;
    --success-50: #f0fdf4;
    --success-500: #22c55e;
    --success-600: #16a34a;
    --danger-50: #fef2f2;
    --danger-500: #ef4444;
    --warning-50: #fffbeb;
    --warning-500: #f59e0b;
    --gray-50: #f8fafc;
    --gray-100: #f1f5f9;
    --gray-200: #e2e8f0;
    --gray-500: #64748b;
    --gray-700: #334155;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-tertiary: #64748b;
    --bg-primary: #ffffff;
    --border-light: #e2e8f0;
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-success: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
    --gradient-danger: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
    --gradient-warning: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    --gradient-neutral: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

html, body, [class*="css"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.main .block-container {
    padding: 1.5rem 1.5rem 2rem 1.5rem !important;
    max-width: 100% !important;
}

/* Enterprise Card System - Fixed Heights */
.enterprise-card {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 16px;
    padding: 20px;
    box-shadow: var(--shadow-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    margin-bottom: 1.5rem;
}

.enterprise-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-primary);
}

.enterprise-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
    border-color: var(--primary-500);
}

/* Fixed Metric Card Heights and Typography */
.metric-card {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 12px;
    padding: 16px;
    box-shadow: var(--shadow-md);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    height: auto;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-card:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary-500);
}

.metric-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

/* Fixed Icon Sizing */
.metric-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 600;
    background: var(--gradient-primary);
    color: white;
    box-shadow: var(--shadow-md);
    flex-shrink: 0;
}

.metric-icon.success { background: var(--gradient-success); }
.metric-icon.danger { background: var(--gradient-danger); }
.metric-icon.warning { background: var(--gradient-warning); }
.metric-icon.neutral { background: var(--gradient-neutral); }

/* Fixed Typography Sizes */
.metric-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
    line-height: 1.2;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 4px 0 2px 0;
    line-height: 1.1;
    font-family: 'JetBrains Mono', monospace;
    word-break: break-word;
}

.metric-subtext {
    font-size: 0.7rem;
    color: var(--text-tertiary);
    font-weight: 500;
    line-height: 1.3;
    margin-top: auto;
}

/* Status Badge System */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    border: 1px solid;
    transition: all 0.3s ease;
}

.badge-open {
    background: var(--success-50);
    border-color: var(--success-500);
    color: var(--success-600);
}

.badge-closed {
    background: var(--danger-50);
    border-color: var(--danger-500);
    color: var(--danger-500);
}

.badge-up {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-color: var(--success-500);
    color: var(--success-600);
    font-weight: 700;
}

.badge-down {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border-color: var(--danger-500);
    color: var(--danger-500);
    font-weight: 700;
}

.badge-neutral {
    background: var(--gray-100);
    border-color: var(--gray-500);
    color: var(--gray-700);
    font-weight: 700;
}

/* Main Header - Fixed Typography */
.main-header {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-primary);
}

.header-title {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 12px;
    line-height: 1.2;
}

.header-subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin: 6px 0 0 0;
    font-weight: 500;
    line-height: 1.4;
}

/* Button Styling */
.stButton > button {
    background: var(--gradient-primary) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
    padding: 10px 16px !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow-md) !important;
    height: 40px !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* Tab System */
.stTabs [data-baseweb="tab-list"] {
    background: var(--gray-100) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 12px !important;
    padding: 6px !important;
    margin-bottom: 24px !important;
    box-shadow: var(--shadow-md) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
    padding: 8px 16px !important;
    transition: all 0.3s ease !important;
}

.stTabs [aria-selected="true"] {
    background: var(--gradient-primary) !important;
    color: white !important;
    box-shadow: var(--shadow-md) !important;
}

/* Form Controls */
.stSelectbox > div > div {
    background: var(--bg-primary) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

.stNumberInput > div > div > input {
    background: var(--bg-primary) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

.stTextInput > div > div > input {
    background: var(--bg-primary) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* Dataframe Styling */
.stDataFrame {
    border: 2px solid var(--border-light) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    font-size: 0.8rem !important;
}

.stDataFrame table {
    font-size: 0.8rem !important;
}

.stDataFrame th {
    background: var(--gray-100) !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
}

/* Alert Styling for Overnight Analysis */
.overnight-alert {
    background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 20%);
    border: 2px solid #f59e0b;
    border-radius: 12px;
    padding: 16px;
    margin: 16px 0;
    color: #92400e;
    font-weight: 600;
}

.overnight-alert-success {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 20%);
    border: 2px solid #22c55e;
    color: #166534;
}

.overnight-alert-danger {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 20%);
    border: 2px solid #ef4444;
    color: #b91c1c;
}

/* Sidebar Styling */
.css-1d391kg {
    background: var(--gray-50) !important;
    border-right: 2px solid var(--border-light) !important;
}

.sidebar-section {
    background: var(--bg-primary) !important;
    border: 1px solid var(--border-light) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin-bottom: 16px !important;
    box-shadow: var(--shadow-md) !important;
}

/* Utility Classes */
.star-highlight {
    color: var(--warning-500) !important;
    font-weight: 700 !important;
}

.text-success { color: var(--success-600) !important; }
.text-danger { color: var(--danger-500) !important; }
.text-warning { color: var(--warning-500) !important; }

/* Animations */
@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-slide-in {
    animation: slideInUp 0.4s ease-out;
}

/* Responsive Design */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
    }
    
    .metric-card {
        min-height: 100px;
        padding: 12px;
    }
    
    .header-title {
        font-size: 1.5rem;
    }
    
    .metric-value {
        font-size: 1.25rem;
    }
    
    .enterprise-card {
        padding: 16px;
    }
}

/* Ensure text doesn't overflow */
* {
    box-sizing: border-box;
}

.metric-card * {
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CORE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def fmt_ct(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return CT_TZ.localize(dt)
    return dt.astimezone(CT_TZ)

def between_time(df: pd.DataFrame, start_str: str, end_str: str) -> pd.DataFrame:
    return df.between_time(start_str, end_str) if not df.empty else df

def rth_slots_ct(target_date: date) -> List[datetime]:
    start_dt = fmt_ct(datetime.combine(target_date, time(8, 30)))
    end_dt = fmt_ct(datetime.combine(target_date, time(14, 30)))
    slots, current = [], start_dt
    while current <= end_dt:
        slots.append(current)
        current += timedelta(minutes=30)
    return slots

def is_maintenance(dt: datetime) -> bool:
    return dt.hour == 16

def in_weekend_gap(dt: datetime) -> bool:
    weekday = dt.weekday()
    if weekday == 5:
        return True
    if weekday == 6 and dt.hour < 17:
        return True
    if weekday == 4 and dt.hour >= 17:
        return True
    return False

def count_effective_blocks(start: datetime, end: datetime) -> float:
    if end <= start:
        return 0.0
    blocks, current = 0, start
    while current < end:
        next_slot = current + timedelta(minutes=30)
        if not is_maintenance(next_slot) and not in_weekend_gap(next_slot):
            blocks += 1
        current = next_slot
    return float(blocks)

def ensure_ohlc_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns]
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
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
    start_dt = fmt_ct(datetime.combine(start_d, time(0, 0)))
    end_dt = fmt_ct(datetime.combine(end_d, time(23, 59)))
    return df.loc[start_dt:end_dt]

@st.cache_data(ttl=120, show_spinner=False)
def fetch_intraday(symbol: str, start_d: date, end_d: date, interval: str) -> pd.DataFrame:
    try:
        ticker = yf.Ticker(symbol)
        if interval in ["1m", "2m", "5m", "15m"]:
            days = max(1, min(7, (end_d - start_d).days + 2))
            df = ticker.history(
                period=f"{days}d",
                interval=interval,
                prepost=True,
                auto_adjust=False,
                back_adjust=False
            )
            df = normalize_to_ct(df, start_d - timedelta(days=1), end_d + timedelta(days=1))
            start_filter = fmt_ct(datetime.combine(start_d, time(0, 0)))
            end_filter = fmt_ct(datetime.combine(end_d, time(23, 59)))
            df = df.loc[start_filter:end_filter]
        else:
            df = ticker.history(
                start=(start_d - timedelta(days=5)).strftime("%Y-%m-%d"),
                end=(end_d + timedelta(days=2)).strftime("%Y-%m-%d"),
                interval=interval,
                prepost=True,
                auto_adjust=False,
                back_adjust=False
            )
            df = normalize_to_ct(df, start_d, end_d)
        return df
    except Exception:
        return pd.DataFrame()

def resample_to_30m_ct(min_df: pd.DataFrame) -> pd.DataFrame:
    if min_df.empty or not isinstance(min_df.index, pd.DatetimeIndex):
        return pd.DataFrame()
    df = min_df.sort_index()
    agg_rules = {}
    if "Open" in df.columns:
        agg_rules["Open"] = "first"
    if "High" in df.columns:
        agg_rules["High"] = "max"
    if "Low" in df.columns:
        agg_rules["Low"] = "min"
    if "Close" in df.columns:
        agg_rules["Close"] = "last"
    if "Volume" in df.columns:
        agg_rules["Volume"] = "sum"
    resampled = df.resample("30T", label="right", closed="right").agg(agg_rules)
    ohlc_cols = [c for c in ["Open", "High", "Low", "Close"] if c in resampled.columns]
    resampled = resampled.dropna(subset=ohlc_cols, how="any")
    return resampled

# ═══════════════════════════════════════════════════════════════════════════════
# ES→SPX OFFSET CALCULATION
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_es_spx_offset(prev_day: date, spx_anchor_close: float, spx_anchor_time: datetime) -> Tuple[Optional[float], str]:
    """
    Calculate ES→SPX offset at the anchor time.
    Returns (offset, method_used)
    """
    # Try to get ES price at the same time as SPX anchor
    for interval in ["1m", "5m", "30m"]:
        es_data = fetch_intraday("ES=F", prev_day, prev_day, interval)
        if es_data.empty:
            continue
            
        # Find ES close nearest to SPX anchor time
        time_window = timedelta(minutes=30)
        start_window = spx_anchor_time - time_window
        end_window = spx_anchor_time + time_window
        
        es_window = es_data.loc[start_window:end_window]
        if not es_window.empty:
            es_close = float(es_window["Close"].iloc[-1])
            offset = es_close - spx_anchor_close
            return offset, f"Direct ({interval})"
    
    # Fallback: Calculate recent median offset
    offsets = []
    for i in range(1, 8):  # Look back 7 days
        check_day = prev_day - timedelta(days=i)
        
        # Get SPX at 3PM
        spx_check = fetch_intraday("^GSPC", check_day, check_day, "30m")
        if spx_check.empty:
            continue
            
        target_3pm = fmt_ct(datetime.combine(check_day, time(15, 0)))
        spx_before_3pm = spx_check.loc[:target_3pm]
        if spx_before_3pm.empty:
            continue
            
        spx_3pm = float(spx_before_3pm["Close"].iloc[-1])
        spx_3pm_time = spx_before_3pm.index[-1]
        
        # Get ES at same time
        es_check = fetch_intraday("ES=F", check_day, check_day, "5m")
        if es_check.empty:
            continue
            
        es_window = es_check.loc[spx_3pm_time-timedelta(minutes=15):spx_3pm_time+timedelta(minutes=15)]
        if not es_window.empty:
            es_3pm = float(es_window["Close"].iloc[-1])
            offsets.append(es_3pm - spx_3pm)
    
    if offsets:
        median_offset = float(np.median(offsets))
        return median_offset, f"Median ({len(offsets)} days)"
    
    return None, "Failed"

# ═══════════════════════════════════════════════════════════════════════════════
# OVERNIGHT ES ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_overnight_es(prev_day: date, proj_day: date) -> pd.DataFrame:
    """
    Fetch overnight ES futures data from 5PM prev_day to 8:30AM proj_day.
    """
    start_time = fmt_ct(datetime.combine(prev_day, time(OVERNIGHT_START_HOUR, 0)))
    end_time = fmt_ct(datetime.combine(proj_day, time(OVERNIGHT_END_HOUR, 30)))
    
    # Try different intervals for best coverage
    for interval in ["30m", "5m", "1m"]:
        es_data = fetch_intraday("ES=F", prev_day, proj_day, interval)
        if not es_data.empty:
            overnight_data = es_data.loc[start_time:end_time]
            if not overnight_data.empty:
                # Resample to 30m if needed
                if interval in ["5m", "1m"]:
                    return resample_to_30m_ct(overnight_data)
                return overnight_data
    
    return pd.DataFrame()

def analyze_overnight_fan_interactions(es_data: pd.DataFrame, es_spx_offset: float, 
                                     anchor_close: float, anchor_time: datetime) -> Dict:
    """
    Analyze overnight ES interactions with projected SPX fan levels.
    """
    if es_data.empty:
        return {"interactions": [], "summary": "No overnight data available"}
    
    # Convert ES to SPX equivalent
    spx_equivalent = es_data.copy()
    for col in ["Open", "High", "Low", "Close"]:
        if col in spx_equivalent.columns:
            spx_equivalent[col] = spx_equivalent[col] - es_spx_offset
    
    # Get fan slopes
    top_slope, bottom_slope = get_current_slopes()
    
    interactions = []
    session_summary = {
        "total_touches": 0,
        "top_touches": 0,
        "bottom_touches": 0,
        "breakouts": 0,
        "key_levels": [],
        "directional_bias": "NEUTRAL",
        "strength": 0
    }
    
    for idx, row in spx_equivalent.iterrows():
        # Calculate fan levels at this time
        blocks_from_anchor = count_effective_blocks(anchor_time, idx)
        fan_top = anchor_close + (top_slope * blocks_from_anchor)
        fan_bottom = anchor_close - (bottom_slope * blocks_from_anchor)
        
        high = float(row["High"])
        low = float(row["Low"])
        close = float(row["Close"])
        
        # Check for fan interactions
        interaction_type = None
        
        # Top interactions
        if abs(high - fan_top) <= FAN_TOUCH_TOLERANCE:
            if close < fan_top:
                interaction_type = "TOP_REJECTION"
                session_summary["top_touches"] += 1
            elif close > fan_top:
                interaction_type = "TOP_BREAKOUT"
                session_summary["breakouts"] += 1
        
        # Bottom interactions  
        elif abs(low - fan_bottom) <= FAN_TOUCH_TOLERANCE:
            if close > fan_bottom:
                interaction_type = "BOTTOM_BOUNCE"
                session_summary["bottom_touches"] += 1
            elif close < fan_bottom:
                interaction_type = "BOTTOM_BREAKDOWN"
                session_summary["breakouts"] += 1
        
        # Clear breakouts
        elif high > fan_top + FAN_TOUCH_TOLERANCE:
            interaction_type = "ABOVE_FAN"
        elif low < fan_bottom - FAN_TOUCH_TOLERANCE:
            interaction_type = "BELOW_FAN"
        
        if interaction_type:
            interactions.append({
                "time": idx.strftime("%H:%M"),
                "datetime": idx,
                "spx_equiv_close": round(close, 2),
                "fan_top": round(fan_top, 2),
                "fan_bottom": round(fan_bottom, 2),
                "interaction": interaction_type,
                "significance": calculate_interaction_significance(interaction_type, close, fan_top, fan_bottom)
            })
            
            session_summary["total_touches"] += 1
    
    # Determine overall directional bias
    if interactions:
        latest_interaction = interactions[-1]
        latest_close = latest_interaction["spx_equiv_close"]
        latest_top = latest_interaction["fan_top"]
        latest_bottom = latest_interaction["fan_bottom"]
        
        if latest_close > latest_top:
            session_summary["directional_bias"] = "BULLISH"
            session_summary["strength"] = min(100, ((latest_close - latest_top) / (latest_top - latest_bottom)) * 100)
        elif latest_close < latest_bottom:
            session_summary["directional_bias"] = "BEARISH"
            session_summary["strength"] = min(100, ((latest_bottom - latest_close) / (latest_top - latest_bottom)) * 100)
        else:
            # Inside fan - check proximity
            fan_center = (latest_top + latest_bottom) / 2
            if latest_close > fan_center:
                session_summary["directional_bias"] = "SLIGHTLY_BULLISH"
                session_summary["strength"] = 25
            else:
                session_summary["directional_bias"] = "SLIGHTLY_BEARISH"
                session_summary["strength"] = 25
    
    return {
        "interactions": interactions,
        "summary": session_summary,
        "last_spx_equiv": round(spx_equivalent["Close"].iloc[-1], 2) if not spx_equivalent.empty else None
    }

def calculate_interaction_significance(interaction_type: str, close: float, fan_top: float, fan_bottom: float) -> str:
    """Calculate significance of fan interaction."""
    fan_width = fan_top - fan_bottom
    
    if interaction_type in ["TOP_BREAKOUT", "BOTTOM_BREAKDOWN"]:
        return "HIGH"
    elif interaction_type in ["TOP_REJECTION", "BOTTOM_BOUNCE"]:
        return "MEDIUM"
    elif interaction_type in ["ABOVE_FAN", "BELOW_FAN"]:
        return "HIGH"
    else:
        return "LOW"

def generate_rth_entry_signals(overnight_analysis: Dict, current_fan_levels: Dict) -> List[Dict]:
    """
    Generate RTH entry signals based on overnight ES analysis.
    """
    if not overnight_analysis["interactions"]:
        return [{"signal": "NO_SETUP", "description": "No overnight fan interactions detected", "confidence": "LOW"}]
    
    signals = []
    summary = overnight_analysis["summary"]
    bias = summary["directional_bias"]
    strength = summary["strength"]
    
    # Generate signals based on overnight bias
    if bias == "BULLISH":
        signals.append({
            "signal": "LONG_BIAS",
            "description": f"Overnight ES broke above fan top. Look for long entries on any dip toward {current_fan_levels['bottom']:.2f}",
            "entry_level": current_fan_levels["bottom"],
            "stop_level": current_fan_levels["bottom"] - 10,
            "target_level": current_fan_levels["top"] + (current_fan_levels["top"] - current_fan_levels["bottom"]) * 0.5,
            "confidence": "HIGH" if strength > 50 else "MEDIUM"
        })
    elif bias == "BEARISH":
        signals.append({
            "signal": "SHORT_BIAS", 
            "description": f"Overnight ES broke below fan bottom. Look for short entries on any rally toward {current_fan_levels['top']:.2f}",
            "entry_level": current_fan_levels["top"],
            "stop_level": current_fan_levels["top"] + 10,
            "target_level": current_fan_levels["bottom"] - (current_fan_levels["top"] - current_fan_levels["bottom"]) * 0.5,
            "confidence": "HIGH" if strength > 50 else "MEDIUM"
        })
    elif bias in ["SLIGHTLY_BULLISH", "SLIGHTLY_BEARISH"]:
        signals.append({
            "signal": "RANGE_TRADE",
            "description": f"ES stayed within fan overnight. Trade the range: Buy near {current_fan_levels['bottom']:.2f}, Sell near {current_fan_levels['top']:.2f}",
            "entry_level": current_fan_levels["bottom"] if bias == "SLIGHTLY_BULLISH" else current_fan_levels["top"],
            "confidence": "MEDIUM"
        })
    
    # Add volume-based signals if significant touches occurred
    if summary["total_touches"] >= 3:
        signals.append({
            "signal": "HIGH_CONVICTION",
            "description": f"Multiple fan interactions ({summary['total_touches']}) overnight indicate strong levels. Respect fan boundaries.",
            "confidence": "HIGH"
        })
    
    return signals

# ═══════════════════════════════════════════════════════════════════════════════
# EXISTING TRADING LOGIC (UNCHANGED)
# ═══════════════════════════════════════════════════════════════════════════════

def get_spx_anchor_prevday(prev_day: date) -> Tuple[Optional[float], Optional[datetime], bool]:
    target_time = fmt_ct(datetime.combine(prev_day, time(15, 0)))
    for interval in ["30m", "5m", "1m"]:
        spx_data = fetch_intraday("^GSPC", prev_day, prev_day, interval)
        if spx_data.empty:
            continue
        before_target = spx_data.loc[:target_time]
        if before_target.empty:
            continue
        anchor_close = float(before_target["Close"].iloc[-1])
        anchor_time = before_target.index[-1].to_pydatetime()
        return anchor_close, fmt_ct(anchor_time), False
    return None, None, True

def get_current_slopes() -> Tuple[float, float]:
    top_slope = float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT))
    bottom_slope = float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT))
    return top_slope, bottom_slope

def project_fan_levels(anchor_close: float, anchor_time: datetime, target_day: date) -> pd.DataFrame:
    top_slope, bottom_slope = get_current_slopes()
    rth_slots = rth_slots_ct(target_day)
    
    projections = []
    for slot_time in rth_slots:
        effective_blocks = count_effective_blocks(anchor_time, slot_time)
        top_level = anchor_close + (top_slope * effective_blocks)
        bottom_level = anchor_close - (bottom_slope * effective_blocks)
        fan_width = top_level - bottom_level
        
        projections.append({
            "DateTime": slot_time,
            "Time": slot_time.strftime("%H:%M"),
            "Top": round(top_level, 2),
            "Bottom": round(bottom_level, 2),
            "Fan_Width": round(fan_width, 2),
        })
    
    return pd.DataFrame(projections)

def determine_bias(price: float, top_level: float, bottom_level: float, 
                  neutral_band_pct: float = NEUTRAL_BAND_DEFAULT) -> str:
    if price > top_level:
        return "UP"
    if price < bottom_level:
        return "DOWN"
    
    fan_width = top_level - bottom_level
    fan_center = (top_level + bottom_level) / 2
    neutral_band_size = neutral_band_pct * fan_width
    
    if abs(price - fan_center) <= neutral_band_size:
        return "NEUTRAL"
    
    distance_to_top = top_level - price
    distance_to_bottom = price - bottom_level
    
    return "UP" if distance_to_bottom < distance_to_top else "DOWN"

def calculate_bias_strength(price: float, top_level: float, bottom_level: float) -> float:
    if price > top_level:
        distance_above = price - top_level
        fan_width = top_level - bottom_level
        strength = min(100, 50 + (distance_above / fan_width) * 50)
    elif price < bottom_level:
        distance_below = bottom_level - price
        fan_width = top_level - bottom_level
        strength = min(100, 50 + (distance_below / fan_width) * 50)
    else:
        fan_center = (top_level + bottom_level) / 2
        distance_from_center = abs(price - fan_center)
        half_width = (top_level - bottom_level) / 2
        strength = (distance_from_center / half_width) * 50
    
    return round(strength, 1)

def build_spx_strategy_table(anchor_close: float, anchor_time: datetime, 
                            target_day: date, spx_rth_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    fan_df = project_fan_levels(anchor_close, anchor_time, target_day)
    
    strategy_rows = []
    neutral_band = float(st.session_state.get("neutral_band_pct", NEUTRAL_BAND_DEFAULT))
    
    for _, row in fan_df.iterrows():
        slot_time = row["Time"]
        top_level = row["Top"]
        bottom_level = row["Bottom"]
        fan_width = row["Fan_Width"]
        
        actual_price = None
        if spx_rth_data is not None and not spx_rth_data.empty:
            slot_datetime = row["DateTime"]
            if slot_datetime in spx_rth_data.index:
                actual_price = float(spx_rth_data.loc[slot_datetime, "Close"])
        
        if actual_price is not None:
            bias = determine_bias(actual_price, top_level, bottom_level, neutral_band)
            bias_strength = calculate_bias_strength(actual_price, top_level, bottom_level)
            price_display = f"{actual_price:.2f}"
            entry_signal = generate_entry_signal(actual_price, top_level, bottom_level, bias)
        else:
            bias = "NO DATA"
            bias_strength = 0
            price_display = "—"
            entry_signal = "Fan projection only"
        
        slot_display = "⭐ 8:30" if slot_time == "08:30" else slot_time
        
        strategy_rows.append({
            "Slot": slot_display,
            "Time": slot_time,
            "Price": price_display,
            "Bias": bias,
            "Strength": f"{bias_strength:.1f}%" if bias_strength > 0 else "—",
            "Top": top_level,
            "Bottom": bottom_level,
            "Width": fan_width,
            "Entry_Signal": entry_signal
        })
    
    return pd.DataFrame(strategy_rows)

def generate_entry_signal(price: float, top: float, bottom: float, bias: str) -> str:
    if bias == "UP":
        if price > top:
            return "Long breakout above fan"
        else:
            return "Long on dip to bottom"
    elif bias == "DOWN":
        if price < bottom:
            return "Short breakdown below fan"
        else:
            return "Short on rally to top"
    elif bias == "NEUTRAL":
        return "Range-bound - wait for breakout"
    else:
        return "—"

def project_contract_line(bounce1_time: datetime, bounce1_price: float,
                         bounce2_time: datetime, bounce2_price: float,
                         target_day: date, line_label: str) -> Tuple[pd.DataFrame, float]:
    effective_blocks = count_effective_blocks(bounce1_time, bounce2_time)
    if effective_blocks <= 0:
        slope = 0.0
    else:
        slope = (bounce2_price - bounce1_price) / effective_blocks
    
    rth_slots = rth_slots_ct(target_day)
    projections = []
    
    for slot_time in rth_slots:
        blocks_from_bounce1 = count_effective_blocks(bounce1_time, slot_time)
        projected_price = bounce1_price + (slope * blocks_from_bounce1)
        
        projections.append({
            "Time": slot_time.strftime("%H:%M"),
            line_label: round(projected_price, 2)
        })
    
    return pd.DataFrame(projections), slope

def calculate_expected_exit_time(bounce1_time: datetime, high1_time: datetime,
                               bounce2_time: datetime, high2_time: datetime,
                               target_day: date) -> str:
    duration1 = count_effective_blocks(bounce1_time, high1_time)
    duration2 = count_effective_blocks(bounce2_time, high2_time)
    
    durations = [d for d in [duration1, duration2] if d > 0]
    if not durations:
        return "N/A"
    
    median_duration = int(np.median(durations))
    
    exit_candidate = bounce2_time
    blocks_added = 0
    
    while blocks_added < median_duration:
        exit_candidate += timedelta(minutes=30)
        if not is_maintenance(exit_candidate) and not in_weekend_gap(exit_candidate):
            blocks_added += 1
    
    rth_slots = rth_slots_ct(target_day)
    for slot in rth_slots:
        if slot >= exit_candidate:
            return slot.strftime("%H:%M")
    
    return "After RTH"

# ═══════════════════════════════════════════════════════════════════════════════
# UI COMPONENT BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def create_metric_card(title: str, value: str, subtext: str = "", icon: str = "📊", 
                      card_type: str = "primary") -> str:
    return f"""
    <div class="metric-card animate-slide-in">
        <div class="metric-header">
            <div class="metric-icon {card_type}">{icon}</div>
            <div class="metric-title">{title}</div>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtext">{subtext}</div>
    </div>
    """

def create_status_badge(text: str, status: str = "neutral") -> str:
    return f'<span class="status-badge badge-{status}">{text}</span>'

def create_header_section(title: str, subtitle: str = "") -> str:
    return f"""
    <div class="main-header animate-slide-in">
        <h1 class="header-title">{title}</h1>
        {f'<p class="header-subtitle">{subtitle}</p>' if subtitle else ''}
    </div>
    """

def create_overnight_alert(analysis: Dict, signal_type: str) -> str:
    """Create styled alert box for overnight analysis."""
    css_class = f"overnight-alert-{signal_type}" if signal_type in ["success", "danger"] else "overnight-alert"
    
    summary = analysis["summary"]
    bias = summary["directional_bias"]
    strength = summary["strength"]
    
    if bias == "BULLISH":
        icon = "📈"
        message = f"BULLISH SETUP: ES broke above fan overnight (Strength: {strength:.0f}%)"
    elif bias == "BEARISH":
        icon = "📉"
        message = f"BEARISH SETUP: ES broke below fan overnight (Strength: {strength:.0f}%)"
    else:
        icon = "⚖️"
        message = f"NEUTRAL: ES stayed within fan range overnight"
    
    return f"""
    <div class="{css_class}">
        <strong>{icon} OVERNIGHT ANALYSIS:</strong> {message}
        <br><small>Total fan interactions: {summary['total_touches']} | Top touches: {summary['top_touches']} | Bottom touches: {summary['bottom_touches']}</small>
    </div>
    """

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def render_main_header():
    current_time = datetime.now(CT_TZ)
    
    st.markdown(create_header_section(
        "⚡ SPX Prophet",
        "Enterprise Trading Analytics Platform - SPX Anchors | BC Forecast | Plan Card"
    ), unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        time_str = current_time.strftime("%H:%M:%S")
        date_str = current_time.strftime("%a, %b %d")
        st.markdown(create_metric_card(
            "Current Time (CT)", 
            time_str,
            date_str,
            "🕒",
            "primary"
        ), unsafe_allow_html=True)
    
    with col2:
        is_weekday = current_time.weekday() < 5
        market_open = current_time.replace(hour=8, minute=30, second=0, microsecond=0)
        market_close = current_time.replace(hour=14, minute=30, second=0, microsecond=0)
        is_open = is_weekday and (market_open <= current_time <= market_close)
        
        status_text = "OPEN" if is_open else "CLOSED"
        status_type = "success" if is_open else "danger"
        status_subtext = "RTH: 08:30-14:30 CT"
        
        st.markdown(create_metric_card(
            "Market Status",
            status_text,
            status_subtext,
            "📊",
            status_type
        ), unsafe_allow_html=True)
    
    with col3:
        top_slope, bottom_slope = get_current_slopes()
        slope_text = f"+{top_slope:.3f}"
        override_active = ("top_slope_per_block" in st.session_state or 
                          "bottom_slope_per_block" in st.session_state)
        slope_subtext = f"Bot: -{bottom_slope:.3f}"
        slope_type = "warning" if override_active else "neutral"
        
        st.markdown(create_metric_card(
            "SPX Slopes /30m",
            slope_text,
            slope_subtext,
            "📐",
            slope_type
        ), unsafe_allow_html=True)
    
    with col4:
        try:
            test_data = fetch_intraday("^GSPC", current_time.date() - timedelta(days=1), 
                                     current_time.date(), "30m")
            connectivity = "CONNECTED" if not test_data.empty else "LIMITED"
            conn_type = "success" if not test_data.empty else "warning"
            conn_subtext = f"{len(test_data)} bars" if not test_data.empty else "Check source"
        except:
            connectivity = "ERROR"
            conn_type = "danger"
            conn_subtext = "Data fetch failed"
        
        st.markdown(create_metric_card(
            "Data Status",
            connectivity,
            conn_subtext,
            "🔗",
            conn_type
        ), unsafe_allow_html=True)

def render_sidebar_controls():
    st.sidebar.title("🎛️ Controls")
    
    today_ct = datetime.now(CT_TZ).date()
    
    prev_day = st.sidebar.date_input(
        "Previous Trading Day",
        value=today_ct - timedelta(days=1),
        help="Day to get SPX anchor close ≤ 3:00 PM CT"
    )
    
    proj_day = st.sidebar.date_input(
        "Projection Day", 
        value=prev_day + timedelta(days=1),
        help="Target day for RTH projections"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("✍️ Manual Anchor")
    
    use_manual = st.sidebar.checkbox(
        "Override with manual 3:00 PM close",
        value=False,
        help="Use custom anchor instead of fetched ^GSPC data"
    )
    
    manual_value = st.sidebar.number_input(
        "Manual Anchor Close",
        value=6400.00,
        step=0.25,
        format="%.2f",
        disabled=not use_manual,
        help="SPX close price for anchor calculations"
    )
    
    st.sidebar.markdown("---")
    
    refresh_anchors = st.sidebar.button(
        "🔮 Refresh SPX Anchors",
        type="primary",
        use_container_width=True,
        help="Rebuild fan projections and strategy table"
    )
    
    return {
        "prev_day": prev_day,
        "proj_day": proj_day,
        "use_manual": use_manual,
        "manual_value": manual_value,
        "refresh_anchors": refresh_anchors
    }

def render_spx_anchors_tab(controls: Dict):
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            🎯 SPX Anchors - Fan Analysis & Overnight ES Signals
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Previous day anchor projection with overnight ES analysis for RTH entry signals
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if controls["refresh_anchors"] or "anchors_data" not in st.session_state:
        with st.spinner("Building SPX anchor analysis with overnight ES signals..."):
            try:
                # Get SPX anchor
                if controls["use_manual"]:
                    anchor_close = float(controls["manual_value"])
                    anchor_time = fmt_ct(datetime.combine(controls["prev_day"], time(15, 0)))
                    anchor_label = " (Manual)"
                    estimated = False
                else:
                    anchor_close, anchor_time, estimated = get_spx_anchor_prevday(controls["prev_day"])
                    if anchor_close is None:
                        st.error("❌ Could not resolve SPX anchor for previous day")
                        return
                    anchor_label = " (Estimated)" if estimated else ""
                
                # Calculate ES→SPX offset
                es_spx_offset, offset_method = calculate_es_spx_offset(controls["prev_day"], anchor_close, anchor_time)
                
                # Fetch overnight ES data
                overnight_es = fetch_overnight_es(controls["prev_day"], controls["proj_day"])
                
                # Analyze overnight ES interactions with fan
                overnight_analysis = None
                if not overnight_es.empty and es_spx_offset is not None:
                    overnight_analysis = analyze_overnight_fan_interactions(
                        overnight_es, es_spx_offset, anchor_close, anchor_time
                    )
                
                # Get RTH SPX data for comparison
                spx_rth_data = fetch_intraday("^GSPC", controls["proj_day"], controls["proj_day"], "30m")
                spx_rth_data = between_time(spx_rth_data, RTH_START, RTH_END) if not spx_rth_data.empty else pd.DataFrame()
                
                # Build strategy table
                strategy_df = build_spx_strategy_table(
                    anchor_close, anchor_time, controls["proj_day"], spx_rth_data
                )
                
                # Generate RTH entry signals from overnight analysis
                rth_signals = []
                if overnight_analysis:
                    # Get current fan levels (8:30 AM)
                    fan_830 = strategy_df[strategy_df['Time'] == '08:30']
                    if not fan_830.empty:
                        current_levels = {
                            "top": fan_830['Top'].iloc[0],
                            "bottom": fan_830['Bottom'].iloc[0]
                        }
                        rth_signals = generate_rth_entry_signals(overnight_analysis, current_levels)
                
                # Store results
                st.session_state["anchors_data"] = {
                    "anchor_close": anchor_close,
                    "anchor_time": anchor_time,
                    "anchor_label": anchor_label,
                    "strategy_df": strategy_df,
                    "spx_data": spx_rth_data,
                    "estimated": estimated,
                    "es_spx_offset": es_spx_offset,
                    "offset_method": offset_method,
                    "overnight_analysis": overnight_analysis,
                    "rth_signals": rth_signals
                }
                
            except Exception as e:
                st.error(f"Error building anchor analysis: {str(e)}")
                return
    
    if "anchors_data" in st.session_state:
        data = st.session_state["anchors_data"]
        
        # Main metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Anchor Close",
                f"{data['anchor_close']:.2f}",
                f"Prev day ≤3PM{data['anchor_label']}",
                "⚓",
                "warning" if data['estimated'] else "primary"
            ), unsafe_allow_html=True)
        
        with col2:
            if data['es_spx_offset'] is not None:
                st.markdown(create_metric_card(
                    "ES→SPX Offset",
                    f"{data['es_spx_offset']:+.2f}",
                    f"Method: {data['offset_method']}",
                    "🔄",
                    "success"
                ), unsafe_allow_html=True)
            else:
                st.markdown(create_metric_card(
                    "ES→SPX Offset",
                    "Failed",
                    "Could not calculate",
                    "❌",
                    "danger"
                ), unsafe_allow_html=True)
        
        with col3:
            df = data['strategy_df']
            width_830 = df[df['Time'] == '08:30']['Width'].iloc[0] if not df.empty else 0
            st.markdown(create_metric_card(
                "Fan Width @ 8:30",
                f"{width_830:.2f}",
                "Points top to bottom",
                "📏",
                "neutral"
            ), unsafe_allow_html=True)
        
        with col4:
            if data['overnight_analysis']:
                overnight_bias = data['overnight_analysis']['summary']['directional_bias']
                if overnight_bias == "BULLISH":
                    bias_display = "BULLISH"
                    bias_type = "success"
                elif overnight_bias == "BEARISH":
                    bias_display = "BEARISH"
                    bias_type = "danger"
                else:
                    bias_display = "NEUTRAL"
                    bias_type = "neutral"
                
                st.markdown(create_metric_card(
                    "Overnight Bias",
                    bias_display,
                    f"ES analysis based",
                    "🌙",
                    bias_type
                ), unsafe_allow_html=True)
            else:
                st.markdown(create_metric_card(
                    "Overnight Bias",
                    "NO DATA",
                    "ES data unavailable",
                    "❌",
                    "danger"
                ), unsafe_allow_html=True)
        
        # Overnight Analysis Alert
        if data['overnight_analysis']:
            overnight_summary = data['overnight_analysis']['summary']
            if overnight_summary['directional_bias'] == "BULLISH":
                alert_type = "success"
            elif overnight_summary['directional_bias'] == "BEARISH":
                alert_type = "danger"
            else:
                alert_type = "warning"
            
            st.markdown(create_overnight_alert(data['overnight_analysis'], alert_type), unsafe_allow_html=True)
        
        # RTH Entry Signals
        if data['rth_signals']:
            st.markdown("### 🚨 RTH Entry Signals (Based on Overnight ES Analysis)")
            
            for signal in data['rth_signals']:
                confidence_color = {
                    "HIGH": "success",
                    "MEDIUM": "warning", 
                    "LOW": "neutral"
                }.get(signal.get('confidence', 'LOW'), 'neutral')
                
                signal_card = f"""
                <div class="enterprise-card">
                    <h4 style="margin-top: 0; color: var(--text-primary);">
                        {signal['signal']} 
                        <span class="status-badge badge-{confidence_color}">{signal.get('confidence', 'LOW')} CONFIDENCE</span>
                    </h4>
                    <p style="color: var(--text-secondary); margin-bottom: 8px;">{signal['description']}</p>
                """
                
                if 'entry_level' in signal:
                    signal_card += f"<p><strong>Entry Level:</strong> {signal['entry_level']:.2f}"
                    if 'stop_level' in signal:
                        signal_card += f" | <strong>Stop:</strong> {signal['stop_level']:.2f}"
                    if 'target_level' in signal:
                        signal_card += f" | <strong>Target:</strong> {signal['target_level']:.2f}"
                    signal_card += "</p>"
                
                signal_card += "</div>"
                st.markdown(signal_card, unsafe_allow_html=True)
        
        # Strategy Table
        st.markdown("### 📊 Trading Strategy Table")
        
        if not data['strategy_df'].empty:
            st.dataframe(
                data['strategy_df'],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Slot": st.column_config.TextColumn("", width="small"),
                    "Time": st.column_config.TextColumn("Time", width="small"),
                    "Price": st.column_config.TextColumn("SPX Price", width="medium"),
                    "Bias": st.column_config.TextColumn("Bias", width="small"),
                    "Strength": st.column_config.TextColumn("Strength", width="small"),
                    "Top": st.column_config.NumberColumn("Top", width="medium", format="%.2f"),
                    "Bottom": st.column_config.NumberColumn("Bottom", width="medium", format="%.2f"),
                    "Width": st.column_config.NumberColumn("Width", width="small", format="%.1f"),
                    "Entry_Signal": st.column_config.TextColumn("Entry Signal", width="large")
                }
            )
        
        # Overnight Interaction Details
        if data['overnight_analysis'] and data['overnight_analysis']['interactions']:
            with st.expander("🌙 Detailed Overnight ES Interactions", expanded=False):
                interactions_df = pd.DataFrame(data['overnight_analysis']['interactions'])
                st.dataframe(
                    interactions_df[['time', 'spx_equiv_close', 'fan_top', 'fan_bottom', 'interaction', 'significance']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "time": "Time",
                        "spx_equiv_close": "SPX Equiv Close",
                        "fan_top": "Fan Top",
                        "fan_bottom": "Fan Bottom", 
                        "interaction": "Interaction Type",
                        "significance": "Significance"
                    }
                )
    
    else:
        st.info("👆 Click 'Refresh SPX Anchors' in the sidebar to begin analysis")

def render_bc_forecast_tab(controls: Dict):
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            🔮 BC Forecast - Bounce + Contract Projections
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Project NY session (8:30-14:30) from exactly 2 overnight bounces with contract entry/exit lines
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    asia_start = fmt_ct(datetime.combine(controls["prev_day"], time(19, 0)))
    europe_end = fmt_ct(datetime.combine(controls["proj_day"], time(7, 0)))
    
    session_slots = []
    current_slot = asia_start
    while current_slot <= europe_end:
        session_slots.append(current_slot)
        current_slot += timedelta(minutes=30)
    
    slot_options = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]
    
    with st.form("bc_forecast_form", clear_on_submit=False):
        st.markdown("### 📍 Underlying Bounces (Exactly 2 Required)")
        
        bounce_col1, bounce_col2 = st.columns(2)
        
        with bounce_col1:
            st.markdown("**Bounce #1**")
            b1_time = st.selectbox(
                "Time (30m slot)",
                options=slot_options,
                index=0,
                key="b1_time"
            )
            b1_price = st.number_input(
                "SPX Price",
                value=6500.00,
                step=0.25,
                format="%.2f",
                key="b1_price"
            )
        
        with bounce_col2:
            st.markdown("**Bounce #2**")
            b2_time = st.selectbox(
                "Time (30m slot)",
                options=slot_options,
                index=min(6, len(slot_options)-1),
                key="b2_time"
            )
            b2_price = st.number_input(
                "SPX Price",
                value=6512.00,
                step=0.25,
                format="%.2f",
                key="b2_price"
            )
        
        st.markdown("---")
        st.markdown("### 📋 Contract A (Required)")
        
        ca_col1, ca_col2 = st.columns(2)
        
        with ca_col1:
            ca_symbol = st.text_input(
                "Contract Symbol",
                value="6525c",
                key="ca_symbol"
            )
            ca_b1_price = st.number_input(
                "Price at Bounce #1",
                value=10.00,
                step=0.05,
                format="%.2f",
                key="ca_b1_price"
            )
            ca_b2_price = st.number_input(
                "Price at Bounce #2", 
                value=12.50,
                step=0.05,
                format="%.2f",
                key="ca_b2_price"
            )
        
        with ca_col2:
            st.markdown("**Exit Reference Points**")
            ca_h1_time = st.selectbox(
                "High after Bounce #1 - Time",
                options=slot_options,
                index=min(2, len(slot_options)-1),
                key="ca_h1_time"
            )
            ca_h1_price = st.number_input(
                "High after Bounce #1 - Price",
                value=14.00,
                step=0.05,
                format="%.2f",
                key="ca_h1_price"
            )
            ca_h2_time = st.selectbox(
                "High after Bounce #2 - Time",
                options=slot_options,
                index=min(8, len(slot_options)-1),
                key="ca_h2_time"
            )
            ca_h2_price = st.number_input(
                "High after Bounce #2 - Price",
                value=16.00,
                step=0.05,
                format="%.2f",
                key="ca_h2_price"
            )
        
        submitted = st.form_submit_button(
            "🚀 Generate NY Session Projections",
            type="primary",
            use_container_width=True
        )
    
    if submitted:
        try:
            b1_dt = fmt_ct(datetime.strptime(st.session_state["b1_time"], "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(st.session_state["b2_time"], "%Y-%m-%d %H:%M"))
            
            if b2_dt <= b1_dt:
                st.error("❌ Bounce #2 must occur after Bounce #1")
                return
            
            underlying_df, underlying_slope = project_contract_line(
                b1_dt, st.session_state["b1_price"],
                b2_dt, st.session_state["b2_price"],
                controls["proj_day"], "SPX_Projected"
            )
            
            underlying_df.insert(0, "Slot", 
                underlying_df["Time"].apply(lambda x: "⭐ 8:30" if x == "08:30" else ""))
            
            ca_entry_df, ca_entry_slope = project_contract_line(
                b1_dt, st.session_state["ca_b1_price"],
                b2_dt, st.session_state["ca_b2_price"],
                controls["proj_day"], f"{st.session_state['ca_symbol']}_Entry"
            )
            
            ca_h1_dt = fmt_ct(datetime.strptime(st.session_state["ca_h1_time"], "%Y-%m-%d %H:%M"))
            ca_h2_dt = fmt_ct(datetime.strptime(st.session_state["ca_h2_time"], "%Y-%m-%d %H:%M"))
            
            ca_exit_df, ca_exit_slope = project_contract_line(
                ca_h1_dt, st.session_state["ca_h1_price"],
                ca_h2_dt, st.session_state["ca_h2_price"],
                controls["proj_day"], f"{st.session_state['ca_symbol']}_Exit"
            )
            
            ca_expected_exit = calculate_expected_exit_time(
                b1_dt, ca_h1_dt, b2_dt, ca_h2_dt, controls["proj_day"]
            )
            
            result_df = underlying_df.merge(ca_entry_df, on="Time").merge(ca_exit_df, on="Time")
            result_df[f"{st.session_state['ca_symbol']}_Spread"] = (
                result_df[f"{st.session_state['ca_symbol']}_Exit"] - 
                result_df[f"{st.session_state['ca_symbol']}_Entry"]
            )
            
            st.session_state["bc_results"] = {
                "table": result_df,
                "underlying_slope": underlying_slope,
                "ca_symbol": st.session_state['ca_symbol'],
                "ca_entry_slope": ca_entry_slope,
                "ca_exit_slope": ca_exit_slope,
                "ca_expected_exit": ca_expected_exit,
                "bounce_times": [b1_dt, b2_dt]
            }
            
        except Exception as e:
            st.error(f"❌ Error generating BC forecast: {str(e)}")
            return
    
    if "bc_results" in st.session_state:
        results = st.session_state["bc_results"]
        
        st.markdown("### 📈 Projection Summary")
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.markdown(create_metric_card(
                "Underlying Slope",
                f"{results['underlying_slope']:+.3f}",
                "SPX points per 30m",
                "📐",
                "primary"
            ), unsafe_allow_html=True)
        
        with metric_col2:
            st.markdown(create_metric_card(
                f"{results['ca_symbol']} Entry",
                f"{results['ca_entry_slope']:+.3f}",
                f"Exit: {results['ca_exit_slope']:+.3f}",
                "📊",
                "success"
            ), unsafe_allow_html=True)
        
        with metric_col3:
            st.markdown(create_metric_card(
                "Contracts",
                "1",
                "Single contract analysis",
                "📋",
                "neutral"
            ), unsafe_allow_html=True)
        
        with metric_col4:
            st.markdown(create_metric_card(
                "Expected Exit",
                results['ca_expected_exit'],
                f"Contract A timing",
                "⏰",
                "warning"
            ), unsafe_allow_html=True)
        
        st.markdown("### 🎯 NY Session Projections")
        st.dataframe(
            results['table'],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Slot": st.column_config.TextColumn("", width="small"),
                "Time": st.column_config.TextColumn("Time", width="small")
            }
        )
    
    else:
        st.info("👆 Fill out the form above and click 'Generate NY Session Projections'")

def render_plan_card_tab():
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            📝 Plan Card - Session Preparation
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Pre-market synthesis of SPX Anchors and BC Forecast for 8:25 AM trading plan
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    has_anchors = "anchors_data" in st.session_state
    has_bc = "bc_results" in st.session_state
    
    if not has_anchors:
        st.warning("⚠️ SPX Anchors data required. Please refresh SPX Anchors first.")
        return
    
    anchors = st.session_state["anchors_data"]
    bc = st.session_state.get("bc_results", None)
    
    st.markdown("### 🎯 Session Overview")
    
    plan_col1, plan_col2, plan_col3, plan_col4 = st.columns(4)
    
    with plan_col1:
        st.markdown(create_metric_card(
            "Anchor Close",
            f"{anchors['anchor_close']:.2f}",
            f"Prev day{anchors['anchor_label']}",
            "⚓",
            "primary"
        ), unsafe_allow_html=True)
    
    with plan_col2:
        strategy_df = anchors['strategy_df']
        width_830 = strategy_df[strategy_df['Time'] == '08:30']['Width'].iloc[0] if not strategy_df.empty else 0
        st.markdown(create_metric_card(
            "Fan Width @ 8:30",
            f"{width_830:.2f}",
            "Key decision zone",
            "📏",
            "neutral"
        ), unsafe_allow_html=True)
    
    with plan_col3:
        bc_status = "ACTIVE" if bc else "NOT SET"
        bc_type = "success" if bc else "warning"
        bc_subtext = f"{len(bc['table'])} projections" if bc else "No BC forecast"
        
        st.markdown(create_metric_card(
            "BC Forecast",
            bc_status,
            bc_subtext,
            "🔮",
            bc_type
        ), unsafe_allow_html=True)
    
    with plan_col4:
        overnight_ready = anchors.get('overnight_analysis') is not None
        readiness_score = 90 if (has_anchors and bc and overnight_ready) else 75 if (has_anchors and overnight_ready) else 60 if has_anchors else 25
        readiness_type = "success" if readiness_score >= 80 else "warning" if readiness_score >= 60 else "danger"
        
        st.markdown(create_metric_card(
            "Readiness",
            f"{readiness_score}%",
            "Plan completeness",
            "🎯",
            readiness_type
        ), unsafe_allow_html=True)
    
    plan_left, plan_right = st.columns(2)
    
    with plan_left:
        st.markdown("""
        <div class="enterprise-card">
            <h3 style="margin-top: 0; display: flex; align-items: center; gap: 8px;">
                🎯 Primary Setup (SPX Anchors + Overnight)
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        row_830 = strategy_df[strategy_df['Time'] == '08:30']
        if not row_830.empty:
            setup = row_830.iloc[0]
            st.markdown(f"""
            **8:30 AM Key Levels:**
            - **Fan Top:** {setup['Top']:.2f}
            - **Fan Bottom:** {setup['Bottom']:.2f}
            - **Fan Bias:** {create_status_badge(setup['Bias'], 'up' if setup['Bias'] == 'UP' else 'down' if setup['Bias'] == 'DOWN' else 'neutral')}
            """, unsafe_allow_html=True)
            
            # Add overnight bias if available
            if anchors.get('overnight_analysis'):
                overnight_bias = anchors['overnight_analysis']['summary']['directional_bias']
                st.markdown(f"- **Overnight Bias:** {create_status_badge(overnight_bias, 'up' if 'BULL' in overnight_bias else 'down' if 'BEAR' in overnight_bias else 'neutral')}", unsafe_allow_html=True)
        else:
            st.info("8:30 AM data not available")
        
        # Show key RTH signals if available
        if anchors.get('rth_signals'):
            st.markdown("**Key RTH Signals:**")
            for signal in anchors['rth_signals'][:2]:  # Show top 2 signals
                confidence_icon = {"HIGH": "🔥", "MEDIUM": "⚡", "LOW": "💡"}.get(signal.get('confidence', 'LOW'), '💡')
                st.markdown(f"- {confidence_icon} **{signal['signal']}**: {signal.get('confidence', 'LOW')} confidence")
    
    with plan_right:
        st.markdown("""
        <div class="enterprise-card">
            <h3 style="margin-top: 0; display: flex; align-items: center; gap: 8px;">
                💼 Contract Strategy (BC Forecast)
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if bc:
            bc_table = bc['table']
            row_830_bc = bc_table[bc_table['Time'] == '08:30']
            
            if not row_830_bc.empty:
                bc_row = row_830_bc.iloc[0]
                st.markdown(f"""
                **8:30 AM Contract Levels:**
                - **SPX Projected:** {bc_row['SPX_Projected']:.2f}
                - **{bc['ca_symbol']} Entry:** {bc_row[f"{bc['ca_symbol']}_Entry"]:.2f}
                - **{bc['ca_symbol']} Exit Ref:** {bc_row[f"{bc['ca_symbol']}_Exit"]:.2f}
                - **Expected Exit Time:** {bc['ca_expected_exit']}
                """)
        else:
            st.info("Set up BC Forecast for contract projections")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    try:
        if "app_initialized" not in st.session_state:
            st.session_state["app_initialized"] = True
            st.session_state["neutral_band_pct"] = NEUTRAL_BAND_DEFAULT
        
        render_main_header()
        controls = render_sidebar_controls()
        
        tab_anchors, tab_bc, tab_plan = st.tabs([
            "🎯 SPX Anchors", 
            "🔮 BC Forecast", 
            "📝 Plan Card"
        ])
        
        with tab_anchors:
            render_spx_anchors_tab(controls)
        
        with tab_bc:
            render_bc_forecast_tab(controls)
        
        with tab_plan:
            render_plan_card_tab()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: var(--text-tertiary); font-size: 0.8rem; padding: 16px;">
            <p><strong>SPX Prophet</strong> - Professional Trading Analytics Platform with Overnight ES Analysis</p>
            <p>⚠️ <strong>Risk Disclaimer:</strong> This software is for educational purposes only. 
            Trading involves substantial risk of loss. Always consult with qualified financial professionals.</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page and try again.")

if __name__ == "__main__":
    main()