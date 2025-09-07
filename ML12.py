# app.py - Part 1/4 (STREAMLINED)
# SPX Prophet - Enterprise Trading Analytics Platform
# 3 Core Tabs: SPX Anchors | BC Forecast | Plan Card

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

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION & ENTERPRISE UI SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SPX Prophet - Enterprise Trading Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Complete Enterprise UI System - Light Theme with Vibrant Colors
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    /* Primary Color Palette */
    --primary-50: #eff6ff;
    --primary-100: #dbeafe;
    --primary-500: #3b82f6;
    --primary-600: #2563eb;
    --primary-700: #1d4ed8;
    --primary-900: #1e3a8a;
    
    /* Success Colors */
    --success-50: #f0fdf4;
    --success-100: #dcfce7;
    --success-500: #22c55e;
    --success-600: #16a34a;
    --success-700: #15803d;
    
    /* Danger Colors */
    --danger-50: #fef2f2;
    --danger-100: #fee2e2;
    --danger-500: #ef4444;
    --danger-600: #dc2626;
    --danger-700: #b91c1c;
    
    /* Warning Colors */
    --warning-50: #fffbeb;
    --warning-100: #fef3c7;
    --warning-500: #f59e0b;
    --warning-600: #d97706;
    --warning-700: #b45309;
    
    /* Neutral Colors */
    --gray-50: #f8fafc;
    --gray-100: #f1f5f9;
    --gray-200: #e2e8f0;
    --gray-300: #cbd5e1;
    --gray-400: #94a3b8;
    --gray-500: #64748b;
    --gray-600: #475569;
    --gray-700: #334155;
    --gray-800: #1e293b;
    --gray-900: #0f172a;
    
    /* Surface Colors */
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    
    /* Text Colors */
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-tertiary: #64748b;
    
    /* Border & Shadow */
    --border-light: #e2e8f0;
    --border-medium: #cbd5e1;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
    
    /* Gradients */
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-success: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
    --gradient-danger: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
    --gradient-warning: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    --gradient-neutral: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
    
    /* Trading Specific */
    --bias-up-bg: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    --bias-down-bg: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    --bias-neutral-bg: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    
    --bias-up-border: #22c55e;
    --bias-down-border: #ef4444;
    --bias-neutral-border: #94a3b8;
}

/* Global Reset & Base Styles */
html, body, [class*="css"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.main .block-container {
    padding: 2rem 2rem 3rem 2rem !important;
    max-width: 100% !important;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   ENTERPRISE CARD SYSTEM
   ═══════════════════════════════════════════════════════════════════════════════ */

.enterprise-card {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 20px;
    padding: 28px;
    box-shadow: var(--shadow-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.enterprise-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--gradient-primary);
}

.enterprise-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
    border-color: var(--primary-500);
}

.metric-card {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 16px;
    padding: 24px;
    box-shadow: var(--shadow-md);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary-500);
}

.metric-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}

.metric-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 600;
    background: var(--gradient-primary);
    color: white;
    box-shadow: var(--shadow-md);
}

.metric-icon.success {
    background: var(--gradient-success);
}

.metric-icon.danger {
    background: var(--gradient-danger);
}

.metric-icon.warning {
    background: var(--gradient-warning);
}

.metric-icon.neutral {
    background: var(--gradient-neutral);
}

.metric-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0;
}

.metric-value {
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: 8px 0 4px 0;
    line-height: 1;
    font-family: 'JetBrains Mono', monospace;
}

.metric-subtext {
    font-size: 0.75rem;
    color: var(--text-tertiary);
    font-weight: 500;
    line-height: 1.4;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   STATUS & BADGE SYSTEM
   ═══════════════════════════════════════════════════════════════════════════════ */

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 24px;
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border: 2px solid;
    transition: all 0.3s ease;
}

.badge-open {
    background: var(--success-50);
    border-color: var(--success-500);
    color: var(--success-700);
}

.badge-closed {
    background: var(--danger-50);
    border-color: var(--danger-500);
    color: var(--danger-700);
}

.badge-up {
    background: var(--bias-up-bg);
    border-color: var(--bias-up-border);
    color: var(--success-700);
    font-weight: 700;
}

.badge-down {
    background: var(--bias-down-bg);
    border-color: var(--bias-down-border);
    color: var(--danger-700);
    font-weight: 700;
}

.badge-neutral {
    background: var(--bias-neutral-bg);
    border-color: var(--bias-neutral-border);
    color: var(--gray-700);
    font-weight: 700;
}

.override-indicator {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: var(--primary-50);
    border: 1px solid var(--primary-500);
    color: var(--primary-700);
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 8px;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   HEADER & NAVIGATION
   ═══════════════════════════════════════════════════════════════════════════════ */

.main-header {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 20px;
    padding: 24px 32px;
    margin-bottom: 32px;
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
    height: 4px;
    background: var(--gradient-primary);
}

.header-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 16px;
}

.header-subtitle {
    font-size: 1.125rem;
    color: var(--text-secondary);
    margin: 8px 0 0 0;
    font-weight: 500;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   TABLE SYSTEM
   ═══════════════════════════════════════════════════════════════════════════════ */

.enterprise-table {
    background: var(--bg-primary) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-md) !important;
}

.enterprise-table table {
    background: transparent !important;
    font-family: 'Inter', sans-serif !important;
}

.enterprise-table th {
    background: var(--bg-tertiary) !important;
    color: var(--text-secondary) !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
    padding: 16px 12px !important;
    border-bottom: 2px solid var(--border-medium) !important;
}

.enterprise-table td {
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    padding: 12px !important;
    border-bottom: 1px solid var(--border-light) !important;
}

.table-highlight {
    background: var(--warning-50) !important;
    border-left: 4px solid var(--warning-500) !important;
    font-weight: 700 !important;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   BUTTON & INTERACTION SYSTEM
   ═══════════════════════════════════════════════════════════════════════════════ */

.stButton > button {
    background: var(--gradient-primary) !important;
    border: none !important;
    border-radius: 16px !important;
    color: white !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: var(--shadow-md) !important;
    height: 48px !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   TAB SYSTEM
   ═══════════════════════════════════════════════════════════════════════════════ */

.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-tertiary) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 16px !important;
    padding: 8px !important;
    margin-bottom: 32px !important;
    box-shadow: var(--shadow-md) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 12px !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
}

.stTabs [aria-selected="true"] {
    background: var(--gradient-primary) !important;
    color: white !important;
    box-shadow: var(--shadow-md) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   SIDEBAR SYSTEM
   ═══════════════════════════════════════════════════════════════════════════════ */

.css-1d391kg {
    background: var(--bg-secondary) !important;
    border-right: 2px solid var(--border-light) !important;
}

.sidebar-card {
    background: var(--bg-primary) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    margin-bottom: 20px !important;
    box-shadow: var(--shadow-md) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   FORM SYSTEM
   ═══════════════════════════════════════════════════════════════════════════════ */

.stSelectbox > div > div {
    background: var(--bg-primary) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 12px !important;
}

.stNumberInput > div > div > input {
    background: var(--bg-primary) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

.stTextInput > div > div > input {
    background: var(--bg-primary) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   UTILITY CLASSES
   ═══════════════════════════════════════════════════════════════════════════════ */

.star-highlight {
    color: var(--warning-600) !important;
    font-weight: 800 !important;
}

.text-success {
    color: var(--success-600) !important;
}

.text-danger {
    color: var(--danger-600) !important;
}

.text-warning {
    color: var(--warning-600) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   ANIMATIONS
   ═══════════════════════════════════════════════════════════════════════════════ */

@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.8;
    }
}

.animate-slide-in {
    animation: slideInUp 0.6s ease-out;
}

.animate-pulse {
    animation: pulse 2s infinite;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   RESPONSIVE DESIGN
   ═══════════════════════════════════════════════════════════════════════════════ */

@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
    }
    
    .metric-card {
        height: auto;
        min-height: 120px;
    }
    
    .header-title {
        font-size: 2rem;
    }
    
    .metric-value {
        font-size: 1.875rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CORE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def fmt_ct(dt: datetime) -> datetime:
    """Convert datetime to Chicago timezone."""
    if dt.tzinfo is None:
        return CT_TZ.localize(dt)
    return dt.astimezone(CT_TZ)

def between_time(df: pd.DataFrame, start_str: str, end_str: str) -> pd.DataFrame:
    """Filter DataFrame between specific times."""
    return df.between_time(start_str, end_str) if not df.empty else df

def rth_slots_ct(target_date: date) -> List[datetime]:
    """Generate 30-minute RTH time slots for target date."""
    start_dt = fmt_ct(datetime.combine(target_date, time(8, 30)))
    end_dt = fmt_ct(datetime.combine(target_date, time(14, 30)))
    slots, current = [], start_dt
    while current <= end_dt:
        slots.append(current)
        current += timedelta(minutes=30)
    return slots

def is_maintenance(dt: datetime) -> bool:
    """Check if datetime falls in maintenance window."""
    return dt.hour == 16

def in_weekend_gap(dt: datetime) -> bool:
    """Check if datetime falls in weekend gap."""
    weekday = dt.weekday()
    if weekday == 5:  # Saturday
        return True
    if weekday == 6 and dt.hour < 17:  # Sunday before 5 PM
        return True
    if weekday == 4 and dt.hour >= 17:  # Friday after 5 PM
        return True
    return False

def count_effective_blocks(start: datetime, end: datetime) -> float:
    """Count 30-minute blocks excluding maintenance and weekend gaps."""
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
    """Ensure DataFrame has required OHLC columns."""
    if df.empty:
        return df
    
    # Handle MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns]
    
    # Check for required columns
    required_cols = ["Open", "High", "Low", "Close"]
    for col in required_cols:
        if col not in df.columns:
            return pd.DataFrame()
    
    return df

def normalize_to_ct(df: pd.DataFrame, start_d: date, end_d: date) -> pd.DataFrame:
    """Normalize DataFrame index to Chicago timezone and filter by date range."""
    if df.empty:
        return df
    
    df = ensure_ohlc_cols(df)
    if df.empty:
        return df
    
    # Convert timezone
    if df.index.tz is None:
        df.index = df.index.tz_localize("US/Eastern")
    df.index = df.index.tz_convert(CT_TZ)
    
    # Filter by date range
    start_dt = fmt_ct(datetime.combine(start_d, time(0, 0)))
    end_dt = fmt_ct(datetime.combine(end_d, time(23, 59)))
    
    return df.loc[start_dt:end_dt]

@st.cache_data(ttl=120, show_spinner=False)
def fetch_intraday(symbol: str, start_d: date, end_d: date, interval: str) -> pd.DataFrame:
    """Fetch intraday data with caching and error handling."""
    try:
        ticker = yf.Ticker(symbol)
        
        if interval in ["1m", "2m", "5m", "15m"]:
            # For minute data, use period parameter
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
            # For hourly/daily data, use start/end parameters
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
    """Resample minute data to 30-minute bars."""
    if min_df.empty or not isinstance(min_df.index, pd.DatetimeIndex):
        return pd.DataFrame()
    
    df = min_df.sort_index()
    
    # Define aggregation rules
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
    
    # Resample to 30-minute bars
    resampled = df.resample("30T", label="right", closed="right").agg(agg_rules)
    
    # Drop rows with missing OHLC data
    ohlc_cols = [c for c in ["Open", "High", "Low", "Close"] if c in resampled.columns]
    resampled = resampled.dropna(subset=ohlc_cols, how="any")
    
    return resampled

# ═══════════════════════════════════════════════════════════════════════════════
# VOLUME CONTEXT ANALYSIS (New Feature)
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_session_volume(df: pd.DataFrame, target_date: date) -> Dict[str, float]:
    """Analyze volume patterns across trading sessions."""
    if df.empty or "Volume" not in df.columns:
        return {"asia": 0.0, "london": 0.0, "premarket": 0.0, "avg_volume": 0.0}
    
    day_data = df.loc[df.index.date == target_date] if not df.empty else pd.DataFrame()
    if day_data.empty:
        return {"asia": 0.0, "london": 0.0, "premarket": 0.0, "avg_volume": 0.0}
    
    asia_vol = day_data.between_time("19:00", "01:00")["Volume"].sum() if not day_data.empty else 0
    london_vol = day_data.between_time("01:00", "07:00")["Volume"].sum() if not day_data.empty else 0
    premarket_vol = day_data.between_time("07:00", "08:30")["Volume"].sum() if not day_data.empty else 0
    avg_vol = day_data["Volume"].mean() if not day_data.empty else 0
    
    return {
        "asia": float(asia_vol),
        "london": float(london_vol), 
        "premarket": float(premarket_vol),
        "avg_volume": float(avg_vol)
    }

def volume_weighted_score(price_level: float, fan_levels: Dict[str, float], 
                         volume_data: Dict[str, float]) -> float:
    """Calculate volume-weighted significance score for price levels."""
    if volume_data["avg_volume"] == 0:
        return 1.0
    
    # Distance to key levels
    top_dist = abs(price_level - fan_levels.get("top", 0))
    bottom_dist = abs(price_level - fan_levels.get("bottom", 0))
    min_dist = min(top_dist, bottom_dist)
    
    # Volume context multiplier
    total_session_vol = volume_data["asia"] + volume_data["london"] + volume_data["premarket"]
    vol_multiplier = 1.0 + (total_session_vol / (volume_data["avg_volume"] * 10))
    
    # Closer to levels + higher volume = higher score
    distance_score = 1.0 / (1.0 + min_dist)
    
    return distance_score * vol_multiplier

# ═══════════════════════════════════════════════════════════════════════════════
# TIME-BASED EDGE SCORING (New Feature)  
# ═══════════════════════════════════════════════════════════════════════════════

def session_momentum_score(df: pd.DataFrame, current_time: datetime) -> float:
    """Calculate momentum persistence across session transitions."""
    if df.empty:
        return 0.5
    
    # Look back at recent 4 periods for momentum
    lookback_start = current_time - timedelta(hours=SESSION_MOMENTUM_LOOKBACK)
    recent_data = df.loc[lookback_start:current_time] if not df.empty else pd.DataFrame()
    
    if recent_data.empty or len(recent_data) < 2:
        return 0.5
    
    # Calculate directional consistency
    closes = recent_data["Close"]
    direction_changes = 0
    prev_direction = None
    
    for i in range(1, len(closes)):
        current_direction = "up" if closes.iloc[i] > closes.iloc[i-1] else "down"
        if prev_direction and current_direction != prev_direction:
            direction_changes += 1
        prev_direction = current_direction
    
    # More consistent direction = higher score
    consistency_score = 1.0 - (direction_changes / max(1, len(closes) - 1))
    return consistency_score

def time_decay_factor(interaction_time: datetime, current_time: datetime) -> float:
    """Calculate time decay factor for edge interactions."""
    hours_elapsed = (current_time - interaction_time).total_seconds() / 3600
    
    if hours_elapsed <= 0:
        return 1.0
    
    # Exponential decay over TIME_DECAY_HOURS
    decay_rate = np.log(0.5) / TIME_DECAY_HOURS  # Half-life decay
    return np.exp(decay_rate * hours_elapsed)

# ═══════════════════════════════════════════════════════════════════════════════
# UI COMPONENT BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def create_metric_card(title: str, value: str, subtext: str = "", icon: str = "📊", 
                      card_type: str = "primary") -> str:
    """Create a metric card with icon and styling."""
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
    """Create a status badge with appropriate styling."""
    return f'<span class="status-badge badge-{status}">{text}</span>'

def create_header_section(title: str, subtitle: str = "") -> str:
    """Create main header section."""
    return f"""
    <div class="main-header animate-slide-in">
        <h1 class="header-title">{title}</h1>
        {f'<p class="header-subtitle">{subtitle}</p>' if subtitle else ''}
    </div>
    """
