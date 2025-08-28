# app_part1.py
# MarketLens Pro v6 — Part 1: Core Infrastructure & Enhanced Theme System
# Professional trading analytics with maximum screen real estate utilization

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, time as dtime, date
import pytz
from typing import List, Tuple, Optional, Dict
import warnings
warnings.filterwarnings('ignore')

APP_NAME = "MarketLens Pro v6 — Elite Analytics Suite"

# ===============================
# ENHANCED THEME SYSTEM — Professional Trading Interface
# ===============================

def get_advanced_theme(mode: str) -> Dict:
    """Advanced theme system optimized for trading analytics"""
    
    if mode == "Dark":
        return {
            # Core colors
            "bg_primary": "#0a0b0d",
            "bg_secondary": "#1a1b1e", 
            "bg_tertiary": "#2a2d32",
            "surface": "rgba(42, 45, 50, 0.95)",
            "surface_elevated": "rgba(58, 62, 68, 0.98)",
            "surface_glass": "rgba(26, 27, 30, 0.85)",
            
            # Text hierarchy
            "text_primary": "#ffffff",
            "text_secondary": "#e0e2e5",
            "text_muted": "#9ca3af",
            "text_accent": "#60a5fa",
            
            # Status colors
            "success": "#10b981",
            "success_bg": "rgba(16, 185, 129, 0.1)",
            "danger": "#ef4444", 
            "danger_bg": "rgba(239, 68, 68, 0.1)",
            "warning": "#f59e0b",
            "warning_bg": "rgba(245, 158, 11, 0.1)",
            "info": "#3b82f6",
            "info_bg": "rgba(59, 130, 246, 0.1)",
            
            # Trading specific
            "bullish": "#10b981",
            "bearish": "#ef4444",
            "neutral": "#6b7280",
            
            # Borders and shadows
            "border": "rgba(255, 255, 255, 0.08)",
            "border_accent": "rgba(96, 165, 250, 0.3)",
            "shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)",
            "shadow_elevated": "0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)",
            
            # Gradients
            "gradient_primary": "linear-gradient(135deg, #1f2937 0%, #111827 100%)",
            "gradient_accent": "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
            "gradient_success": "linear-gradient(135deg, #10b981 0%, #059669 100%)",
            "gradient_danger": "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
        }
    else:  # Light theme
        return {
            # Core colors
            "bg_primary": "#ffffff",
            "bg_secondary": "#f8fafc",
            "bg_tertiary": "#f1f5f9",
            "surface": "rgba(255, 255, 255, 0.95)",
            "surface_elevated": "rgba(248, 250, 252, 0.98)",
            "surface_glass": "rgba(255, 255, 255, 0.85)",
            
            # Text hierarchy
            "text_primary": "#0f172a",
            "text_secondary": "#334155",
            "text_muted": "#64748b",
            "text_accent": "#2563eb",
            
            # Status colors
            "success": "#059669",
            "success_bg": "rgba(5, 150, 105, 0.1)",
            "danger": "#dc2626",
            "danger_bg": "rgba(220, 38, 38, 0.1)",
            "warning": "#d97706",
            "warning_bg": "rgba(217, 119, 6, 0.1)",
            "info": "#2563eb",
            "info_bg": "rgba(37, 99, 235, 0.1)",
            
            # Trading specific
            "bullish": "#059669",
            "bearish": "#dc2626",
            "neutral": "#6b7280",
            
            # Borders and shadows
            "border": "rgba(0, 0, 0, 0.08)",
            "border_accent": "rgba(37, 99, 235, 0.3)",
            "shadow": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
            "shadow_elevated": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            
            # Gradients
            "gradient_primary": "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)",
            "gradient_accent": "linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)",
            "gradient_success": "linear-gradient(135deg, #059669 0%, #047857 100%)",
            "gradient_danger": "linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)",
        }

def generate_professional_css(theme: Dict) -> str:
    """Generate professional CSS optimized for trading analytics"""
    
    return f"""
    <style>
    /* ===== GLOBAL RESET & BASE ===== */
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    
    html, body, [data-testid="stAppViewContainer"] {{
        background: {theme['bg_primary']};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        color: {theme['text_primary']};
        line-height: 1.5;
    }}
    
    /* ===== SIDEBAR OPTIMIZATION ===== */
    [data-testid="stSidebar"] {{
        background: {theme['surface_glass']};
        border-right: 1px solid {theme['border']};
        backdrop-filter: blur(20px) saturate(180%);
        width: 280px !important;
        min-width: 280px !important;
    }}
    
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }}
    
    /* ===== MAIN CONTENT AREA ===== */
    .main .block-container {{
        padding: 1rem 2rem;
        max-width: none;
    }}
    
    /* ===== CUSTOM COMPONENTS ===== */
    .ml-metric-card {{
        background: {theme['surface_elevated']};
        border: 1px solid {theme['border']};
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: {theme['shadow']};
        backdrop-filter: blur(10px);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .ml-metric-card:hover {{
        border-color: {theme['border_accent']};
        box-shadow: {theme['shadow_elevated']};
        transform: translateY(-1px);
    }}
    
    .ml-metric-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: {theme['gradient_accent']};
        opacity: 0;
        transition: opacity 0.2s ease;
    }}
    
    .ml-metric-card:hover::before {{
        opacity: 1;
    }}
    
    .ml-metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {theme['text_primary']};
        line-height: 1.2;
        margin: 0.5rem 0;
    }}
    
    .ml-metric-label {{
        font-size: 0.875rem;
        font-weight: 600;
        color: {theme['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }}
    
    .ml-metric-change {{
        font-size: 0.875rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }}
    
    .ml-metric-change.positive {{
        color: {theme['success']};
    }}
    
    .ml-metric-change.negative {{
        color: {theme['danger']};
    }}
    
    .ml-grid {{
        display: grid;
        gap: 1rem;
        margin: 1rem 0;
    }}
    
    .ml-grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
    .ml-grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
    .ml-grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
    .ml-grid-auto {{ grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    
    /* ===== STATUS INDICATORS ===== */
    .ml-status-bullish {{
        color: {theme['bullish']};
        background: {theme['success_bg']};
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .ml-status-bearish {{
        color: {theme['bearish']};
        background: {theme['danger_bg']};
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .ml-status-neutral {{
        color: {theme['neutral']};
        background: rgba(107, 114, 128, 0.1);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    /* ===== TABLE ENHANCEMENTS ===== */
    .stDataFrame {{
        border: 1px solid {theme['border']};
        border-radius: 8px;
        overflow: hidden;
        box-shadow: {theme['shadow']};
    }}
    
    .stDataFrame [data-testid="stTable"] {{
        background: {theme['surface']};
    }}
    
    .stDataFrame table {{
        font-size: 0.875rem;
        font-variant-numeric: tabular-nums;
    }}
    
    .stDataFrame th {{
        background: {theme['bg_tertiary']} !important;
        color: {theme['text_secondary']} !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em;
        padding: 0.75rem !important;
        border-bottom: 1px solid {theme['border']} !important;
    }}
    
    .stDataFrame td {{
        padding: 0.75rem !important;
        border-bottom: 1px solid {theme['border']} !important;
        color: {theme['text_secondary']} !important;
    }}
    
    /* ===== BUTTON ENHANCEMENTS ===== */
    .stButton > button, .stDownloadButton > button {{
        background: {theme['gradient_accent']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.625rem 1.25rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        box-shadow: {theme['shadow']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .stButton > button:hover, .stDownloadButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: {theme['shadow_elevated']};
        filter: brightness(1.05);
    }}
    
    /* ===== INPUT ENHANCEMENTS ===== */
    .stSelectbox > div > div, .stNumberInput > div > div > input, .stTextInput > div > div > input {{
        background: {theme['surface']} !important;
        border: 1px solid {theme['border']} !important;
        border-radius: 6px !important;
        color: {theme['text_primary']} !important;
        font-size: 0.875rem !important;
    }}
    
    .stSelectbox > div > div:focus-within, .stNumberInput > div > div:focus-within, .stTextInput > div > div:focus-within {{
        border-color: {theme['border_accent']} !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }}
    
    /* ===== TABS ENHANCEMENT ===== */
    .stTabs [data-baseweb="tab-list"] {{
        background: {theme['surface']};
        border-radius: 8px;
        padding: 0.25rem;
        border: 1px solid {theme['border']};
        gap: 0.25rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 6px;
        color: {theme['text_muted']};
        font-weight: 500;
        padding: 0.75rem 1rem;
        transition: all 0.2s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {theme['gradient_accent']} !important;
        color: white !important;
        font-weight: 600;
    }}
    
    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 1024px) {{
        .ml-grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
        .ml-grid-3 {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    
    @media (max-width: 768px) {{
        .ml-grid-4, .ml-grid-3, .ml-grid-2 {{ grid-template-columns: 1fr; }}
        .main .block-container {{ padding: 1rem; }}
        [data-testid="stSidebar"] {{ width: 250px !important; min-width: 250px !important; }}
    }}
    
    /* ===== UTILITY CLASSES ===== */
    .ml-text-success {{ color: {theme['success']}; }}
    .ml-text-danger {{ color: {theme['danger']}; }}
    .ml-text-warning {{ color: {theme['warning']}; }}
    .ml-text-muted {{ color: {theme['text_muted']}; }}
    .ml-bg-success {{ background: {theme['success_bg']}; }}
    .ml-bg-danger {{ background: {theme['danger_bg']}; }}
    .ml-bg-warning {{ background: {theme['warning_bg']}; }}
    
    .ml-font-mono {{
        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
        font-variant-numeric: tabular-nums;
    }}
    
    .ml-text-lg {{ font-size: 1.125rem; font-weight: 600; }}
    .ml-text-sm {{ font-size: 0.875rem; }}
    .ml-text-xs {{ font-size: 0.75rem; }}
    
    /* ===== HIDE STREAMLIT ELEMENTS ===== */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
    
    .stApp > header {{ display: none; }}
    .stDeployButton {{ display: none; }}
    
    </style>
    """

def inject_professional_theme(mode: str = "Dark"):
    """Inject the professional theme into the Streamlit app"""
    theme = get_advanced_theme(mode)
    css = generate_professional_css(theme)
    st.markdown(css, unsafe_allow_html=True)
    return theme

# ===============================
# TIMEZONE UTILITIES (CT-centric)
# ===============================

CT = pytz.timezone("America/Chicago")
ET = pytz.timezone("America/New_York")
UTC = pytz.UTC

def as_ct(ts: datetime) -> datetime:
    """Convert timestamp to Central Time"""
    if ts.tzinfo is None:
        ts = UTC.localize(ts)
    return ts.astimezone(CT)

def format_ct(ts: datetime, with_date=True, short=False) -> str:
    """Format timestamp in Central Time"""
    ts_ct = as_ct(ts)
    if short:
        return ts_ct.strftime("%H:%M")
    return ts_ct.strftime("%Y-%m-%d %H:%M CT" if with_date else "%H:%M CT")

def rth_slots_ct_dt(proj_date: date, start="08:30", end="14:30") -> List[datetime]:
    """Generate RTH time slots in Central Time"""
    h1, m1 = map(int, start.split(":"))
    h2, m2 = map(int, end.split(":"))
    start_dt = CT.localize(datetime.combine(proj_date, dtime(h1, m1)))
    end_dt = CT.localize(datetime.combine(proj_date, dtime(h2, m2)))
    idx = pd.date_range(start=start_dt, end=end_dt, freq="30min", tz=CT)
    return list(idx.to_pydatetime())

def get_trading_session_info() -> Dict:
    """Get current trading session information"""
    now_ct = datetime.now(CT)
    current_time = now_ct.time()
    
    # Define session times in CT
    sessions = {
        "pre_market": (dtime(7, 0), dtime(8, 30)),
        "rth": (dtime(8, 30), dtime(15, 0)),
        "after_hours": (dtime(15, 0), dtime(20, 0)),
        "overnight": (dtime(20, 0), dtime(7, 0))  # Next day
    }
    
    current_session = "closed"
    for session_name, (start_time, end_time) in sessions.items():
        if session_name == "overnight":
            if current_time >= start_time or current_time < end_time:
                current_session = session_name
                break
        else:
            if start_time <= current_time < end_time:
                current_session = session_name
                break
    
    return {
        "current_session": current_session,
        "current_time_ct": now_ct,
        "formatted_time": format_ct(now_ct, with_date=True, short=False),
        "is_trading_day": now_ct.weekday() < 5,  # Monday=0, Friday=4
        "sessions": sessions
    }

# ===============================
# ENHANCED UI COMPONENTS
# ===============================

class UIComponents:
    """Professional UI components for trading analytics"""
    
    @staticmethod
    def metric_card(title: str, value: str, change: str = None, change_positive: bool = True, 
                   subtitle: str = None, icon: str = None):
        """Create a professional metric card"""
        change_class = "positive" if change_positive else "negative"
        icon_html = f"<span style='margin-right: 0.5rem;'>{icon}</span>" if icon else ""
        change_html = f"<div class='ml-metric-change {change_class}'>{change}</div>" if change else ""
        subtitle_html = f"<div class='ml-text-sm ml-text-muted' style='margin-top: 0.25rem;'>{subtitle}</div>" if subtitle else ""
        
        st.markdown(f"""
        <div class="ml-metric-card">
            <div class="ml-metric-label">{icon_html}{title}</div>
            <div class="ml-metric-value">{value}</div>
            {change_html}
            {subtitle_html}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def status_badge(text: str, status: str = "neutral"):
        """Create a status badge"""
        return f"<span class='ml-status-{status}'>{text}</span>"
    
    @staticmethod
    def grid_container(columns: int = 3):
        """Create a grid container"""
        return f"<div class='ml-grid ml-grid-{columns}'>"
    
    @staticmethod
    def close_container():
        """Close any container"""
        return "</div>"

# ===============================
# MARKET DATA SLOPES & CONSTANTS
# ===============================

ENHANCED_SLOPES = {
    "SPX": {"Skyline": +0.268, "Baseline": -0.235},
    "AAPL": 0.0155, "MSFT": 0.0541, "NVDA": 0.0086, "AMZN": 0.0139, 
    "GOOGL": 0.0122, "TSLA": 0.0285, "META": 0.0674, "NFLX": 0.0230,
    "QQQ": 0.0180, "SPY": 0.0125, "IWM": 0.0095, "VXX": -0.0220,
    "GLD": 0.0085, "TLT": 0.0065, "UNG": 0.0195, "USO": 0.0175
}

DEFAULT_STOCK_SLOPE = 0.0150

# Market regime indicators
MARKET_REGIMES = {
    "BULL": {"vix_threshold": 20, "color": "success"},
    "BEAR": {"vix_threshold": 30, "color": "danger"},
    "NEUTRAL": {"vix_threshold": 25, "color": "warning"}
}

def get_slope_for_symbol(sym: str) -> float:
    """Get slope for symbol with enhanced lookup"""
    s = sym.upper().strip()
    
    # Direct lookup
    if s in ENHANCED_SLOPES:
        slope_data = ENHANCED_SLOPES[s]
        return float(slope_data) if isinstance(slope_data, (int, float)) else float(slope_data.get("Skyline", DEFAULT_STOCK_SLOPE))
    
    # Handle common aliases
    aliases = {
        "GOOG": "GOOGL", 
        "BRK.B": "BRK-B", 
        "BRK-B": "BRK-B",
        "^GSPC": "SPX",
        "^VIX": "VXX"
    }
    
    if s in aliases and aliases[s] in ENHANCED_SLOPES:
        slope_data = ENHANCED_SLOPES[aliases[s]]
        return float(slope_data) if isinstance(slope_data, (int, float)) else float(slope_data.get("Skyline", DEFAULT_STOCK_SLOPE))
    
    return DEFAULT_STOCK_SLOPE

def calculate_dynamic_slope(symbol: str, historical_data: pd.DataFrame) -> float:
    """Calculate dynamic slope based on recent price action"""
    if historical_data.empty or len(historical_data) < 20:
        return get_slope_for_symbol(symbol)
    
    try:
        # Calculate 20-period ATR-normalized slope
        close = historical_data['Close']
        returns = close.pct_change().dropna()
        
        # ATR-based normalization
        high_low = historical_data['High'] - historical_data['Low']
        high_close = abs(historical_data['High'] - close.shift(1))
        low_close = abs(historical_data['Low'] - close.shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean().iloc[-1]
        
        # Recent volatility adjusted slope
        recent_vol = returns.tail(20).std() * np.sqrt(252)  # Annualized
        base_slope = get_slope_for_symbol(symbol)
        
        # Adjust slope based on recent volatility
        volatility_adjustment = min(2.0, max(0.5, recent_vol / 0.25))  # Scale factor
        
        return base_slope * volatility_adjustment
        
    except Exception:
        return get_slope_for_symbol(symbol)


# Part 1 includes: Enhanced theme system, timezone utilities, UI components, and enhanced slopes/constants.
