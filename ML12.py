# app.py - SPX Prophet - Lean & Fixed Version
# Enterprise Trading Analytics Platform
# SPX Anchors | BC Forecast | Plan Card

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
NEUTRAL_BAND_DEFAULT = 0.10  # 10% from fan center

# Data lookback for reliability
ES_LOOKBACK_DAYS = 30

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION & STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SPX Prophet - Enterprise Trading Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enterprise UI System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --primary-500: #3b82f6;
    --success-500: #22c55e;
    --danger-500: #ef4444;
    --warning-500: #f59e0b;
    --gray-100: #f1f5f9;
    --gray-200: #e2e8f0;
    --gray-500: #64748b;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-tertiary: #64748b;
    --bg-primary: #ffffff;
    --border-light: #e2e8f0;
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-success: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
    --gradient-danger: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
    --gradient-warning: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    --gradient-neutral: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

html, body, [class*="css"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

.main .block-container {
    padding: 1.5rem !important;
    max-width: 100% !important;
}

.enterprise-card {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 16px;
    padding: 20px;
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
    margin-bottom: 1.5rem;
}

.enterprise-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-primary);
}

.metric-card {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 12px;
    padding: 16px;
    box-shadow: var(--shadow-md);
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.metric-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.metric-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 600;
    background: var(--gradient-primary);
    color: white;
}

.metric-icon.success { background: var(--gradient-success); }
.metric-icon.danger { background: var(--gradient-danger); }
.metric-icon.warning { background: var(--gradient-warning); }
.metric-icon.neutral { background: var(--gradient-neutral); }

.metric-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 4px 0 2px 0;
    font-family: 'JetBrains Mono', monospace;
}

.metric-subtext {
    font-size: 0.7rem;
    color: var(--text-tertiary);
    font-weight: 500;
    margin-top: auto;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    border: 1px solid;
}

.badge-up {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-color: var(--success-500);
    color: var(--success-500);
}

.badge-down {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border-color: var(--danger-500);
    color: var(--danger-500);
}

.badge-neutral {
    background: var(--gray-100);
    border-color: var(--gray-500);
    color: var(--gray-500);
}

.main-header {
    background: var(--bg-primary);
    border: 2px solid var(--border-light);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-lg);
    position: relative;
}

.main-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-primary);
}

.header-title {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: 0;
}

.header-subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin: 6px 0 0 0;
    font-weight: 500;
}

.stButton > button {
    background: var(--gradient-primary) !important;
    border: none !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    height: 40px !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: var(--gray-100) !important;
    border: 2px solid var(--border-light) !important;
    border-radius: 12px !important;
    padding: 6px !important;
    margin-bottom: 24px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--text-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
}

.stTabs [aria-selected="true"] {
    background: var(--gradient-primary) !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CORE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def fmt_ct(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return CT_TZ.localize(dt)
    return dt.astimezone(CT_TZ)

def get_business_day_before(target_date: date) -> date:
    """Get the last business day before target_date, handling weekends properly."""
    current = target_date - timedelta(days=1)
    while current.weekday() >= 5:  # Saturday=5, Sunday=6
        current -= timedelta(days=1)
    return current

def rth_slots_ct(target_date: date) -> List[datetime]:
    start_dt = fmt_ct(datetime.combine(target_date, time(8, 30)))
    end_dt = fmt_ct(datetime.combine(target_date, time(14, 30)))
    slots, current = [], start_dt
    while current <= end_dt:
        slots.append(current)
        current += timedelta(minutes=30)
    return slots

def count_effective_blocks(start: datetime, end: datetime) -> float:
    if end <= start:
        return 0.0
    return (end - start).total_seconds() / 1800.0  # 30 minutes = 1800 seconds

def ensure_ohlc_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns]
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
            return pd.DataFrame()
    return df

def normalize_to_ct(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = ensure_ohlc_cols(df)
    if df.empty:
        return df
    if df.index.tz is None:
        df.index = df.index.tz_localize("US/Eastern")
    df.index = df.index.tz_convert(CT_TZ)
    return df

@st.cache_data(ttl=300, show_spinner=False)
def fetch_data_with_lookback(symbol: str, target_date: date, lookback_days: int = ES_LOOKBACK_DAYS) -> pd.DataFrame:
    """Fetch data with extended lookback for reliability."""
    try:
        start_date = target_date - timedelta(days=lookback_days)
        end_date = target_date + timedelta(days=2)
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            interval="30m",
            prepost=True,
            auto_adjust=False,
            back_adjust=False
        )
        
        if df.empty:
            # Try 1m data and resample
            df = ticker.history(
                period="30d",
                interval="1m",
                prepost=True,
                auto_adjust=False,
                back_adjust=False
            )
            if not df.empty:
                df = df.resample("30T", label="right").agg({
                    'Open': 'first',
                    'High': 'max', 
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
        
        return normalize_to_ct(df)
    except Exception:
        return pd.DataFrame()

# ═══════════════════════════════════════════════════════════════════════════════
# SPX ANCHOR & OFFSET CALCULATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_spx_anchor(prev_business_day: date) -> Tuple[Optional[float], Optional[datetime]]:
    """Get SPX anchor from 3:00 PM CT on previous business day."""
    spx_data = fetch_data_with_lookback("^GSPC", prev_business_day)
    if spx_data.empty:
        return None, None
    
    target_time = fmt_ct(datetime.combine(prev_business_day, time(15, 0)))
    day_data = spx_data.loc[spx_data.index.date == prev_business_day]
    
    if day_data.empty:
        return None, None
    
    # Find last close <= 3:00 PM
    before_3pm = day_data.loc[:target_time]
    if before_3pm.empty:
        return None, None
    
    anchor_close = float(before_3pm["Close"].iloc[-1])
    anchor_time = before_3pm.index[-1].to_pydatetime()
    
    return anchor_close, fmt_ct(anchor_time)

def calculate_es_spx_offset(prev_business_day: date) -> Optional[float]:
    """Calculate ES-SPX offset using 2:30 PM prices from previous business day."""
    target_time = fmt_ct(datetime.combine(prev_business_day, time(14, 30)))
    
    # Get SPX at 2:30 PM
    spx_data = fetch_data_with_lookback("^GSPC", prev_business_day)
    if spx_data.empty:
        return None
    
    spx_day = spx_data.loc[spx_data.index.date == prev_business_day]
    if spx_day.empty:
        return None
    
    spx_before_230 = spx_day.loc[:target_time]
    if spx_before_230.empty:
        return None
    
    spx_price = float(spx_before_230["Close"].iloc[-1])
    
    # Get ES at 2:30 PM
    es_data = fetch_data_with_lookback("ES=F", prev_business_day)
    if es_data.empty:
        return None
    
    es_day = es_data.loc[es_data.index.date == prev_business_day]
    if es_day.empty:
        return None
    
    es_before_230 = es_day.loc[:target_time]
    if es_before_230.empty:
        return None
    
    es_price = float(es_before_230["Close"].iloc[-1])
    
    # Offset = ES - SPX (to convert ES to SPX frame later)
    return es_price - spx_price

# ═══════════════════════════════════════════════════════════════════════════════
# FAN PROJECTION & TOUCH DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_slopes() -> Tuple[float, float]:
    top_slope = float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT))
    bottom_slope = float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT))
    return top_slope, bottom_slope

def project_fan_levels(anchor_close: float, anchor_time: datetime, target_date: date) -> pd.DataFrame:
    top_slope, bottom_slope = get_current_slopes()
    rth_slots = rth_slots_ct(target_date)
    
    projections = []
    for slot_time in rth_slots:
        blocks = count_effective_blocks(anchor_time, slot_time)
        top_level = anchor_close + (top_slope * blocks)
        bottom_level = anchor_close - (bottom_slope * blocks)
        
        projections.append({
            "DateTime": slot_time,
            "Time": slot_time.strftime("%H:%M"),
            "Top": round(top_level, 2),
            "Bottom": round(bottom_level, 2),
            "Fan_Width": round(top_level - bottom_level, 2),
        })
    
    return pd.DataFrame(projections)

def determine_bias(price: float, top_level: float, bottom_level: float) -> str:
    if price > top_level:
        return "UP"
    if price < bottom_level:
        return "DOWN"
    
    # Neutral band: 10% from center
    fan_center = (top_level + bottom_level) / 2
    fan_width = top_level - bottom_level
    neutral_threshold = fan_width * NEUTRAL_BAND_DEFAULT
    
    if abs(price - fan_center) <= neutral_threshold:
        return "NEUTRAL"
    
    return "UP" if price > fan_center else "DOWN"

def detect_overnight_touches(prev_business_day: date, proj_day: date, 
                           anchor_close: float, anchor_time: datetime, 
                           offset: float) -> List[Dict]:
    """Detect overnight fan touches using ES data converted to SPX frame."""
    
    # Get overnight ES data (5 PM prev day to 8:30 AM proj day)
    start_time = fmt_ct(datetime.combine(prev_business_day, time(17, 0)))
    end_time = fmt_ct(datetime.combine(proj_day, time(8, 30)))
    
    es_data = fetch_data_with_lookback("ES=F", proj_day)
    if es_data.empty:
        return []
    
    # Filter to overnight period
    overnight_data = es_data.loc[start_time:end_time]
    if overnight_data.empty:
        return []
    
    touches = []
    top_slope, bottom_slope = get_current_slopes()
    
    for timestamp, bar in overnight_data.iterrows():
        # Convert ES to SPX frame
        es_high = float(bar["High"]) - offset
        es_low = float(bar["Low"]) - offset
        es_close = float(bar["Close"]) - offset
        
        # Calculate fan levels at this time
        blocks = count_effective_blocks(anchor_time, timestamp)
        fan_top = anchor_close + (top_slope * blocks)
        fan_bottom = anchor_close - (bottom_slope * blocks)
        
        # Check for real touches (candle range intersects fan levels)
        # NOT when entire candle is above/below fan
        touched_top = False
        touched_bottom = False
        
        # Touch top: candle high >= fan_top AND candle low < fan_top
        if es_high >= fan_top and es_low < fan_top:
            touched_top = True
        
        # Touch bottom: candle low <= fan_bottom AND candle high > fan_bottom  
        if es_low <= fan_bottom and es_high > fan_bottom:
            touched_bottom = True
        
        if touched_top or touched_bottom:
            bias = determine_bias(es_close, fan_top, fan_bottom)
            
            touches.append({
                "Time": timestamp.strftime("%H:%M"),
                "DateTime": timestamp,
                "SPX_High": round(es_high, 2),
                "SPX_Low": round(es_low, 2), 
                "SPX_Close": round(es_close, 2),
                "Fan_Top": round(fan_top, 2),
                "Fan_Bottom": round(fan_bottom, 2),
                "Touched": "Top" if touched_top else "Bottom",
                "Bias": bias
            })
    
    return touches

# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY TABLE BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_strategy_table(anchor_close: float, anchor_time: datetime, 
                        target_date: date, spx_rth_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    fan_df = project_fan_levels(anchor_close, anchor_time, target_date)
    
    strategy_rows = []
    
    for _, row in fan_df.iterrows():
        slot_time = row["Time"]
        top_level = row["Top"]
        bottom_level = row["Bottom"]
        fan_width = row["Fan_Width"]
        
        # Try to get actual SPX price
        actual_price = None
        if spx_rth_data is not None and not spx_rth_data.empty:
            slot_datetime = row["DateTime"]
            if slot_datetime in spx_rth_data.index:
                actual_price = float(spx_rth_data.loc[slot_datetime, "Close"])
        
        if actual_price is not None:
            bias = determine_bias(actual_price, top_level, bottom_level)
            price_display = f"{actual_price:.2f}"
            
            # Entry signal
            if bias == "UP":
                entry_signal = "Long breakout" if actual_price > top_level else "Long on dip"
            elif bias == "DOWN": 
                entry_signal = "Short breakdown" if actual_price < bottom_level else "Short on rally"
            else:
                entry_signal = "Wait for breakout"
        else:
            bias = "NO DATA"
            price_display = "—"
            entry_signal = "Fan projection only"
        
        slot_display = "⭐ 8:30" if slot_time == "08:30" else slot_time
        
        strategy_rows.append({
            "Slot": slot_display,
            "Time": slot_time,
            "Price": price_display,
            "Bias": bias,
            "Top": top_level,
            "Bottom": bottom_level,
            "Width": fan_width,
            "Entry_Signal": entry_signal
        })
    
    return pd.DataFrame(strategy_rows)

# ═══════════════════════════════════════════════════════════════════════════════
# BC FORECAST FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def project_contract_line(bounce1_time: datetime, bounce1_price: float,
                         bounce2_time: datetime, bounce2_price: float,
                         target_date: date, line_label: str) -> Tuple[pd.DataFrame, float]:
    blocks = count_effective_blocks(bounce1_time, bounce2_time)
    slope = (bounce2_price - bounce1_price) / blocks if blocks > 0 else 0.0
    
    rth_slots = rth_slots_ct(target_date)
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
                               target_date: date) -> str:
    duration1 = count_effective_blocks(bounce1_time, high1_time)
    duration2 = count_effective_blocks(bounce2_time, high2_time)
    
    durations = [d for d in [duration1, duration2] if d > 0]
    if not durations:
        return "N/A"
    
    median_duration_hours = np.median(durations)
    exit_time = bounce2_time + timedelta(hours=median_duration_hours)
    
    # Find closest RTH slot
    rth_slots = rth_slots_ct(target_date)
    for slot in rth_slots:
        if slot >= exit_time:
            return slot.strftime("%H:%M")
    
    return "After RTH"

# ═══════════════════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

def create_metric_card(title: str, value: str, subtext: str = "", icon: str = "📊", 
                      card_type: str = "primary") -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-header">
            <div class="metric-icon {card_type}">{icon}</div>
            <div class="metric-title">{title}</div>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-subtext">{subtext}</div>
    </div>
    """

def create_status_badge(text: str, status: str = "neutral") -> str:
    return f'<span class="status-badge badge-{status}">{text}</span>'

def create_header_section(title: str, subtitle: str = "") -> str:
    return f"""
    <div class="main-header">
        <h1 class="header-title">{title}</h1>
        {f'<p class="header-subtitle">{subtitle}</p>' if subtitle else ''}
    </div>
    """

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def render_main_header():
    current_time = datetime.now(CT_TZ)
    
    st.markdown(create_header_section(
        "⚡ SPX Prophet",
        "Enterprise Trading Analytics - SPX Anchors | BC Forecast | Plan Card"
    ), unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        time_str = current_time.strftime("%H:%M:%S")
        date_str = current_time.strftime("%a, %b %d")
        st.markdown(create_metric_card(
            "Current Time (CT)", 
            time_str,
            date_str,
            "🕒",
            "primary"
        ), unsafe_allow_html=True)
    
    with col2:
        is_weekday = current_time.weekday() < 5
        market_open = current_time.replace(hour=8, minute=30, second=0, microsecond=0)
        market_close = current_time.replace(hour=14, minute=30, second=0, microsecond=0)
        is_open = is_weekday and (market_open <= current_time <= market_close)
        
        status_text = "OPEN" if is_open else "CLOSED"
        status_type = "success" if is_open else "danger"
        
        st.markdown(create_metric_card(
            "Market Status",
            status_text,
            "RTH: 08:30-14:30 CT",
            "📊",
            status_type
        ), unsafe_allow_html=True)
    
    with col3:
        top_slope, bottom_slope = get_current_slopes()
        slope_text = f"+{top_slope:.3f}"
        
        st.markdown(create_metric_card(
            "SPX Slopes /30m",
            slope_text,
            f"Bot: -{bottom_slope:.3f}",
            "📐",
            "neutral"
        ), unsafe_allow_html=True)
    
    with col4:
        try:
            test_data = fetch_data_with_lookback("^GSPC", current_time.date())
            connectivity = "CONNECTED" if not test_data.empty else "LIMITED"
            conn_type = "success" if not test_data.empty else "warning"
        except:
            connectivity = "ERROR"
            conn_type = "danger"
        
        st.markdown(create_metric_card(
            "Data Status",
            connectivity,
            f"30-day lookback",
            "🔗",
            conn_type
        ), unsafe_allow_html=True)

def render_sidebar_controls():
    st.sidebar.title("🎛️ Controls")
    
    today_ct = datetime.now(CT_TZ).date()
    
    prev_day = st.sidebar.date_input(
        "Previous Trading Day",
        value=get_business_day_before(today_ct)
    )
    
    proj_day = st.sidebar.date_input(
        "Projection Day", 
        value=today_ct
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("✍️ Manual Anchor")
    
    use_manual = st.sidebar.checkbox(
        "Override with manual 3:00 PM close",
        value=False
    )
    
    manual_value = st.sidebar.number_input(
        "Manual Anchor Close",
        value=6400.00,
        step=0.25,
        format="%.2f",
        disabled=not use_manual
    )
    
    st.sidebar.markdown("---")
    
    refresh_anchors = st.sidebar.button(
        "🔮 Refresh SPX Anchors",
        type="primary",
        use_container_width=True
    )
    
    return {
        "prev_day": prev_day,
        "proj_day": proj_day,
        "use_manual": use_manual,
        "manual_value": manual_value,
        "refresh_anchors": refresh_anchors
    }

def render_spx_anchors_tab(controls: Dict):
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0;">🎯 SPX Anchors - Fan Analysis & Overnight Touches</h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Previous day 3PM anchor with ES overnight touch detection converted to SPX frame
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if controls["refresh_anchors"] or "anchors_data" not in st.session_state:
        with st.spinner("Building SPX anchor analysis..."):
            try:
                if controls["use_manual"]:
                    anchor_close = float(controls["manual_value"])
                    anchor_time = fmt_ct(datetime.combine(controls["prev_day"], time(15, 0)))
                    anchor_source = "Manual"
                else:
                    anchor_close, anchor_time = get_spx_anchor(controls["prev_day"])
                    if anchor_close is None:
                        st.error("❌ Could not get SPX anchor for previous day")
                        return
                    anchor_source = "^GSPC"
                
                # Calculate ES-SPX offset
                offset = calculate_es_spx_offset(controls["prev_day"])
                if offset is None:
                    st.warning("⚠️ Could not calculate ES-SPX offset, overnight analysis limited")
                    offset = 0.0
                
                # Get projection day SPX data
                spx_data = fetch_data_with_lookback("^GSPC", controls["proj_day"])
                rth_data = spx_data.loc[spx_data.index.date == controls["proj_day"]] if not spx_data.empty else pd.DataFrame()
                
                if not rth_data.empty:
                    rth_data = rth_data.between_time(RTH_START, RTH_END)
                
                # Build strategy table
                strategy_df = build_strategy_table(anchor_close, anchor_time, controls["proj_day"], rth_data)
                
                # Detect overnight touches
                touches = detect_overnight_touches(
                    controls["prev_day"], controls["proj_day"], 
                    anchor_close, anchor_time, offset
                )
                
                st.session_state["anchors_data"] = {
                    "anchor_close": anchor_close,
                    "anchor_time": anchor_time,
                    "anchor_source": anchor_source,
                    "strategy_df": strategy_df,
                    "touches": touches,
                    "offset": offset
                }
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                return
    
    if "anchors_data" in st.session_state:
        data = st.session_state["anchors_data"]
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Anchor Close",
                f"{data['anchor_close']:.2f}",
                f"{data['anchor_source']} @ 3:00 PM",
                "⚓",
                "primary"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                "ES-SPX Offset",
                f"{data['offset']:+.2f}",
                "From 2:30 PM prices",
                "🔄",
                "neutral"
            ), unsafe_allow_html=True)
        
        with col3:
            touches_count = len(data['touches'])
            st.markdown(create_metric_card(
                "Overnight Touches",
                str(touches_count),
                "ES converted to SPX",
                "👆",
                "warning" if touches_count > 0 else "neutral"
            ), unsafe_allow_html=True)
        
        with col4:
            df = data['strategy_df']
            row_830 = df[df['Time'] == '08:30']
            current_bias = row_830['Bias'].iloc[0] if not row_830.empty else "N/A"
            bias_type = "success" if current_bias == "UP" else "danger" if current_bias == "DOWN" else "neutral"
            
            st.markdown(create_metric_card(
                "8:30 Bias",
                current_bias,
                "Key decision point",
                "🧭",
                bias_type
            ), unsafe_allow_html=True)
        
        # Overnight touches table
        if data['touches']:
            st.markdown("### 🌙 Overnight Fan Touches (ES→SPX Converted)")
            touches_df = pd.DataFrame(data['touches'])
            st.dataframe(
                touches_df[["Time", "SPX_Close", "Fan_Top", "Fan_Bottom", "Touched", "Bias"]],
                use_container_width=True,
                hide_index=True
            )
        
        # Strategy table
        st.markdown("### 📊 RTH Strategy Table")
        st.dataframe(
            data['strategy_df'],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("👆 Click 'Refresh SPX Anchors' in the sidebar")

def render_bc_forecast_tab(controls: Dict):
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0;">🔮 BC Forecast - Contract Projections</h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Project NY session from exactly 2 overnight bounces
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate overnight slots
    asia_start = fmt_ct(datetime.combine(controls["prev_day"], time(19, 0)))
    europe_end = fmt_ct(datetime.combine(controls["proj_day"], time(7, 0)))
    
    session_slots = []
    current_slot = asia_start
    while current_slot <= europe_end:
        session_slots.append(current_slot)
        current_slot += timedelta(minutes=30)
    
    slot_options = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]
    
    with st.form("bc_form"):
        st.markdown("### 📍 Underlying Bounces")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Bounce #1**")
            b1_time = st.selectbox("Time", slot_options, index=0)
            b1_price = st.number_input("SPX Price", value=6500.00, step=0.25, format="%.2f")
        
        with col2:
            st.markdown("**Bounce #2**")
            b2_time = st.selectbox("Time ", slot_options, index=min(6, len(slot_options)-1))
            b2_price = st.number_input("SPX Price ", value=6512.00, step=0.25, format="%.2f")
        
        st.markdown("### 📋 Contract A")
        
        col3, col4 = st.columns(2)
        
        with col3:
            ca_symbol = st.text_input("Contract Symbol", value="6525c")
            ca_b1_price = st.number_input("Price at Bounce #1", value=10.00, step=0.05, format="%.2f")
            ca_b2_price = st.number_input("Price at Bounce #2", value=12.50, step=0.05, format="%.2f")
        
        with col4:
            ca_h1_time = st.selectbox("High #1 Time", slot_options, index=min(2, len(slot_options)-1))
            ca_h1_price = st.number_input("High #1 Price", value=14.00, step=0.05, format="%.2f")
            ca_h2_time = st.selectbox("High #2 Time", slot_options, index=min(8, len(slot_options)-1))
            ca_h2_price = st.number_input("High #2 Price", value=16.00, step=0.05, format="%.2f")
        
        submitted = st.form_submit_button("🚀 Generate Projections", type="primary")
    
    if submitted:
        try:
            b1_dt = fmt_ct(datetime.strptime(b1_time, "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(b2_time, "%Y-%m-%d %H:%M"))
            
            if b2_dt <= b1_dt:
                st.error("❌ Bounce #2 must be after Bounce #1")
                return
            
            # Project underlying
            underlying_df, underlying_slope = project_contract_line(
                b1_dt, b1_price, b2_dt, b2_price, controls["proj_day"], "SPX_Projected"
            )
            
            # Project contract entry line
            ca_entry_df, ca_entry_slope = project_contract_line(
                b1_dt, ca_b1_price, b2_dt, ca_b2_price, controls["proj_day"], f"{ca_symbol}_Entry"
            )
            
            # Project contract exit line
            ca_h1_dt = fmt_ct(datetime.strptime(ca_h1_time, "%Y-%m-%d %H:%M"))
            ca_h2_dt = fmt_ct(datetime.strptime(ca_h2_time, "%Y-%m-%d %H:%M"))
            
            ca_exit_df, ca_exit_slope = project_contract_line(
                ca_h1_dt, ca_h1_price, ca_h2_dt, ca_h2_price, controls["proj_day"], f"{ca_symbol}_Exit"
            )
            
            # Calculate expected exit
            expected_exit = calculate_expected_exit_time(b1_dt, ca_h1_dt, b2_dt, ca_h2_dt, controls["proj_day"])
            
            # Merge results
            result_df = underlying_df.merge(ca_entry_df, on="Time").merge(ca_exit_df, on="Time")
            result_df[f"{ca_symbol}_Spread"] = result_df[f"{ca_symbol}_Exit"] - result_df[f"{ca_symbol}_Entry"]
            result_df.insert(0, "Slot", result_df["Time"].apply(lambda x: "⭐ 8:30" if x == "08:30" else ""))
            
            st.session_state["bc_results"] = {
                "table": result_df,
                "underlying_slope": underlying_slope,
                "ca_symbol": ca_symbol,
                "ca_entry_slope": ca_entry_slope,
                "ca_exit_slope": ca_exit_slope,
                "expected_exit": expected_exit
            }
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Display results
    if "bc_results" in st.session_state:
        results = st.session_state["bc_results"]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Underlying Slope",
                f"{results['underlying_slope']:+.3f}",
                "SPX per 30m",
                "📐",
                "primary"
            ), unsafe_allow_html=True)
        
        with col2:
            st.markdown(create_metric_card(
                f"{results['ca_symbol']} Entry",
                f"{results['ca_entry_slope']:+.3f}",
                "Per 30m slope",
                "📊",
                "success"
            ), unsafe_allow_html=True)
        
        with col3:
            st.markdown(create_metric_card(
                f"{results['ca_symbol']} Exit",
                f"{results['ca_exit_slope']:+.3f}",
                "Target slope",
                "🎯",
                "warning"
            ), unsafe_allow_html=True)
        
        with col4:
            st.markdown(create_metric_card(
                "Expected Exit",
                results['expected_exit'],
                "Median duration",
                "⏰",
                "neutral"
            ), unsafe_allow_html=True)
        
        # Projections table
        st.markdown("### 🎯 NY Session Projections")
        st.dataframe(results['table'], use_container_width=True, hide_index=True)

def render_plan_card_tab():
    st.markdown("""
    <div class="enterprise-card">
        <h2 style="margin-top: 0;">📝 Plan Card - Session Preparation</h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Trading plan synthesis for 8:25 AM preparation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    has_anchors = "anchors_data" in st.session_state
    has_bc = "bc_results" in st.session_state
    
    if not has_anchors:
        st.warning("⚠️ Please refresh SPX Anchors first")
        return
    
    anchors = st.session_state["anchors_data"]
    bc = st.session_state.get("bc_results")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            "Anchor",
            f"{anchors['anchor_close']:.2f}",
            anchors['anchor_source'],
            "⚓",
            "primary"
        ), unsafe_allow_html=True)
    
    with col2:
        touches_count = len(anchors['touches'])
        st.markdown(create_metric_card(
            "Overnight Touches",
            str(touches_count),
            "ES converted touches",
            "🌙",
            "warning" if touches_count > 0 else "neutral"
        ), unsafe_allow_html=True)
    
    with col3:
        bc_status = "SET" if bc else "NONE"
        st.markdown(create_metric_card(
            "BC Forecast",
            bc_status,
            "Contract projections",
            "🔮",
            "success" if bc else "neutral"
        ), unsafe_allow_html=True)
    
    with col4:
        readiness = 90 if (has_anchors and bc) else 70 if has_anchors else 30
        st.markdown(create_metric_card(
            "Readiness",
            f"{readiness}%",
            "Plan completeness",
            "🎯",
            "success" if readiness >= 80 else "warning"
        ), unsafe_allow_html=True)
    
    # Trading plan
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("""
        <div class="enterprise-card">
            <h3 style="margin-top: 0;">🎯 SPX Setup</h3>
        </div>
        """, unsafe_allow_html=True)
        
        df = anchors['strategy_df']
        row_830 = df[df['Time'] == '08:30']
        
        if not row_830.empty:
            setup = row_830.iloc[0]
            st.markdown(f"""
            **8:30 AM Key Levels:**
            - **Bias:** {create_status_badge(setup['Bias'], 'up' if setup['Bias'] == 'UP' else 'down' if setup['Bias'] == 'DOWN' else 'neutral')}
            - **Fan Top:** {setup['Top']:.2f}
            - **Fan Bottom:** {setup['Bottom']:.2f} 
            - **Entry:** {setup['Entry_Signal']}
            """, unsafe_allow_html=True)
        
        if anchors['touches']:
            st.markdown("**Overnight Activity:**")
            for touch in anchors['touches'][-3:]:  # Last 3 touches
                st.markdown(f"- {touch['Time']}: {touch['Touched']} touch → {touch['Bias']}")
    
    with col_right:
        st.markdown("""
        <div class="enterprise-card">
            <h3 style="margin-top: 0;">💼 Contract Plan</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if bc:
            table = bc['table']
            row_830 = table[table['Time'] == '08:30']
            
            if not row_830.empty:
                bc_row = row_830.iloc[0]
                st.markdown(f"""
                **{bc['ca_symbol']} @ 8:30:**
                - **SPX Projected:** {bc_row['SPX_Projected']:.2f}
                - **Entry Level:** {bc_row[f"{bc['ca_symbol']}_Entry"]:.2f}
                - **Exit Target:** {bc_row[f"{bc['ca_symbol']}_Exit"]:.2f}
                - **Expected Exit:** {bc['expected_exit']}
                - **Spread:** {bc_row[f"{bc['ca_symbol']}_Spread"]:.2f}
                """)
        else:
            st.info("Set up BC Forecast for contract strategy")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if "app_initialized" not in st.session_state:
        st.session_state["app_initialized"] = True
    
    render_main_header()
    controls = render_sidebar_controls()
    
    tab1, tab2, tab3 = st.tabs(["🎯 SPX Anchors", "🔮 BC Forecast", "📝 Plan Card"])
    
    with tab1:
        render_spx_anchors_tab(controls)
    
    with tab2:
        render_bc_forecast_tab(controls)
    
    with tab3:
        render_plan_card_tab()

if __name__ == "__main__":
    main()