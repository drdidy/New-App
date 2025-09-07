# app.py - Part 1/4 (COMPLETE WITH FIX)
# SPX Prophet - Enterprise Trading Analytics Platform
# Complete UI overhaul with premium card layout, icons, and light theme

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

# Liquidity session windows (CT)
SYD_TOK = [(21,0), (21,30)]  # Sydney-Tokyo overlap
TOK_LON = [(2,0), (2,30)]    # Tokyo-London overlap  
PRE_NY = [(7,0), (7,30)]     # Pre-NY session

# Liquidity scoring weights
W_SYD_TOK = 25
W_TOK_LON = 40
W_PRE_NY = 20

# Probability scoring weights
WEIGHTS = {
    "confluence": 25,
    "structure": 20,
    "wick": 15,
    "atr": 10,
    "compression": 10,
    "gap": 10,
    "cluster": 10,
    "volume": 8,
    "time_decay": 5,
    "session_momentum": 7
}

# Technical parameters
ATR_LOOKBACK = 14
RANGE_WIN = 20
GAP_LOOKBACK = 3
WICK_MIN_RATIO = 0.6
TOUCH_CLUSTER_WINDOW = 6
VOLUME_SPIKE_THRESHOLD = 1.25

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION & ENTERPRISE UI SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="⚡ SPX Prophet - Enterprise Trading Analytics",
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
    padding: 16px;
    box-shadow: var(--shadow-md);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    min-height: 120px;
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
    gap: 8px;
    margin-bottom: 8px;
}

.metric-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 600;
    background: var(--gradient-primary);
    color: white;
    box-shadow: var(--shadow-md);
    flex-shrink: 0;
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
    margin: 4px 0;
    line-height: 1.1;
    font-family: 'JetBrains Mono', monospace;
}

.metric-subtext {
    font-size: 0.65rem;
    color: var(--text-tertiary);
    font-weight: 500;
    line-height: 1.3;
    margin-top: auto;
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

.action-button-primary {
    background: var(--gradient-primary) !important;
}

.action-button-success {
    background: var(--gradient-success) !important;
}

.action-button-danger {
    background: var(--gradient-danger) !important;
}

/* ═══════════════════════════════════════════════════════════════════════════════
   TAB SYSTEM (FIXED)
   ═══════════════════════════════════════════════════════════════════════════════ */

.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-tertiary) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 16px !important;
    padding: 8px !important;
    margin-top: 40px !important;
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

.bg-pattern {
    background-image: radial-gradient(circle at 25px 25px, var(--border-light) 2%, transparent 0%),
                      radial-gradient(circle at 75px 75px, var(--border-light) 2%, transparent 0%);
    background-size: 100px 100px;
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

def true_range(df: pd.DataFrame) -> pd.Series:
    """Calculate True Range for ATR computation."""
    prev_close = df["Close"].shift(1)
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - prev_close).abs()
    tr3 = (df["Low"] - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

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
        <h1 class="header-title">⚡ {title}</h1>
        {f'<p class="header-subtitle">{subtitle}</p>' if subtitle else ''}
    </div>
    """








# Part 2/4: Trading Logic, Fan Calculations, and New Scoring Features
# SPX-only anchor logic, bias calculations, and enhanced probability scoring

# ═══════════════════════════════════════════════════════════════════════════════
# SPX-ONLY ANCHOR LOGIC (No SPY Fallback)
# ═══════════════════════════════════════════════════════════════════════════════

def get_spx_anchor_prevday(prev_day: date) -> Tuple[Optional[float], Optional[datetime], bool]:
    """
    Fetch SPX anchor from previous day ≤ 3:00 PM CT using ^GSPC only.
    Returns (anchor_close, anchor_time, estimated_flag)
    """
    target = fmt_ct(datetime.combine(prev_day, time(15, 0)))
    
    # Try multiple intervals for ^GSPC
    for interval in ["30m", "5m", "1m"]:
        spx = fetch_intraday("^GSPC", prev_day, prev_day, interval)
        if spx.empty:
            continue
            
        # Find last close ≤ 3:00 PM CT
        subset = spx.loc[:target]
        if subset.empty:
            continue
            
        anchor_close = float(subset["Close"].iloc[-1])
        anchor_time = fmt_ct(subset.index[-1].to_pydatetime())
        return anchor_close, anchor_time, False
    
    # Fallback: Estimate anchor from ES using recent median offset
    est_close, est_time = estimate_anchor_from_es(prev_day)
    return est_close, est_time, True

def recent_median_es_spx_offset(prev_day: date, lookback_days: int = 7) -> Optional[float]:
    """Compute recent median ES→SPX offset for anchor estimation."""
    offsets = []
    
    for i in range(1, lookback_days + 1):
        check_date = prev_day - timedelta(days=i)
        target_3pm = fmt_ct(datetime.combine(check_date, time(15, 0)))
        
        # Get SPX close at ≤ 3:00 PM
        spx_data = None
        for interval in ["30m", "5m", "1m"]:
            spx = fetch_intraday("^GSPC", check_date, check_date, interval)
            if not spx.empty:
                spx_subset = spx.loc[:target_3pm]
                if not spx_subset.empty:
                    spx_data = float(spx_subset["Close"].iloc[-1])
                    break
        
        if spx_data is None:
            continue
            
        # Get ES close at ≤ 3:00 PM
        es_data = None
        for interval in ["5m", "1m"]:
            es = fetch_intraday("ES=F", check_date, check_date, interval)
            if not es.empty:
                es_subset = es.loc[:target_3pm]
                if not es_subset.empty:
                    es_data = float(es_subset["Close"].iloc[-1])
                    break
        
        if es_data is None:
            continue
            
        offsets.append(es_data - spx_data)
    
    return float(np.median(offsets)) if offsets else None

def estimate_anchor_from_es(prev_day: date) -> Tuple[Optional[float], Optional[datetime]]:
    """Estimate SPX anchor from ES when ^GSPC unavailable."""
    target_3pm = fmt_ct(datetime.combine(prev_day, time(15, 0)))
    
    # Get ES close at ≤ 3:00 PM
    es_close = None
    for interval in ["5m", "1m"]:
        es = fetch_intraday("ES=F", prev_day, prev_day, interval)
        if not es.empty:
            es_subset = es.loc[:target_3pm]
            if not es_subset.empty:
                es_close = float(es_subset["Close"].iloc[-1])
                break
    
    if es_close is None:
        return None, None
        
    # Get recent median offset
    offset = recent_median_es_spx_offset(prev_day, lookback_days=7)
    if offset is None:
        return None, None
        
    estimated_spx = es_close - offset
    return float(estimated_spx), target_3pm

# ═══════════════════════════════════════════════════════════════════════════════
# FAN PROJECTION & BIAS LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def current_spx_slopes() -> Tuple[float, float]:
    """Get current fan slopes from session state or defaults."""
    top = float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT))
    bottom = float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT))
    return top, bottom

def project_fan_from_close(close_price: float, anchor_time: datetime, target_day: date) -> pd.DataFrame:
    """Project asymmetric fan lines for RTH slots."""
    top_slope, bottom_slope = current_spx_slopes()
    
    rows = []
    for slot in rth_slots_ct(target_day):
        blocks = count_effective_blocks(anchor_time, slot)
        top_level = close_price + top_slope * blocks
        bottom_level = close_price - bottom_slope * blocks
        
        rows.append({
            "TimeDT": slot,
            "Time": slot.strftime("%H:%M"),
            "Top": round(top_level, 2),
            "Bottom": round(bottom_level, 2),
            "Fan_Width": round(top_level - bottom_level, 2)
        })
    
    return pd.DataFrame(rows)

def compute_bias(price: float, top: float, bottom: float, tol_frac: float) -> str:
    """Compute bias based on price position relative to fan levels."""
    if price > top:
        return "UP"
    if price < bottom:
        return "DOWN"
    
    # Within fan - check proximity to edges
    width = top - bottom
    center = (top + bottom) / 2.0
    neutral_band = tol_frac * width
    
    if abs(price - center) <= neutral_band:
        return "NO BIAS"
    
    # Closer to which edge?
    distance_to_top = top - price
    distance_to_bottom = price - bottom
    
    return "UP" if distance_to_bottom < distance_to_top else "DOWN"

# ═══════════════════════════════════════════════════════════════════════════════
# ES→SPX CONVERSION FOR OVERNIGHT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def _nearest_le_index(idx: pd.DatetimeIndex, ts: pd.Timestamp) -> Optional[pd.Timestamp]:
    """Find nearest index less than or equal to timestamp."""
    subset = idx[idx <= ts]
    return subset[-1] if len(subset) else None

def es_spx_offset_at_anchor(prev_day: date) -> Optional[float]:
    """Calculate ES→SPX offset at anchor time for overnight conversion."""
    # Get SPX anchor first
    spx_close, spx_time, is_estimated = get_spx_anchor_prevday(prev_day)
    
    if spx_close is None or spx_time is None or is_estimated:
        # Fall back to recent median if no real SPX anchor
        return recent_median_es_spx_offset(prev_day, lookback_days=7)
    
    # Try to find ES price near the SPX anchor time
    def try_es_interval(interval: str) -> Optional[float]:
        es_data = fetch_intraday("ES=F", prev_day, prev_day, interval)
        if es_data.empty or "Close" not in es_data.columns:
            return None
            
        # Look for ES data in window around SPX anchor time
        window_start = spx_time - timedelta(minutes=30)
        window_end = spx_time
        window_data = es_data.loc[(es_data.index >= window_start) & (es_data.index <= window_end)]
        
        if not window_data.empty:
            es_close = float(window_data["Close"].iloc[-1])
            return es_close - spx_close
            
        # Fallback: nearest ES close ≤ SPX anchor time
        nearest_idx = _nearest_le_index(es_data.index, spx_time)
        if nearest_idx is not None:
            es_close = float(es_data.loc[nearest_idx, "Close"])
            return es_close - spx_close
            
        return None
    
    # Try intervals in order of preference
    for interval in ["1m", "5m", "30m"]:
        offset = try_es_interval(interval)
        if offset is not None:
            return float(offset)
    
    # Final fallback to recent median
    return recent_median_es_spx_offset(prev_day, lookback_days=7)

def fetch_overnight(prev_day: date, proj_day: date) -> pd.DataFrame:
    """Fetch ES overnight data as 30m bars for analysis."""
    start_time = fmt_ct(datetime.combine(prev_day, time(17, 0)))
    end_time = fmt_ct(datetime.combine(proj_day, time(8, 30)))
    
    # Try 30m directly first
    es_30m = fetch_intraday("ES=F", prev_day, proj_day, "30m")
    if not es_30m.empty:
        return es_30m.loc[start_time:end_time].copy()
    
    # Fallback: resample from finer data
    for interval in ["5m", "1m"]:
        es_data = fetch_intraday("ES=F", prev_day, proj_day, interval)
        if not es_data.empty:
            subset = es_data.loc[start_time:end_time].copy()
            return resample_to_30m_ct(subset)
    
    return pd.DataFrame()

def adjust_to_spx_frame(es_df: pd.DataFrame, offset: float) -> pd.DataFrame:
    """Convert ES prices to SPX equivalent using offset."""
    df = es_df.copy()
    for col in ["Open", "High", "Low", "Close"]:
        if col in df:
            df[col] = df[col] - offset
    return df

# ═══════════════════════════════════════════════════════════════════════════════
# DIRECTION-OF-TRAVEL & EDGE INTERACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def prior_state(prior_close: float, prior_top: float, prior_bottom: float) -> str:
    """Determine where price was coming from relative to fan."""
    if prior_close > prior_top:
        return "from_above"
    if prior_close < prior_bottom:
        return "from_below"
    return "from_inside"

def classify_interaction_30m(prev_close: float, prev_top: float, prev_bot: float,
                           cur_bar: pd.Series, cur_top: float, cur_bot: float) -> Optional[Dict]:
    """
    Classify 30m edge interactions based on direction-of-travel rules:
    - From above, breaks below Top + closes inside → bearish continuation to Bottom
    - From below, breaks above Bottom + closes inside → bullish continuation to Top
    """
    state = prior_state(prev_close, prev_top, prev_bot)
    
    o = float(cur_bar["Open"])
    h = float(cur_bar["High"])
    l = float(cur_bar["Low"])
    c = float(cur_bar["Close"])
    
    inside = (cur_bot < c < cur_top)
    epsilon = max(0.5, 0.02 * (cur_top - cur_bot))  # Small tolerance for edge touches
    
    if state == "from_above":
        # Price was above fan, did it re-enter?
        if (l < cur_top + epsilon) and inside:
            return {
                "edge": "Top",
                "case": "FromAbove_ReenterInside",
                "expected": "Bearish continuation to Bottom",
                "direction": "Down"
            }
    
    elif state == "from_below":
        # Price was below fan, did it re-enter?
        if (h > cur_bot - epsilon) and inside:
            return {
                "edge": "Bottom",
                "case": "FromBelow_ReenterInside", 
                "expected": "Bullish continuation to Top",
                "direction": "Up"
            }
    
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# NEW FEATURE: VOLUME CONTEXT SCORING
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_volume_context(df_30m: pd.DataFrame, ts: pd.Timestamp, expected_dir: str) -> Dict[str, int]:
    """
    Enhanced volume analysis for fan touch significance:
    - Volume spike at edge touch
    - Volume vs session averages  
    - Volume distribution patterns
    """
    volume_scores = {"volume_spike": 0, "volume_trend": 0, "volume_distribution": 0}
    
    if "Volume" not in df_30m.columns or df_30m["Volume"].notna().sum() < 10:
        return volume_scores
    
    current_volume = df_30m.loc[ts, "Volume"]
    if pd.isna(current_volume):
        return volume_scores
    
    # 1. Volume Spike Detection
    volume_ma = df_30m["Volume"].rolling(20, min_periods=10).mean()
    if pd.notna(volume_ma.loc[ts]) and current_volume > volume_ma.loc[ts] * VOLUME_SPIKE_THRESHOLD:
        volume_scores["volume_spike"] = 8
    
    # 2. Volume Trend Analysis (recent 5 bars)
    recent_volumes = df_30m["Volume"].loc[:ts].tail(5)
    if len(recent_volumes) >= 3:
        volume_trend = np.polyfit(range(len(recent_volumes)), recent_volumes.values, 1)[0]
        if expected_dir == "Up" and volume_trend > 0:
            volume_scores["volume_trend"] = 5
        elif expected_dir == "Down" and volume_trend < 0:
            volume_scores["volume_trend"] = 3
    
    # 3. Session Volume Distribution
    # Check if we're in high-volume session window
    ts_ct = fmt_ct(ts.to_pydatetime())
    hour = ts_ct.hour
    
    # Typical high-volume periods: 9-10 AM, 2-3 PM
    if (9 <= hour <= 10) or (14 <= hour <= 15):
        if current_volume > volume_ma.loc[ts] * 1.1:  # Above average in high-volume window
            volume_scores["volume_distribution"] = 4
    else:
        # Off-peak hours with volume spike is more significant
        if current_volume > volume_ma.loc[ts] * 1.3:
            volume_scores["volume_distribution"] = 6
    
    return volume_scores

def calculate_overnight_volume_context(overnight_df: pd.DataFrame) -> Dict[str, float]:
    """Analyze overnight volume patterns vs typical session volume."""
    if "Volume" not in overnight_df.columns or overnight_df["Volume"].notna().sum() < 3:
        return {"overnight_vs_session": 0.0, "overnight_distribution": 0.0}
    
    # Calculate overnight volume metrics
    overnight_volume = overnight_df["Volume"].sum()
    overnight_avg_per_bar = overnight_df["Volume"].mean()
    
    # Rough session volume estimate (would be better with historical data)
    estimated_session_avg = overnight_avg_per_bar * 2.5  # Sessions typically 2.5x overnight volume
    
    volume_ratio = overnight_avg_per_bar / estimated_session_avg if estimated_session_avg > 0 else 0
    
    # Volume distribution across overnight sessions
    asia_volume = overnight_df.loc[overnight_df.index.hour.isin([21, 22, 23, 0, 1]), "Volume"].sum()
    europe_volume = overnight_df.loc[overnight_df.index.hour.isin([2, 3, 4, 5, 6, 7]), "Volume"].sum()
    
    total_overnight = asia_volume + europe_volume
    distribution_score = 0.0
    
    if total_overnight > 0:
        asia_pct = asia_volume / total_overnight
        europe_pct = europe_volume / total_overnight
        
        # Balanced distribution across sessions indicates institutional participation
        if 0.3 <= asia_pct <= 0.7 and 0.3 <= europe_pct <= 0.7:
            distribution_score = 3.0
        # Heavy concentration in one session
        elif asia_pct > 0.8 or europe_pct > 0.8:
            distribution_score = 1.5
    
    return {
        "overnight_vs_session": min(5.0, volume_ratio * 10),  # Cap at 5 points
        "overnight_distribution": distribution_score
    }

# ═══════════════════════════════════════════════════════════════════════════════
# NEW FEATURE: TIME-BASED EDGE SCORING  
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_session_momentum(ts: pd.Timestamp, expected_dir: str, 
                           asia_touches: List[pd.Timestamp], 
                           london_touches: List[pd.Timestamp]) -> Dict[str, int]:
    """
    Analyze session transition momentum and directional persistence:
    - Asia→London→NY handoff patterns
    - Time-of-day significance weighting
    - Cross-session directional alignment
    """
    momentum_scores = {"session_transition": 0, "time_significance": 0, "directional_persistence": 0}
    
    ts_ct = fmt_ct(ts.to_pydatetime())
    hour = ts_ct.hour
    
    # 1. Session Transition Analysis
    # Key transition windows: 2-3 AM (Tokyo-London), 7-8 AM (Pre-NY)
    if 2 <= hour <= 3:  # Tokyo-London transition
        if len(asia_touches) > 0 and len(london_touches) == 0:
            momentum_scores["session_transition"] = 6  # First London touch after Asia setup
        elif len(asia_touches) > 0 and len(london_touches) > 0:
            momentum_scores["session_transition"] = 4  # Continuation pattern
    
    elif 7 <= hour <= 8:  # Pre-NY window
        if len(london_touches) > 0:
            momentum_scores["session_transition"] = 7  # Europe→NY handoff
        if len(asia_touches) > 0 and len(london_touches) > 0:
            momentum_scores["session_transition"] = 9  # Triple session alignment
    
    # 2. Time-of-Day Significance
    # Key decision points: 8:30 AM (NY open), 10:00 AM (follow-through), 2:30 PM (close)
    if hour == 8:  # Pre-NY open (most significant)
        momentum_scores["time_significance"] = 10
    elif hour == 21:  # Asia open
        momentum_scores["time_significance"] = 6
    elif hour == 2:  # London open  
        momentum_scores["time_significance"] = 7
    elif hour == 10:  # NY follow-through
        momentum_scores["time_significance"] = 5
    elif hour == 14:  # NY close approach
        momentum_scores["time_significance"] = 4
    
    # 3. Directional Persistence Analysis
    # Check if recent touches align with current expected direction
    recent_window = pd.Timestamp.now() - timedelta(hours=3)
    recent_asia = [t for t in asia_touches if t >= recent_window]
    recent_london = [t for t in london_touches if t >= recent_window]
    
    total_recent = len(recent_asia) + len(recent_london)
    if total_recent >= 2:
        momentum_scores["directional_persistence"] = 5  # Multiple recent touches suggest momentum
    elif total_recent == 1:
        momentum_scores["directional_persistence"] = 3  # Single recent touch
    
    return momentum_scores

def calculate_time_decay_factor(ts: pd.Timestamp, current_time: pd.Timestamp = None) -> float:
    """Calculate time decay factor - more recent touches weighted higher."""
    if current_time is None:
        current_time = pd.Timestamp.now(tz=CT_TZ)
    
    hours_ago = (current_time - ts).total_seconds() / 3600
    
    # Exponential decay: recent = higher weight
    if hours_ago <= 1:
        return 1.0
    elif hours_ago <= 3:
        return 0.8
    elif hours_ago <= 6:
        return 0.6
    elif hours_ago <= 12:
        return 0.4
    else:
        return 0.2

def analyze_weekend_gap_behavior(prev_day: date, touches_df: pd.DataFrame) -> Dict[str, int]:
    """Analyze weekend gap patterns and Friday→Monday behavior."""
    gap_scores = {"weekend_setup": 0, "gap_direction": 0}
    
    # Check if prev_day was Friday (weekday 4)
    if prev_day.weekday() != 4:
        return gap_scores
    
    # Look for Friday evening / weekend setup patterns
    friday_evening_touches = touches_df[
        (touches_df["TimeDT"].dt.hour >= 17) | 
        (touches_df["TimeDT"].dt.hour <= 23)
    ]
    
    if len(friday_evening_touches) > 0:
        gap_scores["weekend_setup"] = 4
        
        # Analyze directional bias going into weekend
        latest_touch = friday_evening_touches.iloc[-1]
        if latest_touch["ExpectedDir"] == "Up":
            gap_scores["gap_direction"] = 3
        else:
            gap_scores["gap_direction"] = 2
    
    return gap_scores





# Part 3/4: Your Original Working Code (Dashboard Builders & Probability Board)

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD BUILDS (Your exact working functions)
# ═══════════════════════════════════════════════════════════════════════════════

def build_comprehensive_probability_board(prev_day: date, proj_day: date,
                            anchor_close: float, anchor_time: datetime,
                            tol_frac: float) -> Tuple[pd.DataFrame, pd.DataFrame, float, Dict]:
    """Your exact working build_probability_board function with 4 return values for Part 4."""
    fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)

    offset = es_spx_offset_at_anchor(prev_day)
    if offset is None:
        return pd.DataFrame(), fan_df, 0.0, {}

    es_on = fetch_overnight(prev_day, proj_day)
    if es_on.empty:
        return pd.DataFrame(), fan_df, float(offset), {}

    on_30 = adjust_to_spx_frame(es_on, offset)

    rows = []
    for ts, bar in on_30.iterrows():
        blocks = count_effective_blocks(anchor_time, ts)
        tslope, bslope = current_spx_slopes()
        top = anchor_close + tslope * blocks
        bot = anchor_close - bslope * blocks
        rows.append((ts, bar, top, bot))

    touches_rows = []
    qualified_timestamps = []

    for i in range(1, len(rows)):
        prev_ts, prev_bar, prev_top, prev_bot = rows[i-1][0], rows[i-1][1], rows[i-1][2], rows[i-1][3]
        ts, bar, top, bot = rows[i][0], rows[i][1], rows[i][2], rows[i][3]

        prev_close = float(prev_bar["Close"])
        interaction = classify_interaction_30m(prev_close, prev_top, prev_bot, bar, top, bot)
        if interaction is None:
            continue

        expected_dir = interaction["direction"]
        touches_recent = qualified_timestamps[-5:]
        ts_ct = fmt_ct(ts.to_pydatetime())
        is_asia_overlap = in_window(ts_ct, SYD_TOK)
        is_toklon_overlap = in_window(ts_ct, TOK_LON)

        score, parts, lb = compute_score_components(on_30, ts, expected_dir, touches_recent,
                                                    asia_hit=is_asia_overlap, london_hit=is_toklon_overlap)

        qualified_timestamps.append(ts)

        price = float(bar["Close"])
        bias = compute_bias(price, top, bot, tol_frac)

        touches_rows.append({
            "TimeDT": ts, "Time": ts.strftime("%H:%M"),
            "Price": round(price,2), "Top": round(top,2), "Bottom": round(bot,2),
            "Bias": bias, "Edge": interaction["edge"], "Case": interaction["case"],
            "Expectation": interaction["expected"], "ExpectedDir": expected_dir,
            "Score": score, "LiquidityBonus": lb,
            "Confluence_w": parts["Confluence"], "Structure_w": parts["Structure"], "Wick_w": parts["Wick"],
            "ATR_w": parts["ATR"], "Compression_w": parts["Compression"], "Gap_w": parts["Gap"],
            "Cluster_w": parts["Cluster"], "Volume_w": parts["Volume"]
        })

    touches_df = pd.DataFrame(touches_rows).sort_values("TimeDT").reset_index(drop=True)
    
    # Simple summary stats for Part 4
    summary_stats = {
        "total_interactions": len(touches_rows),
        "avg_score": touches_df["Score"].mean() if not touches_df.empty else 0,
        "max_score": touches_df["Score"].max() if not touches_df.empty else 0,
        "asia_touches": len([ts for ts in qualified_timestamps if in_window(fmt_ct(ts.to_pydatetime()), SYD_TOK)]),
        "london_touches": len([ts for ts in qualified_timestamps if in_window(fmt_ct(ts.to_pydatetime()), TOK_LON)]),
        "volume_quality": 3.0
    }
    
    return touches_df, fan_df, float(offset), summary_stats

# ═══════════════════════════════════════════════════════════════════════════════
# BC FORECAST (Your exact working functions)
# ═══════════════════════════════════════════════════════════════════════════════

def project_line(p1_dt, p1_price, p2_dt, p2_price, proj_day, label_proj: str):
    blocks = count_effective_blocks(p1_dt, p2_dt)
    slope = (p2_price - p1_price) / blocks if blocks > 0 else 0.0
    rows = []
    for slot in rth_slots_ct(proj_day):
        b = count_effective_blocks(p1_dt, slot)
        price = p1_price + slope * b
        rows.append({"Time": slot.strftime("%H:%M"), label_proj: round(price,2)})
    return pd.DataFrame(rows), slope

def expected_exit_time(b1_dt, h1_dt, b2_dt, h2_dt, proj_day):
    d1 = count_effective_blocks(b1_dt, h1_dt)
    d2 = count_effective_blocks(b2_dt, h2_dt)
    durations = [d for d in [d1, d2] if d > 0]
    if not durations:
        return "n/a"
    med_blocks = int(round(np.median(durations)))
    candidate = b2_dt
    step = 0
    while step < med_blocks:
        candidate += timedelta(minutes=30)
        if not is_maintenance(candidate) and not in_weekend_gap(candidate):
            step += 1
    for slot in rth_slots_ct(proj_day):
        if slot >= candidate:
            return slot.strftime("%H:%M")
    return "n/a"








# Part 4/4: Your Working UI Layout (No fancy additions, just your tabs that work)

# ═══════════════════════════════════════════════════════════════════════════════
# TABS (Your exact working structure)
# ═══════════════════════════════════════════════════════════════════════════════

tabAnchors, tabBC, tabProb, tabPlan = st.tabs(
    ["SPX Anchors", "BC Forecast", "Probability Board", "Plan Card"]
)

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 1: SPX ANCHORS (Your exact working code)                               ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabAnchors:
    st.subheader("SPX Anchors — Entries & Exits from Fan (⭐ 8:30 highlight)")
    if btn_anchor:
        with st.spinner("Building SPX fan & strategy…"):
            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time  = fmt_ct(datetime.combine(prev_day, time(15,0)))
                anchor_label = ""
            else:
                anchor_close, anchor_time, est = get_spx_anchor_prevday(prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("❌ Could not resolve ^GSPC anchor at ≤ 3:00 PM CT (and ES estimate failed).")
                    st.stop()
                anchor_label = " (est)" if est else ""

            fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)

            # Try to fetch SPX 30m for the projection day (display only)
            spx_proj_rth = fetch_intraday("^GSPC", proj_day, proj_day, "30m")
            spx_proj_rth = between_time(spx_proj_rth, RTH_START, RTH_END) if not spx_proj_rth.empty else pd.DataFrame()

            tslope, bslope = current_spx_slopes()
            rows = []
            iter_index = (spx_proj_rth.index if not spx_proj_rth.empty
                          else pd.DatetimeIndex(rth_slots_ct(proj_day)))
            for dt in iter_index:
                blocks = count_effective_blocks(anchor_time, dt)
                top = anchor_close + tslope * blocks
                bottom = anchor_close - bslope * blocks
                if not spx_proj_rth.empty and dt in spx_proj_rth.index:
                    bar = spx_proj_rth.loc[dt]
                    price = float(bar["Close"])
                    bias = compute_bias(price, top, bottom, st.session_state.get("tol_frac", NEUTRAL_BAND_DEFAULT))
                    note = "—"
                    pdisp = round(price,2)
                else:
                    bias = "—"
                    note = "Fan only"
                    pdisp = "—"
                rows.append({
                    "Slot": "⭐ 8:30" if dt.strftime("%H:%M")=="08:30" else "",
                    "Time": dt.strftime("%H:%M"),
                    "Price": pdisp,
                    "Bias": bias, "Top": round(top,2), "Bottom": round(bottom,2),
                    "Fan_Width": round(top-bottom,2),
                    "Note": note
                })
            strat_df = pd.DataFrame(rows)

            st.session_state["anchors"] = {
                "fan_df": fan_df, "strat_df": strat_df,
                "anchor_close": anchor_close, "anchor_time": anchor_time,
                "anchor_label": anchor_label,
                "prev_day": prev_day, "proj_day": proj_day
            }

    if "anchors" in st.session_state:
        fan_df   = st.session_state["anchors"]["fan_df"]
        strat_df = st.session_state["anchors"]["strat_df"]

        st.markdown("### 🎯 Fan Lines (Top / Bottom @ 30-min) — **SPX levels**")
        st.dataframe(fan_df[["Time","Top","Bottom","Fan_Width"]], use_container_width=True, hide_index=True)

        st.markdown("### 📋 Strategy Table (SPX RTH if available; otherwise fan-only)")
        st.caption("Bias uses within-fan proximity with neutrality band; ⭐ highlights 8:30.")
        st.dataframe(
            strat_df[["Slot","Time","Price","Bias","Top","Bottom","Fan_Width","Note"]],
            use_container_width=True, hide_index=True
        )

        st.info(f"Anchor: {st.session_state['anchors']['anchor_close']:.2f} at {st.session_state['anchors']['anchor_time'].strftime('%Y-%m-%d %H:%M CT')}{st.session_state['anchors']['anchor_label']}")
    else:
        st.info("Use **Refresh SPX Anchors** in the sidebar.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 2: BC FORECAST (Your exact working code)                               ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabBC:
    st.subheader("BC Forecast — Bounce + Contract Forecast (Asia/Europe → NY 8:30–14:30)")
    st.caption("Requires **exactly 2 SPX bounces** (times + prices). For each contract, provide prices at both bounces and highs after each bounce (with times).")

    asia_start = fmt_ct(datetime.combine(prev_day, time(19,0)))
    euro_end   = fmt_ct(datetime.combine(proj_day, time(7,0)))
    session_slots = []
    cur = asia_start
    while cur <= euro_end:
        session_slots.append(cur)
        cur += timedelta(minutes=30)
    slot_labels = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]

    with st.form("bc_form_v3", clear_on_submit=False):
        st.markdown("**Underlying bounces (exactly two):**")
        c1, c2 = st.columns(2)
        with c1:
            b1_sel = st.selectbox("Bounce #1 Time (slot)", slot_labels, index=0, key="bc_b1_sel")
            b1_spx = st.number_input("Bounce #1 SPX Price", value=6500.00, step=0.25, format="%.2f", key="bc_b1_spx")
        with c2:
            b2_sel = st.selectbox("Bounce #2 Time (slot)", slot_labels, index=min(6, len(slot_labels)-1), key="bc_b2_sel")
            b2_spx = st.number_input("Bounce #2 SPX Price", value=6512.00, step=0.25, format="%.2f", key="bc_b2_spx")

        st.markdown("---")
        st.markdown("**Contract A (required)**")
        ca_sym = st.text_input("Contract A Label", value="6525c", key="bc_ca_sym")
        ca_b1_price = st.number_input("A: Price at Bounce #1", value=10.00, step=0.05, format="%.2f", key="bc_ca_b1_price")
        ca_b2_price = st.number_input("A: Price at Bounce #2", value=12.50, step=0.05, format="%.2f", key="bc_ca_b2_price")
        ca_h1_time  = st.selectbox("A: High after Bounce #1 — Time", slot_labels, index=min(2, len(slot_labels)-1), key="bc_ca_h1_time")
        ca_h1_price = st.number_input("A: High after Bounce #1 — Price", value=14.00, step=0.05, format="%.2f", key="bc_ca_h1_price")
        ca_h2_time  = st.selectbox("A: High after Bounce #2 — Time", slot_labels, index=min(8, len(slot_labels)-1), key="bc_ca_h2_time")
        ca_h2_price = st.number_input("A: High after Bounce #2 — Price", value=16.00, step=0.05, format="%.2f", key="bc_ca_h2_price")

        st.markdown("---")
        st.markdown("**Contract B (optional)**")
        cb_enable = st.checkbox("Add Contract B", value=False, key="bc_cb_enable")
        if cb_enable:
            cb_sym = st.text_input("Contract B Label", value="6515c", key="bc_cb_sym")
            cb_b1_price = st.number_input("B: Price at Bounce #1", value=9.50, step=0.05, format="%.2f", key="bc_cb_b1_price")
            cb_b2_price = st.number_input("B: Price at Bounce #2", value=11.80, step=0.05, format="%.2f", key="bc_cb_b2_price")
            cb_h1_time  = st.selectbox("B: High after Bounce #1 — Time", slot_labels, index=min(3, len(slot_labels)-1), key="bc_cb_h1_time")
            cb_h1_price = st.number_input("B: High after Bounce #1 — Price", value=13.30, step=0.05, format="%.2f", key="bc_cb_h1_price")
            cb_h2_time  = st.selectbox("B: High after Bounce #2 — Time", slot_labels, index=min(9, len(slot_labels)-1), key="bc_cb_h2_time")
            cb_h2_price = st.number_input("B: High after Bounce #2 — Price", value=15.10, step=0.05, format="%.2f", key="bc_cb_h2_price")

        submit_bc = st.form_submit_button("📈 Project NY Session (8:30–14:30)")

    if submit_bc:
        try:
            b1_dt = fmt_ct(datetime.strptime(st.session_state["bc_b1_sel"], "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(st.session_state["bc_b2_sel"], "%Y-%m-%d %H:%M"))
            if b2_dt <= b1_dt:
                st.error("Bounce #2 must occur after Bounce #1.")
            else:
                # Underlying slope from bounces
                blocks_u = count_effective_blocks(b1_dt, b2_dt)
                u_slope = (float(b2_spx) - float(b1_spx)) / blocks_u if blocks_u > 0 else 0.0

                # SPX projection from bounces
                rows_u = []
                for slot in rth_slots_ct(proj_day):
                    b = count_effective_blocks(b1_dt, slot)
                    price = float(b1_spx) + u_slope * b
                    rows_u.append({"Time": slot.strftime("%H:%M"), "SPX_Projected": round(price,2)})
                spx_proj_df = pd.DataFrame(rows_u)
                spx_proj_df.insert(0, "Slot", spx_proj_df["Time"].apply(lambda x: "⭐ 8:30" if x=="08:30" else ""))

                # Contract A lines
                ca_entry_df, ca_entry_slope = project_line(b1_dt, float(ca_b1_price), b2_dt, float(ca_b2_price), proj_day, f"{st.session_state['bc_ca_sym']}_Entry")
                ca_h1_dt = fmt_ct(datetime.strptime(st.session_state["bc_ca_h1_time"], "%Y-%m-%d %H:%M"))
                ca_h2_dt = fmt_ct(datetime.strptime(st.session_state["bc_ca_h2_time"], "%Y-%m-%d %H:%M"))
                ca_exit_df, ca_exit_slope = project_line(ca_h1_dt, float(ca_h1_price), ca_h2_dt, float(ca_h2_price), proj_day, f"{st.session_state['bc_ca_sym']}_Exit")

                # Contract B (optional)
                cb_entry_df = cb_exit_df = None
                cb_entry_slope = cb_exit_slope = 0.0
                if cb_enable:
                    cb_entry_df, cb_entry_slope = project_line(b1_dt, float(cb_b1_price), b2_dt, float(cb_b2_price), proj_day, f"{st.session_state['bc_cb_sym']}_Entry")
                    cb_h1_dt = fmt_ct(datetime.strptime(st.session_state["bc_cb_h1_time"], "%Y-%m-%d %H:%M"))
                    cb_h2_dt = fmt_ct(datetime.strptime(st.session_state["bc_cb_h2_time"], "%Y-%m-%d %H:%M"))
                    cb_exit_df, cb_exit_slope = project_line(cb_h1_dt, float(cb_h1_price), cb_h2_dt, float(cb_h2_price), proj_day, f"{st.session_state['bc_cb_sym']}_Exit")

                # Merge & spreads
                out = spx_proj_df.merge(ca_entry_df, on="Time", how="left").merge(ca_exit_df, on="Time", how="left")
                ca = st.session_state["bc_ca_sym"]
                out[f"{ca}_Spread"] = out[f"{ca}_Exit"] - out[f"{ca}_Entry"]
                if cb_enable and cb_entry_df is not None and cb_exit_df is not None:
                    cb = st.session_state["bc_cb_sym"]
                    out = out.merge(cb_entry_df, on="Time", how="left").merge(cb_exit_df, on="Time", how="left")
                    out[f"{cb}_Spread"] = out[f"{cb}_Exit"] - out[f"{cb}_Entry"]

                # Expected exits
                ca_expected = expected_exit_time(b1_dt, ca_h1_dt, b2_dt, ca_h2_dt, proj_day)
                cb_expected = expected_exit_time(b1_dt, cb_h1_dt, b2_dt, cb_h2_dt, proj_day) if cb_enable else None

                # Metrics
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"<div class='metric-card'><p class='metric-title'>Underlying Slope /30m</p><div class='metric-value'>📐 {u_slope:+.3f}</div><div class='kicker'>From 2 bounces</div></div>", unsafe_allow_html=True)
                with m2: st.markdown(f"<div class='metric-card'><p class='metric-title'>{ca} Entry Slope /30m</p><div class='metric-value'>📈 {ca_entry_slope:+.3f}</div><div class='kicker'>Exit slope {ca_exit_slope:+.3f} • Expected exit ≈ {ca_expected}</div></div>", unsafe_allow_html=True)
                with m3:
                    if cb_enable:
                        cb = st.session_state["bc_cb_sym"]
                        st.markdown(f"<div class='metric-card'><p class='metric-title'>{cb} Entry Slope /30m</p><div class='metric-value'>📈 {cb_entry_slope:+.3f}</div><div class='kicker'>Exit slope {cb_exit_slope:+.3f} • Expected exit ≈ {cb_expected}</div></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='metric-card'><p class='metric-title'>Contracts</p><div class='metric-value'>1</div></div>", unsafe_allow_html=True)
                with m4:
                    st.markdown(f"<div class='metric-card'><p class='metric-title'>BC Forecast</p><div class='metric-value'>⭐ 8:30 highlighted</div><div class='kicker'>Spread = Exit − Entry</div></div>", unsafe_allow_html=True)

                st.markdown("### 🔮 NY Session Projection (SPX + Contract Entry/Exit Lines)")
                st.dataframe(out, use_container_width=True, hide_index=True)

                st.session_state["bc_result"] = {
                    "table": out, "u_slope": u_slope,
                    "ca_sym": ca, "cb_sym": (st.session_state["bc_cb_sym"] if cb_enable else None),
                    "ca_expected": ca_expected, "cb_expected": cb_expected
                }
        except Exception as e:
            st.error(f"BC Forecast error: {e}")

    if "bc_result" not in st.session_state:
        st.info("Fill the form and click **Project NY Session**.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 3: PROBABILITY BOARD (Your exact working code)                         ║
# ╚═════════════════════════════════════════════════════════════════════════════╝
with tabProb:
    st.subheader("Probability Board — Overnight Edge Confidence (30m-only, liquidity-weighted)")
    show_adv = st.checkbox("Show advanced component columns", value=False, key="prob_show_adv")

    if btn_prob:
        with st.spinner("Evaluating qualified 30m interactions…"):
            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time  = fmt_ct(datetime.combine(prev_day, time(15,0)))
                anchor_label = ""
            else:
                anchor_close, anchor_time, est = get_spx_anchor_prevday(prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("❌ Could not resolve ^GSPC anchor at ≤ 3:00 PM CT (and ES estimate failed).")
                    st.stop()
                anchor_label = " (est)" if est else ""

            touches_df, fan_df, offset_used, summary_stats = build_comprehensive_probability_board(
                prev_day, proj_day, anchor_close, anchor_time, st.session_state.get("tol_frac", NEUTRAL_BAND_DEFAULT)
            )

            st.session_state["prob_result"] = {
                "touches_df": touches_df, "fan_df": fan_df,
                "offset_used": float(offset_used),
                "anchor_close": anchor_close, "anchor_time": anchor_time,
                "anchor_label": anchor_label,
                "prev_day": prev_day, "proj_day": proj_day,
                "summary_stats": summary_stats
            }

    if "prob_result" in st.session_state:
        pr = st.session_state["prob_result"]
        touches_df = pr["touches_df"]

        cA, cB, cC = st.columns(3)
        with cA:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Anchor Close (Prev ≤3:00 PM)</p><div class='metric-value'>💠 {pr['anchor_close']:.2f}{pr['anchor_label']}</div></div>", unsafe_allow_html=True)
        with cB:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Qualified Interactions</p><div class='metric-value'>🧩 {len(touches_df)}</div></div>", unsafe_allow_html=True)
        with cC:
            st.markdown(f"<div class='metric-card'><p class='metric-title'>ES→SPX Offset</p><div class='metric-value'>Δ {pr['offset_used']:+.2f}</div><div class='kicker'>Applied under the hood</div></div>", unsafe_allow_html=True)

        st.markdown("### 📡 Overnight 30m Edge Interactions (Scored)")
        if touches_df.empty:
            st.info("No qualified edge interactions detected for this window.")
        else:
            base_cols = ["Time","Price","Top","Bottom","Bias","Edge","Case","Expectation","ExpectedDir","Score","LiquidityBonus"]
            adv_cols  = ["Confluence_w","Structure_w","Wick_w","ATR_w","Compression_w","Gap_w","Cluster_w","Volume_w"]
            cols = base_cols + (adv_cols if show_adv else [])
            st.dataframe(touches_df[cols], use_container_width=True, hide_index=True)
    else:
        st.info("Use **Refresh Probability Board** in the sidebar.")

# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║ TAB 4: PLAN CARD (Your exact working code)                                 ║
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

        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f"<div class='metric-card'><p class='metric-title'>Anchor Close</p><div class='metric-value'>💠 {an['anchor_close']:.2f}{an['anchor_label']}</div><div class='kicker'>Prev ≤ 3:00 PM CT</div></div>", unsafe_allow_html=True)
        with m2: 
            w830 = an['fan_df'].loc[an['fan_df']['Time']=='08:30','Fan_Width']
            fan_w = float(w830.iloc[0]) if not w830.empty else np.nan
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Fan Width @ 8:30</p><div class='metric-value'>🧭 {fan_w:.2f}</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-card'><p class='metric-title'>ES→SPX Offset</p><div class='metric-value'>Δ {pr['offset_used']:+.2f}</div><div class='kicker'>Overnight basis</div></div>", unsafe_allow_html=True)
        with m4:
            tdf = pr["touches_df"]
            top3 = int(np.mean(sorted(tdf["Score"].tolist(), reverse=True)[:3])) if not tdf.empty else 0
            st.markdown(f"<div class='metric-card'><p class='metric-title'>Readiness</p><div class='metric-value'>🔥 {top3}</div><div class='kicker'>Top-3 score avg</div></div>", unsafe_allow_html=True)

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
            tdf = pr["touches_df"]
            if not tdf.empty:
                for _, r in tdf.sort_values("Score", ascending=False).head(3).iterrows():
                    st.write(f"- {r['Time']}: **{r['Edge']}** {r['Case']} → *{r['Expectation']}* (Score {r['Score']}, +{r['LiquidityBonus']} liquidity)")
            else:
                st.write("- No scored interactions.")

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
                    if bc.get("ca_expected") and bc["ca_expected"] != "n/a":
                        st.write(f"- **{ca} expected exit ≈ {bc['ca_expected']}**")
                    if cb and bc.get("cb_expected") and bc["cb_expected"] != "n/a":
                        st.write(f"- **{cb} expected exit ≈ {bc['cb_expected']}**")
            else:
                st.write("- Use BC Forecast to pre-compute contract lines and exits.")
