# Part 1: Core Infrastructure & Enhanced UI Framework
# MarketLens Pro v6 - Professional Analytics Platform

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, time as dtime, date
import pytz
from typing import List, Tuple, Optional, Dict, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# =================================================================================
# CONFIGURATION & CONSTANTS
# =================================================================================

APP_NAME = "MarketLens Pro v6 — Elite Analytics Platform"
VERSION = "6.0.0"

# Enhanced slope configuration with more precise values
SLOPES = {
    "SPX": {"Skyline": +0.268, "Baseline": -0.235},
    "AAPL": 0.0155, "MSFT": 0.0541, "NVDA": 0.0086, "AMZN": 0.0139, 
    "GOOGL": 0.0122, "TSLA": 0.0285, "META": 0.0674, "NFLX": 0.0230,
    "QQQ": 0.0234, "IWM": 0.0187, "SPY": 0.0156, "DIA": 0.0143
}
DEFAULT_STOCK_SLOPE = 0.0150

# Market session configurations
MARKET_SESSIONS = {
    "US_RTH": {"start": "08:30", "end": "14:30", "tz": "America/Chicago"},
    "US_EXTENDED": {"start": "07:00", "end": "16:00", "tz": "America/Chicago"},
    "ASIA_FUTURES": {"start": "17:00", "end": "19:30", "tz": "America/Chicago"},
    "EUROPE_OPEN": {"start": "02:00", "end": "04:00", "tz": "America/Chicago"}
}

# Risk management constants
RISK_CONFIGS = {
    "conservative": {"max_risk_per_trade": 0.01, "max_daily_risk": 0.03, "win_rate_threshold": 0.65},
    "moderate": {"max_risk_per_trade": 0.015, "max_daily_risk": 0.045, "win_rate_threshold": 0.60},
    "aggressive": {"max_risk_per_trade": 0.02, "max_daily_risk": 0.06, "win_rate_threshold": 0.55}
}

# =================================================================================
# TIMEZONE & TIME UTILITIES (Enhanced)
# =================================================================================

CT = pytz.timezone("America/Chicago")
ET = pytz.timezone("America/New_York")
UTC = pytz.UTC

def as_ct(ts: datetime) -> datetime:
    """Convert timestamp to Chicago Time"""
    if ts.tzinfo is None:
        ts = UTC.localize(ts)
    return ts.astimezone(CT)

def format_ct(ts: datetime, with_date=True, format_type="standard") -> str:
    """Enhanced timestamp formatting"""
    ts_ct = as_ct(ts)
    if format_type == "compact":
        return ts_ct.strftime("%m/%d %H:%M" if with_date else "%H:%M")
    elif format_type == "detailed":
        return ts_ct.strftime("%A, %Y-%m-%d %H:%M CT" if with_date else "%H:%M CT")
    return ts_ct.strftime("%Y-%m-%d %H:%M CT" if with_date else "%H:%M")

def get_market_session_slots(session_date: date, session_type: str = "US_RTH") -> List[datetime]:
    """Generate time slots for different market sessions"""
    config = MARKET_SESSIONS.get(session_type, MARKET_SESSIONS["US_RTH"])
    tz = pytz.timezone(config["tz"])
    
    start_time = datetime.strptime(config["start"], "%H:%M").time()
    end_time = datetime.strptime(config["end"], "%H:%M").time()
    
    start_dt = tz.localize(datetime.combine(session_date, start_time))
    end_dt = tz.localize(datetime.combine(session_date, end_time))
    
    # Handle overnight sessions
    if end_time < start_time:
        end_dt += timedelta(days=1)
    
    slots = pd.date_range(start=start_dt, end=end_dt, freq="30min", tz=tz)
    return list(slots.to_pydatetime())

def is_market_day(check_date: date) -> bool:
    """Check if date is a trading day (excludes weekends and major holidays)"""
    if check_date.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Major US market holidays (simplified)
    year = check_date.year
    holidays = [
        date(year, 1, 1),   # New Year
        date(year, 7, 4),   # Independence Day
        date(year, 12, 25), # Christmas
    ]
    
    return check_date not in holidays

# =================================================================================
# ADVANCED UI THEME SYSTEM
# =================================================================================

def get_advanced_theme(mode: str, accent_color: str = "blue") -> Dict[str, str]:
    """Enhanced theme system with multiple accent options"""
    
    # Color palettes
    accents = {
        "blue": {"primary": "#2563eb", "secondary": "#06b6d4", "glow": "59, 130, 246"},
        "purple": {"primary": "#7c3aed", "secondary": "#a855f7", "glow": "124, 58, 237"},
        "green": {"primary": "#059669", "secondary": "#10b981", "glow": "5, 150, 105"},
        "orange": {"primary": "#ea580c", "secondary": "#f97316", "glow": "234, 88, 12"},
        "red": {"primary": "#dc2626", "secondary": "#ef4444", "glow": "220, 38, 38"}
    }
    
    accent = accents.get(accent_color, accents["blue"])
    
    if mode == "Dark":
        return {
            "bg_primary": "#0a0f1c",
            "bg_secondary": "#111827",
            "bg_tertiary": "#1f2937",
            "panel_bg": "rgba(17, 24, 39, 0.85)",
            "panel_border": "rgba(75, 85, 99, 0.3)",
            "text_primary": "#f9fafb",
            "text_secondary": "#d1d5db",
            "text_muted": "#9ca3af",
            "accent_primary": accent["primary"],
            "accent_secondary": accent["secondary"],
            "accent_glow": accent["glow"],
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#3b82f6",
            "shadow": "0 25px 50px -12px rgba(0, 0, 0, 0.75)",
            "glow_effect": f"0 0 20px rgba({accent['glow']}, 0.3)"
        }
    else:  # Light mode
        return {
            "bg_primary": "#ffffff",
            "bg_secondary": "#f8fafc",
            "bg_tertiary": "#f1f5f9",
            "panel_bg": "rgba(255, 255, 255, 0.9)",
            "panel_border": "rgba(148, 163, 184, 0.3)",
            "text_primary": "#0f172a",
            "text_secondary": "#334155",
            "text_muted": "#64748b",
            "accent_primary": accent["primary"],
            "accent_secondary": accent["secondary"],
            "accent_glow": accent["glow"],
            "success": "#059669",
            "warning": "#d97706",
            "danger": "#dc2626",
            "info": "#2563eb",
            "shadow": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
            "glow_effect": f"0 0 20px rgba({accent['glow']}, 0.2)"
        }

def inject_advanced_css(theme: Dict[str, str]) -> str:
    """Generate advanced CSS with professional styling"""
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Reset and Base Styles */
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        box-sizing: border-box;
    }}
    
    html, body, [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, {theme['bg_primary']} 0%, {theme['bg_secondary']} 100%);
        background-attachment: fixed;
        min-height: 100vh;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background: {theme['panel_bg']};
        border-right: 1px solid {theme['panel_border']};
        backdrop-filter: blur(20px) saturate(180%);
        box-shadow: inset -1px 0 0 {theme['panel_border']};
    }}
    
    /* Enhanced Card System */
    .analytics-card {{
        background: {theme['panel_bg']};
        border: 1px solid {theme['panel_border']};
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        backdrop-filter: blur(20px) saturate(180%);
        box-shadow: {theme['shadow']};
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .analytics-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, {theme['accent_primary']}, {theme['accent_secondary']});
        opacity: 0;
        transition: opacity 0.3s ease;
    }}
    
    .analytics-card:hover {{
        transform: translateY(-4px);
        box-shadow: {theme['shadow']}, {theme['glow_effect']};
        border-color: {theme['accent_primary']};
    }}
    
    .analytics-card:hover::before {{
        opacity: 1;
    }}
    
    /* Metric Display System */
    .metric-container {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }}
    
    .metric-card {{
        background: {theme['panel_bg']};
        border: 1px solid {theme['panel_border']};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.2s ease;
        position: relative;
    }}
    
    .metric-card:hover {{
        border-color: {theme['accent_primary']};
        box-shadow: {theme['glow_effect']};
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {theme['text_primary']};
        line-height: 1;
        margin-bottom: 8px;
    }}
    
    .metric-label {{
        font-size: 0.875rem;
        color: {theme['text_muted']};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .metric-change {{
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 4px;
    }}
    
    .metric-positive {{ color: {theme['success']}; }}
    .metric-negative {{ color: {theme['danger']}; }}
    .metric-neutral {{ color: {theme['text_muted']}; }}
    
    /* Status Indicators */
    .status-indicator {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .status-bullish {{
        background: rgba(16, 185, 129, 0.1);
        color: {theme['success']};
        border: 1px solid {theme['success']};
    }}
    
    .status-bearish {{
        background: rgba(239, 68, 68, 0.1);
        color: {theme['danger']};
        border: 1px solid {theme['danger']};
    }}
    
    .status-neutral {{
        background: rgba(156, 163, 175, 0.1);
        color: {theme['text_muted']};
        border: 1px solid {theme['text_muted']};
    }}
    
    /* Enhanced Typography */
    h1, h2, h3, h4, h5, h6 {{
        color: {theme['text_primary']} !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        margin-bottom: 16px !important;
    }}
    
    h1 {{ font-size: 2.5rem !important; }}
    h2 {{ font-size: 2rem !important; }}
    h3 {{ font-size: 1.5rem !important; }}
    h4 {{ font-size: 1.25rem !important; }}
    
    p, span, div, label {{
        color: {theme['text_secondary']} !important;
    }}
    
    .text-muted {{
        color: {theme['text_muted']} !important;
        font-size: 0.875rem;
    }}
    
    /* Button Enhancements */
    .stButton > button, .stDownloadButton > button {{
        background: linear-gradient(135deg, {theme['accent_primary']} 0%, {theme['accent_secondary']} 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s ease !important;
        box-shadow: {theme['shadow']} !important;
    }}
    
    .stButton > button:hover, .stDownloadButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: {theme['shadow']}, {theme['glow_effect']} !important;
    }}
    
    /* Table Styling */
    .stDataFrame {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: {theme['shadow']};
    }}
    
    .stDataFrame table {{
        font-variant-numeric: tabular-nums;
    }}
    
    .stDataFrame thead tr th {{
        background: {theme['bg_tertiary']} !important;
        color: {theme['text_primary']} !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.5px !important;
        padding: 16px 12px !important;
        border-bottom: 2px solid {theme['accent_primary']} !important;
    }}
    
    .stDataFrame tbody tr td {{
        color: {theme['text_secondary']} !important;
        padding: 12px !important;
        border-bottom: 1px solid {theme['panel_border']} !important;
    }}
    
    .stDataFrame tbody tr:hover td {{
        background: {theme['bg_tertiary']} !important;
    }}
    
    /* Progress and Loading States */
    .stProgress > div > div {{
        background: linear-gradient(90deg, {theme['accent_primary']}, {theme['accent_secondary']}) !important;
        border-radius: 10px !important;
    }}
    
    /* Custom Components */
    .risk-gauge {{
        width: 100%;
        height: 120px;
        border-radius: 12px;
        background: {theme['panel_bg']};
        border: 1px solid {theme['panel_border']};
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }}
    
    .performance-heatmap {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
        gap: 4px;
        margin: 16px 0;
    }}
    
    .heatmap-cell {{
        aspect-ratio: 1;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }}
    
    /* Responsive Design */
    @media (max-width: 768px) {{
        .metric-container {{
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
        }}
        
        .analytics-card {{
            padding: 16px;
            margin: 12px 0;
        }}
        
        .metric-value {{
            font-size: 1.5rem;
        }}
    }}
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {theme['bg_secondary']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {theme['accent_primary']};
        border-radius: 10px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {theme['accent_secondary']};
    }}
    </style>
    """

# =================================================================================
# ENHANCED DATA PROCESSING & VALIDATION
# =================================================================================

def validate_symbol(symbol: str) -> Tuple[bool, str]:
    """Enhanced symbol validation"""
    symbol = symbol.upper().strip()
    
    # Basic validation
    if not symbol or len(symbol) < 1:
        return False, "Symbol cannot be empty"
    
    if len(symbol) > 10:
        return False, "Symbol too long"
    
    # Common symbol corrections
    corrections = {
        "GOOGL": "GOOGL", "GOOG": "GOOGL",
        "META": "META", "FB": "META",
        "BRK.B": "BRK-B", "BRKB": "BRK-B",
        "SPX": "^GSPC", "SP500": "^GSPC",
        "NDX": "^NDX", "NASDAQ": "^IXIC"
    }
    
    corrected = corrections.get(symbol, symbol)
    return True, corrected

def get_enhanced_slope(symbol: str, volatility_adjustment: bool = True) -> float:
    """Get slope with optional volatility adjustment"""
    base_slope = SLOPES.get(symbol.upper(), DEFAULT_STOCK_SLOPE)
    
    if not volatility_adjustment:
        return float(base_slope)
    
    # Volatility-based adjustments (simplified)
    volatility_multipliers = {
        "TSLA": 1.2, "NVDA": 1.15, "META": 1.1,
        "^GSPC": 0.95, "SPY": 0.95, "QQQ": 1.05
    }
    
    multiplier = volatility_multipliers.get(symbol.upper(), 1.0)
    return float(base_slope * multiplier)

# =================================================================================
# UI COMPONENT BUILDERS
# =================================================================================

def create_metric_card(label: str, value: Any, change: Optional[float] = None, 
                      format_type: str = "number", precision: int = 2) -> str:
    """Create a professional metric display card"""
    
    # Format value based on type
    if format_type == "currency":
        formatted_value = f"${value:,.{precision}f}" if isinstance(value, (int, float)) else str(value)
    elif format_type == "percentage":
        formatted_value = f"{value:.{precision}%}" if isinstance(value, (int, float)) else str(value)
    elif format_type == "number":
        formatted_value = f"{value:,.{precision}f}" if isinstance(value, (int, float)) else str(value)
    else:
        formatted_value = str(value)
    
    # Format change indicator
    change_html = ""
    if change is not None:
        change_class = "metric-positive" if change > 0 else "metric-negative" if change < 0 else "metric-neutral"
        change_symbol = "▲" if change > 0 else "▼" if change < 0 else "●"
        change_html = f'<div class="metric-change {change_class}">{change_symbol} {abs(change):.{precision}f}</div>'
    
    return f"""
    <div class="metric-card">
        <div class="metric-value">{formatted_value}</div>
        <div class="metric-label">{label}</div>
        {change_html}
    </div>
    """

def create_status_indicator(status: str, label: str = "") -> str:
    """Create status indicator badges"""
    status_classes = {
        "bullish": "status-bullish",
        "bearish": "status-bearish",
        "neutral": "status-neutral"
    }
    
    icons = {
        "bullish": "🟢",
        "bearish": "🔴", 
        "neutral": "🟡"
    }
    
    css_class = status_classes.get(status.lower(), "status-neutral")
    icon = icons.get(status.lower(), "●")
    display_text = label or status.title()
    
    return f'<span class="{css_class} status-indicator">{icon} {display_text}</span>'

def render_analytics_card(title: str, content_func, subtitle: str = "", 
                         badge: str = "", height: Optional[int] = None):
    """Render a professional analytics card with content"""
    
    height_style = f"height: {height}px; overflow-y: auto;" if height else ""
    badge_html = f'<span class="status-indicator status-neutral" style="margin-left: 12px;">{badge}</span>' if badge else ""
    subtitle_html = f'<p class="text-muted" style="margin-bottom: 20px;">{subtitle}</p>' if subtitle else ""
    
    st.markdown(f"""
    <div class="analytics-card" style="{height_style}">
        <h4 style="margin-bottom: 8px;">{title}{badge_html}</h4>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)
    
    # Execute the content function
    content_func()
    
    st.markdown("</div>", unsafe_allow_html=True)

# =================================================================================
# INITIALIZATION & SETUP
# =================================================================================

def initialize_session_state():
    """Initialize session state with default values"""
    defaults = {
        "theme_mode": "Dark",
        "accent_color": "blue",
        "selected_symbol": "^GSPC",
        "risk_profile": "moderate",
        "show_advanced_metrics": True,
        "auto_refresh": False,
        "last_update": datetime.now(),
        "performance_history": [],
        "alert_settings": {
            "price_threshold": 0.02,
            "volume_spike": 2.0,
            "confluence_score": 0.75
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title=f"{APP_NAME} v{VERSION}",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': f"# {APP_NAME}\n\nProfessional market analytics platform for systematic trading strategies."
        }
    )

# =================================================================================
# MAIN SETUP FUNCTION
# =================================================================================

def setup_ui_framework():
    """Setup the complete UI framework"""
    setup_page_config()
    initialize_session_state()
    
    # Get theme configuration
    theme = get_advanced_theme(
        st.session_state.theme_mode, 
        st.session_state.accent_color
    )
    
    # Inject CSS
    st.markdown(inject_advanced_css(theme), unsafe_allow_html=True)
    
    return theme



