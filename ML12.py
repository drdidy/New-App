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










# Part 3/4 (FIXED): Dashboard Builders, Probability Board & Advanced Scoring Integration
# Comprehensive scoring system with volume context and time-based edge analysis

# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED SCORING COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

def in_liquidity_window(ts: datetime, window: List[Tuple[int, int]]) -> bool:
    """Check if timestamp falls within liquidity window."""
    minute_of_day = ts.hour * 60 + ts.minute
    start_minute = window[0][0] * 60 + window[0][1]
    end_minute = window[1][0] * 60 + window[1][1]
    return start_minute <= minute_of_day <= end_minute

def calculate_liquidity_bonus(ts: datetime) -> int:
    """Calculate liquidity bonus based on session overlap."""
    if in_liquidity_window(ts, SYD_TOK):
        return W_SYD_TOK
    if in_liquidity_window(ts, TOK_LON):
        return W_TOK_LON
    if in_liquidity_window(ts, PRE_NY):
        return W_PRE_NY
    return 0

def calculate_atr_percentile(df_30m: pd.DataFrame, idx: pd.Timestamp) -> float:
    """Calculate ATR percentile for volatility regime analysis."""
    subset = df_30m.loc[:idx]
    tr_series = true_range(subset)
    atr_series = tr_series.rolling(ATR_LOOKBACK, min_periods=ATR_LOOKBACK//2).mean()
    
    if atr_series.notna().sum() < ATR_LOOKBACK//2:
        return 50.0
    
    percentile = (atr_series.rank(pct=True).iloc[-1]) * 100.0
    return float(percentile)

def detect_range_compression(df_30m: pd.DataFrame, idx: pd.Timestamp) -> bool:
    """Detect if current range is compressed vs recent average."""
    subset = df_30m.loc[:idx]
    if len(subset) < RANGE_WIN:
        return False
    
    current_range = subset["High"].iloc[-1] - subset["Low"].iloc[-1]
    rolling_avg_range = (subset["High"] - subset["Low"]).rolling(RANGE_WIN).mean().iloc[-1]
    
    return current_range <= rolling_avg_range * 0.85

def analyze_gap_context(df_30m: pd.DataFrame, idx: pd.Timestamp, expected_dir: str) -> int:
    """Analyze gap context relative to expected direction."""
    if idx not in df_30m.index:
        return 0
    
    idx_pos = df_30m.index.get_loc(idx)
    if idx_pos == 0:
        return 0
    
    prev_close = float(df_30m["Close"].iloc[idx_pos - 1])
    current_open = float(df_30m["Open"].iloc[idx_pos])
    gap_size = current_open - prev_close
    
    # Positive gap favors upward moves, negative gap favors downward moves
    if expected_dir == "Up":
        return 5 if gap_size >= 0 else 0
    else:
        return 5 if gap_size <= 0 else 0

def assess_wick_quality(bar: pd.Series, expected_dir: str) -> bool:
    """Assess wick rejection quality relative to expected direction."""
    o, h, l, c = float(bar["Open"]), float(bar["High"]), float(bar["Low"]), float(bar["Close"])
    
    body_size = max(1e-9, abs(c - o))
    upper_wick = max(0.0, h - max(o, c))
    lower_wick = max(0.0, min(o, c) - l)
    
    if expected_dir == "Up":
        # Lower wick rejection supports upward move
        return (lower_wick / body_size) >= WICK_MIN_RATIO
    else:
        # Upper wick rejection supports downward move
        return (upper_wick / body_size) >= WICK_MIN_RATIO

def detect_touch_clustering(touch_history: List[pd.Timestamp], current_ts: pd.Timestamp) -> bool:
    """Detect if similar qualified touches occurred recently."""
    cutoff_time = current_ts - pd.Timedelta(hours=TOUCH_CLUSTER_WINDOW / 2)
    recent_touches = [t for t in touch_history if cutoff_time <= t < current_ts]
    return len(recent_touches) > 0

# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATED SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_comprehensive_score(df_30m: pd.DataFrame, ts: pd.Timestamp, expected_dir: str,
                               touch_history: List[pd.Timestamp], asia_hits: set, 
                               london_hits: set, overnight_volume_context: Dict) -> Tuple[int, Dict[str, int], int]:
    """
    Comprehensive scoring engine integrating all probability components:
    - Traditional technical factors
    - Volume context analysis  
    - Time-based edge scoring
    - Session transition momentum
    """
    ts_ct = fmt_ct(ts.to_pydatetime())
    
    # Base liquidity bonus
    liquidity_bonus = calculate_liquidity_bonus(ts_ct)
    
    # Traditional scoring components
    score_components = {}
    
    # 1. Confluence (cross-session alignment)
    asia_hit = ts in asia_hits
    london_hit = ts in london_hits
    if asia_hit and london_hit:
        score_components["confluence"] = WEIGHTS["confluence"]
    elif asia_hit or london_hit:
        score_components["confluence"] = WEIGHTS["confluence"] // 2
    else:
        score_components["confluence"] = 0
    
    # 2. Structure (edge interaction qualification)
    score_components["structure"] = WEIGHTS["structure"]  # Already qualified
    
    # 3. Wick quality
    score_components["wick"] = WEIGHTS["wick"] if assess_wick_quality(df_30m.loc[ts], expected_dir) else 0
    
    # 4. ATR regime analysis
    atr_percentile = calculate_atr_percentile(df_30m, ts)
    if expected_dir == "Up":
        score_components["atr"] = WEIGHTS["atr"] if atr_percentile <= 40 else 0
    else:
        score_components["atr"] = WEIGHTS["atr"] if atr_percentile >= 60 else 0
    
    # 5. Range compression
    score_components["compression"] = WEIGHTS["compression"] if detect_range_compression(df_30m, ts) else 0
    
    # 6. Gap context
    score_components["gap"] = analyze_gap_context(df_30m, ts, expected_dir)
    
    # 7. Touch clustering
    score_components["cluster"] = WEIGHTS["cluster"] if detect_touch_clustering(touch_history, ts) else 0
    
    # NEW: Volume Context Scoring
    volume_analysis = analyze_volume_context(df_30m, ts, expected_dir)
    score_components["volume_spike"] = volume_analysis["volume_spike"]
    score_components["volume_trend"] = volume_analysis["volume_trend"] 
    score_components["volume_distribution"] = volume_analysis["volume_distribution"]
    
    # Add overnight volume context
    score_components["overnight_volume"] = int(overnight_volume_context.get("overnight_vs_session", 0))
    score_components["volume_dist_quality"] = int(overnight_volume_context.get("overnight_distribution", 0))
    
    # NEW: Time-Based Edge Scoring
    asia_touch_times = [t for t in touch_history if t in asia_hits]
    london_touch_times = [t for t in touch_history if t in london_hits]
    
    momentum_analysis = analyze_session_momentum(ts, expected_dir, asia_touch_times, london_touch_times)
    score_components["session_transition"] = momentum_analysis["session_transition"]
    score_components["time_significance"] = momentum_analysis["time_significance"]
    score_components["directional_persistence"] = momentum_analysis["directional_persistence"]
    
    # Time decay factor
    decay_factor = calculate_time_decay_factor(ts)
    score_components["time_decay"] = int(WEIGHTS["time_decay"] * decay_factor)
    
    # Calculate total score
    base_score = sum(score_components.values())
    final_score = min(100, max(0, base_score + liquidity_bonus))
    
    return final_score, score_components, liquidity_bonus

# ═══════════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE PROBABILITY BOARD BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_comprehensive_probability_board(prev_day: date, proj_day: date,
                                        anchor_close: float, anchor_time: datetime,
                                        tolerance_fraction: float) -> Tuple[pd.DataFrame, pd.DataFrame, float, Dict]:
    """
    Build comprehensive probability board with enhanced scoring:
    - Fan projection for RTH
    - Overnight edge interaction detection
    - Volume context analysis
    - Time-based momentum scoring
    """
    
    # Generate RTH fan projection
    fan_projection = project_fan_from_close(anchor_close, anchor_time, proj_day)
    
    # Calculate ES→SPX offset
    es_offset = es_spx_offset_at_anchor(prev_day)
    if es_offset is None:
        return pd.DataFrame(), fan_projection, 0.0, {}
    
    # Fetch overnight ES data
    overnight_es = fetch_overnight(prev_day, proj_day)
    if overnight_es.empty:
        return pd.DataFrame(), fan_projection, float(es_offset), {}
    
    # Convert to SPX frame
    overnight_spx = adjust_to_spx_frame(overnight_es, es_offset)
    
    # Analyze overnight volume context
    overnight_vol_context = calculate_overnight_volume_context(overnight_spx)
    
    # Generate fan levels for each overnight timestamp
    fan_timeline = []
    for ts, bar in overnight_spx.iterrows():
        blocks_from_anchor = count_effective_blocks(anchor_time, ts)
        top_slope, bottom_slope = current_spx_slopes()
        
        top_level = anchor_close + top_slope * blocks_from_anchor
        bottom_level = anchor_close - bottom_slope * blocks_from_anchor
        
        fan_timeline.append((ts, bar, top_level, bottom_level))
    
    # Detect qualified edge interactions
    qualified_interactions = []
    touch_history = []
    asia_touches = set()
    london_touches = set()
    
    for i in range(1, len(fan_timeline)):
        prev_ts, prev_bar, prev_top, prev_bottom = fan_timeline[i-1]
        current_ts, current_bar, current_top, current_bottom = fan_timeline[i]
        
        # Check for qualified interaction
        prev_close = float(prev_bar["Close"])
        interaction = classify_interaction_30m(prev_close, prev_top, prev_bottom, 
                                             current_bar, current_top, current_bottom)
        
        if interaction is None:
            continue
        
        # Track session hits
        ts_ct = fmt_ct(current_ts.to_pydatetime())
        if in_liquidity_window(ts_ct, SYD_TOK):
            asia_touches.add(current_ts)
        if in_liquidity_window(ts_ct, TOK_LON):
            london_touches.add(current_ts)
        
        # Calculate comprehensive score
        expected_direction = interaction["direction"]
        final_score, score_breakdown, liquidity_bonus = compute_comprehensive_score(
            overnight_spx, current_ts, expected_direction, touch_history[-10:],  # Last 10 touches
            asia_touches, london_touches, overnight_vol_context
        )
        
        # Update touch history
        touch_history.append(current_ts)
        
        # Calculate current bias
        current_price = float(current_bar["Close"])
        current_bias = compute_bias(current_price, current_top, current_bottom, tolerance_fraction)
        
        # Store interaction record
        interaction_record = {
            "TimeDT": current_ts,
            "Time": current_ts.strftime("%H:%M"),
            "Price": round(current_price, 2),
            "Top": round(current_top, 2),
            "Bottom": round(current_bottom, 2),
            "Bias": current_bias,
            "Edge": interaction["edge"],
            "Case": interaction["case"],
            "Expectation": interaction["expected"],
            "ExpectedDir": expected_direction,
            "Score": final_score,
            "LiquidityBonus": liquidity_bonus,
            
            # Traditional components (for backwards compatibility)
            "Confluence_w": score_breakdown["confluence"],
            "Structure_w": score_breakdown["structure"], 
            "Wick_w": score_breakdown["wick"],
            "ATR_w": score_breakdown["atr"],
            "Compression_w": score_breakdown["compression"],
            "Gap_w": score_breakdown["gap"],
            "Cluster_w": score_breakdown["cluster"],
            
            # NEW: Volume components
            "VolumeSpike_w": score_breakdown["volume_spike"],
            "VolumeTrend_w": score_breakdown["volume_trend"],
            "VolumeDistribution_w": score_breakdown["volume_distribution"],
            "OvernightVolume_w": score_breakdown["overnight_volume"],
            "VolumeQuality_w": score_breakdown["volume_dist_quality"],
            
            # NEW: Time-based components
            "SessionTransition_w": score_breakdown["session_transition"],
            "TimeSignificance_w": score_breakdown["time_significance"],
            "DirectionalPersistence_w": score_breakdown["directional_persistence"],
            "TimeDecay_w": score_breakdown["time_decay"]
        }
        
        qualified_interactions.append(interaction_record)
    
    # Convert to DataFrame
    interactions_df = pd.DataFrame(qualified_interactions)
    if not interactions_df.empty:
        interactions_df = interactions_df.sort_values("TimeDT").reset_index(drop=True)
    
    # Calculate summary statistics
    summary_stats = {
        "total_interactions": len(qualified_interactions),
        "avg_score": interactions_df["Score"].mean() if not interactions_df.empty else 0,
        "max_score": interactions_df["Score"].max() if not interactions_df.empty else 0,
        "asia_touches": len(asia_touches),
        "london_touches": len(london_touches),
        "volume_quality": overnight_vol_context.get("overnight_distribution", 0)
    }
    
    return interactions_df, fan_projection, float(es_offset), summary_stats

# ═══════════════════════════════════════════════════════════════════════════════
# COMPATIBILITY WRAPPER FOR EXISTING CODE
# ═══════════════════════════════════════════════════════════════════════════════

def build_probability_board(prev_day: date, proj_day: date,
                          anchor_close: float, anchor_time: datetime,
                          tol_frac: float) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Compatibility wrapper for existing code - maintains original function signature.
    Calls comprehensive version and returns only the original 3 values.
    """
    interactions_df, fan_df, es_offset, summary_stats = build_comprehensive_probability_board(
        prev_day, proj_day, anchor_close, anchor_time, tol_frac
    )
    
    return interactions_df, fan_df, es_offset

# ═══════════════════════════════════════════════════════════════════════════════
# BC FORECAST SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

def project_contract_line(bounce1_dt: datetime, bounce1_price: float,
                         bounce2_dt: datetime, bounce2_price: float,
                         projection_day: date, contract_label: str) -> Tuple[pd.DataFrame, float]:
    """Project contract price line from two bounce points."""
    effective_blocks = count_effective_blocks(bounce1_dt, bounce2_dt)
    slope_per_block = (bounce2_price - bounce1_price) / effective_blocks if effective_blocks > 0 else 0.0
    
    projection_rows = []
    for time_slot in rth_slots_ct(projection_day):
        blocks_from_b1 = count_effective_blocks(bounce1_dt, time_slot)
        projected_price = bounce1_price + slope_per_block * blocks_from_b1
        
        projection_rows.append({
            "Time": time_slot.strftime("%H:%M"),
            contract_label: round(projected_price, 2)
        })
    
    return pd.DataFrame(projection_rows), slope_per_block

def calculate_expected_exit_timing(b1_dt: datetime, h1_dt: datetime,
                                 b2_dt: datetime, h2_dt: datetime,
                                 projection_day: date) -> str:
    """Calculate expected exit timing based on historical bounce→high durations."""
    duration1 = count_effective_blocks(b1_dt, h1_dt)
    duration2 = count_effective_blocks(b2_dt, h2_dt)
    
    durations = [d for d in [duration1, duration2] if d > 0]
    if not durations:
        return "n/a"
    
    median_duration = int(round(np.median(durations)))
    
    # Project from second bounce
    exit_candidate = b2_dt
    blocks_walked = 0
    
    while blocks_walked < median_duration:
        exit_candidate += timedelta(minutes=30)
        if not is_maintenance(exit_candidate) and not in_weekend_gap(exit_candidate):
            blocks_walked += 1
    
    # Find corresponding RTH slot
    for rth_slot in rth_slots_ct(projection_day):
        if rth_slot >= exit_candidate:
            return rth_slot.strftime("%H:%M")
    
    return "n/a"

# Keep the original project_line function name for BC Forecast compatibility
def project_line(p1_dt, p1_price, p2_dt, p2_price, proj_day, label_proj: str):
    """Original function name compatibility for BC Forecast."""
    return project_contract_line(p1_dt, p1_price, p2_dt, p2_price, proj_day, label_proj)

def expected_exit_time(b1_dt, h1_dt, b2_dt, h2_dt, proj_day):
    """Original function name compatibility for BC Forecast."""
    return calculate_expected_exit_timing(b1_dt, h1_dt, b2_dt, h2_dt, proj_day)

# ═══════════════════════════════════════════════════════════════════════════════
# READINESS SCORING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_readiness_score(interactions_df: pd.DataFrame, summary_stats: Dict) -> Tuple[int, str, str]:
    """
    Calculate overall trading readiness score and classification:
    - Skip: Low confidence (0-40)
    - Medium: Moderate confidence (41-70)  
    - High: Strong confidence (71-100)
    """
    if interactions_df.empty:
        return 0, "SKIP", "No qualified interactions detected"
    
    # Primary metrics
    scores = interactions_df["Score"].tolist()
    top_3_avg = int(np.mean(sorted(scores, reverse=True)[:3])) if len(scores) >= 3 else int(np.mean(scores))
    
    # Adjustment factors
    volume_quality = summary_stats.get("volume_quality", 0)
    session_coverage = min(summary_stats.get("asia_touches", 0), 1) + min(summary_stats.get("london_touches", 0), 1)
    
    # Calculate adjusted readiness
    base_readiness = top_3_avg
    volume_adjustment = min(5, volume_quality * 2)  # Max +5 for volume quality
    coverage_adjustment = session_coverage * 3      # Max +6 for dual session coverage
    
    final_readiness = min(100, base_readiness + volume_adjustment + coverage_adjustment)
    
    # Classification
    if final_readiness >= 71:
        classification = "HIGH"
        indicator = "High Confidence"
    elif final_readiness >= 41:
        classification = "MEDIUM" 
        indicator = "Medium Confidence"
    else:
        classification = "SKIP"
        indicator = "Low Confidence"
    
    return final_readiness, classification, indicator

def generate_trade_recommendations(interactions_df: pd.DataFrame, fan_df: pd.DataFrame,
                                 readiness_score: int) -> List[str]:
    """Generate specific trade recommendations based on analysis."""
    recommendations = []
    
    if interactions_df.empty:
        recommendations.append("No qualified setups detected - consider waiting")
        return recommendations
    
    # Analyze top interactions
    top_interactions = interactions_df.nlargest(3, "Score")
    
    for _, interaction in top_interactions.iterrows():
        direction = interaction["ExpectedDir"]
        edge = interaction["Edge"]
        score = interaction["Score"]
        time_str = interaction["Time"]
        
        if score >= 70:
            confidence = "High"
        elif score >= 50:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        rec = f"{confidence} confidence {direction.lower()} from {edge} interaction @ {time_str} (Score: {score})"
        recommendations.append(rec)
    
    # Add sizing guidance
    if readiness_score >= 71:
        recommendations.append("Consider standard position sizing")
    elif readiness_score >= 41:
        recommendations.append("Consider reduced position sizing")
    else:
        recommendations.append("Consider skipping or minimal sizing")
    
    return recommendations







# Part 4/4: Complete Enterprise UI Layout with Premium Dashboard
# Main interface, sidebar controls, header metrics, and tab system

# ═══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE SIDEBAR CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

# Main header
st.markdown(create_header_section(
    "SPX Prophet", 
    "Enterprise Trading Analytics Platform • SPX-Only • 30m Focus"
), unsafe_allow_html=True)

# Initialize session state for enhanced features
if "enhanced_features_enabled" not in st.session_state:
    st.session_state["enhanced_features_enabled"] = True

# Sidebar configuration
with st.sidebar:
    st.markdown("""
    <div class="sidebar-card">
        <h3 style="margin-top: 0; color: var(--primary-600); display: flex; align-items: center; gap: 12px;">
            ⚙️ Trading Controls
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Date controls
    st.markdown("### 📅 Session Dates")
    today_ct = datetime.now(CT_TZ).date()
    prev_day = st.date_input(
        "Previous Trading Day", 
        value=today_ct - timedelta(days=1),
        help="Day to use for SPX anchor calculation"
    )
    proj_day = st.date_input(
        "Projection Day", 
        value=prev_day + timedelta(days=1),
        help="Day to project RTH session (8:30-14:30 CT)"
    )
    
    st.caption("📊 Anchor uses last ^GSPC bar ≤ 3:00 PM CT on previous session")
    
    # Manual anchor override
    st.markdown("---")
    st.markdown("### ✏️ Manual Anchor")
    use_manual_close = st.checkbox(
        "Override 3:00 PM Close", 
        value=False,
        help="Manually specify anchor close instead of fetching from ^GSPC"
    )
    manual_close_val = st.number_input(
        "Manual Close Value", 
        value=6400.00, 
        step=0.01, 
        format="%.2f",
        disabled=not use_manual_close,
        help="SPX close price to use as anchor"
    )
    
    # Advanced slope controls
    st.markdown("---")
    with st.expander("🔧 Advanced Settings", expanded=False):
        st.markdown("**Fan Slope Configuration**")
        
        enable_slope_override = st.checkbox(
            "Enable Custom Slopes",
            value=("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state),
            help="Override default asymmetric fan slopes"
        )
        
        col_top, col_bottom = st.columns(2)
        with col_top:
            top_slope_input = st.number_input(
                "Top (+/30m)",
                value=float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT)),
                step=0.001,
                format="%.3f",
                help="Points per 30-minute block for top fan line"
            )
        
        with col_bottom:
            bottom_slope_input = st.number_input(
                "Bottom (-/30m)",
                value=float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT)),
                step=0.001,
                format="%.3f",
                help="Points per 30-minute block for bottom fan line"
            )
        
        # Neutrality band
        tol_frac = st.slider(
            "Neutral Band (%)", 
            0, 40, 
            int(st.session_state.get("tol_frac", NEUTRAL_BAND_DEFAULT) * 100), 
            1,
            help="Percentage of fan width for neutral bias zone"
        ) / 100.0
        st.session_state["tol_frac"] = tol_frac
        
        # Slope control buttons
        col_apply, col_reset = st.columns(2)
        with col_apply:
            if st.button("Apply", use_container_width=True, type="primary"):
                if enable_slope_override:
                    st.session_state["top_slope_per_block"] = float(top_slope_input)
                    st.session_state["bottom_slope_per_block"] = float(bottom_slope_input)
                    st.success("Slopes applied")
                else:
                    for key in ("top_slope_per_block", "bottom_slope_per_block"):
                        st.session_state.pop(key, None)
                    st.info("Using defaults")
        
        with col_reset:
            if st.button("Reset", use_container_width=True):
                for key in ("top_slope_per_block", "bottom_slope_per_block"):
                    st.session_state.pop(key, None)
                st.success("Reset to defaults")
    
    # Action buttons
    st.markdown("---")
    st.markdown("### 🚀 Actions")
    
    btn_anchors = st.button(
        "🎯 Refresh SPX Anchors", 
        use_container_width=True, 
        type="primary",
        help="Calculate fan lines and strategy table"
    )
    
    btn_probability = st.button(
        "🧠 Refresh Probability Board", 
        use_container_width=True,
        help="Analyze overnight edge interactions with enhanced scoring"
    )
    
    # Enhanced features toggle
    st.markdown("---")
    enhanced_enabled = st.checkbox(
        "📈 Enhanced Scoring",
        value=st.session_state.get("enhanced_features_enabled", True),
        help="Enable volume context and time-based edge scoring"
    )
    st.session_state["enhanced_features_enabled"] = enhanced_enabled
    
    if enhanced_enabled:
        st.caption("✅ Volume context & session momentum analysis enabled")
    else:
        st.caption("📊 Standard technical analysis only")

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER METRICS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

# Current time and market status
now = datetime.now(CT_TZ)
is_weekday = now.weekday() < 5
market_open = now.replace(hour=8, minute=30, second=0, microsecond=0)
market_close = now.replace(hour=14, minute=30, second=0, microsecond=0)
is_market_open = is_weekday and (market_open <= now <= market_close)

# Current slopes
current_top_slope, current_bottom_slope = current_spx_slopes()
slopes_overridden = ("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state)

# Create metric cards
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.markdown(create_metric_card(
        title="Current Time (CT)",
        value=now.strftime("%H:%M:%S"),
        subtext=now.strftime("%A, %B %d, %Y"),
        icon="🕒",
        card_type="primary"
    ), unsafe_allow_html=True)

with metric_col2:
    market_status = "OPEN" if is_market_open else "CLOSED"
    market_icon = "📈" if is_market_open else "📊"
    market_type = "success" if is_market_open else "neutral"
    
    st.markdown(create_metric_card(
        title="Market Status",
        value=market_status,
        subtext="RTH: 08:30–14:30 CT • Mon–Fri",
        icon=market_icon,
        card_type=market_type
    ), unsafe_allow_html=True)

with metric_col3:
    slopes_text = f"+{current_top_slope:.3f} / -{current_bottom_slope:.3f}"
    slopes_subtext = "Override Active" if slopes_overridden else "Default Asymmetric"
    
    st.markdown(create_metric_card(
        title="Fan Slopes /30m",
        value=slopes_text,
        subtext=slopes_subtext,
        icon="📐",
        card_type="warning" if slopes_overridden else "primary"
    ), unsafe_allow_html=True)

with metric_col4:
    enhanced_text = "ENABLED" if st.session_state.get("enhanced_features_enabled", True) else "STANDARD"
    enhanced_subtext = "Volume + Time Analysis" if enhanced_enabled else "Technical Only"
    
    st.markdown(create_metric_card(
        title="Scoring Mode",
        value=enhanced_text,
        subtext=enhanced_subtext,
        icon="⚡",
        card_type="success" if enhanced_enabled else "neutral"
    ), unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABBED INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

tab_anchors, tab_bc, tab_probability, tab_plan = st.tabs([
    "🎯 SPX Anchors", 
    "📈 BC Forecast", 
    "🧠 Probability Board", 
    "📋 Plan Card"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SPX ANCHORS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_anchors:
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            🎯 SPX Anchors — Fan Lines & Strategy
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Asymmetric fan projection from previous day anchor with entry/exit bias analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if btn_anchors:
        with st.spinner("🔄 Building SPX fan projection and strategy analysis..."):
            # Get anchor data
            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time = fmt_ct(datetime.combine(prev_day, time(15, 0)))
                anchor_label = ""
                is_estimated = False
            else:
                anchor_close, anchor_time, is_estimated = get_spx_anchor_prevday(prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("❌ Could not resolve ^GSPC anchor at ≤ 3:00 PM CT")
                    st.stop()
                anchor_label = " (estimated)" if is_estimated else ""
            
            # Generate fan projection
            fan_df = project_fan_from_close(anchor_close, anchor_time, proj_day)
            
            # Try to get actual SPX data for projection day
            spx_proj_data = fetch_intraday("^GSPC", proj_day, proj_day, "30m")
            spx_rth_data = between_time(spx_proj_data, RTH_START, RTH_END) if not spx_proj_data.empty else pd.DataFrame()
            
            # Build strategy table
            strategy_rows = []
            rth_slots = rth_slots_ct(proj_day)
            
            for slot_dt in rth_slots:
                blocks = count_effective_blocks(anchor_time, slot_dt)
                top_level = anchor_close + current_top_slope * blocks
                bottom_level = anchor_close - current_bottom_slope * blocks
                
                # Check if we have actual price data
                if not spx_rth_data.empty and slot_dt in spx_rth_data.index:
                    actual_price = float(spx_rth_data.loc[slot_dt, "Close"])
                    bias = compute_bias(actual_price, top_level, bottom_level, tol_frac)
                    price_display = round(actual_price, 2)
                    note = "Live Data"
                else:
                    bias = "—"
                    price_display = "—"
                    note = "Fan Only"
                
                # Highlight 8:30
                slot_marker = "⭐ 8:30" if slot_dt.strftime("%H:%M") == "08:30" else ""
                
                strategy_rows.append({
                    "Slot": slot_marker,
                    "Time": slot_dt.strftime("%H:%M"),
                    "Price": price_display,
                    "Bias": bias,
                    "Top": round(top_level, 2),
                    "Bottom": round(bottom_level, 2),
                    "Width": round(top_level - bottom_level, 2),
                    "Note": note
                })
            
            strategy_df = pd.DataFrame(strategy_rows)
            
            # Store in session state
            st.session_state["anchors"] = {
                "fan_df": fan_df,
                "strategy_df": strategy_df,
                "anchor_close": anchor_close,
                "anchor_time": anchor_time,
                "anchor_label": anchor_label,
                "is_estimated": is_estimated,
                "prev_day": prev_day,
                "proj_day": proj_day
            }
    
    # Display results
    if "anchors" in st.session_state:
        anchor_data = st.session_state["anchors"]
        
        # Anchor info banner
        anchor_info_col1, anchor_info_col2 = st.columns([3, 1])
        with anchor_info_col1:
            st.info(f"📍 **Anchor:** {anchor_data['anchor_close']:.2f} at {anchor_data['anchor_time'].strftime('%Y-%m-%d %H:%M CT')}{anchor_data['anchor_label']}")
        with anchor_info_col2:
            if anchor_data.get('is_estimated', False):
                st.warning("⚠️ Estimated")
        
        # Fan projection table
        st.markdown("### 📊 Fan Line Projection")
        st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
        st.dataframe(
            anchor_data["fan_df"][["Time", "Top", "Bottom", "Fan_Width"]], 
            use_container_width=True, 
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Strategy analysis table
        st.markdown("### 📋 Strategy Analysis")
        st.caption("Bias calculated from price position within fan • ⭐ highlights 8:30 AM key decision time")
        st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
        st.dataframe(
            anchor_data["strategy_df"],
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.info("👆 Click **Refresh SPX Anchors** to generate fan projection and strategy analysis")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: BC FORECAST
# ═══════════════════════════════════════════════════════════════════════════════

with tab_bc:
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            📈 BC Forecast — Bounce + Contract Projection
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Two-bounce slope analysis with contract entry/exit line projections
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate overnight session slots
    asia_start = fmt_ct(datetime.combine(prev_day, time(19, 0)))
    europe_end = fmt_ct(datetime.combine(proj_day, time(7, 0)))
    
    session_slots = []
    current_slot = asia_start
    while current_slot <= europe_end:
        session_slots.append(current_slot)
        current_slot += timedelta(minutes=30)
    
    slot_options = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]
    
    # BC Forecast form
    with st.form("bc_forecast_form", clear_on_submit=False):
        st.markdown("#### 🎯 Underlying Bounces (Exactly Two Required)")
        
        bounce_col1, bounce_col2 = st.columns(2)
        with bounce_col1:
            b1_time = st.selectbox("Bounce #1 Time", slot_options, index=0, key="bc_b1")
            b1_price = st.number_input("Bounce #1 SPX Price", value=6500.00, step=0.25, format="%.2f", key="bc_b1_price")
        
        with bounce_col2:
            b2_time = st.selectbox("Bounce #2 Time", slot_options, index=min(6, len(slot_options)-1), key="bc_b2")
            b2_price = st.number_input("Bounce #2 SPX Price", value=6512.00, step=0.25, format="%.2f", key="bc_b2_price")
        
        st.markdown("---")
        st.markdown("#### 📊 Contract A (Required)")
        
        contract_a_col1, contract_a_col2 = st.columns(2)
        with contract_a_col1:
            ca_symbol = st.text_input("Contract A Symbol", value="6525c", key="bc_ca_symbol")
            ca_b1_price = st.number_input("A: Price at Bounce #1", value=10.00, step=0.05, format="%.2f", key="bc_ca_b1")
            ca_b2_price = st.number_input("A: Price at Bounce #2", value=12.50, step=0.05, format="%.2f", key="bc_ca_b2")
        
        with contract_a_col2:
            ca_h1_time = st.selectbox("A: High #1 Time", slot_options, index=min(2, len(slot_options)-1), key="bc_ca_h1_time")
            ca_h1_price = st.number_input("A: High #1 Price", value=14.00, step=0.05, format="%.2f", key="bc_ca_h1")
            ca_h2_time = st.selectbox("A: High #2 Time", slot_options, index=min(8, len(slot_options)-1), key="bc_ca_h2_time")
            ca_h2_price = st.number_input("A: High #2 Price", value=16.00, step=0.05, format="%.2f", key="bc_ca_h2")
        
        st.markdown("---")
        st.markdown("#### 📈 Contract B (Optional)")
        
        enable_contract_b = st.checkbox("Enable Contract B", value=False, key="bc_enable_b")
        
        if enable_contract_b:
            contract_b_col1, contract_b_col2 = st.columns(2)
            with contract_b_col1:
                cb_symbol = st.text_input("Contract B Symbol", value="6515c", key="bc_cb_symbol")
                cb_b1_price = st.number_input("B: Price at Bounce #1", value=9.50, step=0.05, format="%.2f", key="bc_cb_b1")
                cb_b2_price = st.number_input("B: Price at Bounce #2", value=11.80, step=0.05, format="%.2f", key="bc_cb_b2")
            
            with contract_b_col2:
                cb_h1_time = st.selectbox("B: High #1 Time", slot_options, index=min(3, len(slot_options)-1), key="bc_cb_h1_time")
                cb_h1_price = st.number_input("B: High #1 Price", value=13.30, step=0.05, format="%.2f", key="bc_cb_h1")
                cb_h2_time = st.selectbox("B: High #2 Time", slot_options, index=min(9, len(slot_options)-1), key="bc_cb_h2_time")
                cb_h2_price = st.number_input("B: High #2 Price", value=15.10, step=0.05, format="%.2f", key="bc_cb_h2")
        
        # Submit button
        submit_forecast = st.form_submit_button("🚀 Generate NY Session Projection", type="primary", use_container_width=True)
    
    # Process BC Forecast
    if submit_forecast:
        try:
            # Parse bounce times
            b1_dt = fmt_ct(datetime.strptime(st.session_state["bc_b1"], "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(st.session_state["bc_b2"], "%Y-%m-%d %H:%M"))
            
            if b2_dt <= b1_dt:
                st.error("❌ Bounce #2 must occur after Bounce #1")
            else:
                # Calculate underlying slope
                underlying_blocks = count_effective_blocks(b1_dt, b2_dt)
                underlying_slope = (st.session_state["bc_b2_price"] - st.session_state["bc_b1_price"]) / underlying_blocks if underlying_blocks > 0 else 0.0
                
                # Generate SPX projection
                spx_projection = []
                for rth_slot in rth_slots_ct(proj_day):
                    blocks_from_b1 = count_effective_blocks(b1_dt, rth_slot)
                    projected_spx = st.session_state["bc_b1_price"] + underlying_slope * blocks_from_b1
                    
                    slot_marker = "⭐ 8:30" if rth_slot.strftime("%H:%M") == "08:30" else ""
                    spx_projection.append({
                        "Slot": slot_marker,
                        "Time": rth_slot.strftime("%H:%M"),
                        "SPX_Projected": round(projected_spx, 2)
                    })
                
                projection_df = pd.DataFrame(spx_projection)
                
                # Contract A projections
                ca_entry_df, ca_entry_slope = project_line(b1_dt, st.session_state["bc_ca_b1"], b2_dt, st.session_state["bc_ca_b2"], proj_day, f"{st.session_state['bc_ca_symbol']}_Entry")
                
                ca_h1_dt = fmt_ct(datetime.strptime(st.session_state["bc_ca_h1_time"], "%Y-%m-%d %H:%M"))
                ca_h2_dt = fmt_ct(datetime.strptime(st.session_state["bc_ca_h2_time"], "%Y-%m-%d %H:%M"))
                ca_exit_df, ca_exit_slope = project_line(ca_h1_dt, st.session_state["bc_ca_h1"], ca_h2_dt, st.session_state["bc_ca_h2"], proj_day, f"{st.session_state['bc_ca_symbol']}_Exit")
                
                # Merge contract A data
                projection_df = projection_df.merge(ca_entry_df, on="Time", how="left")
                projection_df = projection_df.merge(ca_exit_df, on="Time", how="left")
                projection_df[f"{st.session_state['bc_ca_symbol']}_Spread"] = projection_df[f"{st.session_state['bc_ca_symbol']}_Exit"] - projection_df[f"{st.session_state['bc_ca_symbol']}_Entry"]
                
                # Contract B (if enabled)
                cb_entry_slope = cb_exit_slope = 0.0
                cb_expected_exit = "n/a"
                
                if enable_contract_b:
                    cb_entry_df, cb_entry_slope = project_line(b1_dt, st.session_state["bc_cb_b1"], b2_dt, st.session_state["bc_cb_b2"], proj_day, f"{st.session_state['bc_cb_symbol']}_Entry")
                    
                    cb_h1_dt = fmt_ct(datetime.strptime(st.session_state["bc_cb_h1_time"], "%Y-%m-%d %H:%M"))
                    cb_h2_dt = fmt_ct(datetime.strptime(st.session_state["bc_cb_h2_time"], "%Y-%m-%d %H:%M"))
                    cb_exit_df, cb_exit_slope = project_line(cb_h1_dt, st.session_state["bc_cb_h1"], cb_h2_dt, st.session_state["bc_cb_h2"], proj_day, f"{st.session_state['bc_cb_symbol']}_Exit")
                    
                    projection_df = projection_df.merge(cb_entry_df, on="Time", how="left")
                    projection_df = projection_df.merge(cb_exit_df, on="Time", how="left")
                    projection_df[f"{st.session_state['bc_cb_symbol']}_Spread"] = projection_df[f"{st.session_state['bc_cb_symbol']}_Exit"] - projection_df[f"{st.session_state['bc_cb_symbol']}_Entry"]
                    
                    cb_expected_exit = expected_exit_time(b1_dt, cb_h1_dt, b2_dt, cb_h2_dt, proj_day)
                
                # Calculate expected exits
                ca_expected_exit = expected_exit_time(b1_dt, ca_h1_dt, b2_dt, ca_h2_dt, proj_day)
                
                # Display results
                st.success("✅ BC Forecast Generated Successfully")
                
                # Metrics summary
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.markdown(create_metric_card(
                        title="Underlying Slope",
                        value=f"{underlying_slope:+.3f}",
                        subtext="Points per 30m block",
                        icon="📐",
                        card_type="primary"
                    ), unsafe_allow_html=True)
                
                with metric_col2:
                    st.markdown(create_metric_card(
                        title=f"{st.session_state['bc_ca_symbol']} Entry",
                        value=f"{ca_entry_slope:+.3f}",
                        subtext=f"Exit: {ca_exit_slope:+.3f} • Target: {ca_expected_exit}",
                        icon="📈",
                        card_type="success"
                    ), unsafe_allow_html=True)
                
                with metric_col3:
                    if enable_contract_b:
                        st.markdown(create_metric_card(
                            title=f"{st.session_state['bc_cb_symbol']} Entry",
                            value=f"{cb_entry_slope:+.3f}",
                            subtext=f"Exit: {cb_exit_slope:+.3f} • Target: {cb_expected_exit}",
                            icon="📊",
                            card_type="success"
                        ), unsafe_allow_html=True)
                    else:
                        st.markdown(create_metric_card(
                            title="Contract B",
                            value="DISABLED",
                            subtext="Optional second contract",
                            icon="➖",
                            card_type="neutral"
                        ), unsafe_allow_html=True)
                
                with metric_col4:
                    contracts_count = 2 if enable_contract_b else 1
                    st.markdown(create_metric_card(
                        title="Projection Status",
                        value="COMPLETE",
                        subtext=f"{contracts_count} contract(s) analyzed",
                        icon="✅",
                        card_type="success"
                    ), unsafe_allow_html=True)
                
                # Projection table
                st.markdown("### 🎯 NY Session Projection (8:30–14:30 CT)")
                st.caption("Entry lines from bounces • Exit lines from highs • Spread = Exit - Entry")
                st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
                st.dataframe(projection_df, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Store results
                st.session_state["bc_result"] = {
                    "table": projection_df,
                    "underlying_slope": underlying_slope,
                    "ca_symbol": st.session_state['bc_ca_symbol'],
                    "cb_symbol": st.session_state['bc_cb_symbol'] if enable_contract_b else None,
                    "ca_expected": ca_expected_exit,
                    "cb_expected": cb_expected_exit if enable_contract_b else None
                }
                
        except Exception as e:
            st.error(f"❌ BC Forecast Error: {str(e)}")
    
    if "bc_result" not in st.session_state:
        st.info("👆 Configure bounce points and contracts, then click **Generate NY Session Projection**")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: PROBABILITY BOARD
# ═══════════════════════════════════════════════════════════════════════════════

with tab_probability:
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            🧠 Probability Board — Overnight Edge Confidence
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            30m edge interaction analysis with volume context and time-based momentum scoring
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced columns toggle
    show_advanced_columns = st.checkbox(
        "🔍 Show Advanced Scoring Components", 
        value=False,
        help="Display detailed breakdown of volume, time, and technical scoring factors"
    )
    
    if btn_probability:
        with st.spinner("🔄 Analyzing overnight edge interactions and probability factors..."):
            # Get anchor
            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time = fmt_ct(datetime.combine(prev_day, time(15, 0)))
                anchor_label = ""
            else:
                anchor_close, anchor_time, is_estimated = get_spx_anchor_prevday(prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("❌ Could not resolve SPX anchor")
                    st.stop()
                anchor_label = " (estimated)" if is_estimated else ""
            
            # Build probability analysis
            if st.session_state.get("enhanced_features_enabled", True):
                interactions_df, fan_df, es_offset, summary_stats = build_comprehensive_probability_board(
                    prev_day, proj_day, anchor_close, anchor_time, tol_frac
                )
                readiness_score, readiness_class, readiness_indicator = calculate_readiness_score(interactions_df, summary_stats)
            else:
                # Use compatibility version for standard analysis
                interactions_df, fan_df, es_offset = build_probability_board(
                    prev_day, proj_day, anchor_close, anchor_time, tol_frac
                )
                summary_stats = {}
                readiness_score = int(interactions_df["Score"].mean()) if not interactions_df.empty else 0
                readiness_class = "MEDIUM" if readiness_score >= 50 else "LOW"
                readiness_indicator = f"{readiness_class.title()} Confidence"
            
            # Store results
            st.session_state["probability_result"] = {
                "interactions_df": interactions_df,
                "fan_df": fan_df,
                "es_offset": es_offset,
                "summary_stats": summary_stats,
                "anchor_close": anchor_close,
                "anchor_time": anchor_time,
                "anchor_label": anchor_label,
                "readiness_score": readiness_score,
                "readiness_class": readiness_class,
                "readiness_indicator": readiness_indicator
            }
    
    # Display results
    if "probability_result" in st.session_state:
        prob_data = st.session_state["probability_result"]
        interactions_df = prob_data["interactions_df"]
        
        # Summary metrics
        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        
        with summary_col1:
            st.markdown(create_metric_card(
                title="Anchor Close",
                value=f"{prob_data['anchor_close']:.2f}",
                subtext=f"Prev ≤ 3:00 PM CT{prob_data['anchor_label']}",
                icon="📍",
                card_type="primary"
            ), unsafe_allow_html=True)
        
        with summary_col2:
            interaction_count = len(interactions_df)
            st.markdown(create_metric_card(
                title="Interactions",
                value=str(interaction_count),
                subtext="Qualified edge touches",
                icon="🎯",
                card_type="success" if interaction_count > 0 else "neutral"
            ), unsafe_allow_html=True)
        
        with summary_col3:
            st.markdown(create_metric_card(
                title="ES→SPX Offset",
                value=f"{prob_data['es_offset']:+.2f}",
                subtext="Applied for overnight conversion",
                icon="🔄",
                card_type="primary"
            ), unsafe_allow_html=True)
        
        with summary_col4:
            readiness_type = "success" if prob_data['readiness_score'] >= 71 else ("warning" if prob_data['readiness_score'] >= 41 else "danger")
            st.markdown(create_metric_card(
                title="Readiness Score",
                value=str(prob_data['readiness_score']),
                subtext=prob_data['readiness_indicator'],
                icon="🔥" if readiness_type == "success" else ("⚡" if readiness_type == "warning" else "🚫"),
                card_type=readiness_type
            ), unsafe_allow_html=True)
        
        # Interactions table
        st.markdown("### 📊 Overnight Edge Interactions")
        
        if interactions_df.empty:
            st.info("No qualified edge interactions detected for the selected overnight window")
        else:
            # Base columns
            base_columns = ["Time", "Price", "Top", "Bottom", "Bias", "Edge", "Case", "Expectation", "ExpectedDir", "Score", "LiquidityBonus"]
            
            # Enhanced columns (only if enhanced features enabled)
            enhanced_columns = []
            if st.session_state.get("enhanced_features_enabled", True) and show_advanced_columns:
                enhanced_columns = [
                    "Confluence_w", "Structure_w", "Wick_w", "ATR_w", "Compression_w", "Gap_w", "Cluster_w",
                    "VolumeSpike_w", "VolumeTrend_w", "VolumeDistribution_w", "OvernightVolume_w", "VolumeQuality_w",
                    "SessionTransition_w", "TimeSignificance_w", "DirectionalPersistence_w", "TimeDecay_w"
                ]
            elif show_advanced_columns:
                # Standard advanced columns for non-enhanced mode
                enhanced_columns = ["Confluence_w", "Structure_w", "Wick_w", "ATR_w", "Compression_w", "Gap_w", "Cluster_w", "Volume_w"]
            
            display_columns = base_columns + enhanced_columns
            available_columns = [col for col in display_columns if col in interactions_df.columns]
            
            st.caption(f"Showing {len(available_columns)} columns • Enhanced scoring: {'✅' if st.session_state.get('enhanced_features_enabled', True) else '📊 Standard'}")
            st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
            st.dataframe(interactions_df[available_columns], use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Summary insights
            if st.session_state.get("enhanced_features_enabled", True) and prob_data.get("summary_stats"):
                stats = prob_data["summary_stats"]
                st.markdown("### 📈 Analysis Summary")
                
                insight_col1, insight_col2 = st.columns(2)
                with insight_col1:
                    st.write(f"**Session Coverage:** {stats.get('asia_touches', 0)} Asia • {stats.get('london_touches', 0)} London touches")
                    st.write(f"**Average Score:** {stats.get('avg_score', 0):.1f} • **Peak Score:** {stats.get('max_score', 0)}")
                
                with insight_col2:
                    vol_quality = stats.get('volume_quality', 0)
                    st.write(f"**Volume Quality:** {vol_quality:.1f} (overnight distribution)")
                    
                    recommendations = generate_trade_recommendations(interactions_df, prob_data["fan_df"], prob_data["readiness_score"])
                    if recommendations:
                        st.write("**Top Recommendation:**")
                        st.write(f"• {recommendations[0]}")
    
    else:
        st.info("👆 Click **Refresh Probability Board** to analyze overnight edge interactions")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: PLAN CARD
# ═══════════════════════════════════════════════════════════════════════════════

with tab_plan:
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            📋 Plan Card — 8:25 AM Session Prep
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Integrated trading plan combining SPX anchors, probability analysis, and BC projections
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if required data is available
    has_anchors = "anchors" in st.session_state
    has_probability = "probability_result" in st.session_state
    has_bc_forecast = "bc_result" in st.session_state
    
    if not (has_anchors and has_probability):
        st.warning("⚠️ **Missing Required Data**")
        missing_items = []
        if not has_anchors:
            missing_items.append("SPX Anchors")
        if not has_probability:
            missing_items.append("Probability Board")
        
        st.write(f"Please generate: {', '.join(missing_items)}")
        st.info("BC Forecast is optional but recommended for complete trading plan")
    
    else:
        # Get data
        anchor_data = st.session_state["anchors"]
        prob_data = st.session_state["probability_result"]
        bc_data = st.session_state.get("bc_result", None)
        
        # Plan summary metrics
        plan_col1, plan_col2, plan_col3, plan_col4 = st.columns(4)
        
        with plan_col1:
            st.markdown(create_metric_card(
                title="Anchor",
                value=f"{anchor_data['anchor_close']:.2f}",
                subtext=f"From {anchor_data['prev_day']}",
                icon="📍",
                card_type="primary"
            ), unsafe_allow_html=True)
        
        with plan_col2:
            fan_830 = anchor_data['fan_df'][anchor_data['fan_df']['Time'] == '08:30']
            fan_width = float(fan_830['Fan_Width'].iloc[0]) if not fan_830.empty else 0
            st.markdown(create_metric_card(
                title="8:30 Fan Width",
                value=f"{fan_width:.1f}",
                subtext="Points between levels",
                icon="📐",
                card_type="primary"
            ), unsafe_allow_html=True)
        
        with plan_col3:
            st.markdown(create_metric_card(
                title="Readiness",
                value=f"{prob_data['readiness_score']}%",
                subtext=prob_data['readiness_class'],
                icon="🔥",
                card_type="success" if prob_data['readiness_score'] >= 71 else ("warning" if prob_data['readiness_score'] >= 41 else "danger")
            ), unsafe_allow_html=True)
        
        with plan_col4:
            bc_status = "INCLUDED" if bc_data else "MISSING"
            bc_type = "success" if bc_data else "neutral"
            st.markdown(create_metric_card(
                title="BC Forecast",
                value=bc_status,
                subtext="Contract projections",
                icon="📈" if bc_data else "➖",
                card_type=bc_type
            ), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Trading plan sections
        plan_left, plan_right = st.columns(2)
        
        with plan_left:
            st.markdown("### 🎯 Primary Setup")
            
            # 8:30 analysis
            strategy_830 = anchor_data['strategy_df'][anchor_data['strategy_df']['Time'] == '08:30']
            if not strategy_830.empty:
                setup_info = strategy_830.iloc[0]
                st.write(f"**8:30 AM Analysis:**")
                st.write(f"• **Price:** {setup_info['Price']}")
                st.write(f"• **Bias:** {create_status_badge(setup_info['Bias'], 'up' if setup_info['Bias'] == 'UP' else ('down' if setup_info['Bias'] == 'DOWN' else 'neutral'))}", unsafe_allow_html=True)
                st.write(f"• **Fan Levels:** Top {setup_info['Top']:.2f} / Bottom {setup_info['Bottom']:.2f}")
                st.write(f"• **Status:** {setup_info['Note']}")
            else:
                st.write("8:30 AM data not available in strategy table")
            
            st.markdown("### 🧠 Probability Insights")
            interactions_df = prob_data['interactions_df']
            if not interactions_df.empty:
                top_interactions = interactions_df.nlargest(3, 'Score')
                for i, (_, interaction) in enumerate(top_interactions.iterrows()):
                    if i < 3:  # Show top 3
                        score_badge = "success" if interaction['Score'] >= 70 else ("warning" if interaction['Score'] >= 50 else "neutral")
                        st.write(f"**{interaction['Time']}:** {interaction['Edge']} → {interaction['Expectation']}")
                        st.write(f"  Score: {create_status_badge(str(interaction['Score']), score_badge)} (+{interaction['LiquidityBonus']} liquidity)", unsafe_allow_html=True)
            else:
                st.write("No scored overnight interactions detected")
        
        with plan_right:
            st.markdown("### 💼 Trade Execution Plan")
            
            if bc_data:
                # BC Forecast integration
                bc_table = bc_data['table']
                bc_830 = bc_table[bc_table['Time'] == '08:30']
                
                if not bc_830.empty:
                    bc_row = bc_830.iloc[0]
                    st.write(f"**Projected at 8:30 AM:**")
                    st.write(f"• **SPX:** {bc_row['SPX_Projected']:.2f}")
                    
                    ca_symbol = bc_data['ca_symbol']
                    if f"{ca_symbol}_Entry" in bc_row:
                        st.write(f"• **{ca_symbol} Entry:** {bc_row[f'{ca_symbol}_Entry']:.2f}")
                    if f"{ca_symbol}_Exit" in bc_row:
                        st.write(f"• **{ca_symbol} Exit Target:** {bc_row[f'{ca_symbol}_Exit']:.2f}")
                    
                    if bc_data['cb_symbol']:
                        cb_symbol = bc_data['cb_symbol']
                        if f"{cb_symbol}_Entry" in bc_row:
                            st.write(f"• **{cb_symbol} Entry:** {bc_row[f'{cb_symbol}_Entry']:.2f}")
                
                # Expected exits
                if bc_data['ca_expected'] != "n/a":
                    st.write(f"**Expected Exits:**")
                    st.write(f"• **{bc_data['ca_symbol']}:** ~{bc_data['ca_expected']}")
                    if bc_data['cb_symbol'] and bc_data['cb_expected'] != "n/a":
                        st.write(f"• **{bc_data['cb_symbol']}:** ~{bc_data['cb_expected']}")
            
            else:
                st.write("**Contract Analysis:** Not available")
                st.write("Generate BC Forecast for entry/exit projections")
            
            st.markdown("### 📊 Risk Management")
            
            # Position sizing based on readiness
            readiness = prob_data['readiness_score']
            if readiness >= 71:
                sizing = "Standard position sizing recommended"
                risk_color = "success"
            elif readiness >= 41:
                sizing = "Reduced position sizing suggested"
                risk_color = "warning"
            else:
                sizing = "Minimal sizing or skip session"
                risk_color = "danger"
            
            st.write(f"**Sizing Guidance:** {create_status_badge(sizing, risk_color)}", unsafe_allow_html=True)
            
            # Key invalidation levels
            st.write(f"**Key Levels:**")
            if not strategy_830.empty:
                st.write(f"• **Bias fails if:** Price moves decisively outside fan")
                st.write(f"• **Fan width:** {setup_info['Width']:.1f} points")

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER & DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

footer_col1, footer_col2 = st.columns([1, 2])

with footer_col1:
    if st.button("🔌 Test Data Connection", help="Verify yfinance data access"):
        test_date = today_ct - timedelta(days=2)
        test_data = fetch_intraday("^GSPC", test_date, test_date, "30m")
        
        if not test_data.empty:
            st.success(f"✅ Connection OK • {len(test_data)} bars received")
        else:
            st.error("❌ No data received • Check date/symbol")

with footer_col2:
    st.caption("""
    **SPX Prophet** • Enterprise Trading Analytics • SPX-Only Anchor System • 
    Asymmetric Fan Projection • Volume Context Analysis • Session Momentum Scoring • 
    30m Block Logic • ⭐ 8:30 AM Focus
    """)

# Performance metrics (if enabled)
if st.session_state.get("show_debug_info", False):
    with st.expander("🔧 Debug Information", expanded=False):
        st.json({
            "session_state_keys": list(st.session_state.keys()),
            "current_slopes": current_spx_slopes(),
            "enhanced_features": st.session_state.get("enhanced_features_enabled", True),
            "timezone": str(CT_TZ),
            "dates": {"prev_day": str(prev_day), "proj_day": str(proj_day)}
        })
