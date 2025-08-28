# MarketLens Pro v6 - Part 1: Core Infrastructure & Enhanced Theme
# Professional Analytics Platform for Line-Based Trading Strategies

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, time as dtime, date
import pytz
from typing import List, Tuple, Optional, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# ===============================
# APPLICATION CONSTANTS
# ===============================

APP_NAME = "MarketLens Pro v6 — Professional Analytics Platform"
APP_VERSION = "6.0"

# Market configuration
CT = pytz.timezone("America/Chicago")
ET = pytz.timezone("America/New_York")
UTC = pytz.UTC

# Enhanced slope configurations with confidence intervals
SLOPES = {
    "SPX": {
        "Skyline": {"base": 0.268, "confidence": 0.85, "range": (0.220, 0.315)},
        "Baseline": {"base": -0.235, "confidence": 0.82, "range": (-0.280, -0.190)}
    },
    "AAPL": {"base": 0.0155, "confidence": 0.78, "range": (0.012, 0.019)},
    "MSFT": {"base": 0.0541, "confidence": 0.81, "range": (0.045, 0.063)},
    "NVDA": {"base": 0.0086, "confidence": 0.73, "range": (0.006, 0.011)},
    "AMZN": {"base": 0.0139, "confidence": 0.79, "range": (0.011, 0.017)},
    "GOOGL": {"base": 0.0122, "confidence": 0.80, "range": (0.010, 0.015)},
    "TSLA": {"base": 0.0285, "confidence": 0.71, "range": (0.022, 0.035)},
    "META": {"base": 0.0674, "confidence": 0.77, "range": (0.055, 0.080)},
    "NFLX": {"base": 0.0230, "confidence": 0.76, "range": (0.018, 0.028)}
}

DEFAULT_STOCK_SLOPE = {"base": 0.0150, "confidence": 0.60, "range": (0.010, 0.020)}

# ===============================
# ENHANCED THEME SYSTEM
# ===============================

def get_enhanced_theme(mode: str = "Dark") -> Dict[str, str]:
    """Professional theme system with enhanced visual hierarchy"""
    
    themes = {
        "Dark": {
            "primary_bg": "#0a0d14",
            "secondary_bg": "#151922",
            "surface": "rgba(21, 25, 34, 0.85)",
            "surface_elevated": "rgba(25, 31, 42, 0.90)",
            "glass": "rgba(21, 25, 34, 0.75)",
            "text_primary": "#ffffff",
            "text_secondary": "#b8bcc8",
            "text_muted": "#6b7280",
            "accent_primary": "#00d4aa",
            "accent_secondary": "#0ea5e9",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "border": "rgba(255, 255, 255, 0.08)",
            "border_hover": "rgba(0, 212, 170, 0.3)",
            "shadow": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            "shadow_elevated": "0 25px 50px -12px rgba(0, 0, 0, 0.4)",
            "glow": "0 0 40px rgba(0, 212, 170, 0.15)",
            "gradient_bg": "radial-gradient(1200px 800px at 20% 10%, rgba(0, 212, 170, 0.08), transparent 70%), radial-gradient(1000px 600px at 80% 20%, rgba(14, 165, 233, 0.06), transparent 70%)",
            "gradient_accent": "linear-gradient(135deg, #00d4aa 0%, #0ea5e9 100%)",
            "backdrop_filter": "blur(20px) saturate(180%)"
        },
        "Light": {
            "primary_bg": "#fafbfc",
            "secondary_bg": "#ffffff",
            "surface": "rgba(255, 255, 255, 0.90)",
            "surface_elevated": "rgba(255, 255, 255, 0.95)",
            "glass": "rgba(255, 255, 255, 0.80)",
            "text_primary": "#0f172a",
            "text_secondary": "#334155",
            "text_muted": "#64748b",
            "accent_primary": "#059669",
            "accent_secondary": "#0284c7",
            "success": "#16a34a",
            "warning": "#d97706",
            "danger": "#dc2626",
            "border": "rgba(15, 23, 42, 0.08)",
            "border_hover": "rgba(5, 150, 105, 0.3)",
            "shadow": "0 10px 25px -3px rgba(15, 23, 42, 0.1)",
            "shadow_elevated": "0 20px 25px -5px rgba(15, 23, 42, 0.15)",
            "glow": "0 0 30px rgba(5, 150, 105, 0.12)",
            "gradient_bg": "radial-gradient(1200px 800px at 20% 10%, rgba(5, 150, 105, 0.04), transparent 70%), radial-gradient(1000px 600px at 80% 20%, rgba(2, 132, 199, 0.03), transparent 70%)",
            "gradient_accent": "linear-gradient(135deg, #059669 0%, #0284c7 100%)",
            "backdrop_filter": "blur(20px) saturate(180%)"
        }
    }
    
    return themes.get(mode, themes["Dark"])

def inject_enhanced_css(theme: Dict[str, str]):
    """Inject comprehensive CSS styling"""
    
    css = f"""
    <style>
    /* Root Variables */
    :root {{
        --primary-bg: {theme['primary_bg']};
        --secondary-bg: {theme['secondary_bg']};
        --surface: {theme['surface']};
        --surface-elevated: {theme['surface_elevated']};
        --glass: {theme['glass']};
        --text-primary: {theme['text_primary']};
        --text-secondary: {theme['text_secondary']};
        --text-muted: {theme['text_muted']};
        --accent-primary: {theme['accent_primary']};
        --accent-secondary: {theme['accent_secondary']};
        --success: {theme['success']};
        --warning: {theme['warning']};
        --danger: {theme['danger']};
        --border: {theme['border']};
        --border-hover: {theme['border_hover']};
        --shadow: {theme['shadow']};
        --shadow-elevated: {theme['shadow_elevated']};
        --glow: {theme['glow']};
        --gradient-bg: {theme['gradient_bg']};
        --gradient-accent: {theme['gradient_accent']};
        --backdrop-filter: {theme['backdrop_filter']};
    }}
    
    /* Base Layout */
    html, body, [data-testid="stAppViewContainer"] {{
        background: var(--primary-bg);
        background-image: var(--gradient-bg);
        background-attachment: fixed;
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        overflow-x: hidden;
    }}
    
    /* Sidebar Enhancement */
    [data-testid="stSidebar"] {{
        background: var(--glass);
        border-right: 1px solid var(--border);
        backdrop-filter: var(--backdrop-filter);
        -webkit-backdrop-filter: var(--backdrop-filter);
    }}
    
    [data-testid="stSidebar"] .stSelectbox > div > div {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
    }}
    
    /* Header Styling */
    .main-header {{
        background: var(--surface-elevated);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 24px 32px;
        margin-bottom: 24px;
        backdrop-filter: var(--backdrop-filter);
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
    }}
    
    .main-header::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--gradient-accent);
        border-radius: 20px 20px 0 0;
    }}
    
    .main-header h1 {{
        margin: 0 0 8px 0;
        font-size: 2.2rem;
        font-weight: 700;
        background: var(--gradient-accent);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    .main-header .subtitle {{
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 500;
        margin: 0;
    }}
    
    /* Enhanced Card System */
    .analytics-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        backdrop-filter: var(--backdrop-filter);
        box-shadow: var(--shadow);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .analytics-card:hover {{
        transform: translateY(-4px);
        box-shadow: var(--shadow-elevated);
        border-color: var(--border-hover);
    }}
    
    .analytics-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--gradient-accent);
        transform: translateX(-100%);
        transition: transform 0.3s ease;
    }}
    
    .analytics-card:hover::before {{
        transform: translateX(0);
    }}
    
    .card-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
    }}
    
    .card-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }}
    
    .card-subtitle {{
        color: var(--text-muted);
        font-size: 0.875rem;
        margin: 4px 0 0 0;
    }}
    
    .card-badge {{
        background: var(--gradient-accent);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    /* Metric Cards Grid */
    .metrics-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin: 20px 0;
    }}
    
    .metric-card {{
        background: var(--surface-elevated);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        backdrop-filter: var(--backdrop-filter);
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: var(--glow);
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 800;
        margin: 8px 0 4px 0;
        font-variant-numeric: tabular-nums;
    }}
    
    .metric-label {{
        color: var(--text-muted);
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }}
    
    .metric-positive {{ color: var(--success); }}
    .metric-negative {{ color: var(--danger); }}
    .metric-neutral {{ color: var(--warning); }}
    
    /* Enhanced Tables */
    .stDataFrame {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border);
        backdrop-filter: var(--backdrop-filter);
    }}
    
    .stDataFrame [data-testid="stTable"] {{
        background: var(--surface) !important;
    }}
    
    .stDataFrame th {{
        background: var(--surface-elevated) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
        border-bottom: 2px solid var(--border) !important;
    }}
    
    .stDataFrame td {{
        padding: 10px 16px !important;
        border-bottom: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        font-variant-numeric: tabular-nums;
    }}
    
    /* Enhanced Buttons */
    .stButton > button, .stDownloadButton > button {{
        background: var(--gradient-accent);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: var(--shadow);
    }}
    
    .stButton > button:hover, .stDownloadButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: var(--shadow-elevated);
        filter: brightness(110%);
    }}
    
    /* Form Controls */
    .stSelectbox > div > div, .stTextInput > div > div > input, .stNumberInput > div > div > input {{
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        padding: 8px 12px !important;
    }}
    
    .stSelectbox > div > div:focus-within, .stTextInput > div > div > input:focus, .stNumberInput > div > div > input:focus {{
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.1) !important;
    }}
    
    /* Tabs Enhancement */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: var(--surface);
        border-radius: 12px;
        padding: 6px;
        border: 1px solid var(--border);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 8px;
        color: var(--text-muted);
        font-weight: 600;
        padding: 8px 16px;
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: var(--gradient-accent);
        color: white;
    }}
    
    /* Status Indicators */
    .status-indicator {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }}
    
    .status-bullish {{
        background: rgba(34, 197, 94, 0.1);
        color: var(--success);
        border: 1px solid rgba(34, 197, 94, 0.3);
    }}
    
    .status-bearish {{
        background: rgba(239, 68, 68, 0.1);
        color: var(--danger);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    
    .status-neutral {{
        background: rgba(245, 158, 11, 0.1);
        color: var(--warning);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }}
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--surface);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--accent-primary);
    }}
    
    /* Utility Classes */
    .text-gradient {{
        background: var(--gradient-accent);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }}
    
    .glass-panel {{
        background: var(--glass);
        backdrop-filter: var(--backdrop-filter);
        border: 1px solid var(--border);
        border-radius: 16px;
    }}
    
    .data-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }}
    
    /* Performance optimizations */
    * {{
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

# ===============================
# UTILITY FUNCTIONS
# ===============================

def get_slope_data(symbol: str) -> Dict[str, Any]:
    """Get comprehensive slope data for a symbol including confidence metrics"""
    symbol = symbol.upper()
    
    # Handle aliases
    aliases = {
        "GOOG": "GOOGL",
        "BRK.B": "BRK-B", 
        "BRK-B": "BRK-B"
    }
    
    symbol = aliases.get(symbol, symbol)
    
    if symbol in SLOPES:
        if isinstance(SLOPES[symbol], dict) and "base" in SLOPES[symbol]:
            return SLOPES[symbol]
        else:
            # Handle simple numeric slopes (convert to new format)
            return {
                "base": float(SLOPES[symbol]),
                "confidence": 0.70,
                "range": (float(SLOPES[symbol]) * 0.8, float(SLOPES[symbol]) * 1.2)
            }
    
    return DEFAULT_STOCK_SLOPE

def format_currency(value: float, decimals: int = 2) -> str:
    """Format currency values with proper styling"""
    return f"${value:,.{decimals}f}"

def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage values"""
    return f"{value:.{decimals}f}%"

def format_metric(value: float, metric_type: str = "default") -> str:
    """Format metrics based on type"""
    if metric_type == "currency":
        return format_currency(value)
    elif metric_type == "percentage":
        return format_percentage(value)
    elif metric_type == "ratio":
        return f"{value:.2f}"
    else:
        return f"{value:.4f}"

def calculate_confidence_score(data: pd.Series) -> float:
    """Calculate confidence score based on data quality"""
    if len(data) == 0:
        return 0.0
    
    # Remove NaN values
    clean_data = data.dropna()
    if len(clean_data) == 0:
        return 0.0
    
    # Calculate various quality metrics
    completeness = len(clean_data) / len(data)
    volatility = clean_data.std() / clean_data.mean() if clean_data.mean() != 0 else float('inf')
    consistency = 1.0 / (1.0 + volatility) if volatility != float('inf') else 0.0
    
    # Combined confidence score (0-1)
    confidence = (completeness * 0.4 + consistency * 0.6)
    return min(max(confidence, 0.0), 1.0)

# ===============================
# TIME AND DATE UTILITIES
# ===============================

def as_ct(timestamp: datetime) -> datetime:
    """Convert timestamp to Central Time"""
    if timestamp.tzinfo is None:
        timestamp = UTC.localize(timestamp)
    return timestamp.astimezone(CT)

def format_ct_time(timestamp: datetime, include_date: bool = True) -> str:
    """Format timestamp in CT with optional date"""
    ct_time = as_ct(timestamp)
    if include_date:
        return ct_time.strftime("%Y-%m-%d %H:%M CT")
    return ct_time.strftime("%H:%M CT")

def get_trading_sessions_ct(target_date: date, start_time: str = "08:30", end_time: str = "14:30") -> List[datetime]:
    """Generate 30-minute trading session slots in CT"""
    start_hour, start_min = map(int, start_time.split(":"))
    end_hour, end_min = map(int, end_time.split(":"))
    
    start_dt = CT.localize(datetime.combine(target_date, dtime(start_hour, start_min)))
    end_dt = CT.localize(datetime.combine(target_date, dtime(end_hour, end_min)))
    
    sessions = pd.date_range(start=start_dt, end=end_dt, freq="30min", tz=CT)
    return list(sessions.to_pydatetime())

def get_market_state(current_time: datetime = None) -> Dict[str, Any]:
    """Determine current market state and timing information"""
    if current_time is None:
        current_time = datetime.now(CT)
    
    current_date = current_time.date()
    current_weekday = current_date.weekday()
    
    # Market hours in CT
    market_open = CT.localize(datetime.combine(current_date, dtime(8, 30)))
    market_close = CT.localize(datetime.combine(current_date, dtime(15, 0)))
    
    is_weekend = current_weekday >= 5  # Saturday = 5, Sunday = 6
    is_market_hours = market_open <= current_time <= market_close and not is_weekend
    
    return {
        "is_market_open": is_market_hours,
        "is_weekend": is_weekend,
        "current_session": "RTH" if is_market_hours else "Closed",
        "next_open": market_open + timedelta(days=1) if current_time > market_close else market_open,
        "time_to_open": (market_open - current_time).total_seconds() / 3600 if current_time < market_open else 0,
        "time_to_close": (market_close - current_time).total_seconds() / 3600 if is_market_hours else 0
    }

# ===============================
# UI COMPONENT SYSTEM
# ===============================

def render_metric_card(title: str, value: Any, subtitle: str = "", metric_type: str = "default", 
                      trend: Optional[str] = None, confidence: Optional[float] = None) -> None:
    """Render a professional metric card"""
    
    # Determine value class based on trend or value
    value_class = "metric-neutral"
    if trend:
        value_class = f"metric-{trend}"
    elif isinstance(value, (int, float)):
        if value > 0:
            value_class = "metric-positive"
        elif value < 0:
            value_class = "metric-negative"
    
    # Format the value
    formatted_value = format_metric(value, metric_type) if isinstance(value, (int, float)) else str(value)
    
    # Build confidence indicator
    confidence_indicator = ""
    if confidence is not None:
        conf_percent = confidence * 100
        conf_color = "var(--success)" if confidence >= 0.8 else "var(--warning)" if confidence >= 0.6 else "var(--danger)"
        confidence_indicator = f'<div style="font-size: 0.7rem; color: {conf_color}; margin-top: 4px;">Confidence: {conf_percent:.0f}%</div>'
    
    card_html = f'''
    <div class="metric-card">
        <div class="metric-label">{title}</div>
        <div class="metric-value {value_class}">{formatted_value}</div>
        {f'<div class="card-subtitle">{subtitle}</div>' if subtitle else ''}
        {confidence_indicator}
    </div>
    '''
    
    st.markdown(card_html, unsafe_allow_html=True)

def render_status_badge(status: str, label: str = "") -> str:
    """Generate HTML for status badges"""
    status_map = {
        "bullish": "status-bullish",
        "bearish": "status-bearish", 
        "neutral": "status-neutral"
    }
    
    status_class = status_map.get(status.lower(), "status-neutral")
    display_text = label if label else status.title()
    
    return f'<span class="status-indicator {status_class}">{display_text}</span>'

def render_analytics_card(title: str, subtitle: str = "", badge: str = "", content_func: callable = None) -> None:
    """Render a professional analytics card with content"""
    
    badge_html = f'<div class="card-badge">{badge}</div>' if badge else ''
    
    st.markdown(f'''
    <div class="analytics-card">
        <div class="card-header">
            <div>
                <h3 class="card-title">{title}</h3>
                {f'<p class="card-subtitle">{subtitle}</p>' if subtitle else ''}
            </div>
            {badge_html}
        </div>
    ''', unsafe_allow_html=True)
    
    if content_func and callable(content_func):
        content_func()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# INITIALIZATION FUNCTIONS
# ===============================

def initialize_session_state():
    """Initialize session state with default values"""
    defaults = {
        'theme_mode': 'Dark',
        'selected_symbol': 'AAPL',
        'analysis_mode': 'Live',
        'show_advanced': False,
        'last_update': datetime.now(),
        'cache_timeout': 300  # 5 minutes
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': f"{APP_NAME} v{APP_VERSION} - Professional Trading Analytics Platform"
        }
    )

# ===============================
# MAIN APPLICATION SETUP
# ===============================

def setup_application():
    """Initialize the complete application setup"""
    setup_page_config()
    initialize_session_state()
    
    # Apply theme
    theme = get_enhanced_theme(st.session_state.theme_mode)
    inject_enhanced_css(theme)
    
    # Render main header
    st.markdown(f'''
    <div class="main-header">
        <h1>{APP_NAME}</h1>
        <p class="subtitle">Professional Analytics Platform for Line-Based Trading Strategies • All times in Central Time (CT)</p>
    </div>
    ''', unsafe_allow_html=True)

# This completes Part 1 of the modular redesign
# Next parts will include: Data Management, Analytics Engine, UI Components, and Main Application Logic



# MarketLens Pro v6 - Part 2A: Data Quality & Enhanced Fetching System
# Advanced data validation, caching, and quality assessment

from dataclasses import dataclass
from enum import Enum
import hashlib
import json

# ===============================
# DATA QUALITY & VALIDATION SYSTEM
# ===============================

class DataQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INSUFFICIENT = "insufficient"

@dataclass
class MarketDataQuality:
    symbol: str
    timeframe: str
    completeness: float  # 0-1
    consistency: float   # 0-1 
    freshness: float     # 0-1 (how recent)
    reliability: float   # 0-1 (overall score)
    quality_grade: DataQuality
    issues: List[str]
    last_updated: datetime

def assess_data_quality(df: pd.DataFrame, symbol: str, expected_intervals: int = None) -> MarketDataQuality:
    """Comprehensive data quality assessment for trading decisions"""
    
    if df.empty:
        return MarketDataQuality(
            symbol=symbol,
            timeframe="30min",
            completeness=0.0,
            consistency=0.0,
            freshness=0.0,
            reliability=0.0,
            quality_grade=DataQuality.INSUFFICIENT,
            issues=["No data available"],
            last_updated=datetime.now()
        )
    
    issues = []
    
    # Completeness analysis
    if expected_intervals:
        completeness = len(df) / expected_intervals
    else:
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = 1.0 - (missing_cells / total_cells) if total_cells > 0 else 0.0
    
    if completeness < 0.9:
        issues.append(f"Data completeness: {completeness*100:.1f}%")
    
    # Price consistency validation
    consistency = 1.0
    if 'Close' in df.columns:
        close_prices = pd.to_numeric(df['Close'], errors='coerce').dropna()
        
        if len(close_prices) > 1:
            # Check for extreme price movements (>15% in single bar)
            price_changes = close_prices.pct_change().abs()
            extreme_moves = (price_changes > 0.15).sum()
            
            if extreme_moves > len(close_prices) * 0.02:  # >2% of bars
                consistency -= 0.3
                issues.append(f"Detected {extreme_moves} extreme price movements")
            
            # Check for zero or negative prices
            invalid_prices = (close_prices <= 0).sum()
            if invalid_prices > 0:
                consistency -= 0.5
                issues.append(f"Found {invalid_prices} invalid price points")
            
            # Price sequence validation (ensure OHLC relationships)
            if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
                ohlc_valid = (
                    (df['High'] >= df['Low']) &
                    (df['High'] >= df['Open']) &
                    (df['High'] >= df['Close']) &
                    (df['Low'] <= df['Open']) &
                    (df['Low'] <= df['Close'])
                ).sum()
                
                invalid_ohlc = len(df) - ohlc_valid
                if invalid_ohlc > len(df) * 0.01:  # >1% invalid
                    consistency -= 0.2
                    issues.append(f"OHLC validation failed for {invalid_ohlc} bars")
    
    # Volume analysis (if available)
    if 'Volume' in df.columns:
        volumes = pd.to_numeric(df['Volume'], errors='coerce').dropna()
        if len(volumes) > 0:
            zero_volume_pct = (volumes == 0).sum() / len(volumes)
            if zero_volume_pct > 0.1:  # >10% zero volume
                consistency -= 0.15
                issues.append(f"High zero-volume frequency: {zero_volume_pct*100:.1f}%")
    
    # Data freshness assessment
    if not df.empty:
        latest_timestamp = df.index[-1]
        if latest_timestamp.tzinfo is None:
            latest_timestamp = UTC.localize(latest_timestamp)
        
        current_time = datetime.now(UTC)
        time_delta = current_time - latest_timestamp
        hours_old = time_delta.total_seconds() / 3600
        
        # Freshness score (decays over 24 hours)
        freshness = max(0.0, 1.0 - (hours_old / 24))
        
        if hours_old > 2:
            issues.append(f"Data is {hours_old:.1f} hours old")
    else:
        freshness = 0.0
    
    # Calculate overall reliability
    weights = {'completeness': 0.35, 'consistency': 0.45, 'freshness': 0.20}
    reliability = (
        completeness * weights['completeness'] + 
        consistency * weights['consistency'] + 
        freshness * weights['freshness']
    )
    
    # Assign quality grade
    if reliability >= 0.90:
        grade = DataQuality.EXCELLENT
    elif reliability >= 0.75:
        grade = DataQuality.GOOD
    elif reliability >= 0.60:
        grade = DataQuality.FAIR
    elif reliability >= 0.40:
        grade = DataQuality.POOR
    else:
        grade = DataQuality.INSUFFICIENT
    
    return MarketDataQuality(
        symbol=symbol,
        timeframe="30min",
        completeness=completeness,
        consistency=consistency,
        freshness=freshness,
        reliability=reliability,
        quality_grade=grade,
        issues=issues,
        last_updated=datetime.now()
    )

def render_data_quality_panel(quality: MarketDataQuality) -> None:
    """Render comprehensive data quality assessment panel"""
    
    # Quality grade color mapping
    grade_colors = {
        DataQuality.EXCELLENT: "var(--success)",
        DataQuality.GOOD: "var(--accent-primary)", 
        DataQuality.FAIR: "var(--warning)",
        DataQuality.POOR: "var(--danger)",
        DataQuality.INSUFFICIENT: "var(--text-muted)"
    }
    
    grade_color = grade_colors.get(quality.quality_grade, "var(--text-muted)")
    
    st.markdown(f"""
    <div class="analytics-card">
        <div class="card-header">
            <div>
                <h4 class="card-title">Data Quality Assessment</h4>
                <p class="card-subtitle">{quality.symbol} • {quality.timeframe} • Updated {quality.last_updated.strftime('%H:%M:%S')}</p>
            </div>
            <div class="card-badge" style="background: {grade_color}">{quality.quality_grade.value.title()}</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Reliability Score</div>
                <div class="metric-value" style="color: {grade_color}">{quality.reliability:.1%}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Completeness</div>
                <div class="metric-value metric-{'positive' if quality.completeness > 0.9 else 'neutral'}">{quality.completeness:.1%}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Consistency</div>
                <div class="metric-value metric-{'positive' if quality.consistency > 0.9 else 'neutral'}">{quality.consistency:.1%}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Freshness</div>
                <div class="metric-value metric-{'positive' if quality.freshness > 0.8 else 'neutral'}">{quality.freshness:.1%}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show issues if any
    if quality.issues:
        with st.expander("Quality Issues Detected", expanded=False):
            for issue in quality.issues:
                st.warning(f"⚠️ {issue}")

# ===============================
# ADVANCED CACHING SYSTEM
# ===============================

class DataCacheManager:
    """Advanced caching system with intelligent invalidation"""
    
    def __init__(self, cache_duration: int = 300, max_cache_size: int = 100):
        self.cache_duration = cache_duration
        self.max_cache_size = max_cache_size
        
        # Initialize cache in session state
        if 'market_data_cache' not in st.session_state:
            st.session_state.market_data_cache = {}
        if 'cache_metadata' not in st.session_state:
            st.session_state.cache_metadata = {}
    
    def _generate_cache_key(self, symbol: str, start: datetime, end: datetime, interval: str) -> str:
        """Generate deterministic cache key"""
        key_components = [
            symbol.upper(),
            start.isoformat(),
            end.isoformat(), 
            interval
        ]
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check cache validity with multiple criteria"""
        if cache_key not in st.session_state.cache_metadata:
            return False
        
        metadata = st.session_state.cache_metadata[cache_key]
        current_time = datetime.now()
        
        # Time-based expiry
        age_seconds = (current_time - metadata['timestamp']).total_seconds()
        if age_seconds > self.cache_duration:
            return False
        
        # Market hours consideration (fresher data needed during market hours)
        market_state = get_market_state(current_time)
        if market_state['is_market_open'] and age_seconds > 60:  # 1 minute during market hours
            return False
        
        return True
    
    def _cleanup_old_cache(self):
        """Remove expired or excess cache entries"""
        current_time = datetime.now()
        
        # Remove expired entries
        expired_keys = []
        for key, metadata in st.session_state.cache_metadata.items():
            age = (current_time - metadata['timestamp']).total_seconds()
            if age > self.cache_duration * 2:  # Double expiry for cleanup
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_cache_entry(key)
        
        # Enforce size limit (LRU eviction)
        if len(st.session_state.market_data_cache) > self.max_cache_size:
            # Sort by last access time
            sorted_entries = sorted(
                st.session_state.cache_metadata.items(),
                key=lambda x: x[1].get('last_access', x[1]['timestamp'])
            )
            
            # Remove oldest entries
            excess_count = len(st.session_state.market_data_cache) - self.max_cache_size
            for i in range(excess_count):
                key_to_remove = sorted_entries[i][0]
                self._remove_cache_entry(key_to_remove)
    
    def _remove_cache_entry(self, cache_key: str):
        """Safely remove cache entry"""
        st.session_state.market_data_cache.pop(cache_key, None)
        st.session_state.cache_metadata.pop(cache_key, None)
    
    def get_cached_data(self, symbol: str, start: datetime, end: datetime, 
                       interval: str) -> Optional[Tuple[pd.DataFrame, MarketDataQuality]]:
        """Retrieve cached data if valid"""
        cache_key = self._generate_cache_key(symbol, start, end, interval)
        
        if cache_key in st.session_state.market_data_cache and self._is_cache_valid(cache_key):
            # Update access time
            st.session_state.cache_metadata[cache_key]['last_access'] = datetime.now()
            return st.session_state.market_data_cache[cache_key]
        
        return None
    
    def store_data(self, symbol: str, start: datetime, end: datetime, interval: str,
                  data: pd.DataFrame, quality: MarketDataQuality):
        """Store data in cache with metadata"""
        cache_key = self._generate_cache_key(symbol, start, end, interval)
        
        # Cleanup before storing
        self._cleanup_old_cache()
        
        # Store data and metadata
        st.session_state.market_data_cache[cache_key] = (data.copy(), quality)
        st.session_state.cache_metadata[cache_key] = {
            'timestamp': datetime.now(),
            'last_access': datetime.now(),
            'symbol': symbol.upper(),
            'data_size': len(data),
            'quality_score': quality.reliability
        }
    
    def clear_symbol_cache(self, symbol: str):
        """Clear all cache entries for a specific symbol"""
        symbol = symbol.upper()
        keys_to_remove = [
            key for key, metadata in st.session_state.cache_metadata.items()
            if metadata.get('symbol') == symbol
        ]
        
        for key in keys_to_remove:
            self._remove_cache_entry(key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_entries = len(st.session_state.market_data_cache)
        total_size = sum(
            metadata.get('data_size', 0) 
            for metadata in st.session_state.cache_metadata.values()
        )
        
        avg_quality = np.mean([
            metadata.get('quality_score', 0)
            for metadata in st.session_state.cache_metadata.values()
        ]) if total_entries > 0 else 0
        
        return {
            'total_entries': total_entries,
            'total_data_points': total_size,
            'average_quality': avg_quality,
            'cache_utilization': min(1.0, total_entries / self.max_cache_size)
        }

# Initialize global cache manager
cache_manager = DataCacheManager(cache_duration=300, max_cache_size=50)

# ===============================
# ENHANCED DATA FETCHING SYSTEM
# ===============================

def normalize_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Advanced market data normalization with validation"""
    if df.empty:
        return pd.DataFrame()
    
    # Handle MultiIndex columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        level_0_cols = set([col[0] for col in df.columns])
        if {'Open', 'High', 'Low', 'Close', 'Volume'}.issubset(level_0_cols):
            # Standard OHLCV structure
            df.columns = [col[0] for col in df.columns]
        else:
            # Flatten other structures
            df.columns = ['_'.join([str(c) for c in col if pd.notna(c)]).strip('_') for col in df.columns.values]
    
    # Create standardized OHLCV DataFrame
    standard_data = {}
    column_mapping = {
        'Open': ['Open', 'open'],
        'High': ['High', 'high'], 
        'Low': ['Low', 'low'],
        'Close': ['Close', 'close'],
        'Volume': ['Volume', 'volume', 'Vol']
    }
    
    for standard_col, possible_cols in column_mapping.items():
        found_col = None
        for col in possible_cols:
            if col in df.columns:
                found_col = col
                break
        
        if found_col:
            standard_data[standard_col] = pd.to_numeric(df[found_col], errors='coerce')
        else:
            # Create empty series if not found
            standard_data[standard_col] = pd.Series(np.nan, index=df.index)
    
    # Handle Adjusted Close if available
    if 'Adj Close' in df.columns:
        standard_data['Adj Close'] = pd.to_numeric(df['Adj Close'], errors='coerce')
    
    normalized_df = pd.DataFrame(standard_data, index=df.index)
    
    # Data validation and correction
    if not normalized_df.empty:
        # Remove completely empty rows
        ohlc_cols = ['Open', 'High', 'Low', 'Close']
        normalized_df = normalized_df.dropna(subset=ohlc_cols, how='all')
        
        # Fix basic OHLC relationship violations
        if len(normalized_df) > 0:
            # Ensure High >= Low
            invalid_hl = normalized_df['High'] < normalized_df['Low']
            if invalid_hl.any():
                # Swap High and Low for invalid rows
                normalized_df.loc[invalid_hl, ['High', 'Low']] = (
                    normalized_df.loc[invalid_hl, ['Low', 'High']].values
                )
            
            # Ensure High >= max(Open, Close) and Low <= min(Open, Close)
            normalized_df['High'] = np.maximum.reduce([
                normalized_df['High'], 
                normalized_df['Open'], 
                normalized_df['Close']
            ])
            
            normalized_df['Low'] = np.minimum.reduce([
                normalized_df['Low'],
                normalized_df['Open'],
                normalized_df['Close'] 
            ])
    
    return normalized_df

@st.cache_data(ttl=300, show_spinner=False, max_entries=20)
def fetch_market_data_cached(symbol: str, start_time: datetime, end_time: datetime,
                           interval: str = "30m") -> Tuple[pd.DataFrame, MarketDataQuality]:
    """Enhanced market data fetching with caching and quality assessment"""
    
    # Check cache first
    cached_result = cache_manager.get_cached_data(symbol, start_time, end_time, interval)
    if cached_result is not None:
        return cached_result
    
    try:
        # Fetch from yfinance with error handling
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            start=start_time,
            end=end_time,
            interval=interval,
            auto_adjust=False,
            back_adjust=False,
            progress=False,
            actions=False
        )
        
        if df.empty:
            # Try alternative method
            df = yf.download(
                symbol,
                start=start_time,
                end=end_time,
                interval=interval,
                auto_adjust=False,
                progress=False,
                show_errors=False
            )
        
        # Handle timezone information
        if not df.empty and df.index.tz is None:
            df.index = df.index.tz_localize(UTC)
        
        # Normalize the data structure
        normalized_df = normalize_market_data(df)
        
        # Calculate expected intervals for quality assessment
        total_minutes = (end_time - start_time).total_seconds() / 60
        expected_intervals = int(total_minutes / 30) if interval == "30m" else None
        
        # Assess data quality
        quality = assess_data_quality(normalized_df, symbol, expected_intervals)
        
        # Store in cache
        cache_manager.store_data(symbol, start_time, end_time, interval, normalized_df, quality)
        
        return normalized_df, quality
        
    except Exception as e:
        error_msg = f"Failed to fetch data for {symbol}: {str(e)}"
        st.error(error_msg)
        
        # Return empty result with error quality assessment
        quality = MarketDataQuality(
            symbol=symbol,
            timeframe=interval,
            completeness=0.0,
            consistency=0.0,
            freshness=0.0,
            reliability=0.0,
            quality_grade=DataQuality.INSUFFICIENT,
            issues=[error_msg],
            last_updated=datetime.now()
        )
        
        return pd.DataFrame(), quality

def validate_trading_data(df: pd.DataFrame, min_price: float = 0.01, 
                         max_price_ratio: float = 10.0) -> Tuple[bool, List[str]]:
    """Comprehensive trading data validation"""
    
    if df.empty:
        return False, ["No data provided"]
    
    issues = []
    
    # Basic structure validation
    required_columns = ['Open', 'High', 'Low', 'Close']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")
        return False, issues
    
    # Price range validation
    for col in required_columns:
        prices = pd.to_numeric(df[col], errors='coerce').dropna()
        if len(prices) == 0:
            issues.append(f"No valid prices in {col} column")
            continue
            
        min_col_price = prices.min()
        max_col_price = prices.max()
        
        if min_col_price < min_price:
            issues.append(f"{col} contains prices below ${min_price}")
        
        if max_col_price / min_col_price > max_price_ratio:
            issues.append(f"{col} price range too wide (ratio: {max_col_price/min_col_price:.1f})")
    
    # Temporal validation
    if not df.index.is_monotonic_increasing:
        issues.append("Timestamps are not in chronological order")
    
    # Check for duplicate timestamps
    duplicate_times = df.index.duplicated().sum()
    if duplicate_times > 0:
        issues.append(f"Found {duplicate_times} duplicate timestamps")
    
    return len(issues) == 0, issues

# This completes Part 2A: Data Quality & Enhanced Fetching System


# MarketLens Pro v6 - Part 2B: Advanced Swing Detection & Anchor System
# Sophisticated swing detection with confidence scoring and anchor identification

# ===============================
# SWING POINT DATA STRUCTURES
# ===============================

@dataclass
class SwingPoint:
    """Enhanced swing point with comprehensive metadata"""
    price: float
    timestamp: datetime
    swing_type: str  # 'high' or 'low'
    strength: int    # lookback/lookahead periods used
    volume: float
    confidence: float  # 0-1 confidence score
    atr_ratio: float  # price move relative to ATR
    volume_ratio: float  # volume relative to average
    market_session: str  # 'RTH', 'Asian', 'European', etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display"""
        return {
            'Price': f"${self.price:.2f}",
            'Time (CT)': format_ct_time(self.timestamp),
            'Type': self.swing_type.title(),
            'Confidence': f"{self.confidence:.1%}",
            'Volume Ratio': f"{self.volume_ratio:.1f}x",
            'ATR Ratio': f"{self.atr_ratio:.2f}",
            'Session': self.market_session
        }

class SwingDetectionConfig:
    """Configuration for swing detection parameters"""
    
    def __init__(self, 
                 lookback: int = 1,
                 min_confidence: float = 0.5,
                 volume_weight: float = 0.3,
                 atr_weight: float = 0.4,
                 time_weight: float = 0.3):
        self.lookback = lookback
        self.min_confidence = min_confidence
        self.volume_weight = volume_weight
        self.atr_weight = atr_weight
        self.time_weight = time_weight

# ===============================
# ADVANCED SWING DETECTION ENGINE
# ===============================

class AdvancedSwingDetector:
    """Professional-grade swing detection with multi-factor confidence scoring"""
    
    def __init__(self, config: SwingDetectionConfig = None):
        self.config = config or SwingDetectionConfig()
        
    def detect_swings_with_confidence(self, df: pd.DataFrame, 
                                    price_col: str = 'Close') -> pd.DataFrame:
        """Detect swings with comprehensive confidence analysis"""
        
        if df.empty or price_col not in df.columns:
            return self._empty_swing_result(df)
        
        # Prepare data
        result_df = df.copy()
        prices = pd.to_numeric(df[price_col], errors='coerce')
        volumes = pd.to_numeric(df.get('Volume', pd.Series(1.0, index=df.index)), errors='coerce')
        
        # Calculate ATR for context
        atr_series = self._calculate_atr(df) if self._has_ohlc(df) else pd.Series(1.0, index=df.index)
        
        # Initialize swing arrays
        n = len(prices)
        swing_highs = np.zeros(n, dtype=bool)
        swing_lows = np.zeros(n, dtype=bool)
        confidence_scores = np.zeros(n, dtype=float)
        volume_ratios = np.zeros(n, dtype=float)
        atr_ratios = np.zeros(n, dtype=float)
        
        # Detect swings with lookback/lookahead
        for i in range(self.config.lookback, n - self.config.lookback):
            if pd.isna(prices.iloc[i]):
                continue
                
            current_price = prices.iloc[i]
            
            # Check for swing high
            is_high = self._is_swing_high(prices, i, self.config.lookback)
            
            # Check for swing low
            is_low = self._is_swing_low(prices, i, self.config.lookback)
            
            if is_high or is_low:
                # Calculate confidence components
                price_confidence = self._calculate_price_confidence(prices, i, self.config.lookback)
                volume_confidence = self._calculate_volume_confidence(volumes, i, self.config.lookback)
                atr_confidence = self._calculate_atr_confidence(prices, atr_series, i)
                time_confidence = self._calculate_time_confidence(df.index[i])
                
                # Combined confidence score
                total_confidence = (
                    price_confidence * (1 - self.config.volume_weight - self.config.atr_weight - self.config.time_weight) +
                    volume_confidence * self.config.volume_weight +
                    atr_confidence * self.config.atr_weight +
                    time_confidence * self.config.time_weight
                )
                
                # Apply minimum confidence threshold
                if total_confidence >= self.config.min_confidence:
                    swing_highs[i] = is_high
                    swing_lows[i] = is_low
                    confidence_scores[i] = total_confidence
                    
                    # Store additional metrics
                    volume_ratios[i] = self._get_volume_ratio(volumes, i, self.config.lookback)
                    atr_ratios[i] = self._get_atr_ratio(prices, atr_series, i, self.config.lookback)
        
        # Add results to DataFrame
        result_df['swing_high'] = swing_highs
        result_df['swing_low'] = swing_lows
        result_df['swing_confidence'] = confidence_scores
        result_df['volume_ratio'] = volume_ratios
        result_df['atr_ratio'] = atr_ratios
        
        return result_df
    
    def find_optimal_anchors(self, swing_df: pd.DataFrame, 
                           price_col: str = 'Close') -> Tuple[Optional[SwingPoint], Optional[SwingPoint]]:
        """Find optimal swing anchors using multi-criteria optimization"""
        
        if swing_df.empty:
            return None, None
        
        # Find swing high anchor (skyline)
        high_candidates = swing_df[swing_df['swing_high'] == True].copy()
        skyline_anchor = None
        
        if not high_candidates.empty:
            # Score highs: prefer higher prices with good confidence
            high_candidates['anchor_score'] = (
                (high_candidates[price_col] / high_candidates[price_col].max()) * 0.4 +
                high_candidates['swing_confidence'] * 0.35 +
                (high_candidates['volume_ratio'] / high_candidates['volume_ratio'].max()) * 0.15 +
                (high_candidates['atr_ratio'] / high_candidates['atr_ratio'].max()) * 0.1
            )
            
            best_high = high_candidates.loc[high_candidates['anchor_score'].idxmax()]
            skyline_anchor = self._create_swing_point(best_high, 'high', price_col)
        
        # Find swing low anchor (baseline)  
        low_candidates = swing_df[swing_df['swing_low'] == True].copy()
        baseline_anchor = None
        
        if not low_candidates.empty:
            # Score lows: prefer lower prices with good confidence
            low_candidates['anchor_score'] = (
                (1 - low_candidates[price_col] / low_candidates[price_col].max()) * 0.4 +
                low_candidates['swing_confidence'] * 0.35 +
                (low_candidates['volume_ratio'] / low_candidates['volume_ratio'].max()) * 0.15 +
                (low_candidates['atr_ratio'] / low_candidates['atr_ratio'].max()) * 0.1
            )
            
            best_low = low_candidates.loc[low_candidates['anchor_score'].idxmax()]
            baseline_anchor = self._create_swing_point(best_low, 'low', price_col)
        
        return skyline_anchor, baseline_anchor
    
    def _is_swing_high(self, prices: pd.Series, index: int, lookback: int) -> bool:
        """Check if point is a swing high"""
        current = prices.iloc[index]
        
        for j in range(1, lookback + 1):
            if (index - j < 0 or index + j >= len(prices) or
                pd.isna(prices.iloc[index - j]) or pd.isna(prices.iloc[index + j])):
                continue
                
            if (current <= prices.iloc[index - j] or current <= prices.iloc[index + j]):
                return False
        
        return True
    
    def _is_swing_low(self, prices: pd.Series, index: int, lookback: int) -> bool:
        """Check if point is a swing low"""
        current = prices.iloc[index]
        
        for j in range(1, lookback + 1):
            if (index - j < 0 or index + j >= len(prices) or
                pd.isna(prices.iloc[index - j]) or pd.isna(prices.iloc[index + j])):
                continue
                
            if (current >= prices.iloc[index - j] or current >= prices.iloc[index + j]):
                return False
        
        return True
    
    def _calculate_price_confidence(self, prices: pd.Series, index: int, lookback: int) -> float:
        """Calculate confidence based on price separation"""
        current = prices.iloc[index]
        surrounding_prices = []
        
        for j in range(1, lookback + 1):
            if index - j >= 0 and not pd.isna(prices.iloc[index - j]):
                surrounding_prices.append(prices.iloc[index - j])
            if index + j < len(prices) and not pd.isna(prices.iloc[index + j]):
                surrounding_prices.append(prices.iloc[index + j])
        
        if not surrounding_prices:
            return 0.0
        
        avg_surrounding = np.mean(surrounding_prices)
        if avg_surrounding == 0:
            return 0.0
        
        separation = abs(current - avg_surrounding) / avg_surrounding
        return min(1.0, separation * 8)  # Scale factor for reasonable confidence range
    
    def _calculate_volume_confidence(self, volumes: pd.Series, index: int, lookback: int) -> float:
        """Calculate confidence based on volume confirmation"""
        if volumes.empty or pd.isna(volumes.iloc[index]):
            return 0.5  # Neutral if no volume data
        
        current_volume = volumes.iloc[index]
        surrounding_volumes = []
        
        for j in range(1, lookback + 2):  # Slightly wider range for volume
            if index - j >= 0 and not pd.isna(volumes.iloc[index - j]):
                surrounding_volumes.append(volumes.iloc[index - j])
            if index + j < len(volumes) and not pd.isna(volumes.iloc[index + j]):
                surrounding_volumes.append(volumes.iloc[index + j])
        
        if not surrounding_volumes or current_volume == 0:
            return 0.3
        
        avg_volume = np.mean(surrounding_volumes)
        if avg_volume == 0:
            return 0.3
        
        volume_ratio = current_volume / avg_volume
        # Higher volume increases confidence, but with diminishing returns
        return min(1.0, 0.3 + (volume_ratio - 1) * 0.2) if volume_ratio > 1 else 0.3
    
    def _calculate_atr_confidence(self, prices: pd.Series, atr_series: pd.Series, index: int) -> float:
        """Calculate confidence based on price move relative to ATR"""
        if atr_series.empty or pd.isna(atr_series.iloc[index]):
            return 0.5
        
        current_atr = atr_series.iloc[index]
        if current_atr == 0:
            return 0.5
        
        # Look at price range around the swing point
        range_start = max(0, index - 2)
        range_end = min(len(prices), index + 3)
        local_prices = prices.iloc[range_start:range_end].dropna()
        
        if len(local_prices) < 2:
            return 0.5
        
        price_range = local_prices.max() - local_prices.min()
        atr_ratio = price_range / current_atr
        
        # Moderate ATR ratios (0.5-2.0) are most reliable
        if 0.5 <= atr_ratio <= 2.0:
            return 0.8
        elif atr_ratio < 0.5:
            return 0.4  # Too small move
        else:
            return max(0.2, 1.0 - (atr_ratio - 2.0) * 0.1)  # Diminishing confidence for extreme moves
    
    def _calculate_time_confidence(self, timestamp: pd.Timestamp) -> float:
        """Calculate confidence based on market session timing"""
        if timestamp.tz is None:
            timestamp = UTC.localize(timestamp)
        
        ct_time = timestamp.astimezone(CT)
        hour = ct_time.hour
        minute = ct_time.minute
        
        # Higher confidence during key market sessions
        if 8 <= hour <= 10:  # Market open
            return 0.9
        elif 14 <= hour <= 15:  # Market close
            return 0.85
        elif 10 <= hour <= 14:  # Mid-day
            return 0.7
        elif 17 <= hour <= 19:  # Asian session
            return 0.8
        else:  # Off-hours
            return 0.4
    
    def _get_volume_ratio(self, volumes: pd.Series, index: int, lookback: int) -> float:
        """Get volume ratio for the swing point"""
        if volumes.empty or pd.isna(volumes.iloc[index]):
            return 1.0
        
        current_volume = volumes.iloc[index]
        surrounding_volumes = []
        
        for j in range(1, lookback + 2):
            if index - j >= 0 and not pd.isna(volumes.iloc[index - j]):
                surrounding_volumes.append(volumes.iloc[index - j])
        
        if not surrounding_volumes:
            return 1.0
        
        avg_volume = np.mean(surrounding_volumes)
        return current_volume / avg_volume if avg_volume > 0 else 1.0
    
    def _get_atr_ratio(self, prices: pd.Series, atr_series: pd.Series, 
                      index: int, lookback: int) -> float:
        """Get ATR ratio for the swing point"""
        if atr_series.empty or pd.isna(atr_series.iloc[index]):
            return 1.0
        
        current_atr = atr_series.iloc[index]
        if current_atr == 0:
            return 1.0
        
        # Price move from previous bar
        if index > 0 and not pd.isna(prices.iloc[index - 1]):
            price_move = abs(prices.iloc[index] - prices.iloc[index - 1])
            return price_move / current_atr
        
        return 1.0
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        if not self._has_ohlc(df):
            return pd.Series(1.0, index=df.index)
        
        high = pd.to_numeric(df['High'], errors='coerce')
        low = pd.to_numeric(df['Low'], errors='coerce')
        close = pd.to_numeric(df['Close'], errors='coerce')
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.ewm(span=period, adjust=False).mean()
    
    def _has_ohlc(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame has OHLC columns"""
        return all(col in df.columns for col in ['Open', 'High', 'Low', 'Close'])
    
    def _empty_swing_result(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return empty swing result structure"""
        result = df.copy() if not df.empty else pd.DataFrame()
        result['swing_high'] = False
        result['swing_low'] = False  
        result['swing_confidence'] = 0.0
        result['volume_ratio'] = 1.0
        result['atr_ratio'] = 1.0
        return result
    
    def _create_swing_point(self, row: pd.Series, swing_type: str, price_col: str) -> SwingPoint:
        """Create SwingPoint from DataFrame row"""
        timestamp = row.name
        if timestamp.tz is None:
            timestamp = UTC.localize(timestamp)
        
        # Determine market session
        ct_time = timestamp.astimezone(CT)
        hour = ct_time.hour
        
        if 8 <= hour <= 15:
            session = 'RTH'
        elif 17 <= hour <= 19:
            session = 'Asian'
        elif 2 <= hour <= 8:
            session = 'European'
        else:
            session = 'Extended'
        
        return SwingPoint(
            price=float(row[price_col]),
            timestamp=timestamp,
            swing_type=swing_type,
            strength=self.config.lookback,
            volume=float(row.get('Volume', 0)),
            confidence=float(row.get('swing_confidence', 0.5)),
            atr_ratio=float(row.get('atr_ratio', 1.0)),
            volume_ratio=float(row.get('volume_ratio', 1.0)),
            market_session=session
        )

# ===============================
# ANCHOR DETECTION SYSTEM
# ===============================

class ProfessionalAnchorDetector:
    """Professional anchor detection system for SPX and individual stocks"""
    
    def __init__(self):
        self.swing_detector = AdvancedSwingDetector()
        self.ct_tz = CT
        self.et_tz = ET
    
    def detect_spx_anchors_from_es(self, reference_date: date, 
                                  strength: int = 1) -> Tuple[Optional[SwingPoint], Optional[SwingPoint], Optional[float], Dict[str, Any]]:
        """Enhanced SPX anchor detection from ES Asian session"""
        
        # Configure swing detector
        config = SwingDetectionConfig(
            lookback=strength,
            min_confidence=0.6,  # Higher threshold for ES
            volume_weight=0.2,   # Lower volume weight for futures
            atr_weight=0.5,      # Higher ATR weight
            time_weight=0.3
        )
        self.swing_detector.config = config
        
        # Define Asian session window (17:00-19:30 CT)
        session_start = self.ct_tz.localize(datetime.combine(reference_date, dtime(16, 45)))
        session_end = self.ct_tz.localize(datetime.combine(reference_date, dtime(19, 45)))
        
        # Fetch ES futures data with quality assessment
        es_data, es_quality = fetch_market_data_cached(
            "ES=F",
            session_start.astimezone(UTC),
            session_end.astimezone(UTC),
            "30m"
        )
        
        analysis_metadata = {
            'session_start': session_start,
            'session_end': session_end,
            'data_quality': es_quality,
            'bars_analyzed': 0,
            'swing_candidates': {'highs': 0, 'lows': 0}
        }
        
        if es_data.empty or es_quality.reliability < 0.5:
            return None, None, None, analysis_metadata
        
        # Convert to CT timezone and filter
        es_data_ct = es_data.copy()
        es_data_ct.index = es_data_ct.index.tz_convert(self.ct_tz)
        session_data = es_data_ct.between_time("17:00", "19:30")
        
        if session_data.empty:
            return None, None, None, analysis_metadata
        
        analysis_metadata['bars_analyzed'] = len(session_data)
        
        # Detect swings with confidence scoring
        swing_data = self.swing_detector.detect_swings_with_confidence(session_data, 'Close')
        
        # Count swing candidates
        analysis_metadata['swing_candidates']['highs'] = swing_data['swing_high'].sum()
        analysis_metadata['swing_candidates']['lows'] = swing_data['swing_low'].sum()
        
        # Find optimal anchors
        skyline_anchor, baseline_anchor = self.swing_detector.find_optimal_anchors(swing_data, 'Close')
        
        # Calculate ES to SPX offset
        es_spx_offset = self._calculate_es_spx_offset(reference_date)
        
        return skyline_anchor, baseline_anchor, es_spx_offset, analysis_metadata
    
    def detect_stock_anchors_multi_session(self, symbol: str, start_date: date, 
                                         end_date: date, strength: int = 1) -> Tuple[Optional[SwingPoint], Optional[SwingPoint], Dict[str, Any]]:
        """Enhanced stock anchor detection across multiple sessions"""
        
        # Configure swing detector for stocks
        config = SwingDetectionConfig(
            lookback=strength,
            min_confidence=0.5,
            volume_weight=0.4,   # Higher volume weight for stocks
            atr_weight=0.3,
            time_weight=0.3
        )
        self.swing_detector.config = config
        
        # Define session window (09:30-16:00 ET)
        session_start = self.et_tz.localize(datetime.combine(start_date, dtime(9, 15)))
        session_end = self.et_tz.localize(datetime.combine(end_date, dtime(16, 15)))
        
        # Fetch stock data
        stock_data, stock_quality = fetch_market_data_cached(
            symbol,
            session_start.astimezone(UTC),
            session_end.astimezone(UTC),
            "30m"
        )
        
        analysis_metadata = {
            'symbol': symbol,
            'session_start': session_start,
            'session_end': session_end,
            'data_quality': stock_quality,
            'bars_analyzed': 0,
            'swing_candidates': {'highs': 0, 'lows': 0},
            'price_range': {'min': 0, 'max': 0}
        }
        
        if stock_data.empty or stock_quality.reliability < 0.4:
            return None, None, analysis_metadata
        
        # Convert to ET and filter to RTH
        stock_data_et = stock_data.copy()
        stock_data_et.index = stock_data_et.index.tz_convert(self.et_tz)
        rth_data = stock_data_et.between_time("09:30", "16:00")
        
        if rth_data.empty:
            return None, None, analysis_metadata
        
        analysis_metadata['bars_analyzed'] = len(rth_data)
        analysis_metadata['price_range']['min'] = float(rth_data['Close'].min())
        analysis_metadata['price_range']['max'] = float(rth_data['Close'].max())
        
        # Detect swings
        swing_data = self.swing_detector.detect_swings_with_confidence(rth_data, 'Close')
        
        # Count candidates
        analysis_metadata['swing_candidates']['highs'] = swing_data['swing_high'].sum()
        analysis_metadata['swing_candidates']['lows'] = swing_data['swing_low'].sum()
        
        # Find optimal anchors
        skyline_anchor, baseline_anchor = self.swing_detector.find_optimal_anchors(swing_data, 'Close')
        
        # Convert timestamps to CT for consistency
        if skyline_anchor:
            skyline_anchor.timestamp = skyline_anchor.timestamp.tz_convert(self.ct_tz)
        if baseline_anchor:
            baseline_anchor.timestamp = baseline_anchor.timestamp.tz_convert(self.ct_tz)
        
        return skyline_anchor, baseline_anchor, analysis_metadata
    
    def _calculate_es_spx_offset(self, reference_date: date) -> Optional[float]:
        """Calculate ES to SPX offset using recent RTH comparison"""
        
        # Use previous trading day RTH close (14:30-15:30 CT)
        rth_start = self.ct_tz.localize(datetime.combine(reference_date, dtime(14, 15)))
        rth_end = self.ct_tz.localize(datetime.combine(reference_date, dtime(15, 45)))
        
        try:
            # Fetch both instruments
            es_data, es_qual = fetch_market_data_cached("ES=F", rth_start.astimezone(UTC), rth_end.astimezone(UTC))
            spx_data, spx_qual = fetch_market_data_cached("^GSPC", rth_start.astimezone(UTC), rth_end.astimezone(UTC))
            
            if (not es_data.empty and not spx_data.empty and 
                es_qual.reliability > 0.6 and spx_qual.reliability > 0.6):
                
                es_close = float(es_data['Close'].iloc[-1])
                spx_close = float(spx_data['Close'].iloc[-1])
                return spx_close - es_close
        
        except Exception:
            pass
        
        return None

def render_anchor_analysis_panel(anchors: Tuple[Optional[SwingPoint], Optional[SwingPoint]], 
                               metadata: Dict[str, Any], symbol: str = "SPX") -> None:
    """Render comprehensive anchor analysis panel"""
    
    skyline, baseline = anchors
    
    st.markdown(f'''
    <div class="analytics-card">
        <div class="card-header">
            <div>
                <h4 class="card-title">{symbol} Anchor Analysis</h4>
                <p class="card-subtitle">Professional swing detection with confidence scoring</p>
            </div>
            <div class="card-badge">{symbol}</div>
        </div>
    ''', unsafe_allow_html=True)
    
    # Data quality summary
    if 'data_quality' in metadata:
        quality = metadata['data_quality']
        quality_color = "var(--success)" if quality.reliability > 0.8 else "var(--warning)" if quality.reliability > 0.6 else "var(--danger)"
        
        st.markdown(f'''
        <div style="margin-bottom: 16px; padding: 12px; background: var(--surface-elevated); border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>Data Quality: <strong style="color: {quality_color}">{quality.quality_grade.value.title()}</strong></span>
                <span>{metadata.get('bars_analyzed', 0)} bars analyzed</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Anchor results
    col1, col2 = st.columns(2)
    
    with col1:
        if skyline:
            st.markdown("**Skyline Anchor (High)**")
            anchor_data = skyline.to_dict()
            for key, value in anchor_data.items():
                st.text(f"{key}: {value}")
        else:
            st.warning("No valid skyline anchor found")
    
    with col2:
        if baseline:
            st.markdown("**Baseline Anchor (Low)**")
            anchor_data = baseline.to_dict()
            for key, value in anchor_data.items():
                st.text(f"{key}: {value}")
        else:
            st.warning("No valid baseline anchor found")
    
    # Analysis metadata
    if metadata.get('swing_candidates'):
        candidates = metadata['swing_candidates']
        st.info(f"Swing candidates found: {candidates['highs']} highs, {candidates['lows']} lows")
    
    st.markdown('</div>', unsafe_allow_html=True)

# This completes Part 2B: Advanced Swing Detection & Anchor System

# MarketLens Pro v6 - Part 2C: Technical Indicators & Market Analysis Engine
# Advanced technical analysis with regime detection and confluence scoring

# ===============================
# TECHNICAL INDICATORS ENGINE
# ===============================

class AdvancedTechnicalIndicators:
    """Professional technical analysis toolkit with adaptive algorithms"""
    
    @staticmethod
    def intraday_vwap_with_bands(df: pd.DataFrame, std_dev: float = 1.0) -> Dict[str, pd.Series]:
        """Calculate intraday VWAP with standard deviation bands"""
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close', 'Volume']):
            empty_series = pd.Series(dtype=float, index=df.index if not df.empty else [])
            return {'vwap': empty_series, 'vwap_upper': empty_series, 'vwap_lower': empty_series}
        
        # Ensure CT timezone
        data = df.copy()
        if data.index.tz is None:
            data.index = data.index.tz_localize(UTC)
        data.index = data.index.tz_convert(CT)
        
        # Calculate typical price and price-volume
        data['typical_price'] = (data['High'] + data['Low'] + data['Close']) / 3.0
        data['pv'] = data['typical_price'] * data['Volume']
        data['v2p'] = data['Volume'] * (data['typical_price'] ** 2)
        
        # Group by trading day for daily resets
        trading_dates = data.index.date
        
        # Calculate cumulative values
        cumulative_pv = data['pv'].groupby(trading_dates).cumsum()
        cumulative_volume = data['Volume'].groupby(trading_dates).cumsum()
        cumulative_v2p = data['v2p'].groupby(trading_dates).cumsum()
        
        # VWAP calculation
        vwap = cumulative_pv / cumulative_volume.replace(0, np.nan)
        
        # VWAP standard deviation calculation
        vwap_variance = (cumulative_v2p / cumulative_volume.replace(0, np.nan)) - (vwap ** 2)
        vwap_std = np.sqrt(vwap_variance.clip(lower=0))  # Ensure non-negative variance
        
        # VWAP bands
        vwap_upper = vwap + (vwap_std * std_dev)
        vwap_lower = vwap - (vwap_std * std_dev)
        
        return {
            'vwap': vwap,
            'vwap_upper': vwap_upper,
            'vwap_lower': vwap_lower,
            'vwap_std': vwap_std
        }
    
    @staticmethod
    def adaptive_atr(df: pd.DataFrame, period: int = 14, volatility_factor: float = 2.0) -> pd.Series:
        """Adaptive Average True Range with volatility-based smoothing"""
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
            return pd.Series(dtype=float, index=df.index if not df.empty else [])
        
        data = df.copy()
        prev_close = data['Close'].shift(1)
        
        # True Range components
        tr_components = pd.DataFrame({
            'hl': data['High'] - data['Low'],
            'hc': (data['High'] - prev_close).abs(),
            'lc': (data['Low'] - prev_close).abs()
        })
        
        true_range = tr_components.max(axis=1)
        
        # Adaptive smoothing based on recent volatility
        volatility_window = min(period, 10)
        recent_volatility = true_range.rolling(window=volatility_window).std()
        
        # Calculate adaptive alpha (smoothing factor)
        base_alpha = 2.0 / (period + 1)
        volatility_adjustment = (recent_volatility / recent_volatility.rolling(window=period).mean()).fillna(1.0)
        adaptive_alpha = base_alpha * (1 + (volatility_adjustment - 1) * volatility_factor)
        adaptive_alpha = adaptive_alpha.clip(upper=0.5)  # Prevent over-smoothing
        
        # Calculate adaptive ATR
        atr = pd.Series(index=data.index, dtype=float)
        atr.iloc[0] = true_range.iloc[0] if len(true_range) > 0 else 0
        
        for i in range(1, len(true_range)):
            if pd.notna(adaptive_alpha.iloc[i]) and pd.notna(true_range.iloc[i]):
                atr.iloc[i] = (adaptive_alpha.iloc[i] * true_range.iloc[i] + 
                              (1 - adaptive_alpha.iloc[i]) * atr.iloc[i-1])
            else:
                atr.iloc[i] = atr.iloc[i-1]
        
        return atr
    
    @staticmethod
    def multi_ema_system(df: pd.DataFrame, periods: List[int] = None) -> Dict[str, pd.Series]:
        """Multi-timeframe EMA system with trend strength"""
        if df.empty or 'Close' not in df.columns:
            return {}
        
        if periods is None:
            periods = [8, 21, 50, 100, 200]
        
        close_prices = pd.to_numeric(df['Close'], errors='coerce')
        emas = {}
        
        for period in periods:
            ema_key = f'ema_{period}'
            emas[ema_key] = close_prices.ewm(span=period, adjust=False).mean()
        
        return emas
    
    @staticmethod
    def regime_detection_advanced(emas: Dict[str, pd.Series], 
                                price_series: pd.Series) -> Dict[str, pd.Series]:
        """Advanced market regime detection with strength metrics"""
        
        if not emas or len(emas) < 2:
            empty_result = {
                'regime': pd.Series(dtype=str),
                'trend_strength': pd.Series(dtype=float),
                'regime_consistency': pd.Series(dtype=float)
            }
            return empty_result
        
        # Get EMAs sorted by period
        ema_items = [(int(k.split('_')[1]), v) for k, v in emas.items()]
        ema_items.sort()
        periods, ema_series = zip(*ema_items)
        
        # Primary regime: fastest vs slowest EMA
        fast_ema = ema_series[0]  # Shortest period
        slow_ema = ema_series[-1]  # Longest period
        
        # Calculate regime
        regime_numeric = np.where(fast_ema > slow_ema, 1, -1)
        regime_labels = np.where(regime_numeric == 1, 'Bullish', 'Bearish')
        regime = pd.Series(regime_labels, index=fast_ema.index)
        
        # Trend strength based on EMA separation
        ema_separation = (fast_ema - slow_ema) / slow_ema
        trend_strength = ema_separation.abs().rolling(window=20).mean()
        
        # Regime consistency (how long has regime been the same)
        regime_changes = regime != regime.shift(1)
        regime_groups = regime_changes.cumsum()
        regime_consistency = regime.groupby(regime_groups).cumcount() + 1
        regime_consistency = regime_consistency / regime_consistency.rolling(window=50).max()
        
        # EMA alignment score (how well all EMAs align with trend)
        if len(ema_series) >= 3:
            alignment_scores = []
            for i in range(len(price_series)):
                if pd.isna(regime_numeric[i]):
                    alignment_scores.append(0.0)
                    continue
                
                current_emas = [ema.iloc[i] for ema in ema_series if not pd.isna(ema.iloc[i])]
                if len(current_emas) < 2:
                    alignment_scores.append(0.0)
                    continue
                
                # Check if EMAs are properly ordered
                if regime_numeric[i] == 1:  # Bullish
                    properly_ordered = all(current_emas[i] >= current_emas[i+1] 
                                         for i in range(len(current_emas)-1))
                else:  # Bearish
                    properly_ordered = all(current_emas[i] <= current_emas[i+1] 
                                         for i in range(len(current_emas)-1))
                
                alignment_scores.append(1.0 if properly_ordered else 0.5)
            
            ema_alignment = pd.Series(alignment_scores, index=regime.index)
        else:
            ema_alignment = pd.Series(1.0, index=regime.index)
        
        return {
            'regime': regime,
            'trend_strength': trend_strength,
            'regime_consistency': regime_consistency,
            'ema_alignment': ema_alignment,
            'ema_separation': ema_separation
        }
    
    @staticmethod
    def volume_profile_intraday(df: pd.DataFrame, bins: int = 20) -> Dict[str, Any]:
        """Intraday volume profile analysis"""
        if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close', 'Volume']):
            return {'poc': np.nan, 'vah': np.nan, 'val': np.nan, 'profile': pd.DataFrame()}
        
        data = df.copy()
        
        # Ensure we have valid price and volume data
        valid_data = data.dropna(subset=['High', 'Low', 'Close', 'Volume'])
        if valid_data.empty:
            return {'poc': np.nan, 'vah': np.nan, 'val': np.nan, 'profile': pd.DataFrame()}
        
        # Price range for the session
        session_high = valid_data['High'].max()
        session_low = valid_data['Low'].min()
        
        if session_high == session_low:
            return {'poc': session_high, 'vah': session_high, 'val': session_low, 'profile': pd.DataFrame()}
        
        # Create price bins
        price_levels = np.linspace(session_low, session_high, bins + 1)
        volume_at_price = np.zeros(bins)
        
        # Distribute volume across price levels for each bar
        for _, row in valid_data.iterrows():
            high, low, volume = row['High'], row['Low'], row['Volume']
            
            # Find bins that intersect with this bar's price range
            overlapping_bins = []
            for i in range(bins):
                bin_low = price_levels[i]
                bin_high = price_levels[i + 1]
                
                # Check if price range overlaps with bin
                if not (high < bin_low or low > bin_high):
                    overlap_low = max(low, bin_low)
                    overlap_high = min(high, bin_high)
                    overlap_ratio = (overlap_high - overlap_low) / (high - low) if high != low else 1.0
                    overlapping_bins.append((i, overlap_ratio))
            
            # Distribute volume proportionally
            if overlapping_bins:
                total_ratio = sum(ratio for _, ratio in overlapping_bins)
                for bin_idx, ratio in overlapping_bins:
                    volume_at_price[bin_idx] += volume * (ratio / total_ratio)
        
        # Calculate key levels
        total_volume = volume_at_price.sum()
        
        if total_volume == 0:
            return {'poc': (session_high + session_low) / 2, 'vah': session_high, 'val': session_low, 'profile': pd.DataFrame()}
        
        # Point of Control (highest volume price level)
        poc_idx = np.argmax(volume_at_price)
        poc_price = (price_levels[poc_idx] + price_levels[poc_idx + 1]) / 2
        
        # Value Area High and Low (70% of volume)
        target_volume = total_volume * 0.7
        
        # Start from POC and expand until we capture 70% of volume
        included_bins = {poc_idx}
        captured_volume = volume_at_price[poc_idx]
        
        while captured_volume < target_volume and len(included_bins) < bins:
            # Find adjacent bins with highest volume
            candidates = []
            for bin_idx in list(included_bins):
                if bin_idx > 0 and (bin_idx - 1) not in included_bins:
                    candidates.append((bin_idx - 1, volume_at_price[bin_idx - 1]))
                if bin_idx < bins - 1 and (bin_idx + 1) not in included_bins:
                    candidates.append((bin_idx + 1, volume_at_price[bin_idx + 1]))
            
            if not candidates:
                break
            
            # Add the bin with highest volume
            best_bin_idx, best_volume = max(candidates, key=lambda x: x[1])
            included_bins.add(best_bin_idx)
            captured_volume += best_volume
        
        # Calculate VAH and VAL
        if included_bins:
            vah_idx = max(included_bins)
            val_idx = min(included_bins)
            vah_price = price_levels[vah_idx + 1]  # Top of the bin
            val_price = price_levels[val_idx]      # Bottom of the bin
        else:
            vah_price = session_high
            val_price = session_low
        
        # Create profile DataFrame
        bin_centers = [(price_levels[i] + price_levels[i + 1]) / 2 for i in range(bins)]
        profile_df = pd.DataFrame({
            'price_level': bin_centers,
            'volume': volume_at_price,
            'volume_pct': volume_at_price / total_volume * 100
        })
        
        return {
            'poc': poc_price,
            'vah': vah_price,
            'val': val_price,
            'profile': profile_df,
            'total_volume': total_volume
        }
    
    @staticmethod
    def momentum_oscillator_suite(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Comprehensive momentum analysis suite"""
        if df.empty or 'Close' not in df.columns:
            return {}
        
        close = pd.to_numeric(df['Close'], errors='coerce')
        results = {}
        
        # RSI (14-period)
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.ewm(span=14, adjust=False).mean()
        avg_loss = loss.ewm(span=14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.inf)
        results['rsi'] = 100 - (100 / (1 + rs))
        
        # Rate of Change (10-period)
        results['roc'] = (close / close.shift(10) - 1) * 100
        
        # Williams %R (14-period)
        if all(col in df.columns for col in ['High', 'Low']):
            high = pd.to_numeric(df['High'], errors='coerce')
            low = pd.to_numeric(df['Low'], errors='coerce')
            
            highest_high = high.rolling(window=14).max()
            lowest_low = low.rolling(window=14).min()
            results['williams_r'] = ((highest_high - close) / (highest_high - lowest_low)) * -100
        
        # Stochastic Oscillator (14, 3, 3)
        if all(col in df.columns for col in ['High', 'Low']):
            high = pd.to_numeric(df['High'], errors='coerce')
            low = pd.to_numeric(df['Low'], errors='coerce')
            
            lowest_low = low.rolling(window=14).min()
            highest_high = high.rolling(window=14).max()
            k_percent = ((close - lowest_low) / (highest_high - lowest_low)) * 100
            results['stoch_k'] = k_percent.rolling(window=3).mean()
            results['stoch_d'] = results['stoch_k'].rolling(window=3).mean()
        
        return results

# ===============================
# CONFLUENCE ANALYSIS ENGINE
# ===============================

class ConfluenceAnalysisEngine:
    """Advanced confluence analysis for trade setup evaluation"""
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            'line_proximity': 0.25,
            'vwap_alignment': 0.20,
            'ema_regime': 0.20,
            'volume_confirmation': 0.15,
            'momentum_alignment': 0.10,
            'session_timing': 0.10
        }
    
    def calculate_confluence_scores(self, df: pd.DataFrame, line_prices: pd.Series,
                                  technical_data: Dict[str, Any]) -> pd.DataFrame:
        """Calculate comprehensive confluence scores for each time period"""
        
        if df.empty:
            return pd.DataFrame()
        
        confluence_df = df.copy()
        confluence_df['time_ct'] = confluence_df.index.strftime('%H:%M')
        
        # Initialize scoring components
        scores = {component: np.zeros(len(df)) for component in self.weights.keys()}
        
        # 1. Line Proximity Score
        if not line_prices.empty:
            line_map = line_prices.to_dict()
            confluence_df['line_price'] = confluence_df['time_ct'].map(line_map)
            
            # Calculate proximity using ATR context
            atr = technical_data.get('atr', pd.Series(1.0, index=df.index))
            price_diff = (confluence_df['Close'] - confluence_df['line_price']).abs()
            proximity_ratio = price_diff / atr.reindex(df.index).fillna(atr.mean())
            
            # Score: closer to line = higher score (max 1.0 when at line)
            scores['line_proximity'] = np.exp(-proximity_ratio * 2).fillna(0)
        
        # 2. VWAP Alignment Score
        vwap_data = technical_data.get('vwap', {})
        if 'vwap' in vwap_data:
            vwap = vwap_data['vwap'].reindex(df.index)
            vwap_upper = vwap_data.get('vwap_upper', vwap).reindex(df.index)
            vwap_lower = vwap_data.get('vwap_lower', vwap).reindex(df.index)
            
            close_prices = confluence_df['Close']
            
            # Score based on position relative to VWAP bands
            vwap_scores = np.zeros(len(df))
            
            for i in range(len(df)):
                if pd.isna(vwap.iloc[i]):
                    vwap_scores[i] = 0.5
                    continue
                
                close_price = close_prices.iloc[i]
                vwap_price = vwap.iloc[i]
                upper_band = vwap_upper.iloc[i]
                lower_band = vwap_lower.iloc[i]
                
                if close_price > upper_band:
                    vwap_scores[i] = 1.0  # Strong bullish
                elif close_price > vwap_price:
                    vwap_scores[i] = 0.75  # Moderate bullish
                elif close_price > lower_band:
                    vwap_scores[i] = 0.25  # Weak bearish
                else:
                    vwap_scores[i] = 0.0  # Strong bearish
            
            scores['vwap_alignment'] = vwap_scores
        
        # 3. EMA Regime Score
        regime_data = technical_data.get('regime', {})
        if 'regime' in regime_data:
            regime = regime_data['regime'].reindex(df.index)
            trend_strength = regime_data.get('trend_strength', pd.Series(0.5, index=df.index)).reindex(df.index)
            ema_alignment = regime_data.get('ema_alignment', pd.Series(0.5, index=df.index)).reindex(df.index)
            
            # Combine regime direction with strength and alignment
            regime_numeric = np.where(regime == 'Bullish', 1.0, 0.0)
            regime_scores = (regime_numeric * 0.5 + 
                           trend_strength.fillna(0.5) * 0.3 + 
                           ema_alignment.fillna(0.5) * 0.2)
            
            scores['ema_regime'] = regime_scores.values
        
        # 4. Volume Confirmation Score
        if 'Volume' in df.columns:
            volume = pd.to_numeric(df['Volume'], errors='coerce').fillna(0)
            avg_volume = volume.rolling(window=20).mean().fillna(volume.mean())
            
            # Relative volume score (higher = better confirmation)
            volume_ratio = volume / avg_volume.replace(0, 1)
            volume_scores = np.minimum(volume_ratio / 2.0, 1.0)  # Cap at 1.0, normalize around 2x avg
            
            scores['volume_confirmation'] = volume_scores.values
        
        # 5. Momentum Alignment Score
        momentum_data = technical_data.get('momentum', {})
        if momentum_data:
            momentum_scores = np.zeros(len(df))
            
            # RSI component
            if 'rsi' in momentum_data:
                rsi = momentum_data['rsi'].reindex(df.index).fillna(50)
                # Score based on RSI extremes (30-70 range gets lower scores)
                rsi_scores = np.where(rsi < 30, 0.9,  # Oversold
                                    np.where(rsi > 70, 0.9,  # Overbought
                                           1.0 - np.abs(rsi - 50) / 50 * 0.5))  # Neutral zone
                momentum_scores += rsi_scores * 0.4
            
            # Williams %R component
            if 'williams_r' in momentum_data:
                williams = momentum_data['williams_r'].reindex(df.index).fillna(-50)
                williams_scores = np.where(williams < -80, 0.9,  # Oversold
                                         np.where(williams > -20, 0.9,  # Overbought
                                                1.0 - np.abs(williams + 50) / 50 * 0.5))
                momentum_scores += williams_scores * 0.3
            
            # Stochastic component
            if 'stoch_k' in momentum_data:
                stoch = momentum_data['stoch_k'].reindex(df.index).fillna(50)
                stoch_scores = np.where(stoch < 20, 0.9,
                                      np.where(stoch > 80, 0.9,
                                             1.0 - np.abs(stoch - 50) / 50 * 0.5))
                momentum_scores += stoch_scores * 0.3
            
            # Normalize if we have any momentum indicators
            if any(indicator in momentum_data for indicator in ['rsi', 'williams_r', 'stoch_k']):
                scores['momentum_alignment'] = momentum_scores
        
        # 6. Session Timing Score
        session_scores = np.zeros(len(df))
        for i, timestamp in enumerate(df.index):
            ct_time = timestamp.astimezone(CT) if timestamp.tz else CT.localize(timestamp)
            hour = ct_time.hour
            
            # Score based on market session importance
            if 8 <= hour <= 10:  # Market open
                session_scores[i] = 1.0
            elif 14 <= hour <= 15:  # Market close  
                session_scores[i] = 0.9
            elif 10 <= hour <= 14:  # Mid-day
                session_scores[i] = 0.7
            elif 17 <= hour <= 19:  # Asian session
                session_scores[i] = 0.8
            else:  # Off-hours
                session_scores[i] = 0.3
        
        scores['session_timing'] = session_scores
        
        # Calculate weighted confluence score
        total_score = np.zeros(len(df))
        for component, score_array in scores.items():
            weight = self.weights.get(component, 0)
            total_score += np.array(score_array) * weight
        
        # Add all scores to DataFrame
        for component, score_array in scores.items():
            confluence_df[f'{component}_score'] = score_array
        
        confluence_df['confluence_score'] = total_score
        confluence_df['confluence_grade'] = pd.cut(
            total_score, 
            bins=[0, 0.4, 0.6, 0.8, 1.0], 
            labels=['Poor', 'Fair', 'Good', 'Excellent'],
            include_lowest=True
        )
        
        return confluence_df

def render_confluence_analysis_panel(confluence_df: pd.DataFrame, 
                                   top_n: int = 5) -> None:
    """Render confluence analysis results panel"""
    
    if confluence_df.empty:
        st.warning("No confluence data available")
        return
    
    st.markdown('''
    <div class="analytics-card">
        <div class="card-header">
            <div>
                <h4 class="card-title">Confluence Analysis</h4>
                <p class="card-subtitle">Multi-factor trade setup evaluation with weighted scoring</p>
            </div>
            <div class="card-badge">Advanced</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Top confluence opportunities
    if 'confluence_score' in confluence_df.columns:
        top_setups = confluence_df.nlargest(top_n, 'confluence_score')
        
        st.subheader(f"Top {top_n} Confluence Setups")
        
        display_cols = ['time_ct', 'Close', 'confluence_score', 'confluence_grade']
        score_cols = [col for col in confluence_df.columns if col.endswith('_score') and col != 'confluence_score']
        
        # Add individual component scores
        for col in score_cols[:3]:  # Show top 3 components
            if col in top_setups.columns:
                display_cols.append(col)
        
        # Format display data
        display_data = top_setups[display_cols].copy()
        if 'Close' in display_data.columns:
            display_data['Close'] = display_data['Close'].round(2)
        if 'confluence_score' in display_data.columns:
            display_data['confluence_score'] = display_data['confluence_score'].round(3)
        
        # Format score columns
        for col in score_cols:
            if col in display_data.columns:
                display_data[col] = display_data[col].round(3)
        
        st.dataframe(display_data, use_container_width=True)
        
        # Confluence distribution
        if len(confluence_df) > 0:
            grade_counts = confluence_df['confluence_grade'].value_counts()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                render_metric_card("Excellent", grade_counts.get('Excellent', 0), "setups", trend="positive")
            with col2:
                render_metric_card("Good", grade_counts.get('Good', 0), "setups", trend="positive")
            with col3:
                render_metric_card("Fair", grade_counts.get('Fair', 0), "setups", trend="neutral")
            with col4:
                render_metric_card("Poor", grade_counts.get('Poor', 0), "setups", trend="negative")

# This completes Part 2C: Technical Indicators & Market Analysis Engine


# MarketLens Pro v6 - Part 3A: Enhanced UI Components & Signal Detection System
# Professional user interface components and advanced signal generation

# ===============================
# PROFESSIONAL UI COMPONENTS
# ===============================

class UIComponentSystem:
    """Professional UI component library for trading analytics"""
    
    @staticmethod
    def render_symbol_selector(core_symbols: List[str] = None, 
                              selected_symbol: str = "AAPL",
                              key_prefix: str = "main") -> str:
        """Enhanced symbol selection with quick picks and custom input"""
        
        if core_symbols is None:
            core_symbols = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "META", "AMZN", "NFLX"]
        
        st.markdown("##### Symbol Selection")
        
        # Quick select buttons in grid
        cols = st.columns(len(core_symbols))
        selected_from_buttons = None
        
        for i, symbol in enumerate(core_symbols):
            with cols[i]:
                slope_data = get_slope_data(symbol)
                confidence_color = "var(--success)" if slope_data['confidence'] > 0.8 else "var(--warning)" if slope_data['confidence'] > 0.6 else "var(--danger)"
                
                if st.button(
                    symbol, 
                    key=f"{key_prefix}_btn_{symbol}",
                    help=f"Confidence: {slope_data['confidence']:.1%}",
                    use_container_width=True
                ):
                    selected_from_buttons = symbol
                    st.session_state[f'{key_prefix}_selected_symbol'] = symbol
        
        # Selection mode
        selection_mode = st.selectbox(
            "Symbol Input Method",
            options=["Quick Select", "Custom Symbol"],
            index=0,
            key=f"{key_prefix}_symbol_mode"
        )
        
        if selection_mode == "Custom Symbol":
            custom_symbol = st.text_input(
                "Enter Symbol",
                value="",
                key=f"{key_prefix}_custom_symbol",
                help="Enter any valid ticker symbol (e.g., BRK-B, QQQ, SPY)"
            ).upper().strip()
            
            if custom_symbol:
                # Validate and show slope data
                slope_data = get_slope_data(custom_symbol)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Base Slope", f"{slope_data['base']:.4f}")
                with col2:
                    st.metric("Confidence", f"{slope_data['confidence']:.1%}")
                with col3:
                    range_str = f"{slope_data['range'][0]:.4f} - {slope_data['range'][1]:.4f}"
                    st.metric("Range", range_str)
                
                return custom_symbol
        
        # Return selected symbol
        if selected_from_buttons:
            return selected_from_buttons
        else:
            return st.session_state.get(f'{key_prefix}_selected_symbol', selected_symbol)
    
    @staticmethod
    def render_date_range_selector(default_start: date = None, 
                                  default_end: date = None,
                                  key_prefix: str = "main") -> Tuple[date, date]:
        """Smart date range selector with presets"""
        
        if default_start is None:
            default_start = (datetime.now(CT) - timedelta(days=7)).date()
        if default_end is None:
            default_end = datetime.now(CT).date()
        
        st.markdown("##### Date Range Selection")
        
        # Quick preset buttons
        preset_cols = st.columns(4)
        
        with preset_cols[0]:
            if st.button("Last 5 Days", key=f"{key_prefix}_preset_5d"):
                end_date = datetime.now(CT).date()
                start_date = end_date - timedelta(days=5)
                st.session_state[f'{key_prefix}_start_date'] = start_date
                st.session_state[f'{key_prefix}_end_date'] = end_date
        
        with preset_cols[1]:
            if st.button("Last 10 Days", key=f"{key_prefix}_preset_10d"):
                end_date = datetime.now(CT).date()
                start_date = end_date - timedelta(days=10)
                st.session_state[f'{key_prefix}_start_date'] = start_date
                st.session_state[f'{key_prefix}_end_date'] = end_date
        
        with preset_cols[2]:
            if st.button("This Week", key=f"{key_prefix}_preset_week"):
                today = datetime.now(CT).date()
                start_date = today - timedelta(days=today.weekday())
                end_date = today
                st.session_state[f'{key_prefix}_start_date'] = start_date
                st.session_state[f'{key_prefix}_end_date'] = end_date
        
        with preset_cols[3]:
            if st.button("Last Mon-Tue", key=f"{key_prefix}_preset_montue"):
                today = datetime.now(CT).date()
                days_since_monday = today.weekday()
                last_monday = today - timedelta(days=days_since_monday + 7 if days_since_monday < 2 else days_since_monday)
                last_tuesday = last_monday + timedelta(days=1)
                st.session_state[f'{key_prefix}_start_date'] = last_monday
                st.session_state[f'{key_prefix}_end_date'] = last_tuesday
        
        # Manual date inputs
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=st.session_state.get(f'{key_prefix}_start_date', default_start),
                key=f"{key_prefix}_start_manual"
            )
        with col2:
            end_date = st.date_input(
                "End Date", 
                value=st.session_state.get(f'{key_prefix}_end_date', default_end),
                key=f"{key_prefix}_end_manual"
            )
        
        return start_date, end_date
    
    @staticmethod
    def render_slope_configuration_panel(symbol: str, key_prefix: str = "main") -> Tuple[float, float]:
        """Advanced slope configuration with confidence intervals"""
        
        slope_data = get_slope_data(symbol)
        
        st.markdown(f"##### {symbol} Slope Configuration")
        
        # Display confidence metrics
        confidence_color = "success" if slope_data['confidence'] > 0.8 else "warning" if slope_data['confidence'] > 0.6 else "error"
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Confidence Level</div>
            <div class="metric-value metric-{confidence_color}">{slope_data['confidence']:.1%}</div>
            <div class="card-subtitle">Based on historical performance</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Slope magnitude input with validation
        col1, col2 = st.columns(2)
        
        with col1:
            slope_magnitude = st.number_input(
                "Slope Magnitude (per 30min)",
                min_value=0.0001,
                max_value=1.0,
                value=float(slope_data['base']),
                step=0.0001,
                format="%.4f",
                key=f"{key_prefix}_slope_mag",
                help=f"Recommended range: {slope_data['range'][0]:.4f} to {slope_data['range'][1]:.4f}"
            )
        
        with col2:
            slope_adjustment = st.selectbox(
                "Slope Adjustment",
                options=["Use Base Slope", "Conservative (-20%)", "Aggressive (+20%)", "Custom Range"],
                index=0,
                key=f"{key_prefix}_slope_adj"
            )
        
        # Apply adjustments
        if slope_adjustment == "Conservative (-20%)":
            slope_magnitude *= 0.8
        elif slope_adjustment == "Aggressive (+20%)":
            slope_magnitude *= 1.2
        elif slope_adjustment == "Custom Range":
            range_factor = st.slider(
                "Range Factor", 
                min_value=0.5, 
                max_value=2.0, 
                value=1.0, 
                step=0.1,
                key=f"{key_prefix}_range_factor"
            )
            slope_magnitude *= range_factor
        
        # Warning if outside recommended range
        min_slope, max_slope = slope_data['range']
        if not (min_slope <= slope_magnitude <= max_slope):
            st.warning(f"⚠️ Slope outside recommended range ({min_slope:.4f} - {max_slope:.4f})")
        
        return float(slope_magnitude), float(-slope_magnitude)

    @staticmethod
    def render_trading_parameters_panel(key_prefix: str = "main") -> Dict[str, Any]:
        """Professional trading parameters configuration"""
        
        st.markdown("##### Trading Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            risk_reward = st.number_input(
                "Risk:Reward Target",
                min_value=0.5,
                max_value=10.0,
                value=1.5,
                step=0.1,
                key=f"{key_prefix}_rr_target",
                help="Target profit as multiple of stop loss"
            )
        
        with col2:
            atr_stop_multiple = st.number_input(
                "ATR Stop Multiple",
                min_value=0.2,
                max_value=5.0,
                value=1.0,
                step=0.1,
                key=f"{key_prefix}_atr_stop",
                help="Stop loss distance as ATR multiple"
            )
        
        with col3:
            min_confidence = st.number_input(
                "Minimum Signal Confidence",
                min_value=0.1,
                max_value=1.0,
                value=0.6,
                step=0.05,
                key=f"{key_prefix}_min_conf",
                help="Minimum confluence score for signals"
            )
        
        # Advanced filters
        st.markdown("**Signal Filters**")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            require_vwap = st.checkbox(
                "Require VWAP Alignment",
                value=True,
                key=f"{key_prefix}_req_vwap",
                help="BUY: price above VWAP, SELL: price below VWAP"
            )
        
        with col5:
            require_ema_regime = st.checkbox(
                "Require EMA Regime",
                value=False,
                key=f"{key_prefix}_req_ema",
                help="Align signals with EMA trend direction"
            )
        
        with col6:
            require_volume = st.checkbox(
                "Require Volume Confirmation", 
                value=True,
                key=f"{key_prefix}_req_volume",
                help="Higher than average volume required"
            )
        
        return {
            'risk_reward': risk_reward,
            'atr_stop_multiple': atr_stop_multiple,
            'min_confidence': min_confidence,
            'require_vwap': require_vwap,
            'require_ema_regime': require_ema_regime,
            'require_volume': require_volume
        }

# ===============================
# ADVANCED SIGNAL DETECTION SYSTEM
# ===============================

@dataclass
class TradingSignal:
    """Enhanced trading signal with comprehensive metadata"""
    timestamp: datetime
    signal_type: str  # 'BUY' or 'SELL'
    entry_price: float
    line_price: float
    stop_loss: float
    target_price: float
    confluence_score: float
    confidence_grade: str
    atr_context: float
    volume_ratio: float
    vwap_alignment: str
    ema_regime: str
    session: str
    risk_reward_actual: float
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display"""
        return {
            'Time (CT)': format_ct_time(self.timestamp, include_date=False),
            'Signal': self.signal_type,
            'Entry': f"${self.entry_price:.2f}",
            'Line': f"${self.line_price:.2f}",
            'Stop': f"${self.stop_loss:.2f}",
            'Target': f"${self.target_price:.2f}",
            'R:R': f"{self.risk_reward_actual:.2f}",
            'Confluence': f"{self.confluence_score:.3f}",
            'Grade': self.confidence_grade,
            'Volume': f"{self.volume_ratio:.1f}x",
            'VWAP': self.vwap_alignment,
            'EMA': self.ema_regime,
            'Session': self.session
        }

class AdvancedSignalDetector:
    """Professional signal detection with multi-factor validation"""
    
    def __init__(self, trading_params: Dict[str, Any]):
        self.params = trading_params
        self.technical_indicators = AdvancedTechnicalIndicators()
        self.confluence_engine = ConfluenceAnalysisEngine()
    
    def detect_line_touch_signals(self, df: pd.DataFrame, line_prices: pd.Series,
                                 signal_mode: str = "BUY") -> List[TradingSignal]:
        """Detect line touch signals with comprehensive validation"""
        
        if df.empty or line_prices.empty:
            return []
        
        # Calculate technical indicators
        technical_data = self._calculate_technical_context(df)
        
        # Calculate confluence scores
        confluence_df = self.confluence_engine.calculate_confluence_scores(
            df, line_prices, technical_data
        )
        
        signals = []
        
        for i, (timestamp, row) in enumerate(confluence_df.iterrows()):
            # Get line price for this time
            time_str = timestamp.strftime('%H:%M')
            if time_str not in line_prices.index:
                continue
            
            line_price = line_prices[time_str]
            
            # Basic OHLC data
            open_price = float(row['Open'])
            high_price = float(row['High'])
            low_price = float(row['Low'])
            close_price = float(row['Close'])
            
            # Check for line touch
            line_touched = low_price <= line_price <= high_price
            if not line_touched:
                continue
            
            # Determine bar type
            is_bullish_bar = close_price > open_price
            is_bearish_bar = close_price < open_price
            
            # Signal logic
            valid_signal = False
            entry_price = close_price
            
            if signal_mode == "BUY":
                # BUY: bearish bar that touches line but closes above line and above open
                valid_signal = (is_bearish_bar and 
                              close_price > line_price and 
                              open_price > line_price)
            elif signal_mode == "SELL":
                # SELL: bullish bar that touches line but closes below line and below open  
                valid_signal = (is_bullish_bar and
                              close_price < line_price and
                              open_price < line_price)
            
            if not valid_signal:
                continue
            
            # Apply confluence filter
            confluence_score = float(row.get('confluence_score', 0))
            if confluence_score < self.params['min_confidence']:
                continue
            
            # Calculate stop loss and target
            atr_value = technical_data['atr'].iloc[i] if len(technical_data['atr']) > i else 1.0
            stop_distance = atr_value * self.params['atr_stop_multiple']
            
            if signal_mode == "BUY":
                stop_loss = entry_price - stop_distance
                target_price = entry_price + (stop_distance * self.params['risk_reward'])
            else:
                stop_loss = entry_price + stop_distance  
                target_price = entry_price - (stop_distance * self.params['risk_reward'])
            
            actual_rr = abs(target_price - entry_price) / abs(entry_price - stop_loss)
            
            # Apply additional filters
            if not self._validate_signal_filters(row, technical_data, i):
                continue
            
            # Determine market session
            session = self._get_market_session(timestamp)
            
            # Create signal
            signal = TradingSignal(
                timestamp=timestamp,
                signal_type=signal_mode,
                entry_price=entry_price,
                line_price=line_price,
                stop_loss=stop_loss,
                target_price=target_price,
                confluence_score=confluence_score,
                confidence_grade=str(row.get('confluence_grade', 'Fair')),
                atr_context=float(atr_value),
                volume_ratio=float(row.get('volume_ratio', 1.0)),
                vwap_alignment=self._get_vwap_alignment(row, technical_data, i),
                ema_regime=self._get_ema_regime(technical_data, i),
                session=session,
                risk_reward_actual=actual_rr
            )
            
            signals.append(signal)
        
        # Sort by confluence score (best first)
        signals.sort(key=lambda s: s.confluence_score, reverse=True)
        return signals
    
    def _calculate_technical_context(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators for context"""
        
        technical_data = {}
        
        # VWAP with bands
        vwap_data = self.technical_indicators.intraday_vwap_with_bands(df)
        technical_data['vwap'] = vwap_data
        
        # Adaptive ATR
        technical_data['atr'] = self.technical_indicators.adaptive_atr(df)
        
        # Multi-EMA system
        emas = self.technical_indicators.multi_ema_system(df)
        technical_data['emas'] = emas
        
        # Regime detection
        regime_data = self.technical_indicators.regime_detection_advanced(emas, df['Close'])
        technical_data['regime'] = regime_data
        
        # Momentum indicators
        momentum_data = self.technical_indicators.momentum_oscillator_suite(df)
        technical_data['momentum'] = momentum_data
        
        # Volume profile
        volume_profile = self.technical_indicators.volume_profile_intraday(df)
        technical_data['volume_profile'] = volume_profile
        
        return technical_data
    
    def _validate_signal_filters(self, row: pd.Series, technical_data: Dict[str, Any], 
                               index: int) -> bool:
        """Apply additional signal validation filters"""
        
        # VWAP filter
        if self.params.get('require_vwap', False):
            vwap_alignment = self._get_vwap_alignment(row, technical_data, index)
            if vwap_alignment not in ['Above', 'Below']:  # Require clear alignment
                return False
        
        # EMA regime filter
        if self.params.get('require_ema_regime', False):
            regime_data = technical_data.get('regime', {})
            if 'ema_alignment' in regime_data:
                alignment_score = regime_data['ema_alignment'].iloc[index] if len(regime_data['ema_alignment']) > index else 0.5
                if alignment_score < 0.8:  # Require strong EMA alignment
                    return False
        
        # Volume filter
        if self.params.get('require_volume', False):
            volume_ratio = float(row.get('volume_ratio', 1.0))
            if volume_ratio < 1.2:  # Require above-average volume
                return False
        
        return True
    
    def _get_vwap_alignment(self, row: pd.Series, technical_data: Dict[str, Any], 
                          index: int) -> str:
        """Determine VWAP alignment"""
        vwap_data = technical_data.get('vwap', {})
        if 'vwap' not in vwap_data:
            return 'Unknown'
        
        vwap_series = vwap_data['vwap']
        if len(vwap_series) <= index:
            return 'Unknown'
        
        vwap_price = vwap_series.iloc[index]
        close_price = float(row['Close'])
        
        if pd.isna(vwap_price):
            return 'Unknown'
        
        return 'Above' if close_price > vwap_price else 'Below'
    
    def _get_ema_regime(self, technical_data: Dict[str, Any], index: int) -> str:
        """Determine EMA regime"""
        regime_data = technical_data.get('regime', {})
        if 'regime' not in regime_data:
            return 'Unknown'
        
        regime_series = regime_data['regime']
        if len(regime_series) <= index:
            return 'Unknown'
        
        return str(regime_series.iloc[index])
    
    def _get_market_session(self, timestamp: datetime) -> str:
        """Determine market session"""
        ct_time = timestamp.astimezone(CT) if timestamp.tz else CT.localize(timestamp)
        hour = ct_time.hour
        
        if 8 <= hour <= 15:
            return 'RTH'
        elif 17 <= hour <= 19:
            return 'Asian'
        elif 2 <= hour <= 8:
            return 'European'
        else:
            return 'Extended'

def render_signals_analysis_panel(signals: List[TradingSignal], 
                                max_display: int = 10) -> None:
    """Render comprehensive signals analysis panel"""
    
    if not signals:
        st.warning("No signals detected with current parameters")
        return
    
    st.markdown('''
    <div class="analytics-card">
        <div class="card-header">
            <div>
                <h4 class="card-title">Trading Signals Analysis</h4>
                <p class="card-subtitle">Line-touch signals with multi-factor validation</p>
            </div>
            <div class="card-badge">Professional</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Summary metrics
    total_signals = len(signals)
    avg_confluence = np.mean([s.confluence_score for s in signals])
    avg_rr = np.mean([s.risk_reward_actual for s in signals])
    
    # Grade distribution
    grade_counts = {}
    for signal in signals:
        grade = signal.confidence_grade
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    
    # Display summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Signals", total_signals, "detected")
    with col2:
        render_metric_card("Avg Confluence", avg_confluence, metric_type="ratio", confidence=avg_confluence)
    with col3:
        render_metric_card("Avg Risk:Reward", avg_rr, metric_type="ratio")
    with col4:
        excellent_signals = grade_counts.get('Excellent', 0)
        render_metric_card("Excellent Grade", excellent_signals, f"of {total_signals}", trend="positive" if excellent_signals > 0 else "neutral")
    
    # Detailed signals table
    st.subheader(f"Top {min(max_display, total_signals)} Signals")
    
    display_signals = signals[:max_display]
    signals_data = [signal.to_display_dict() for signal in display_signals]
    
    if signals_data:
        signals_df = pd.DataFrame(signals_data)
        st.dataframe(signals_df, use_container_width=True, hide_index=True)
        
        # Download option
        csv_data = pd.DataFrame([{
            'Timestamp': signal.timestamp.isoformat(),
            'Signal_Type': signal.signal_type,
            'Entry_Price': signal.entry_price,
            'Stop_Loss': signal.stop_loss,
            'Target_Price': signal.target_price,
            'Confluence_Score': signal.confluence_score,
            'Confidence_Grade': signal.confidence_grade,
            'Session': signal.session
        } for signal in signals])
        
        st.download_button(
            "Download Signals CSV",
            csv_data.to_csv(index=False).encode(),
            "trading_signals.csv",
            "text/csv",
            use_container_width=True
        )

# This completes Part 3A: Enhanced UI Components & Signal Detection System

