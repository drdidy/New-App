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





# Part 3/4: Dashboard Builders, Probability Board & Advanced Scoring Integration
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
# PROBABILITY BOARD BUILDER
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
            
            # Traditional components
            "Confluence": score_breakdown["confluence"],
            "Structure": score_breakdown["structure"], 
            "Wick": score_breakdown["wick"],
            "ATR": score_breakdown["atr"],
            "Compression": score_breakdown["compression"],
            "Gap": score_breakdown["gap"],
            "Cluster": score_breakdown["cluster"],
            
            # NEW: Volume components
            "VolumeSpike": score_breakdown["volume_spike"],
            "VolumeTrend": score_breakdown["volume_trend"],
            "VolumeDistribution": score_breakdown["volume_distribution"],
            "OvernightVolume": score_breakdown["overnight_volume"],
            "VolumeQuality": score_breakdown["volume_dist_quality"],
            
            # NEW: Time-based components
            "SessionTransition": score_breakdown["session_transition"],
            "TimeSignificance": score_breakdown["time_significance"],
            "DirectionalPersistence": score_breakdown["directional_persistence"],
            "TimeDecay": score_breakdown["time_decay"]
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
        return 0, "SKIP", "🚫 No qualified interactions detected"
    
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
        indicator = "🔥 High Confidence"
    elif final_readiness >= 41:
        classification = "MEDIUM" 
        indicator = "⚡ Medium Confidence"
    else:
        classification = "SKIP"
        indicator = "🚫 Low Confidence"
    
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








# Part 4/4: Complete Enterprise Dashboard UI & Interactive Components
# Main application layout with sidebar, tabs, and premium enterprise components

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

use_manual_anchor = st.sidebar.checkbox(
    "Use Manual Anchor Close", 
    value=False,
    help="Override automatic anchor detection"
)

manual_anchor_value = st.sidebar.number_input(
    "Manual Anchor Close",
    value=6400.00,
    step=0.01,
    format="%.2f",
    disabled=not use_manual_anchor,
    help="Manual 3:00 PM CT close value"
)

# Advanced configuration
with st.sidebar.expander("⚙️ Advanced Configuration", expanded=False):
    st.markdown("**Fan Slope Configuration**")
    
    enable_slope_override = st.checkbox(
        "Enable Custom Slopes",
        value=("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state),
        help="Override default asymmetric fan slopes"
    )
    
    col_top, col_bottom = st.columns(2)
    with col_top:
        top_slope_input = st.number_input(
            "Top Slope",
            value=float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT)),
            step=0.001,
            format="%.3f",
            help="Points per 30m block (upward)"
        )
    
    with col_bottom:
        bottom_slope_input = st.number_input(
            "Bottom Slope", 
            value=float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT)),
            step=0.001,
            format="%.3f",
            help="Points per 30m block (downward)"
        )
    
    tolerance_fraction = st.slider(
        "Neutral Zone Width (%)",
        min_value=0,
        max_value=40,
        value=int(NEUTRAL_BAND_DEFAULT * 100),
        step=1,
        help="Percentage of fan width for neutral bias zone"
    ) / 100.0
    
    st.session_state["tolerance_fraction"] = tolerance_fraction
    
    # Slope control buttons
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("💾 Apply", use_container_width=True, key="apply_slopes"):
            if enable_slope_override:
                st.session_state["top_slope_per_block"] = float(top_slope_input)
                st.session_state["bottom_slope_per_block"] = float(bottom_slope_input)
                st.success("Slopes applied!")
            else:
                for key in ("top_slope_per_block", "bottom_slope_per_block"):
                    st.session_state.pop(key, None)
                st.info("Using default slopes")
    
    with btn_col2:
        if st.button("🔄 Reset", use_container_width=True, key="reset_slopes"):
            for key in ("top_slope_per_block", "bottom_slope_per_block"):
                st.session_state.pop(key, None)
            st.success("Reset to defaults!")

# Action buttons
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="sidebar-card">
    <h4 style="margin-top: 0; color: var(--success-600); display: flex; align-items: center; gap: 8px;">
        🚀 Quick Actions
    </h4>
</div>
""", unsafe_allow_html=True)

refresh_anchors = st.sidebar.button(
    "📐 Refresh SPX Anchors",
    type="primary",
    use_container_width=True,
    help="Recalculate fan projections and strategy table"
)

refresh_probability = st.sidebar.button(
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
current_time = datetime.now(CT_TZ)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(create_metric_card(
        title="Current Time",
        value=current_time.strftime("%H:%M:%S"),
        subtext=f"{current_time.strftime('%A, %B %d, %Y')} CT",
        icon="🕐",
        card_type="primary"
    ), unsafe_allow_html=True)

with col2:
    # Market status logic
    is_weekday = current_time.weekday() < 5
    market_open = current_time.replace(hour=8, minute=30, second=0, microsecond=0)
    market_close = current_time.replace(hour=14, minute=30, second=0, microsecond=0)
    is_market_open = is_weekday and (market_open <= current_time <= market_close)
    
    status_text = "OPEN" if is_market_open else "CLOSED"
    status_badge = create_status_badge(status_text, "open" if is_market_open else "closed")
    
    st.markdown(create_metric_card(
        title="Market Status",
        value=status_badge,
        subtext="RTH: 08:30–14:30 CT • Monday–Friday",
        icon="📊",
        card_type="success" if is_market_open else "danger"
    ), unsafe_allow_html=True)

with col3:
    # Current slopes
    current_top, current_bottom = current_spx_slopes()
    slope_override = ("top_slope_per_block" in st.session_state or "bottom_slope_per_block" in st.session_state)
    
    slope_display = f"+{current_top:.3f} / -{current_bottom:.3f}"
    override_indicator = "🔧 Override Active" if slope_override else "📐 Default Slopes"
    
    st.markdown(create_metric_card(
        title="Fan Slopes",
        value=slope_display,
        subtext=f"{override_indicator} • Per 30m Block",
        icon="📐",
        card_type="warning" if slope_override else "neutral"
    ), unsafe_allow_html=True)

with col4:
    # System status
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

tab1, tab2, tab3, tab4 = st.tabs([
    "📐 SPX Anchors", 
    "📈 BC Forecast", 
    "🧠 Probability Board", 
    "📋 Plan Card"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SPX ANCHORS
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
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
    
    if refresh_anchors:
        with st.spinner("🔄 Building SPX anchor analysis..."):
            # Determine anchor source
            if use_manual_anchor:
                anchor_close = float(manual_anchor_value)
                anchor_time = fmt_ct(datetime.combine(prev_day, time(15, 0)))
                anchor_label = ""
                is_estimated = False
            else:
                anchor_close, anchor_time, is_estimated = get_spx_anchor_prevday(prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("❌ Cannot resolve SPX anchor for selected date")
                    st.stop()
                anchor_label = " (estimated)" if is_estimated else ""
            
            # Generate fan projection
            fan_projection = project_fan_from_close(anchor_close, anchor_time, proj_day)
            
            # Fetch current SPX data for strategy table
            current_spx = fetch_intraday("^GSPC", proj_day, proj_day, "30m")
            rth_spx = between_time(current_spx, RTH_START, RTH_END) if not current_spx.empty else pd.DataFrame()
            
            # Build strategy table
            strategy_rows = []
            rth_slots = rth_slots_ct(proj_day)
            
            for time_slot in rth_slots:
                blocks_from_anchor = count_effective_blocks(anchor_time, time_slot)
                top_level = anchor_close + current_top * blocks_from_anchor
                bottom_level = anchor_close + current_bottom * blocks_from_anchor
                
                # Check if we have real SPX data for this slot
                if not rth_spx.empty and time_slot in rth_spx.index:
                    current_bar = rth_spx.loc[time_slot]
                    current_price = float(current_bar["Close"])
                    current_bias = compute_bias(current_price, top_level, bottom_level, tolerance_fraction)
                    price_display = f"{current_price:.2f}"
                    data_note = "Live Data"
                else:
                    current_bias = "—"
                    price_display = "—"
                    data_note = "Projection Only"
                
                # Highlight 8:30 AM
                slot_marker = "⭐ 08:30" if time_slot.strftime("%H:%M") == "08:30" else ""
                
                strategy_rows.append({
                    "Highlight": slot_marker,
                    "Time": time_slot.strftime("%H:%M"),
                    "Price": price_display,
                    "Bias": current_bias,
                    "Top": f"{top_level:.2f}",
                    "Bottom": f"{bottom_level:.2f}",
                    "Width": f"{top_level - bottom_level:.2f}",
                    "Note": data_note
                })
            
            strategy_df = pd.DataFrame(strategy_rows)
            
            # Store results
            st.session_state["anchor_results"] = {
                "fan_projection": fan_projection,
                "strategy_table": strategy_df,
                "anchor_close": anchor_close,
                "anchor_time": anchor_time,
                "anchor_label": anchor_label,
                "is_estimated": is_estimated
            }
    
    # Display results
    if "anchor_results" in st.session_state:
        results = st.session_state["anchor_results"]
        
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
                        {"Manual" if use_manual_anchor else ("Estimated" if results['is_estimated'] else "^GSPC")}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Fan projection table
        st.markdown("### 🎯 Fan Level Projection")
        fan_display = results["fan_projection"][["Time", "Top", "Bottom", "Fan_Width"]].copy()
        fan_display.loc[fan_display["Time"] == "08:30", "Time"] = "⭐ 08:30"
        
        st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
        st.dataframe(
            fan_display, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Time": st.column_config.TextColumn("Time", width="small"),
                "Top": st.column_config.NumberColumn("Top Level", format="%.2f"),
                "Bottom": st.column_config.NumberColumn("Bottom Level", format="%.2f"),
                "Fan_Width": st.column_config.NumberColumn("Fan Width", format="%.2f")
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Strategy table
        st.markdown("### 📊 Trading Strategy Table")
        st.markdown("Real-time bias analysis with entry/exit levels. ⭐ indicates key 8:30 decision point.")
        
        st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
        st.dataframe(
            results["strategy_table"],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Highlight": st.column_config.TextColumn("", width="small"),
                "Time": st.column_config.TextColumn("Time", width="small"),
                "Price": st.column_config.TextColumn("SPX Price", width="medium"),
                "Bias": st.column_config.TextColumn("Bias", width="small"),
                "Top": st.column_config.TextColumn("Top", width="small"),
                "Bottom": st.column_config.TextColumn("Bottom", width="small"),
                "Width": st.column_config.TextColumn("Width", width="small"),
                "Note": st.column_config.TextColumn("Data Source", width="medium")
            }
        )
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

with tab2:
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
    
    # Generate overnight session slots for bounce selection
    overnight_start = fmt_ct(datetime.combine(prev_day, time(19, 0)))
    overnight_end = fmt_ct(datetime.combine(proj_day, time(7, 0)))
    
    session_slots = []
    current_slot = overnight_start
    while current_slot <= overnight_end:
        session_slots.append(current_slot)
        current_slot += timedelta(minutes=30)
    
    slot_options = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]
    
    # BC Forecast form
    with st.form("bc_forecast_form", clear_on_submit=False):
        st.markdown("#### 🎯 Underlying Bounce Configuration")
        st.markdown("Define exactly **two bounce points** from overnight session:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Bounce #1**")
            bounce1_time = st.selectbox(
                "Time Slot",
                slot_options,
                index=0,
                key="b1_time",
                help="First bounce timestamp"
            )
            bounce1_price = st.number_input(
                "SPX Price",
                value=6500.00,
                step=0.25,
                format="%.2f",
                key="b1_price",
                help="SPX price at first bounce"
            )
        
        with col2:
            st.markdown("**Bounce #2**")
            bounce2_time = st.selectbox(
                "Time Slot",
                slot_options,
                index=min(6, len(slot_options) - 1),
                key="b2_time",
                help="Second bounce timestamp"
            )
            bounce2_price = st.number_input(
                "SPX Price",
                value=6512.00,
                step=0.25,
                format="%.2f",
                key="b2_price",
                help="SPX price at second bounce"
            )
        
        st.markdown("---")
        st.markdown("#### 📋 Contract A Configuration (Required)")
        
        contract_a_symbol = st.text_input(
            "Contract Symbol",
            value="6525c",
            key="ca_symbol",
            help="Option contract identifier"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Entry Line (from bounces)**")
            ca_bounce1_price = st.number_input(
                "Price at Bounce #1",
                value=10.00,
                step=0.05,
                format="%.2f",
                key="ca_b1_price"
            )
            ca_bounce2_price = st.number_input(
                "Price at Bounce #2",
                value=12.50,
                step=0.05,
                format="%.2f",
                key="ca_b2_price"
            )
        
        with col2:
            st.markdown("**Exit Line (from highs)**")
            ca_high1_time = st.selectbox(
                "High #1 Time",
                slot_options,
                index=min(2, len(slot_options) - 1),
                key="ca_h1_time"
            )
            ca_high1_price = st.number_input(
                "High #1 Price",
                value=14.00,
                step=0.05,
                format="%.2f",
                key="ca_h1_price"
            )
            ca_high2_time = st.selectbox(
                "High #2 Time",
                slot_options,
                index=min(8, len(slot_options) - 1),
                key="ca_h2_time"
            )
            ca_high2_price = st.number_input(
                "High #2 Price",
                value=16.00,
                step=0.05,
                format="%.2f",
                key="ca_h2_price"
            )
        
        st.markdown("---")
        st.markdown("#### 📋 Contract B Configuration (Optional)")
        
        enable_contract_b = st.checkbox(
            "Enable Contract B",
            value=False,
            key="enable_cb",
            help="Add second contract for comparison"
        )
        
        if enable_contract_b:
            contract_b_symbol = st.text_input(
                "Contract B Symbol",
                value="6515c",
                key="cb_symbol"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Entry Line**")
                cb_bounce1_price = st.number_input(
                    "Price at Bounce #1",
                    value=9.50,
                    step=0.05,
                    format="%.2f",
                    key="cb_b1_price"
                )
                cb_bounce2_price = st.number_input(
                    "Price at Bounce #2",
                    value=11.80,
                    step=0.05,
                    format="%.2f",
                    key="cb_b2_price"
                )
            
            with col2:
                st.markdown("**Exit Line**")
                cb_high1_time = st.selectbox(
                    "High #1 Time",
                    slot_options,
                    index=min(3, len(slot_options) - 1),
                    key="cb_h1_time"
                )
                cb_high1_price = st.number_input(
                    "High #1 Price",
                    value=13.30,
                    step=0.05,
                    format="%.2f",
                    key="cb_h1_price"
                )
                cb_high2_time = st.selectbox(
                    "High #2 Time",
                    slot_options,
                    index=min(9, len(slot_options) - 1),
                    key="cb_h2_time"
                )
                cb_high2_price = st.number_input(
                    "High #2 Price",
                    value=15.10,
                    step=0.05,
                    format="%.2f",
                    key="cb_h2_price"
                )
        
        # Submit button
        submit_forecast = st.form_submit_button(
            "🚀 Generate NY Session Projection",
            type="primary",
            use_container_width=True
        )
    
    # Process BC Forecast
    if submit_forecast:
        try:
            # Parse bounce timestamps
            b1_dt = fmt_ct(datetime.strptime(st.session_state["b1_time"], "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(st.session_state["b2_time"], "%Y-%m-%d %H:%M"))
            
            if b2_dt <= b1_dt:
                st.error("❌ Bounce #2 must occur after Bounce #1")
            else:
                # Calculate underlying projection
                underlying_df, underlying_slope = project_contract_line(
                    b1_dt, st.session_state["b1_price"],
                    b2_dt, st.session_state["b2_price"],
                    proj_day, "SPX_Projected"
                )
                
                # Add highlight column
                underlying_df.insert(0, "Highlight", underlying_df["Time"].apply(
                    lambda x: "⭐ 08:30" if x == "08:30" else ""
                ))
                
                # Contract A projections
                ca_entry_df, ca_entry_slope = project_contract_line(
                    b1_dt, st.session_state["ca_b1_price"],
                    b2_dt, st.session_state["ca_b2_price"],
                    proj_day, f"{st.session_state['ca_symbol']}_Entry"
                )
                
                ca_h1_dt = fmt_ct(datetime.strptime(st.session_state["ca_h1_time"], "%Y-%m-%d %H:%M"))
                ca_h2_dt = fmt_ct(datetime.strptime(st.session_state["ca_h2_time"], "%Y-%m-%d %H:%M"))
                
                ca_exit_df, ca_exit_slope = project_contract_line(
                    ca_h1_dt, st.session_state["ca_h1_price"],
                    ca_h2_dt, st.session_state["ca_h2_price"],
                    proj_day, f"{st.session_state['ca_symbol']}_Exit"
                )
                
                # Merge data
                projection_df = underlying_df.merge(ca_entry_df, on="Time").merge(ca_exit_df, on="Time")
                
                # Calculate spreads
                ca_symbol = st.session_state["ca_symbol"]
                projection_df[f"{ca_symbol}_Spread"] = (
                    projection_df[f"{ca_symbol}_Exit"] - projection_df[f"{ca_symbol}_Entry"]
                )
                
                # Expected exit timing
                ca_expected_exit = calculate_expected_exit_timing(b1_dt, ca_h1_dt, b2_dt, ca_h2_dt, proj_day)
                
                # Contract B (if enabled)
                cb_data = {}
                if enable_contract_b:
                    cb_symbol = st.session_state["cb_symbol"]
                    
                    cb_entry_df, cb_entry_slope = project_contract_line(
                        b1_dt, st.session_state["cb_b1_price"],
                        b2_dt, st.session_state["cb_b2_price"],
                        proj_day, f"{cb_symbol}_Entry"
                    )
                    
                    cb_h1_dt = fmt_ct(datetime.strptime(st.session_state["cb_h1_time"], "%Y-%m-%d %H:%M"))
                    cb_h2_dt = fmt_ct(datetime.strptime(st.session_state["cb_h2_time"], "%Y-%m-%d %H:%M"))
                    
                    cb_exit_df, cb_exit_slope = project_contract_line(
                        cb_h1_dt, st.session_state["cb_h1_price"],
                        cb_h2_dt, st.session_state["cb_h2_price"],
                        proj_day, f"{cb_symbol}_Exit"
                    )
                    
                    projection_df = projection_df.merge(cb_entry_df, on="Time").merge(cb_exit_df, on="Time")
                    projection_df[f"{cb_symbol}_Spread"] = (
                        projection_df[f"{cb_symbol}_Exit"] - projection_df[f"{cb_symbol}_Entry"]
                    )
                    
                    cb_expected_exit = calculate_expected_exit_timing(b1_dt, cb_h1_dt, b2_dt, cb_h2_dt, proj_day)
                    
                    cb_data = {
                        "symbol": cb_symbol,
                        "entry_slope": cb_entry_slope,
                        "exit_slope": cb_exit_slope,
                        "expected_exit": cb_expected_exit
                    }
                
                # Display results
                st.markdown("### 📊 Projection Results")
                
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(create_metric_card(
                        title="Underlying Slope",
                        value=f"{underlying_slope:+.3f}",
                        subtext="SPX points per 30m block",
                        icon="📐",
                        card_type="primary"
                    ), unsafe_allow_html=True)
                
                with col2:
                    st.markdown(create_metric_card(
                        title=f"{ca_symbol} Entry",
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
                        value=ca_expected_exit,
                        subtext="Based on historical duration",
                        icon="⏰",
                        card_type="warning"
                    ), unsafe_allow_html=True)
                
                # Projection table
                st.markdown("### 🔮 NY Session Projection Table")
                st.markdown("Complete projection from overnight bounces through RTH session.")
                
                st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
                st.dataframe(
                    projection_df,
                    use_container_width=True,
                    hide_index=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Store results
                st.session_state["bc_results"] = {
                    "projection_table": projection_df,
                    "underlying_slope": underlying_slope,
                    "ca_symbol": ca_symbol,
                    "ca_expected_exit": ca_expected_exit,
                    "cb_data": cb_data if enable_contract_b else None
                }
                
        except Exception as e:
            st.error(f"❌ BC Forecast Error: {str(e)}")
    
    # Show help if no results
    if "bc_results" not in st.session_state:
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

with tab3:
    st.markdown("""
    <div class="enterprise-card animate-slide-in">
        <h2 style="margin-top: 0; color: var(--primary-600); display: flex; align-items: center; gap: 12px;">
            🧠 Probability Board — Overnight Edge Analysis
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 24px;">
            Advanced scoring of overnight edge interactions with volume context and time-based momentum analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Advanced options
    show_advanced_scoring = st.checkbox(
        "🔬 Show Advanced Scoring Components",
        value=False,
        help="Display detailed scoring breakdown for each interaction"
    )
    
    if refresh_probability:
        with st.spinner("🧠 Analyzing overnight probability patterns..."):
            # Get anchor (reuse from anchors if available)
            if use_manual_anchor:
                anchor_close = float(manual_anchor_value)
                anchor_time = fmt_ct(datetime.combine(prev_day, time(15, 0)))
                anchor_label = ""
            else:
                anchor_close, anchor_time, is_estimated = get_spx_anchor_prevday(prev_day)
                if anchor_close is None or anchor_time is None:
                    st.error("❌ Cannot resolve anchor for probability analysis")
                    st.stop()
                anchor_label = " (estimated)" if is_estimated else ""
            
            # Build comprehensive probability board
            interactions_df, fan_projection, es_offset, summary_stats = build_comprehensive_probability_board(
                prev_day, proj_day, anchor_close, anchor_time, tolerance_fraction
            )
            
            # Calculate readiness score
            readiness_score, readiness_class, readiness_indicator = calculate_readiness_score(
                interactions_df, summary_stats
            )
            
            # Generate recommendations
            recommendations = generate_trade_recommendations(
                interactions_df, fan_projection, readiness_score
            )
            
            # Store results
            st.session_state["probability_results"] = {
                "interactions": interactions_df,
                "fan_projection": fan_projection,
                "es_offset": es_offset,
                "summary_stats": summary_stats,
                "readiness_score": readiness_score,
                "readiness_class": readiness_class,
                "readiness_indicator": readiness_indicator,
                "recommendations": recommendations,
                "anchor_close": anchor_close,
                "anchor_time": anchor_time,
                "anchor_label": anchor_label
            }
    
    # Display results
    if "probability_results" in st.session_state:
        results = st.session_state["probability_results"]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                title="Anchor Close",
                value=f"{results['anchor_close']:.2f}",
                subtext=f"Previous ≤3:00 PM CT{results['anchor_label']}",
                icon="⚓",
                card_type="primary"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                title="Qualified Interactions",
                value=str(results['summary_stats']['total_interactions']),
                subtext="Overnight edge touches detected",
                icon="🎯",
                card_type="neutral"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                title="ES→SPX Offset",
                value=f"{results['es_offset']:+.2f}",
                subtext="Applied for overnight conversion",
                icon="🔄",
                card_type="neutral"
            ), unsafe_allow_html=True)
        
        with col4:
            readiness_type = "success" if results['readiness_class'] == "HIGH" else ("warning" if results['readiness_class'] == "MEDIUM" else "danger")
            st.markdown(create_metric_card(
                title="Readiness Score",
                value=str(results['readiness_score']),
                subtext=results['readiness_indicator'],
                icon="🔥",
                card_type=readiness_type
            ), unsafe_allow_html=True)
        
        # Interactions table
        if not results['interactions'].empty:
            st.markdown("### 📡 Qualified Edge Interactions")
            st.markdown("Scored overnight interactions with comprehensive analysis components.")
            
            # Column selection based on advanced view
            base_columns = [
                "Time", "Price", "Top", "Bottom", "Bias", "Edge", "Case", 
                "Expectation", "ExpectedDir", "Score", "LiquidityBonus"
            ]
            
            advanced_columns = [
                "Confluence", "Structure", "Wick", "ATR", "Compression", "Gap", "Cluster",
                "VolumeSpike", "VolumeTrend", "VolumeDistribution", "OvernightVolume",
                "SessionTransition", "TimeSignificance", "DirectionalPersistence", "TimeDecay"
            ]
            
            display_columns = base_columns + (advanced_columns if show_advanced_scoring else [])
            display_data = results['interactions'][display_columns]
            
            st.markdown('<div class="enterprise-table">', unsafe_allow_html=True)
            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Trade recommendations
            st.markdown("### 💡 Trade Recommendations")
            for i, rec in enumerate(results['recommendations'], 1):
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

with tab4:
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
    has_anchors = "anchor_results" in st.session_state
    has_probability = "probability_results" in st.session_state
    has_bc = "bc_results" in st.session_state
    
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
        # Build comprehensive plan card
        anchor_data = st.session_state["anchor_results"]
        prob_data = st.session_state["probability_results"]
        bc_data = st.session_state.get("bc_results", None)
        
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
            # Get 8:30 fan width
            fan_830 = anchor_data['fan_projection'][anchor_data['fan_projection']['Time'] == '08:30']
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
            strategy_830 = anchor_data['strategy_table'][anchor_data['strategy_table']['Time'] == '08:30']
            
            if not strategy_830.empty:
                row_830 = strategy_830.iloc[0]
                st.markdown(f"**🕰️ 8:30 AM Analysis:**")
                st.markdown(f"• **Current Bias:** {create_status_badge(row_830['Bias'], 'up' if row_830['Bias'] == 'UP' else ('down' if row_830['Bias'] == 'DOWN' else 'neutral'))}")
                st.markdown(f"• **Top Level:** {row_830['Top']}")
                st.markdown(f"• **Bottom Level:** {row_830['Bottom']}")
                st.markdown(f"• **Fan Width:** {row_830['Width']}")
                st.markdown(f"• **Data Source:** {row_830['Note']}")
            
            st.markdown("---")
            
            # Probability insights
            st.markdown("**🧠 Overnight Probability Analysis:**")
            if not prob_data['interactions'].empty:
                top_interactions = prob_data['interactions'].nlargest(3, 'Score')
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
                projection_830 = bc_data['projection_table'][bc_data['projection_table']['Time'] == '08:30']
                
                if not projection_830.empty:
                    row_830 = projection_830.iloc[0]
                    st.markdown("**📈 Contract Projections @ 8:30:**")
                    st.markdown(f"• **SPX Projected:** {row_830['SPX_Projected']:.2f}")
                    
                    ca_symbol = bc_data['ca_symbol']
                    if f"{ca_symbol}_Entry" in row_830:
                        st.markdown(f"• **{ca_symbol} Entry:** {row_830[f'{ca_symbol}_Entry']:.2f}")
                    if f"{ca_symbol}_Exit" in row_830:
                        st.markdown(f"• **{ca_symbol} Exit Target:** {row_830[f'{ca_symbol}_Exit']:.2f}")
                    if f"{ca_symbol}_Spread" in row_830:
                        st.markdown(f"• **{ca_symbol} Spread:** {row_830[f'{ca_symbol}_Spread']:.2f}")
                    
                    st.markdown(f"• **Expected Exit Time:** {bc_data['ca_expected_exit']}")
                    
                    # Contract B if available
                    if bc_data.get('cb_data'):
                        cb_symbol = bc_data['cb_data']['symbol']
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
            if prob_data['readiness_score'] >= 71:
                st.markdown("• ✅ High confidence - standard position sizing")
            elif prob_data['readiness_score'] >= 41:
                st.markdown("• ⚡ Medium confidence - reduced position sizing")
            else:
                st.markdown("• 🚫 Low confidence - consider skipping or minimal size")
            
            st.markdown("• Invalidation: bias reversal beyond fan levels")
            st.markdown("• Monitor volume confirmation at key levels")
        
        # Action recommendations
        st.markdown("### 🚀 Recommended Actions")
        
        action_cards = []
        
        # Generate specific action items
        if prob_data['readiness_score'] >= 71:
            action_cards.append(("🎯 High Probability Setup", "Execute standard trade plan with full position sizing", "success"))
        elif prob_data['readiness_score'] >= 41:
            action_cards.append(("⚡ Medium Probability Setup", "Consider reduced position sizing with tight risk management", "warning"))
        else:
            action_cards.append(("🚫 Low Probability Setup", "Consider skipping or paper trading this session", "danger"))
        
        if bc_data:
            action_cards.append(("📈 Contract Targets Set", f"Monitor {bc_data['ca_symbol']} progression toward exit targets", "success"))
        else:
            action_cards.append(("📋 Set Contract Targets", "Configure BC Forecast for specific contract projections", "neutral"))
        
        # Display action cards
        cols = st.columns(len(action_cards))
        for i, (title, desc, card_type) in enumerate(action_cards):
            with cols[i]:
                st.markdown(f"""
                <div style="background: var(--{card_type}-50); border: 2px solid var(--{card_type}-200); border-radius: 12px; padding: 16px; height: 120px; display: flex; flex-direction: column; justify-content: space-between;">
                    <h4 style="margin: 0; color: var(--{card_type}-700);">{title}</h4>
                    <p style="margin: 8px 0 0 0; color: var(--{card_type}-600); font-size: 0.875rem;">{desc}</p>
                </div>
                """, unsafe_allow_html=True)

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
