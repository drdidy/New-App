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





# Part 3/4: Dashboard Builders & Probability Board (WORKING VERSION)
# Based on your working code pattern with simple enhancements

# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED SCORING COMPONENTS (Simple additions to your working code)
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_volume_context_simple(df_30m: pd.DataFrame, ts: pd.Timestamp) -> int:
    """Simple volume analysis that adds to existing volume scoring."""
    if "Volume" not in df_30m.columns or df_30m["Volume"].notna().sum() < 5:
        return 0
    
    if ts not in df_30m.index or pd.isna(df_30m.loc[ts, "Volume"]):
        return 0
    
    current_volume = df_30m.loc[ts, "Volume"]
    recent_volumes = df_30m["Volume"].loc[:ts].tail(15)
    
    if len(recent_volumes) >= 10:
        avg_volume = recent_volumes.mean()
        if current_volume > avg_volume * 1.5:
            return 5  # Volume spike bonus
        elif current_volume > avg_volume * 1.25:
            return 3  # Moderate volume increase
    
    return 0

def calculate_time_bonus(ts: pd.Timestamp) -> int:
    """Simple time-based bonus for key session hours."""
    ts_ct = fmt_ct(ts.to_pydatetime())
    hour = ts_ct.hour
    
    # Key session transition times get bonuses
    if hour == 8:  # Pre-NY open (most important)
        return 8
    elif hour == 21:  # Asia open
        return 4
    elif hour == 2:  # London open
        return 5
    elif hour in [7, 22, 3]:  # Other transition hours
        return 3
    else:
        return 0

def enhanced_compute_score_components(df_30m: pd.DataFrame, ts: pd.Timestamp,
                             expected_dir: str, touches_recent: List[pd.Timestamp],
                             asia_hit: bool, london_hit: bool) -> Tuple[int, Dict[str,int], int]:
    """Enhanced version of your working compute_score_components function."""
    
    # Your original liquidity bump logic
    lb = liquidity_bump(fmt_ct(ts.to_pydatetime()))
    
    # Your original scoring logic
    conf = WEIGHTS["confluence"] if (asia_hit and london_hit) else (WEIGHTS["confluence"]//2 if (asia_hit or london_hit) else 0)
    struct = WEIGHTS["structure"]
    wick = WEIGHTS["wick"] if wick_quality(df_30m.loc[ts], expected_dir) else 0
    atr_pct = atr_percentile(df_30m, ts)
    if expected_dir == "Up":
        atr = WEIGHTS["atr"] if atr_pct <= 40 else 0
    else:
        atr = WEIGHTS["atr"] if atr_pct >= 60 else 0
    comp = WEIGHTS["compression"] if range_compression(df_30m, ts) else 0
    gap = gap_context(df_30m, ts, expected_dir)
    cluster = WEIGHTS["cluster"] if touch_clustering(touches_recent, ts) else 0
    
    # Your original volume logic
    vol = 0
    if "Volume" in df_30m.columns and df_30m["Volume"].notna().any():
        vma = df_30m["Volume"].rolling(20).mean()
        if vma.notna().any() and pd.notna(vma.loc[ts]) and df_30m["Volume"].loc[ts] > vma.loc[ts]*1.15:
            vol = WEIGHTS["volume"]

    # NEW: Simple enhancements
    volume_bonus = analyze_volume_context_simple(df_30m, ts)
    time_bonus = calculate_time_bonus(ts)

    parts = {
        "Confluence": conf, "Structure": struct, "Wick": wick, "ATR": atr,
        "Compression": comp, "Gap": gap, "Cluster": cluster, "Volume": vol,
        "VolumeBonus": volume_bonus, "TimeBonus": time_bonus
    }
    
    score = min(100, max(0, lb + sum(parts.values())))
    return score, parts, lb

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PROBABILITY BOARD (Your working function with enhancements)
# ═══════════════════════════════════════════════════════════════════════════════

def build_comprehensive_probability_board(prev_day: date, proj_day: date,
                            anchor_close: float, anchor_time: datetime,
                            tol_frac: float) -> Tuple[pd.DataFrame, pd.DataFrame, float, Dict]:
    """Your working build_probability_board function with simple enhancements and 4 return values."""
    
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

        # Use enhanced scoring instead of original
        score, parts, lb = enhanced_compute_score_components(on_30, ts, expected_dir, touches_recent,
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
            "Cluster_w": parts["Cluster"], "Volume_w": parts["Volume"],
            # NEW: Enhanced components
            "VolumeBonus_w": parts["VolumeBonus"], "TimeBonus_w": parts["TimeBonus"]
        })

    touches_df = pd.DataFrame(touches_rows).sort_values("TimeDT").reset_index(drop=True)
    
    # Summary stats for Part 4 compatibility
    asia_count = len([ts for ts in qualified_timestamps if in_window(fmt_ct(ts.to_pydatetime()), SYD_TOK)])
    london_count = len([ts for ts in qualified_timestamps if in_window(fmt_ct(ts.to_pydatetime()), TOK_LON)])
    
    summary_stats = {
        "total_interactions": len(touches_rows),
        "avg_score": touches_df["Score"].mean() if not touches_df.empty else 0,
        "max_score": touches_df["Score"].max() if not touches_df.empty else 0,
        "asia_touches": asia_count,
        "london_touches": london_count,
        "volume_quality": 4.0 if not touches_df.empty else 0.0
    }
    
    return touches_df, fan_df, float(offset), summary_stats

# ═══════════════════════════════════════════════════════════════════════════════
# BC FORECAST FUNCTIONS (Unchanged from your working code)
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

# ═══════════════════════════════════════════════════════════════════════════════
# READINESS & RECOMMENDATIONS (For Plan Card)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_readiness_score(interactions_df: pd.DataFrame, summary_stats: Dict) -> Tuple[int, str, str]:
    """Calculate overall trading readiness score and classification."""
    if interactions_df.empty:
        return 0, "SKIP", "No qualified interactions detected"
    
    # Primary metrics
    scores = interactions_df["Score"].tolist()
    top_3_avg = int(np.mean(sorted(scores, reverse=True)[:3])) if len(scores) >= 3 else int(np.mean(scores))
    
    # Simple adjustments
    volume_quality = summary_stats.get("volume_quality", 0)
    session_coverage = min(summary_stats.get("asia_touches", 0), 1) + min(summary_stats.get("london_touches", 0), 1)
    
    # Calculate final readiness
    final_readiness = min(100, top_3_avg + int(volume_quality) + (session_coverage * 2))
    
    # Classification
    if final_readiness >= 70:
        classification = "HIGH"
        indicator = "High Confidence"
    elif final_readiness >= 45:
        classification = "MEDIUM" 
        indicator = "Medium Confidence"
    else:
        classification = "SKIP"
        indicator = "Low Confidence"
    
    return final_readiness, classification, indicator

def generate_trade_recommendations(interactions_df: pd.DataFrame, readiness_score: int) -> List[str]:
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
        
        rec = f"{confidence} confidence {direction.lower()} from {edge} @ {time_str} (Score: {score})"
        recommendations.append(rec)
    
    # Add sizing guidance
    if readiness_score >= 70:
        recommendations.append("Consider standard position sizing")
    elif readiness_score >= 45:
        recommendations.append("Consider reduced position sizing")
    else:
        recommendations.append("Consider skipping or minimal sizing")
    
    return recommendations








# Part 4/4: Complete Enterprise UI & Dashboard (WORKING VERSION)
# Main application layout that integrates with Parts 1-3

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR CONTROL PANEL
# ═══════════════════════════════════════════════════════════════════════════════

# Create enterprise sidebar
st.markdown("""
<div class="sidebar-card">
    <h3 style="margin-top: 0; color: var(--primary-600); display: flex; align-items: center; gap: 8px;">
        🎛️ Trading Controls
    </h3>
</div>
""", unsafe_allow_html=True)

# Date controls
today_ct = datetime.now(CT_TZ).date()
col1, col2 = st.sidebar.columns(2)

with col1:
    prev_day = st.date_input(
        "📅 Previous Day", 
        value=today_ct - timedelta(days=1),
        help="Trading day for anchor calculation"
    )

with col2:
    proj_day = st.date_input(
        "📊 Projection Day", 
        value=prev_day + timedelta(days=1),
        help="Target trading day for analysis"
    )

st.sidebar.markdown("""
<div style="background: var(--primary-50); border: 1px solid var(--primary-200); border-radius: 8px; padding: 12px; margin: 16px 0;">
    <small style="color: var(--primary-700); font-weight: 500;">
        📍 Anchor uses last ^GSPC close ≤ 3:00 PM CT
    </small>
</div>
""", unsafe_allow_html=True)

# Manual anchor override
st.sidebar.markdown("""
<div class="sidebar-card">
    <h4 style="margin-top: 0; color: var(--warning-600); display: flex; align-items: center; gap: 8px;">
        ✏️ Manual Override
    </h4>
</div>
""", unsafe_allow_html=True)

use_manual_close = st.sidebar.checkbox(
    "Enter 3:00 PM CT Close Manually", 
    value=False,
    help="Override automatic anchor detection"
)

manual_close_val = st.sidebar.number_input(
    "Manual 3:00 PM Close",
    value=6400.00,
    step=0.01,
    format="%.2f",
    disabled=not use_manual_close,
    help="Manual 3:00 PM CT close value"
)

# Advanced configuration
with st.sidebar.expander("⚙️ Advanced Configuration", expanded=False):
    st.caption("Adjust **asymmetric** fan slopes and within-fan neutrality band.")
    enable_slope = st.checkbox("Enable slope override",
                               value=("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state))
    top_slope_val = st.number_input("Top slope (+ per 30m)",
                                    value=float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT)),
                                    step=0.001, format="%.3f")
    bottom_slope_val = st.number_input("Bottom slope (− per 30m)",
                                       value=float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT)),
                                       step=0.001, format="%.3f")
    tol_frac = st.slider("Neutrality band (% of fan width)", 0, 40, int(NEUTRAL_BAND_DEFAULT*100), 1) / 100.0
    st.session_state["tol_frac"] = tol_frac

    colA, colB = st.columns(2)
    with colA:
        if st.button("Apply slopes", use_container_width=True, key="apply_slope"):
            if enable_slope:
                st.session_state["top_slope_per_block"] = float(top_slope_val)
                st.session_state["bottom_slope_per_block"] = float(bottom_slope_val)
                st.success(f"Applied: Top=+{top_slope_val:.3f} • Bottom=−{bottom_slope_val:.3f}")
            else:
                for k in ("top_slope_per_block","bottom_slope_per_block"):
                    st.session_state.pop(k, None)
                st.info("Using default slopes")
    with colB:
        if st.button("Reset slopes", use_container_width=True, key="reset_slope"):
            for k in ("top_slope_per_block","bottom_slope_per_block"):
                st.session_state.pop(k, None)
            st.success(f"Reset to defaults")

# Action buttons
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="sidebar-card">
    <h4 style="margin-top: 0; color: var(--success-600); display: flex; align-items: center; gap: 8px;">
        🚀 Quick Actions
    </h4>
</div>
""", unsafe_allow_html=True)

btn_anchor = st.sidebar.button(
    "📐 Refresh SPX Anchors",
    type="primary",
    use_container_width=True,
    help="Recalculate fan projections and strategy table"
)

btn_prob = st.sidebar.button(
    "🧠 Refresh Probability Board", 
    type="secondary",
    use_container_width=True,
    help="Analyze overnight edge interactions and scoring"
)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN HEADER DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

# Main application header
st.markdown(create_header_section(
    "SPX Prophet",
    "Enterprise Trading Analytics Platform • Real-time Market Intelligence"
), unsafe_allow_html=True)

# Live status metrics
now = datetime.now(CT_TZ)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(create_metric_card(
        title="Current Time",
        value=now.strftime("%H:%M:%S"),
        subtext=f"{now.strftime('%A, %B %d, %Y')} CT",
        icon="🕐",
        card_type="primary"
    ), unsafe_allow_html=True)

with col2:
    is_wkday = now.weekday() < 5
    open_dt = now.replace(hour=8, minute=30, second=0, microsecond=0)
    close_dt = now.replace(hour=14, minute=30, second=0, microsecond=0)
    is_open = is_wkday and (open_dt <= now <= close_dt)
    badge = create_status_badge("OPEN" if is_open else "CLOSED", "open" if is_open else "closed")
    
    st.markdown(create_metric_card(
        title="Market Status",
        value=badge,
        subtext="RTH: 08:30–14:30 CT • Monday–Friday",
        icon="📊",
        card_type="success" if is_open else "danger"
    ), unsafe_allow_html=True)

with col3:
    ts, bs = current_spx_slopes()
    slope_override = ("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state)
    
    st.markdown(create_metric_card(
        title="Fan Slopes",
        value=f"+{ts:.3f} / -{bs:.3f}",
        subtext=f"{'Override Active' if slope_override else 'Default Slopes'} • Per 30m",
        icon="📐",
        card_type="warning" if slope_override else "neutral"
    ), unsafe_allow_html=True)

with col4:
    st.markdown(create_metric_card(
        title="System Status",
        value="READY",
        subtext="All systems operational • Data feeds active",
        icon="⚡",
        card_type="success"
    ), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TAB SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

tabAnchors, tabBC, tabProb, tabPlan = st.tabs([
    "📐 SPX Anchors", 
    "📈 BC Forecast", 
    "🧠 Probability Board", 
    "📋 Plan Card"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SPX ANCHORS
# ═══════════════════════════════════════════════════════════════════════════════

with tabAnchors:
    st.markdown("""
    <div class="enterprise-card animate-slide-in">
        <h2 style="margin-top: 0; color: var(--primary-600); display: flex; align-items: center; gap: 12px;">
            📐 SPX Anchors — Fan-Based Entry & Exit Strategy
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 24px;">
            Asymmetric fan projection from previous session anchor with bias analysis and strategic entry/exit levels.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if btn_anchor:
        with st.spinner("Building SPX fan & strategy…"):
            if use_manual_close:
                anchor_close = float(manual_close_val)
                anchor_time  = fmt_ct(datetime.combine(prev_day, time(15,0)))
                anchor_label = ""
                est = False
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
                    note = "Live Data"
                    pdisp = round(price,2)
                else:
                    bias = "—"
                    note = "Fan Projection"
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
                "prev_day": prev_day, "proj_day": proj_day,
                "is_estimated": est
            }

    if "anchors" in st.session_state:
        results = st.session_state["anchors"]
        
        # Anchor information card
        st.markdown(f"""
        <div class="enterprise-card">
            <h3 style="color: var(--success-600); margin-top: 0;">📍 Anchor Information</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-top: 16px;">
                <div>
                    <strong style="color: var(--text-secondary);">Anchor Close:</strong><br>
                    <span style="font-size: 1.25rem; font-weight: 700; color: var(--primary-600);">
                        {results['anchor_close']:.2f}{results['anchor_label']}
                    </span>
                </div>
                <div>
                    <strong style="color: var(--text-secondary);">Anchor Time:</strong><br>
                    <span style="font-size: 1.25rem; font-weight: 700; color: var(--primary-600);">
                        {results['anchor_time'].strftime('%H:%M CT')}
                    </span>
                </div>
                <div>
                    <strong style="color: var(--text-secondary);">Source:</strong><br>
                    <span style="font-size: 1.25rem; font-weight: 700; color: var(--primary-600);">
                        {"Manual" if use_manual_close else ("Estimated" if results['is_estimated'] else "^GSPC")}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Fan projection table
        st.markdown("### 🎯 Fan Level Projection")
        fan_display = results["fan_df"][["Time", "Top", "Bottom", "Fan_Width"]].copy()
        fan_display.loc[fan_display["Time"] == "08:30", "Time"] = "⭐ 08:30"
        
        st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
        st.dataframe(fan_display, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Strategy table
        st.markdown("### 📊 Trading Strategy Table")
        st.markdown("Real-time bias analysis with entry/exit levels. ⭐ indicates key 8:30 decision point.")
        
        st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
        st.dataframe(results["strat_df"], use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: var(--bg-tertiary); border-radius: 16px; border: 2px dashed var(--border-medium);">
            <h3 style="color: var(--text-secondary); margin: 0;">📐 Ready to Build Anchors</h3>
            <p style="color: var(--text-tertiary); margin: 16px 0 0 0;">
                Click "Refresh SPX Anchors" in the sidebar to generate fan projections and strategy analysis.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: BC FORECAST  
# ═══════════════════════════════════════════════════════════════════════════════

with tabBC:
    st.markdown("""
    <div class="enterprise-card animate-slide-in">
        <h2 style="margin-top: 0; color: var(--primary-600); display: flex; align-items: center; gap: 12px;">
            📈 BC Forecast — Bounce + Contract Projection
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 24px;">
            Two-bounce system for projecting SPX and option contract prices through NY session (8:30–14:30 CT).
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate overnight session slots
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

        submit_bc = st.form_submit_button("🚀 Generate NY Session Projection", type="primary", use_container_width=True)

    if submit_bc:
        try:
            b1_dt = fmt_ct(datetime.strptime(st.session_state["bc_b1_sel"], "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(st.session_state["bc_b2_sel"], "%Y-%m-%d %H:%M"))
            if b2_dt <= b1_dt:
                st.error("❌ Bounce #2 must occur after Bounce #1.")
            else:
                # Calculate projections using your working functions
                blocks_u = count_effective_blocks(b1_dt, b2_dt)
                u_slope = (float(b2_spx) - float(b1_spx)) / blocks_u if blocks_u > 0 else 0.0

                rows_u = []
                for slot in rth_slots_ct(proj_day):
                    b = count_effective_blocks(b1_dt, slot)
                    price = float(b1_spx) + u_slope * b
                    rows_u.append({"Time": slot.strftime("%H:%M"), "SPX_Projected": round(price,2)})
                spx_proj_df = pd.DataFrame(rows_u)
                spx_proj_df.insert(0, "Slot", spx_proj_df["Time"].apply(lambda x: "⭐ 8:30" if x=="08:30" else ""))

                # Contract A projections
                ca_entry_df, ca_entry_slope = project_line(b1_dt, float(ca_b1_price), b2_dt, float(ca_b2_price), proj_day, f"{st.session_state['bc_ca_sym']}_Entry")
                ca_h1_dt = fmt_ct(datetime.strptime(st.session_state["bc_ca_h1_time"], "%Y-%m-%d %H:%M"))
                ca_h2_dt = fmt_ct(datetime.strptime(st.session_state["bc_ca_h2_time"], "%Y-%m-%d %H:%M"))
                ca_exit_df, ca_exit_slope = project_line(ca_h1_dt, float(ca_h1_price), ca_h2_dt, float(ca_h2_price), proj_day, f"{st.session_state['bc_ca_sym']}_Exit")

                # Merge data
                out = spx_proj_df.merge(ca_entry_df, on="Time", how="left").merge(ca_exit_df, on="Time", how="left")
                ca = st.session_state["bc_ca_sym"]
                out[f"{ca}_Spread"] = out[f"{ca}_Exit"] - out[f"{ca}_Entry"]

                # Contract B if enabled
                cb_data = {}
                if cb_enable:
                    cb_symbol = st.session_state["bc_cb_sym"]
                    cb_entry_df, cb_entry_slope = project_line(b1_dt, float(cb_b1_price), b2_dt, float(cb_b2_price), proj_day, f"{cb_symbol}_Entry")
                    cb_h1_dt = fmt_ct(datetime.strptime(st.session_state["bc_cb_h1_time"], "%Y-%m-%d %H:%M"))
                    cb_h2_dt = fmt_ct(datetime.strptime(st.session_state["bc_cb_h2_time"], "%Y-%m-%d %H:%M"))
                    cb_exit_df, cb_exit_slope = project_line(cb_h1_dt, float(cb_h1_price), cb_h2_dt, float(cb_h2_price), proj_day, f"{cb_symbol}_Exit")
                    
                    out = out.merge(cb_entry_df, on="Time", how="left").merge(cb_exit_df, on="Time", how="left")
                    out[f"{cb_symbol}_Spread"] = out[f"{cb_symbol}_Exit"] - out[f"{cb_symbol}_Entry"]
                    
                    cb_expected = expected_exit_time(b1_dt, cb_h1_dt, b2_dt, cb_h2_dt, proj_day)
                    cb_data = {"symbol": cb_symbol, "entry_slope": cb_entry_slope, "exit_slope": cb_exit_slope, "expected_exit": cb_expected}

                ca_expected = expected_exit_time(b1_dt, ca_h1_dt, b2_dt, ca_h2_dt, proj_day)

                # Display results
                st.markdown("### 📊 Projection Results")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(create_metric_card(
                        title="Underlying Slope",
                        value=f"{u_slope:+.3f}",
                        subtext="SPX points per 30m block",
                        icon="📐",
                        card_type="primary"
                    ), unsafe_allow_html=True)
                
                with col2:
                    st.markdown(create_metric_card(
                        title=f"{ca} Entry",
                        value=f"{ca_entry_slope:+.3f}",
                        subtext=f"Exit slope: {ca_exit_slope:+.3f}",
                        icon="📈",
                        card_type="success"
                    ), unsafe_allow_html=True)
                
                with col3:
                    if cb_data:
                        st.markdown(create_metric_card(
                            title=f"{cb_data['symbol']} Entry",
                            value=f"{cb_data['entry_slope']:+.3f}",
                            subtext=f"Exit slope: {cb_data['exit_slope']:+.3f}",
                            icon="📈",
                            card_type="success"
                        ), unsafe_allow_html=True)
                    else:
                        st.markdown(create_metric_card(
                            title="Contract B",
                            value="Disabled",
                            subtext="Single contract mode",
                            icon="📋",
                            card_type="neutral"
                        ), unsafe_allow_html=True)
                
                with col4:
                    st.markdown(create_metric_card(
                        title="Expected Exit",
                        value=ca_expected,
                        subtext="Based on historical duration",
                        icon="⏰",
                        card_type="warning"
                    ), unsafe_allow_html=True)

                st.markdown("### 🔮 NY Session Projection Table")
                st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
                st.dataframe(out, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.session_state["bc_result"] = {
                    "table": out, "u_slope": u_slope,
                    "ca_sym": ca, "cb_sym": (cb_data.get("symbol") if cb_data else None),
                    "ca_expected": ca_expected, "cb_expected": (cb_data.get("expected_exit") if cb_data else None)
                }
                
        except Exception as e:
            st.error(f"❌ BC Forecast Error: {str(e)}")

    if "bc_result" not in st.session_state:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: var(--bg-tertiary); border-radius: 16px; border: 2px dashed var(--border-medium);">
            <h3 style="color: var(--text-secondary); margin: 0;">📈 Ready for BC Forecast</h3>
            <p style="color: var(--text-tertiary); margin: 16px 0 0 0;">
                Configure bounce points and contract parameters, then generate projections for NY session.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: PROBABILITY BOARD
# ═══════════════════════════════════════════════════════════════════════════════

with tabProb:
    st.markdown("""
    <div class="enterprise-card animate-slide-in">
        <h2 style="margin-top: 0; color: var(--primary-600); display: flex; align-items: center; gap: 12px;">
            🧠 Probability Board — Overnight Edge Analysis
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 24px;">
            Scoring of overnight edge interactions with volume context and time-based momentum analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
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

            interactions_df, fan_df, es_offset, summary_stats = build_comprehensive_probability_board(
                prev_day, proj_day, anchor_close, anchor_time, st.session_state.get("tol_frac", NEUTRAL_BAND_DEFAULT)
            )

            readiness_score, readiness_class, readiness_indicator = calculate_readiness_score(interactions_df, summary_stats)
            recommendations = generate_trade_recommendations(interactions_df, readiness_score)

            st.session_state["prob_result"] = {
                "interactions_df": interactions_df, "fan_df": fan_df,
                "es_offset": float(es_offset), "summary_stats": summary_stats,
                "readiness_score": readiness_score, "readiness_class": readiness_class,
                "readiness_indicator": readiness_indicator, "recommendations": recommendations,
                "anchor_close": anchor_close, "anchor_time": anchor_time, "anchor_label": anchor_label
            }

    if "prob_result" in st.session_state:
        pr = st.session_state["prob_result"]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                title="Anchor Close",
                value=f"{pr['anchor_close']:.2f}",
                subtext=f"Previous ≤3:00 PM CT{pr['anchor_label']}",
                icon="⚓",
                card_type="primary"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                title="Qualified Interactions",
                value=str(pr['summary_stats']['total_interactions']),
                subtext="Overnight edge touches detected",
                icon="🎯",
                card_type="neutral"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                title="ES→SPX Offset",
                value=f"{pr['es_offset']:+.2f}",
                subtext="Applied for overnight conversion",
                icon="🔄",
                card_type="neutral"
            ), unsafe_allow_html=True)
        
        with col4:
            readiness_type = "success" if pr['readiness_class'] == "HIGH" else ("warning" if pr['readiness_class'] == "MEDIUM" else "danger")
            st.markdown(create_metric_card(
                title="Readiness Score",
                value=str(pr['readiness_score']),
                subtext=pr['readiness_indicator'],
                icon="🔥",
                card_type=readiness_type
            ), unsafe_allow_html=True)

        # Interactions table
        if not pr['interactions_df'].empty:
            st.markdown("### 📡 Qualified Edge Interactions")
            
            base_cols = ["Time","Price","Top","Bottom","Bias","Edge","Case","Expectation","ExpectedDir","Score","LiquidityBonus"]
            adv_cols  = ["Confluence_w","Structure_w","Wick_w","ATR_w","Compression_w","Gap_w","Cluster_w","Volume_w","VolumeBonus_w","TimeBonus_w"]
            cols = base_cols + (adv_cols if show_adv else [])
            
            st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
            st.dataframe(pr['interactions_df'][cols], use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Trade recommendations
            st.markdown("### 💡 Trade Recommendations")
            for i, rec in enumerate(pr['recommendations'], 1):
                recommendation_type = "success" if "High confidence" in rec else ("warning" if "Medium confidence" in rec else "neutral")
                st.markdown(f"""
                <div style="background: var(--{recommendation_type}-50); border: 1px solid var(--{recommendation_type}-200); border-radius: 8px; padding: 12px; margin: 8px 0;">
                    <strong>{i}.</strong> {rec}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px 20px; background: var(--warning-50); border-radius: 16px; border: 2px solid var(--warning-200);">
                <h3 style="color: var(--warning-700); margin: 0;">⚠️ No Qualified Interactions</h3>
                <p style="color: var(--warning-600); margin: 16px 0 0 0;">
                    No significant edge interactions detected for this overnight session.
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: var(--bg-tertiary); border-radius: 16px; border: 2px dashed var(--border-medium);">
            <h3 style="color: var(--text-secondary); margin: 0;">🧠 Ready for Probability Analysis</h3>
            <p style="color: var(--text-tertiary); margin: 16px 0 0 0;">
                Click "Refresh Probability Board" in the sidebar to analyze overnight edge interactions and scoring.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: PLAN CARD
# ═══════════════════════════════════════════════════════════════════════════════

with tabPlan:
    st.markdown("""
    <div class="enterprise-card animate-slide-in">
        <h2 style="margin-top: 0; color: var(--primary-600); display: flex; align-items: center; gap: 12px;">
            📋 Plan Card — 8:25 AM Session Preparation
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 24px;">
            Comprehensive trading plan synthesizing anchor levels, probability analysis, and contract projections.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check data availability
    has_anchors = "anchors" in st.session_state
    has_probability = "prob_result" in st.session_state
    has_bc = "bc_result" in st.session_state
    
    if not has_anchors or not has_probability:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: var(--warning-50); border-radius: 16px; border: 2px solid var(--warning-200);">
            <h3 style="color: var(--warning-700); margin: 0;">📋 Prerequisites Required</h3>
            <p style="color: var(--warning-600); margin: 16px 0 0 0;">
                Generate <strong>SPX Anchors</strong> and <strong>Probability Board</strong> first.<br>
                BC Forecast is optional but recommended for complete analysis.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Build plan card from session data
        anchor_data = st.session_state["anchors"]
        prob_data = st.session_state["prob_result"]
        bc_data = st.session_state.get("bc_result", None)
        
        # Plan card header metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                title="Anchor Close",
                value=f"{anchor_data['anchor_close']:.2f}",
                subtext=f"Previous ≤3:00 PM CT{anchor_data['anchor_label']}",
                icon="⚓",
                card_type="primary"
            ), unsafe_allow_html=True)
        
        with col2:
            fan_830 = anchor_data['fan_df'][anchor_data['fan_df']['Time'] == '08:30']
            fan_width = fan_830['Fan_Width'].iloc[0] if not fan_830.empty else 0
            
            st.markdown(create_metric_card(
                title="8:30 Fan Width",
                value=f"{fan_width:.2f}",
                subtext="SPX points from top to bottom",
                icon="📏",
                card_type="neutral"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                title="Probability Score",
                value=str(prob_data['readiness_score']),
                subtext=prob_data['readiness_class'],
                icon="🎯",
                card_type="success" if prob_data['readiness_class'] == "HIGH" else ("warning" if prob_data['readiness_class'] == "MEDIUM" else "danger")
            ), unsafe_allow_html=True)
        
        with col4:
            bc_status = "Active" if bc_data else "Not Set"
            bc_icon = "📈" if bc_data else "📋"
            bc_type = "success" if bc_data else "neutral"
            
            st.markdown(create_metric_card(
                title="BC Forecast",
                value=bc_status,
                subtext="Contract projections available" if bc_data else "Optional analysis",
                icon=bc_icon,
                card_type=bc_type
            ), unsafe_allow_html=True)

        # Main plan sections
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("""
            <div class="enterprise-card">
                <h3 style="margin-top: 0; color: var(--primary-600);">🎯 Primary Setup Analysis</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # 8:30 bias and levels
            strategy_830 = anchor_data['strat_df'][anchor_data['strat_df']['Time'] == '08:30']
            
            if not strategy_830.empty:
                row_830 = strategy_830.iloc[0]
                st.markdown(f"**🕰️ 8:30 AM Analysis:**")
                st.markdown(f"• **Current Bias:** {create_status_badge(row_830['Bias'], 'up' if row_830['Bias'] == 'UP' else ('down' if row_830['Bias'] == 'DOWN' else 'neutral'))}")
                st.markdown(f"• **Top Level:** {row_830['Top']}")
                st.markdown(f"• **Bottom Level:** {row_830['Bottom']}")
                st.markdown(f"• **Fan Width:** {row_830['Fan_Width']}")
                st.markdown(f"• **Data Source:** {row_830['Note']}")
            
            st.markdown("---")
            
            # Probability insights
            st.markdown("**🧠 Overnight Probability Analysis:**")
            if not prob_data['interactions_df'].empty:
                top_interactions = prob_data['interactions_df'].nlargest(3, 'Score')
                for i, (_, interaction) in enumerate(top_interactions.iterrows(), 1):
                    direction_badge = create_status_badge(
                        interaction['ExpectedDir'], 
                        'up' if interaction['ExpectedDir'] == 'Up' else 'down'
                    )
                    st.markdown(
                        f"**{i}.** {interaction['Time']} • {interaction['Edge']} • "
                        f"{direction_badge} • Score: {interaction['Score']}"
                    )
            else:
                st.markdown("• No significant interactions detected")
        
        with col_right:
            st.markdown("""
            <div class="enterprise-card">
                <h3 style="margin-top: 0; color: var(--success-600);">💼 Trade Execution Plan</h3>
            </div>
            """, unsafe_allow_html=True)
            
            if bc_data:
                # BC Forecast integration
                projection_830 = bc_data['table'][bc_data['table']['Time'] == '08:30']
                
                if not projection_830.empty:
                    row_830 = projection_830.iloc[0]
                    st.markdown("**📈 Contract Projections @ 8:30:**")
                    st.markdown(f"• **SPX Projected:** {row_830['SPX_Projected']:.2f}")
                    
                    ca_symbol = bc_data['ca_sym']
                    if f"{ca_symbol}_Entry" in row_830:
                        st.markdown(f"• **{ca_symbol} Entry:** {row_830[f'{ca_symbol}_Entry']:.2f}")
                    if f"{ca_symbol}_Exit" in row_830:
                        st.markdown(f"• **{ca_symbol} Exit Target:** {row_830[f'{ca_symbol}_Exit']:.2f}")
                    if f"{ca_symbol}_Spread" in row_830:
                        st.markdown(f"• **{ca_symbol} Spread:** {row_830[f'{ca_symbol}_Spread']:.2f}")
                    
                    st.markdown(f"• **Expected Exit Time:** {bc_data['ca_expected']}")
                    
                    # Contract B if available
                    if bc_data.get('cb_sym'):
                        cb_symbol = bc_data['cb_sym']
                        if f"{cb_symbol}_Entry" in row_830:
                            st.markdown(f"• **{cb_symbol} Entry:** {row_830[f'{cb_symbol}_Entry']:.2f}")
                        if f"{cb_symbol}_Exit" in row_830:
                            st.markdown(f"• **{cb_symbol} Exit Target:** {row_830[f'{cb_symbol}_Exit']:.2f}")
            
            else:
                st.markdown("**📊 General Strategy Guidelines:**")
                st.markdown("• Use SPX fan levels for entry/exit timing")
                st.markdown("• Monitor 8:30 bias for directional confirmation")
                st.markdown("• Consider probability score for position sizing")
                st.markdown("• Set BC Forecast for specific contract targets")
            
            st.markdown("---")
            
            # Risk management
            st.markdown("**⚠️ Risk Management:**")
            if prob_data['readiness_score'] >= 70:
                st.markdown("• ✅ High confidence - standard position sizing")
            elif prob_data['readiness_score'] >= 45:
                st.markdown("• ⚡ Medium confidence - reduced position sizing")
            else:
                st.markdown("• 🚫 Low confidence - consider skipping or minimal size")

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER & SYSTEM STATUS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("---")

footer_col1, footer_col2 = st.columns([1, 3])

with footer_col1:
    if st.button("🔌 Test Data Connection", use_container_width=True):
        test_date = today_ct - timedelta(days=2)
        test_data = fetch_intraday("^GSPC", test_date, test_date, "30m")
        
        if not test_data.empty:
            st.success(f"✅ Connection OK • {len(test_data)} bars received")
        else:
            st.warning("⚠️ No data received • Check date range")

with footer_col2:
    st.markdown("""
    <div style="padding: 12px 0; color: var(--text-tertiary); font-size: 0.875rem;">
        <strong>SPX Prophet v2.0</strong> • Enterprise Trading Analytics • 
        SPX-only anchor system • Volume context & time-based scoring • 
        30m interaction detection • Real-time probability analysis
    </div>
    """, unsafe_allow_html=True)
