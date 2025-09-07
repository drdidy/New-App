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





# app.py - Part 2/4
# SPX Prophet - Core Trading Logic & Calculations
# Fan projections, bias determination, volume context, time-based scoring

# ═══════════════════════════════════════════════════════════════════════════════
# SPX ANCHOR LOGIC (SPX-only, no SPY fallback)
# ═══════════════════════════════════════════════════════════════════════════════

def get_spx_anchor_prevday(prev_day: date) -> Tuple[Optional[float], Optional[datetime], bool]:
    """
    Get SPX anchor from previous day ≤ 3:00 PM CT using ^GSPC only.
    Returns (anchor_close, anchor_time, estimated_flag)
    """
    target_time = fmt_ct(datetime.combine(prev_day, time(15, 0)))
    
    # Try 30m, 5m, 1m intervals in sequence
    for interval in ["30m", "5m", "1m"]:
        spx_data = fetch_intraday("^GSPC", prev_day, prev_day, interval)
        if spx_data.empty:
            continue
            
        # Find last close ≤ 3:00 PM CT
        before_target = spx_data.loc[:target_time]
        if before_target.empty:
            continue
            
        anchor_close = float(before_target["Close"].iloc[-1])
        anchor_time = before_target.index[-1].to_pydatetime()
        return anchor_close, fmt_ct(anchor_time), False
    
    # Fallback to ES estimation if ^GSPC unavailable
    est_close, est_time = estimate_anchor_from_es(prev_day)
    return est_close, est_time, True

def estimate_anchor_from_es(prev_day: date) -> Tuple[Optional[float], Optional[datetime]]:
    """
    Estimate SPX anchor from ES using recent median offset when ^GSPC unavailable.
    """
    target_time = fmt_ct(datetime.combine(prev_day, time(15, 0)))
    
    # Get ES close at ≤ 3:00 PM
    es_data = fetch_intraday("ES=F", prev_day, prev_day, "5m")
    if es_data.empty:
        es_data = fetch_intraday("ES=F", prev_day, prev_day, "1m")
    if es_data.empty:
        return None, None
        
    es_before_target = es_data.loc[:target_time]
    if es_before_target.empty:
        return None, None
        
    es_close = float(es_before_target["Close"].iloc[-1])
    
    # Get recent median ES→SPX offset
    offset = calculate_recent_median_offset(prev_day, lookback_days=7)
    if offset is None:
        return None, None
        
    estimated_spx = es_close - offset
    return float(estimated_spx), target_time

def calculate_recent_median_offset(prev_day: date, lookback_days: int = 7) -> Optional[float]:
    """
    Calculate recent median (ES_close - SPX_close) at ≤3PM across prior days.
    """
    offsets = []
    
    for i in range(1, lookback_days + 1):
        check_day = prev_day - timedelta(days=i)
        target_time = fmt_ct(datetime.combine(check_day, time(15, 0)))
        
        # Get SPX close
        spx_data = fetch_intraday("^GSPC", check_day, check_day, "30m")
        if spx_data.empty:
            spx_data = fetch_intraday("^GSPC", check_day, check_day, "5m")
        if spx_data.empty:
            continue
            
        spx_before = spx_data.loc[:target_time]
        if spx_before.empty:
            continue
        spx_close = float(spx_before["Close"].iloc[-1])
        
        # Get ES close
        es_data = fetch_intraday("ES=F", check_day, check_day, "5m")
        if es_data.empty:
            continue
            
        es_before = es_data.loc[:target_time]
        if es_before.empty:
            continue
        es_close = float(es_before["Close"].iloc[-1])
        
        offsets.append(es_close - spx_close)
    
    return float(np.median(offsets)) if offsets else None

# ═══════════════════════════════════════════════════════════════════════════════
# FAN PROJECTION & BIAS LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_slopes() -> Tuple[float, float]:
    """Get current fan slopes from session state or defaults."""
    top_slope = float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT))
    bottom_slope = float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT))
    return top_slope, bottom_slope

def project_fan_levels(anchor_close: float, anchor_time: datetime, target_day: date) -> pd.DataFrame:
    """
    Project fan top/bottom levels for RTH slots on target day.
    """
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
            "Blocks_From_Anchor": effective_blocks
        })
    
    return pd.DataFrame(projections)

def determine_bias(price: float, top_level: float, bottom_level: float, 
                  neutral_band_pct: float = NEUTRAL_BAND_DEFAULT) -> str:
    """
    Determine bias based on price position relative to fan levels.
    """
    # Above/below fan
    if price > top_level:
        return "UP"
    if price < bottom_level:
        return "DOWN"
    
    # Inside fan - check neutral band
    fan_width = top_level - bottom_level
    fan_center = (top_level + bottom_level) / 2
    neutral_band_size = neutral_band_pct * fan_width
    
    if abs(price - fan_center) <= neutral_band_size:
        return "NEUTRAL"
    
    # Closer to top or bottom
    distance_to_top = top_level - price
    distance_to_bottom = price - bottom_level
    
    return "UP" if distance_to_bottom < distance_to_top else "DOWN"

def calculate_bias_strength(price: float, top_level: float, bottom_level: float) -> float:
    """
    Calculate bias strength as percentage (0-100).
    """
    if price > top_level:
        # Above fan - strength based on distance above
        distance_above = price - top_level
        fan_width = top_level - bottom_level
        strength = min(100, 50 + (distance_above / fan_width) * 50)
    elif price < bottom_level:
        # Below fan - strength based on distance below
        distance_below = bottom_level - price
        fan_width = top_level - bottom_level
        strength = min(100, 50 + (distance_below / fan_width) * 50)
    else:
        # Inside fan - strength based on distance from center
        fan_center = (top_level + bottom_level) / 2
        distance_from_center = abs(price - fan_center)
        half_width = (top_level - bottom_level) / 2
        strength = (distance_from_center / half_width) * 50
    
    return round(strength, 1)

# ═══════════════════════════════════════════════════════════════════════════════
# VOLUME CONTEXT INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_volume_context(spx_data: pd.DataFrame, target_date: date) -> Dict[str, any]:
    """
    Analyze volume context for the target date.
    """
    if spx_data.empty or "Volume" not in spx_data.columns:
        return {
            "session_volumes": {"asia": 0, "london": 0, "premarket": 0},
            "avg_volume": 0,
            "volume_percentile": 50,
            "high_volume_periods": []
        }
    
    # Filter to target date
    target_data = spx_data.loc[spx_data.index.date == target_date]
    if target_data.empty:
        return {
            "session_volumes": {"asia": 0, "london": 0, "premarket": 0},
            "avg_volume": 0,
            "volume_percentile": 50,
            "high_volume_periods": []
        }
    
    # Session volume analysis
    session_volumes = analyze_session_volume(spx_data, target_date)
    
    # Volume percentile calculation
    recent_volumes = spx_data["Volume"].rolling(window=VOLUME_LOOKBACK).mean()
    current_avg = target_data["Volume"].mean()
    
    if not recent_volumes.empty and current_avg > 0:
        volume_percentile = (recent_volumes < current_avg).mean() * 100
    else:
        volume_percentile = 50
    
    # High volume periods identification
    volume_threshold = target_data["Volume"].mean() * VOLUME_SPIKE_THRESHOLD
    high_volume_periods = []
    
    for idx, row in target_data.iterrows():
        if row["Volume"] > volume_threshold:
            high_volume_periods.append({
                "time": idx.strftime("%H:%M"),
                "volume": int(row["Volume"]),
                "multiple": round(row["Volume"] / target_data["Volume"].mean(), 1)
            })
    
    return {
        "session_volumes": session_volumes,
        "avg_volume": float(current_avg),
        "volume_percentile": round(volume_percentile, 1),
        "high_volume_periods": high_volume_periods
    }

def volume_adjusted_bias_score(bias: str, bias_strength: float, volume_context: Dict) -> float:
    """
    Adjust bias score based on volume context.
    """
    base_score = bias_strength
    
    # Volume percentile adjustment
    vol_percentile = volume_context.get("volume_percentile", 50)
    if vol_percentile > 75:
        # High volume periods increase confidence
        volume_multiplier = 1.2
    elif vol_percentile < 25:
        # Low volume periods decrease confidence
        volume_multiplier = 0.8
    else:
        volume_multiplier = 1.0
    
    # Session volume distribution adjustment
    session_vols = volume_context.get("session_volumes", {})
    total_session_vol = session_vols.get("asia", 0) + session_vols.get("london", 0) + session_vols.get("premarket", 0)
    avg_vol = volume_context.get("avg_volume", 1)
    
    if total_session_vol > avg_vol * 2:
        # Strong overnight activity
        session_multiplier = 1.15
    elif total_session_vol < avg_vol * 0.5:
        # Weak overnight activity
        session_multiplier = 0.9
    else:
        session_multiplier = 1.0
    
    adjusted_score = base_score * volume_multiplier * session_multiplier
    return min(100, max(0, adjusted_score))

# ═══════════════════════════════════════════════════════════════════════════════
# TIME-BASED EDGE SCORING INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_time_based_score(spx_data: pd.DataFrame, current_time: datetime, 
                              anchor_time: datetime) -> Dict[str, float]:
    """
    Calculate time-based scoring components.
    """
    if spx_data.empty:
        return {
            "session_momentum": 0.5,
            "time_since_anchor": 0.5,
            "recency_factor": 1.0
        }
    
    # Session momentum score
    momentum_score = session_momentum_score(spx_data, current_time)
    
    # Time since anchor (fresher anchors = higher confidence)
    hours_since_anchor = (current_time - anchor_time).total_seconds() / 3600
    anchor_freshness = max(0.3, 1.0 - (hours_since_anchor / 24))  # Decay over 24 hours
    
    # Recency factor for current analysis
    recency_factor = time_decay_factor(anchor_time, current_time)
    
    return {
        "session_momentum": momentum_score,
        "time_since_anchor": anchor_freshness,
        "recency_factor": recency_factor
    }

def composite_edge_score(bias: str, bias_strength: float, volume_context: Dict, 
                        time_scores: Dict) -> Dict[str, float]:
    """
    Calculate composite edge score combining all factors.
    """
    # Base bias score
    base_score = bias_strength
    
    # Volume adjustment
    volume_adjusted = volume_adjusted_bias_score(bias, bias_strength, volume_context)
    
    # Time-based adjustments
    momentum_factor = time_scores.get("session_momentum", 0.5)
    freshness_factor = time_scores.get("time_since_anchor", 0.5)
    recency_factor = time_scores.get("recency_factor", 1.0)
    
    # Combined time factor
    time_factor = (momentum_factor * 0.4 + freshness_factor * 0.3 + recency_factor * 0.3)
    
    # Final composite score
    composite = volume_adjusted * time_factor
    
    # Confidence level based on composite score
    if composite >= 75:
        confidence = "HIGH"
    elif composite >= 50:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return {
        "base_score": round(base_score, 1),
        "volume_adjusted": round(volume_adjusted, 1),
        "time_factor": round(time_factor, 2),
        "composite_score": round(composite, 1),
        "confidence_level": confidence
    }

# ═══════════════════════════════════════════════════════════════════════════════
# SPX ANCHORS STRATEGY TABLE BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_spx_strategy_table(anchor_close: float, anchor_time: datetime, 
                            target_day: date, spx_rth_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build comprehensive strategy table for SPX Anchors tab.
    """
    # Project fan levels
    fan_df = project_fan_levels(anchor_close, anchor_time, target_day)
    
    # Get volume context if SPX data available
    volume_context = {}
    time_scores = {}
    if spx_rth_data is not None and not spx_rth_data.empty:
        volume_context = get_volume_context(spx_rth_data, target_day)
        time_scores = calculate_time_based_score(spx_rth_data, 
                                               fmt_ct(datetime.combine(target_day, time(8, 30))), 
                                               anchor_time)
    
    strategy_rows = []
    neutral_band = float(st.session_state.get("neutral_band_pct", NEUTRAL_BAND_DEFAULT))
    
    for _, row in fan_df.iterrows():
        slot_time = row["Time"]
        top_level = row["Top"]
        bottom_level = row["Bottom"]
        fan_width = row["Fan_Width"]
        
        # Try to get actual SPX price for this slot
        actual_price = None
        if spx_rth_data is not None and not spx_rth_data.empty:
            slot_datetime = row["DateTime"]
            if slot_datetime in spx_rth_data.index:
                actual_price = float(spx_rth_data.loc[slot_datetime, "Close"])
        
        if actual_price is not None:
            # Real price analysis
            bias = determine_bias(actual_price, top_level, bottom_level, neutral_band)
            bias_strength = calculate_bias_strength(actual_price, top_level, bottom_level)
            
            # Enhanced scoring if volume/time data available
            if volume_context and time_scores:
                edge_scores = composite_edge_score(bias, bias_strength, volume_context, time_scores)
                composite_score = edge_scores["composite_score"]
                confidence = edge_scores["confidence_level"]
            else:
                composite_score = bias_strength
                confidence = "MEDIUM" if bias_strength > 50 else "LOW"
            
            price_display = f"{actual_price:.2f}"
            entry_signal = generate_entry_signal(actual_price, top_level, bottom_level, bias)
        else:
            # No price data - show fan only
            bias = "NO DATA"
            bias_strength = 0
            composite_score = 0
            confidence = "N/A"
            price_display = "—"
            entry_signal = "Fan projection only"
        
        # Star highlight for 8:30
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
            "Score": f"{composite_score:.1f}" if composite_score > 0 else "—",
            "Confidence": confidence,
            "Entry_Signal": entry_signal
        })
    
    return pd.DataFrame(strategy_rows)

def generate_entry_signal(price: float, top: float, bottom: float, bias: str) -> str:
    """
    Generate entry signals based on price position and bias.
    """
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

# ═══════════════════════════════════════════════════════════════════════════════
# BC FORECAST LOGIC (2-bounce projections)
# ═══════════════════════════════════════════════════════════════════════════════

def project_contract_line(bounce1_time: datetime, bounce1_price: float,
                         bounce2_time: datetime, bounce2_price: float,
                         target_day: date, line_label: str) -> Tuple[pd.DataFrame, float]:
    """
    Project contract price line from 2 bounce points across RTH.
    """
    # Calculate slope per 30-minute block
    effective_blocks = count_effective_blocks(bounce1_time, bounce2_time)
    if effective_blocks <= 0:
        slope = 0.0
    else:
        slope = (bounce2_price - bounce1_price) / effective_blocks
    
    # Project across RTH slots
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
    """
    Calculate expected exit time based on historical durations.
    """
    # Calculate durations from bounces to highs
    duration1 = count_effective_blocks(bounce1_time, high1_time)
    duration2 = count_effective_blocks(bounce2_time, high2_time)
    
    durations = [d for d in [duration1, duration2] if d > 0]
    if not durations:
        return "N/A"
    
    # Use median duration
    median_duration = int(np.median(durations))
    
    # Project from bounce2 + median duration
    exit_candidate = bounce2_time
    blocks_added = 0
    
    while blocks_added < median_duration:
        exit_candidate += timedelta(minutes=30)
        if not is_maintenance(exit_candidate) and not in_weekend_gap(exit_candidate):
            blocks_added += 1
    
    # Find corresponding RTH slot
    rth_slots = rth_slots_ct(target_day)
    for slot in rth_slots:
        if slot >= exit_candidate:
            return slot.strftime("%H:%M")
    
    return "After RTH"

# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED DATA FETCHING WITH FALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_spx_with_fallbacks(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Fetch SPX data with multiple interval fallbacks for maximum coverage.
    """
    # Try 30m first for efficiency
    spx_data = fetch_intraday("^GSPC", start_date, end_date, "30m")
    if not spx_data.empty:
        return spx_data
    
    # Fallback to 5m and resample
    spx_5m = fetch_intraday("^GSPC", start_date, end_date, "5m")
    if not spx_5m.empty:
        return resample_to_30m_ct(spx_5m)
    
    # Final fallback to 1m and resample  
    spx_1m = fetch_intraday("^GSPC", start_date, end_date, "1m")
    if not spx_1m.empty:
        return resample_to_30m_ct(spx_1m)
    
    return pd.DataFrame()

def true_range(df: pd.DataFrame) -> pd.Series:
    """
    Calculate True Range for volatility analysis.
    """
    if df.empty or "High" not in df.columns or "Low" not in df.columns or "Close" not in df.columns:
        return pd.Series(dtype=float)
    
    prev_close = df["Close"].shift(1)
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - prev_close).abs()
    tr3 = (df["Low"] - prev_close).abs()
    
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)




# app.py - Part 3/4
# SPX Prophet - Dashboard Builders & UI Components
# Main interface, tabs, forms, and data visualization

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN HEADER & STATUS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_main_header():
    """Render the main application header with live status."""
    current_time = datetime.now(CT_TZ)
    
    # Main header
    st.markdown(create_header_section(
        "SPX Prophet",
        "Enterprise Trading Analytics Platform - SPX Anchors | BC Forecast | Plan Card"
    ), unsafe_allow_html=True)
    
    # Status metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Current time
        time_str = current_time.strftime("%H:%M:%S")
        date_str = current_time.strftime("%A, %B %d")
        st.markdown(create_metric_card(
            "Current Time (CT)", 
            time_str,
            date_str,
            "🕒",
            "primary"
        ), unsafe_allow_html=True)
    
    with col2:
        # Market status
        is_weekday = current_time.weekday() < 5
        market_open = current_time.replace(hour=8, minute=30, second=0, microsecond=0)
        market_close = current_time.replace(hour=14, minute=30, second=0, microsecond=0)
        is_open = is_weekday and (market_open <= current_time <= market_close)
        
        status_text = "OPEN" if is_open else "CLOSED"
        status_type = "success" if is_open else "danger"
        status_subtext = "RTH: 08:30-14:30 CT" if is_open else "Next: Mon 08:30 CT"
        
        st.markdown(create_metric_card(
            "Market Status",
            status_text,
            status_subtext,
            "📊",
            status_type
        ), unsafe_allow_html=True)
    
    with col3:
        # Fan slopes
        top_slope, bottom_slope = get_current_slopes()
        slope_text = f"+{top_slope:.3f} / -{bottom_slope:.3f}"
        override_active = ("top_slope_per_block" in st.session_state or 
                          "bottom_slope_per_block" in st.session_state)
        slope_subtext = "Custom slopes active" if override_active else "Default asymmetric"
        slope_type = "warning" if override_active else "neutral"
        
        st.markdown(create_metric_card(
            "SPX Slopes /30m",
            slope_text,
            slope_subtext,
            "📐",
            slope_type
        ), unsafe_allow_html=True)
    
    with col4:
        # Data connectivity
        try:
            test_data = fetch_intraday("^GSPC", current_time.date() - timedelta(days=1), 
                                     current_time.date(), "30m")
            connectivity = "CONNECTED" if not test_data.empty else "LIMITED"
            conn_type = "success" if not test_data.empty else "warning"
            conn_subtext = f"{len(test_data)} bars available" if not test_data.empty else "Check data source"
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

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar_controls():
    """Render sidebar control panel."""
    st.sidebar.markdown("""
    <div class="sidebar-card">
        <h3 style="margin-top: 0; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
            🎛️ Controls
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Date controls
    today_ct = datetime.now(CT_TZ).date()
    
    with st.sidebar.container():
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.subheader("📅 Trading Dates")
        
        prev_day = st.date_input(
            "Previous Trading Day",
            value=today_ct - timedelta(days=1),
            help="Day to get SPX anchor close ≤ 3:00 PM CT"
        )
        
        proj_day = st.date_input(
            "Projection Day", 
            value=prev_day + timedelta(days=1),
            help="Target day for RTH projections"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Manual anchor override
    with st.sidebar.container():
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.subheader("✍️ Manual Anchor")
        
        use_manual = st.checkbox(
            "Override with manual 3:00 PM close",
            value=False,
            help="Use custom anchor instead of fetched ^GSPC data"
        )
        
        manual_value = st.number_input(
            "Manual Anchor Close",
            value=6400.00,
            step=0.25,
            format="%.2f",
            disabled=not use_manual,
            help="SPX close price for anchor calculations"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Advanced settings
    with st.sidebar.expander("⚙️ Advanced Settings", expanded=False):
        st.markdown("**Fan Slope Configuration**")
        
        enable_slopes = st.checkbox(
            "Enable custom slopes",
            value=("top_slope_per_block" in st.session_state),
            help="Override default asymmetric fan slopes"
        )
        
        if enable_slopes:
            top_slope = st.number_input(
                "Top slope (+per 30m)",
                value=float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT)),
                step=0.001,
                format="%.3f",
                help="Positive slope for fan top line"
            )
            
            bottom_slope = st.number_input(
                "Bottom slope (-per 30m)", 
                value=float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT)),
                step=0.001,
                format="%.3f",
                help="Positive value for fan bottom line slope"
            )
        
        st.markdown("**Bias Configuration**")
        neutral_band = st.slider(
            "Neutral band (% of fan width)",
            min_value=0,
            max_value=50,
            value=int(NEUTRAL_BAND_DEFAULT * 100),
            step=5,
            help="Percentage of fan width for neutral bias zone"
        ) / 100.0
        
        # Apply/Reset buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply", type="primary", use_container_width=True):
                if enable_slopes:
                    st.session_state["top_slope_per_block"] = float(top_slope)
                    st.session_state["bottom_slope_per_block"] = float(bottom_slope)
                else:
                    st.session_state.pop("top_slope_per_block", None)
                    st.session_state.pop("bottom_slope_per_block", None)
                
                st.session_state["neutral_band_pct"] = float(neutral_band)
                st.success("Settings applied!")
                
        with col2:
            if st.button("Reset", use_container_width=True):
                st.session_state.pop("top_slope_per_block", None)
                st.session_state.pop("bottom_slope_per_block", None)
                st.session_state.pop("neutral_band_pct", None)
                st.success("Reset to defaults!")
    
    # Action buttons
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

# ═══════════════════════════════════════════════════════════════════════════════
# SPX ANCHORS TAB
# ═══════════════════════════════════════════════════════════════════════════════

def render_spx_anchors_tab(controls: Dict):
    """Render the SPX Anchors analysis tab."""
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            🎯 SPX Anchors - Fan Analysis & Strategy
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Previous day anchor projection with bias analysis and entry signals
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if controls["refresh_anchors"] or "anchors_data" not in st.session_state:
        with st.spinner("Building SPX anchor analysis..."):
            try:
                # Get anchor
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
                
                # Get projection day SPX data for analysis
                spx_rth_data = fetch_spx_with_fallbacks(controls["proj_day"], controls["proj_day"])
                spx_rth_data = between_time(spx_rth_data, RTH_START, RTH_END) if not spx_rth_data.empty else pd.DataFrame()
                
                # Build strategy table
                strategy_df = build_spx_strategy_table(
                    anchor_close, anchor_time, controls["proj_day"], spx_rth_data
                )
                
                # Store results
                st.session_state["anchors_data"] = {
                    "anchor_close": anchor_close,
                    "anchor_time": anchor_time,
                    "anchor_label": anchor_label,
                    "strategy_df": strategy_df,
                    "spx_data": spx_rth_data,
                    "estimated": estimated
                }
                
            except Exception as e:
                st.error(f"Error building anchor analysis: {str(e)}")
                return
    
    # Display results
    if "anchors_data" in st.session_state:
        data = st.session_state["anchors_data"]
        
        # Anchor info metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Anchor Close",
                f"{data['anchor_close']:.2f}",
                f"Previous day ≤ 3:00 PM{data['anchor_label']}",
                "⚓",
                "warning" if data['estimated'] else "primary"
            ), unsafe_allow_html=True)
        
        with col2:
            anchor_date = data['anchor_time'].strftime("%m/%d %H:%M")
            st.markdown(create_metric_card(
                "Anchor Time",
                anchor_date,
                "Chicago timezone",
                "📍",
                "neutral"
            ), unsafe_allow_html=True)
        
        with col3:
            # Fan width at 8:30
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
            # Current bias (8:30 or latest)
            current_bias = "N/A"
            if not df.empty:
                bias_row = df[df['Time'] == '08:30']
                if bias_row.empty:
                    bias_row = df.iloc[0:1]  # First row if 8:30 not available
                if not bias_row.empty:
                    current_bias = bias_row['Bias'].iloc[0]
            
            bias_type = "success" if current_bias == "UP" else "danger" if current_bias == "DOWN" else "neutral"
            st.markdown(create_metric_card(
                "Current Bias",
                current_bias,
                "At key decision point",
                "🧭",
                bias_type
            ), unsafe_allow_html=True)
        
        # Strategy table
        st.markdown("### 📊 Trading Strategy Table")
        
        # Enhanced table with styling
        if not data['strategy_df'].empty:
            display_df = data['strategy_df'].copy()
            
            # Apply conditional formatting via CSS classes
            def highlight_830(row):
                if row['Time'] == '08:30':
                    return ['background-color: var(--warning-50); font-weight: 700;'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                display_df,
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
                    "Score": st.column_config.TextColumn("Score", width="small"),
                    "Confidence": st.column_config.TextColumn("Confidence", width="small"),
                    "Entry_Signal": st.column_config.TextColumn("Entry Signal", width="large")
                }
            )
        
        # Volume analysis if available
        if not data['spx_data'].empty and "Volume" in data['spx_data'].columns:
            st.markdown("### 📈 Volume Context Analysis")
            
            volume_context = get_volume_context(data['spx_data'], controls['proj_day'])
            
            vol_col1, vol_col2, vol_col3 = st.columns(3)
            
            with vol_col1:
                avg_vol = volume_context.get('avg_volume', 0)
                vol_percentile = volume_context.get('volume_percentile', 50)
                vol_type = "success" if vol_percentile > 75 else "warning" if vol_percentile < 25 else "neutral"
                
                st.markdown(create_metric_card(
                    "Volume Profile",
                    f"{vol_percentile:.0f}%ile",
                    f"Avg: {avg_vol:,.0f}",
                    "📊",
                    vol_type
                ), unsafe_allow_html=True)
            
            with vol_col2:
                session_vols = volume_context.get('session_volumes', {})
                asia_vol = session_vols.get('asia', 0)
                london_vol = session_vols.get('london', 0)
                total_overnight = asia_vol + london_vol
                
                st.markdown(create_metric_card(
                    "Overnight Volume",
                    f"{total_overnight:,.0f}",
                    f"Asia: {asia_vol:,.0f} | London: {london_vol:,.0f}",
                    "🌙",
                    "neutral"
                ), unsafe_allow_html=True)
            
            with vol_col3:
                high_vol_periods = volume_context.get('high_volume_periods', [])
                spike_count = len(high_vol_periods)
                
                st.markdown(create_metric_card(
                    "Volume Spikes",
                    str(spike_count),
                    f">{VOLUME_SPIKE_THRESHOLD}x threshold",
                    "⚡",
                    "warning" if spike_count > 3 else "neutral"
                ), unsafe_allow_html=True)
    
    else:
        st.info("👆 Click 'Refresh SPX Anchors' in the sidebar to begin analysis")

# ═══════════════════════════════════════════════════════════════════════════════
# BC FORECAST TAB
# ═══════════════════════════════════════════════════════════════════════════════

def render_bc_forecast_tab(controls: Dict):
    """Render the BC Forecast (Bounce + Contract) tab."""
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
    
    # Generate overnight session slots for input
    asia_start = fmt_ct(datetime.combine(controls["prev_day"], time(19, 0)))
    europe_end = fmt_ct(datetime.combine(controls["proj_day"], time(7, 0)))
    
    session_slots = []
    current_slot = asia_start
    while current_slot <= europe_end:
        session_slots.append(current_slot)
        current_slot += timedelta(minutes=30)
    
    slot_options = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]
    
    # BC Forecast form
    with st.form("bc_forecast_form", clear_on_submit=False):
        st.markdown("### 📍 Underlying Bounces (Exactly 2 Required)")
        
        bounce_col1, bounce_col2 = st.columns(2)
        
        with bounce_col1:
            st.markdown("**Bounce #1**")
            b1_time = st.selectbox(
                "Time (30m slot)",
                options=slot_options,
                index=0,
                key="b1_time",
                help="First bounce timestamp"
            )
            b1_price = st.number_input(
                "SPX Price",
                value=6500.00,
                step=0.25,
                format="%.2f",
                key="b1_price",
                help="SPX price at first bounce"
            )
        
        with bounce_col2:
            st.markdown("**Bounce #2**")
            b2_time = st.selectbox(
                "Time (30m slot)",
                options=slot_options,
                index=min(6, len(slot_options)-1),
                key="b2_time",
                help="Second bounce timestamp"
            )
            b2_price = st.number_input(
                "SPX Price",
                value=6512.00,
                step=0.25,
                format="%.2f",
                key="b2_price",
                help="SPX price at second bounce"
            )
        
        st.markdown("---")
        st.markdown("### 📋 Contract A (Required)")
        
        ca_col1, ca_col2 = st.columns(2)
        
        with ca_col1:
            ca_symbol = st.text_input(
                "Contract Symbol",
                value="6525c",
                key="ca_symbol",
                help="Contract identifier (e.g., 6525c, 6500p)"
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
        
        st.markdown("---")
        st.markdown("### 📋 Contract B (Optional)")
        
        enable_contract_b = st.checkbox(
            "Add second contract",
            value=False,
            key="enable_cb",
            help="Enable second contract analysis"
        )
        
        if enable_contract_b:
            cb_col1, cb_col2 = st.columns(2)
            
            with cb_col1:
                cb_symbol = st.text_input(
                    "Contract B Symbol",
                    value="6515c",
                    key="cb_symbol"
                )
                cb_b1_price = st.number_input(
                    "B: Price at Bounce #1",
                    value=9.50,
                    step=0.05,
                    format="%.2f",
                    key="cb_b1_price"
                )
                cb_b2_price = st.number_input(
                    "B: Price at Bounce #2",
                    value=11.80,
                    step=0.05,
                    format="%.2f",
                    key="cb_b2_price"
                )
            
            with cb_col2:
                cb_h1_time = st.selectbox(
                    "B: High after Bounce #1 - Time",
                    options=slot_options,
                    index=min(3, len(slot_options)-1),
                    key="cb_h1_time"
                )
                cb_h1_price = st.number_input(
                    "B: High after Bounce #1 - Price",
                    value=13.30,
                    step=0.05,
                    format="%.2f",
                    key="cb_h1_price"
                )
                cb_h2_time = st.selectbox(
                    "B: High after Bounce #2 - Time", 
                    options=slot_options,
                    index=min(9, len(slot_options)-1),
                    key="cb_h2_time"
                )
                cb_h2_price = st.number_input(
                    "B: High after Bounce #2 - Price",
                    value=15.10,
                    step=0.05,
                    format="%.2f",
                    key="cb_h2_price"
                )
        
        # Submit button
        submitted = st.form_submit_button(
            "🚀 Generate NY Session Projections",
            type="primary",
            use_container_width=True
        )
    
    # Process BC forecast
    if submitted:
        try:
            # Parse bounce times
            b1_dt = fmt_ct(datetime.strptime(st.session_state["b1_time"], "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(st.session_state["b2_time"], "%Y-%m-%d %H:%M"))
            
            if b2_dt <= b1_dt:
                st.error("❌ Bounce #2 must occur after Bounce #1")
                return
            
            # Calculate underlying slope and projection
            underlying_df, underlying_slope = project_contract_line(
                b1_dt, st.session_state["b1_price"],
                b2_dt, st.session_state["b2_price"],
                controls["proj_day"], "SPX_Projected"
            )
            
            # Add slot highlighting
            underlying_df.insert(0, "Slot", 
                underlying_df["Time"].apply(lambda x: "⭐ 8:30" if x == "08:30" else ""))
            
            # Contract A projections
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
            
            # Expected exit time for Contract A
            ca_expected_exit = calculate_expected_exit_time(
                b1_dt, ca_h1_dt, b2_dt, ca_h2_dt, controls["proj_day"]
            )
            
            # Merge data
            result_df = underlying_df.merge(ca_entry_df, on="Time").merge(ca_exit_df, on="Time")
            result_df[f"{st.session_state['ca_symbol']}_Spread"] = (
                result_df[f"{st.session_state['ca_symbol']}_Exit"] - 
                result_df[f"{st.session_state['ca_symbol']}_Entry"]
            )
            
            # Contract B if enabled
            cb_data = {}
            if enable_contract_b:
                cb_entry_df, cb_entry_slope = project_contract_line(
                    b1_dt, st.session_state["cb_b1_price"],
                    b2_dt, st.session_state["cb_b2_price"], 
                    controls["proj_day"], f"{st.session_state['cb_symbol']}_Entry"
                )
                
                cb_h1_dt = fmt_ct(datetime.strptime(st.session_state["cb_h1_time"], "%Y-%m-%d %H:%M"))
                cb_h2_dt = fmt_ct(datetime.strptime(st.session_state["cb_h2_time"], "%Y-%m-%d %H:%M"))
                
                cb_exit_df, cb_exit_slope = project_contract_line(
                    cb_h1_dt, st.session_state["cb_h1_price"],
                    cb_h2_dt, st.session_state["cb_h2_price"],
                    controls["proj_day"], f"{st.session_state['cb_symbol']}_Exit"
                )
                
                cb_expected_exit = calculate_expected_exit_time(
                    b1_dt, cb_h1_dt, b2_dt, cb_h2_dt, controls["proj_day"]
                )
                
                result_df = result_df.merge(cb_entry_df, on="Time").merge(cb_exit_df, on="Time")
                result_df[f"{st.session_state['cb_symbol']}_Spread"] = (
                    result_df[f"{st.session_state['cb_symbol']}_Exit"] - 
                    result_df[f"{st.session_state['cb_symbol']}_Entry"]
                )
                
                cb_data = {
                    "symbol": st.session_state['cb_symbol'],
                    "entry_slope": cb_entry_slope,
                    "exit_slope": cb_exit_slope,
                    "expected_exit": cb_expected_exit
                }
            
            # Store results
            st.session_state["bc_results"] = {
                "table": result_df,
                "underlying_slope": underlying_slope,
                "ca_symbol": st.session_state['ca_symbol'],
                "ca_entry_slope": ca_entry_slope,
                "ca_exit_slope": ca_exit_slope,
                "ca_expected_exit": ca_expected_exit,
                "cb_data": cb_data,
                "bounce_times": [b1_dt, b2_dt]
            }
            
        except Exception as e:
            st.error(f"❌ Error generating BC forecast: {str(e)}")
            return
    
    # Display results
    if "bc_results" in st.session_state:
        results = st.session_state["bc_results"]
        
        # Summary metrics
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
                f"Exit: {results['ca_exit_slope']:+.3f} per 30m",
                "📊",
                "success"
            ), unsafe_allow_html=True)
        
        with metric_col3:
            if results['cb_data']:
                cb = results['cb_data']
                st.markdown(create_metric_card(
                    f"{cb['symbol']} Entry",
                    f"{cb['entry_slope']:+.3f}",
                    f"Exit: {cb['exit_slope']:+.3f} per 30m",
                    "📊",
                    "success"
                ), unsafe_allow_html=True)
            else:
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
        
        # Projection table
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

# ═══════════════════════════════════════════════════════════════════════════════
# PLAN CARD TAB  
# ═══════════════════════════════════════════════════════════════════════════════

def render_plan_card_tab():
    """Render the Plan Card session preparation tab."""
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
    
    # Check if required data is available
    has_anchors = "anchors_data" in st.session_state
    has_bc = "bc_results" in st.session_state
    
    if not has_anchors:
        st.warning("⚠️ SPX Anchors data required. Please refresh SPX Anchors first.")
        return
    
    anchors = st.session_state["anchors_data"]
    bc = st.session_state.get("bc_results", None)
    
    # Plan Card metrics
    st.markdown("### 🎯 Session Overview")
    
    plan_col1, plan_col2, plan_col3, plan_col4 = st.columns(4)
    
    with plan_col1:
        st.markdown(create_metric_card(
            "Anchor Close",
            f"{anchors['anchor_close']:.2f}",
            f"Previous day{anchors['anchor_label']}",
            "⚓",
            "primary"
        ), unsafe_allow_html=True)
    
    with plan_col2:
        # Fan width at 8:30
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
        # BC Status
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
        # Readiness score
        readiness_score = 85 if (has_anchors and bc) else 65 if has_anchors else 25
        readiness_type = "success" if readiness_score >= 80 else "warning" if readiness_score >= 60 else "danger"
        
        st.markdown(create_metric_card(
            "Readiness",
            f"{readiness_score}%",
            "Plan completeness",
            "🎯",
            readiness_type
        ), unsafe_allow_html=True)
    
    # Trading plan sections
    plan_left, plan_right = st.columns(2)
    
    with plan_left:
        st.markdown("""
        <div class="enterprise-card">
            <h3 style="margin-top: 0; display: flex; align-items: center; gap: 8px;">
                🎯 Primary Setup (SPX Anchors)
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 8:30 AM setup
        row_830 = strategy_df[strategy_df['Time'] == '08:30']
        if not row_830.empty:
            setup = row_830.iloc[0]
            st.markdown(f"""
            **8:30 AM Key Levels:**
            - **Bias:** {create_status_badge(setup['Bias'], 'up' if setup['Bias'] == 'UP' else 'down' if setup['Bias'] == 'DOWN' else 'neutral')}
            - **Fan Top:** {setup['Top']:.2f}
            - **Fan Bottom:** {setup['Bottom']:.2f}
            - **Strength:** {setup['Strength']}
            - **Entry Signal:** {setup['Entry_Signal']}
            """, unsafe_allow_html=True)
        else:
            st.info("8:30 AM data not available")
        
        # Key bias levels
        st.markdown("**Additional Fan Levels:**")
        key_times = ['09:00', '10:00', '13:00', '14:00']
        for time_slot in key_times:
            time_row = strategy_df[strategy_df['Time'] == time_slot]
            if not time_row.empty:
                row = time_row.iloc[0]
                st.markdown(f"- **{time_slot}:** Top {row['Top']:.2f} | Bottom {row['Bottom']:.2f}")
    
    with plan_right:
        st.markdown("""
        <div class="enterprise-card">
            <h3 style="margin-top: 0; display: flex; align-items: center; gap: 8px;">
                💼 Contract Strategy (BC Forecast)
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if bc:
            # BC contract plan
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
                
                if bc['cb_data']:
                    cb_sym = bc['cb_data']['symbol']
                    st.markdown(f"""
                    - **{cb_sym} Entry:** {bc_row[f"{cb_sym}_Entry"]:.2f}
                    - **{cb_sym} Exit Ref:** {bc_row[f"{cb_sym}_Exit"]:.2f}
                    """)
            
            # Risk parameters
            st.markdown("**Risk Management:**")
            st.markdown(f"""
            - **Underlying Slope:** {bc['underlying_slope']:+.3f} per 30m
            - **Contract A Slope:** {bc['ca_entry_slope']:+.3f} per 30m
            - **Time Decay Risk:** Monitor after {bc['ca_expected_exit']}
            """)
        else:
            st.info("Set up BC Forecast for contract projections")
    
    # Action plan
    st.markdown("### 📋 Pre-Market Action Plan")
    
    action_items = []
    
    if has_anchors:
        bias_830 = strategy_df[strategy_df['Time'] == '08:30']['Bias'].iloc[0] if not strategy_df.empty else "N/A"
        if bias_830 == "UP":
            action_items.append("✅ **Bullish Setup** - Look for long entries on dips to fan bottom")
        elif bias_830 == "DOWN":
            action_items.append("🔻 **Bearish Setup** - Look for short entries on rallies to fan top")
        else:
            action_items.append("⚡ **Neutral Setup** - Wait for fan breakout confirmation")
    
    if bc:
        action_items.append(f"📊 **Contract Focus** - Primary: {bc['ca_symbol']} | Target Exit: {bc['ca_expected_exit']}")
        if bc['cb_data']:
            action_items.append(f"📊 **Secondary Contract** - {bc['cb_data']['symbol']} for diversification")
    
    action_items.extend([
        "⏰ **Key Times** - 8:30 (open), 10:00 (trend confirm), 13:30 (late session)",
        "📏 **Risk Management** - Respect fan levels and time-based exits",
        "🎯 **Decision Points** - Fan breaks, volume spikes, time targets"
    ])
    
    for item in action_items:
        st.markdown(item)
    
    # Export plan button
    if st.button("📄 Export Trading Plan", type="secondary", use_container_width=True):
        st.success("Trading plan exported to session state (ready for external use)")
        
        # Store exportable plan
        export_plan = {
            "date": datetime.now(CT_TZ).strftime("%Y-%m-%d %H:%M CT"),
            "anchor": anchors,
            "bc_forecast": bc,
            "readiness_score": readiness_score,
            "action_items": action_items
        }
        st.session_state["exported_plan"] = export_plan






