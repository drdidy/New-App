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
