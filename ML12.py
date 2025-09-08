# app.py - SPX Prophet - Clean & Focused
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
NEUTRAL_BAND_DEFAULT = 0.15  # 15% from center of fan width

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION & STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SPX Prophet - Enterprise Trading Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean Enterprise UI System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --primary-50: #eff6ff; --primary-500: #3b82f6; --primary-600: #2563eb;
    --success-50: #f0fdf4; --success-500: #22c55e; --success-600: #16a34a;
    --danger-50: #fef2f2; --danger-500: #ef4444; --warning-50: #fffbeb; --warning-500: #f59e0b;
    --gray-50: #f8fafc; --gray-100: #f1f5f9; --gray-200: #e2e8f0; --gray-500: #64748b; --gray-700: #334155;
    --text-primary: #0f172a; --text-secondary: #475569; --text-tertiary: #64748b;
    --bg-primary: #ffffff; --border-light: #e2e8f0;
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
    --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-success: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
    --gradient-danger: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
    --gradient-warning: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    --gradient-neutral: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

html, body, [class*="css"] {
    background: var(--bg-primary) !important; color: var(--text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.main .block-container { padding: 1.5rem 1.5rem 2rem 1.5rem !important; max-width: 100% !important; }

.enterprise-card {
    background: var(--bg-primary); border: 2px solid var(--border-light); border-radius: 16px; padding: 20px;
    box-shadow: var(--shadow-lg); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative; overflow: hidden; margin-bottom: 1.5rem;
}
.enterprise-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--gradient-primary);
}
.enterprise-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-xl); border-color: var(--primary-500); }

.metric-card {
    background: var(--bg-primary); border: 2px solid var(--border-light); border-radius: 12px; padding: 16px;
    box-shadow: var(--shadow-md); transition: all 0.3s ease; position: relative; overflow: hidden;
    height: auto; min-height: 120px; display: flex; flex-direction: column; justify-content: space-between;
}
.metric-card:hover { transform: translateY(-1px); box-shadow: var(--shadow-lg); border-color: var(--primary-500); }

.metric-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.metric-icon {
    width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 600; background: var(--gradient-primary); color: white; box-shadow: var(--shadow-md); flex-shrink: 0;
}
.metric-icon.success { background: var(--gradient-success); }
.metric-icon.danger { background: var(--gradient-danger); }
.metric-icon.warning { background: var(--gradient-warning); }
.metric-icon.neutral { background: var(--gradient-neutral); }

.metric-title {
    font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase;
    letter-spacing: 0.05em; margin: 0; line-height: 1.2;
}
.metric-value {
    font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin: 4px 0 2px 0;
    line-height: 1.1; font-family: 'JetBrains Mono', monospace; word-break: break-word;
}
.metric-subtext {
    font-size: 0.7rem; color: var(--text-tertiary); font-weight: 500; line-height: 1.3; margin-top: auto;
}

.status-badge {
    display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; border-radius: 12px;
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; border: 1px solid; transition: all 0.3s ease;
}
.badge-open { background: var(--success-50); border-color: var(--success-500); color: var(--success-600); }
.badge-closed { background: var(--danger-50); border-color: var(--danger-500); color: var(--danger-500); }
.badge-up { background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-color: var(--success-500); color: var(--success-600); font-weight: 700; }
.badge-down { background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-color: var(--danger-500); color: var(--danger-500); font-weight: 700; }
.badge-neutral { background: var(--gray-100); border-color: var(--gray-500); color: var(--gray-700); font-weight: 700; }

.main-header {
    background: var(--bg-primary); border: 2px solid var(--border-light); border-radius: 16px; padding: 20px 24px;
    margin-bottom: 24px; box-shadow: var(--shadow-lg); position: relative; overflow: hidden;
}
.main-header::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--gradient-primary); }
.header-title { font-size: 2rem; font-weight: 800; color: var(--text-primary); margin: 0; display: flex; align-items: center; gap: 12px; line-height: 1.2; }
.header-subtitle { font-size: 0.95rem; color: var(--text-secondary); margin: 6px 0 0 0; font-weight: 500; line-height: 1.4; }

.stButton > button {
    background: var(--gradient-primary) !important; border: none !important; border-radius: 12px !important; color: white !important;
    font-weight: 600 !important; font-size: 0.8rem !important; text-transform: uppercase !important; letter-spacing: 0.03em !important;
    padding: 10px 16px !important; transition: all 0.3s ease !important; box-shadow: var(--shadow-md) !important; height: 40px !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: var(--shadow-lg) !important; }

.stTabs [data-baseweb="tab-list"] {
    background: var(--gray-100) !important; border: 2px solid var(--border-light) !important; border-radius: 12px !important;
    padding: 6px !important; margin-bottom: 24px !important; box-shadow: var(--shadow-md) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border-radius: 8px !important; color: var(--text-secondary) !important; font-weight: 600 !important;
    font-size: 0.8rem !important; text-transform: uppercase !important; letter-spacing: 0.03em !important;
    padding: 8px 16px !important; transition: all 0.3s ease !important;
}
.stTabs [aria-selected="true"] { background: var(--gradient-primary) !important; color: white !important; box-shadow: var(--shadow-md) !important; }

.star-highlight { color: var(--warning-500) !important; font-weight: 700 !important; }
.text-success { color: var(--success-600) !important; }
.text-danger { color: var(--danger-500) !important; }
.text-warning { color: var(--warning-500) !important; }

@keyframes slideInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.animate-slide-in { animation: slideInUp 0.4s ease-out; }

@media (max-width: 768px) {
    .main .block-container { padding: 1rem !important; }
    .metric-card { min-height: 100px; padding: 12px; }
    .header-title { font-size: 1.5rem; }
    .metric-value { font-size: 1.25rem; }
    .enterprise-card { padding: 16px; }
}

* { box-sizing: border-box; }
.metric-card * { overflow: hidden; text-overflow: ellipsis; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CORE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def fmt_ct(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return CT_TZ.localize(dt)
    return dt.astimezone(CT_TZ)

def between_time(df: pd.DataFrame, start_str: str, end_str: str) -> pd.DataFrame:
    return df.between_time(start_str, end_str) if not df.empty else df

def rth_slots_ct(target_date: date) -> List[datetime]:
    start_dt = fmt_ct(datetime.combine(target_date, time(8, 30)))
    end_dt = fmt_ct(datetime.combine(target_date, time(14, 30)))
    slots, current = [], start_dt
    while current <= end_dt:
        slots.append(current)
        current += timedelta(minutes=30)
    return slots

def is_maintenance(dt: datetime) -> bool:
    return dt.hour == 16

def in_weekend_gap(dt: datetime) -> bool:
    weekday = dt.weekday()
    if weekday == 5:  # Saturday
        return True
    if weekday == 6 and dt.hour < 17:  # Sunday before 5 PM
        return True
    if weekday == 4 and dt.hour >= 17:  # Friday after 5 PM
        return True
    return False

def count_effective_blocks(start: datetime, end: datetime) -> float:
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
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns]
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
            return pd.DataFrame()
    return df

def normalize_to_ct(df: pd.DataFrame, start_d: date, end_d: date) -> pd.DataFrame:
    if df.empty:
        return df
    df = ensure_ohlc_cols(df)
    if df.empty:
        return df
    if df.index.tz is None:
        df.index = df.index.tz_localize("US/Eastern")
    df.index = df.index.tz_convert(CT_TZ)
    start_dt = fmt_ct(datetime.combine(start_d, time(0, 0)))
    end_dt = fmt_ct(datetime.combine(end_d, time(23, 59)))
    return df.loc[start_dt:end_dt]

def get_previous_trading_day(target_date: date) -> date:
    """Get the previous trading day, handling weekends properly."""
    prev_date = target_date - timedelta(days=1)
    
    # If target is Monday, go back to Friday
    if target_date.weekday() == 0:  # Monday
        prev_date = target_date - timedelta(days=3)  # Friday
    # If target is Sunday, go back to Friday  
    elif target_date.weekday() == 6:  # Sunday
        prev_date = target_date - timedelta(days=2)  # Friday
    
    return prev_date

@st.cache_data(ttl=300, show_spinner=False)
def fetch_intraday(symbol: str, start_d: date, end_d: date, interval: str) -> pd.DataFrame:
    try:
        ticker = yf.Ticker(symbol)
        if interval in ["1m", "2m", "5m", "15m"]:
            # For minute data, extend range to capture weekend gaps
            range_days = max(1, min(30, (end_d - start_d).days + 7))
            df = ticker.history(
                period=f"{range_days}d",
                interval=interval,
                prepost=True,
                auto_adjust=False,
                back_adjust=False
            )
            df = normalize_to_ct(df, start_d - timedelta(days=7), end_d + timedelta(days=7))
            start_filter = fmt_ct(datetime.combine(start_d, time(0, 0)))
            end_filter = fmt_ct(datetime.combine(end_d, time(23, 59)))
            df = df.loc[start_filter:end_filter]
        else:
            df = ticker.history(
                start=(start_d - timedelta(days=7)).strftime("%Y-%m-%d"),
                end=(end_d + timedelta(days=7)).strftime("%Y-%m-%d"),
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
    if min_df.empty or not isinstance(min_df.index, pd.DatetimeIndex):
        return pd.DataFrame()
    df = min_df.sort_index()
    agg_rules = {}
    if "Open" in df.columns: agg_rules["Open"] = "first"
    if "High" in df.columns: agg_rules["High"] = "max"
    if "Low" in df.columns: agg_rules["Low"] = "min"
    if "Close" in df.columns: agg_rules["Close"] = "last"
    if "Volume" in df.columns: agg_rules["Volume"] = "sum"
    resampled = df.resample("30T", label="right", closed="right").agg(agg_rules)
    ohlc_cols = [c for c in ["Open", "High", "Low", "Close"] if c in resampled.columns]
    resampled = resampled.dropna(subset=ohlc_cols, how="any")
    return resampled

# ═══════════════════════════════════════════════════════════════════════════════
# SPX ANCHOR & OFFSET LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def get_spx_anchor_3pm(prev_day: date) -> Tuple[Optional[float], Optional[datetime], bool]:
    """Get SPX anchor at 3:00 PM CT from previous trading day."""
    target_time = fmt_ct(datetime.combine(prev_day, time(15, 0)))
    
    for interval in ["30m", "5m", "1m"]:
        spx_data = fetch_intraday("^GSPC", prev_day, prev_day, interval)
        if spx_data.empty:
            continue
        before_target = spx_data.loc[:target_time]
        if before_target.empty:
            continue
        anchor_close = float(before_target["Close"].iloc[-1])
        anchor_time = before_target.index[-1].to_pydatetime()
        return anchor_close, fmt_ct(anchor_time), False
    return None, None, True

def calculate_es_spx_offset_230pm(prev_day: date) -> Optional[float]:
    """Calculate ES-SPX offset using 2:30 PM prices for both instruments."""
    target_time = fmt_ct(datetime.combine(prev_day, time(14, 30)))  # 2:30 PM CT
    
    # Get SPX at 2:30 PM
    spx_230 = None
    for interval in ["30m", "5m", "1m"]:
        spx_data = fetch_intraday("^GSPC", prev_day, prev_day, interval)
        if spx_data.empty:
            continue
        spx_window = spx_data.loc[:target_time]
        if spx_window.empty:
            continue
        spx_230 = float(spx_window["Close"].iloc[-1])
        break
    
    if spx_230 is None:
        return None
    
    # Get ES at 2:30 PM  
    es_230 = None
    for interval in ["5m", "1m", "30m"]:
        es_data = fetch_intraday("ES=F", prev_day, prev_day, interval)
        if es_data.empty:
            continue
        es_window = es_data.loc[:target_time]
        if es_window.empty:
            continue
        es_230 = float(es_window["Close"].iloc[-1])
        break
    
    if es_230 is None:
        return None
    
    return es_230 - spx_230

def get_current_slopes() -> Tuple[float, float]:
    top_slope = float(st.session_state.get("top_slope_per_block", TOP_SLOPE_DEFAULT))
    bottom_slope = float(st.session_state.get("bottom_slope_per_block", BOTTOM_SLOPE_DEFAULT))
    return top_slope, bottom_slope

def project_fan_levels(anchor_close: float, anchor_time: datetime, target_day: date) -> pd.DataFrame:
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
        })
    
    return pd.DataFrame(projections)

def determine_bias(price: float, top_level: float, bottom_level: float, 
                  neutral_band_pct: float = NEUTRAL_BAND_DEFAULT) -> str:
    if price > top_level:
        return "UP"
    if price < bottom_level:
        return "DOWN"
    
    fan_width = top_level - bottom_level
    fan_center = (top_level + bottom_level) / 2
    neutral_band_size = neutral_band_pct * fan_width
    
    if abs(price - fan_center) <= neutral_band_size:
        return "NEUTRAL"
    
    distance_to_top = top_level - price
    distance_to_bottom = price - bottom_level
    
    return "UP" if distance_to_bottom < distance_to_top else "DOWN"

# ═══════════════════════════════════════════════════════════════════════════════
# OVERNIGHT TOUCH DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_es_overnight(prev_day: date, proj_day: date) -> pd.DataFrame:
    """Fetch ES overnight data with proper weekend handling."""
    # Handle Friday to Monday gap
    if prev_day.weekday() == 4 and proj_day.weekday() == 0:  # Friday to Monday
        start_time = fmt_ct(datetime.combine(prev_day, time(17, 0)))  # Friday 5 PM
        end_time = fmt_ct(datetime.combine(proj_day, time(8, 30)))   # Monday 8:30 AM
    else:
        start_time = fmt_ct(datetime.combine(prev_day, time(17, 0)))
        end_time = fmt_ct(datetime.combine(proj_day, time(8, 30)))
    
    # Try multiple intervals for ES data
    for interval in ["30m", "5m", "1m"]:
        es_data = fetch_intraday("ES=F", prev_day, proj_day, interval)
        if es_data.empty:
            continue
        
        # Filter to overnight window
        overnight_data = es_data.loc[start_time:end_time]
        
        if not overnight_data.empty:
            # Resample to 30m if needed
            if interval != "30m":
                overnight_data = resample_to_30m_ct(overnight_data)
            
            return overnight_data
    
    return pd.DataFrame()

def detect_overnight_fan_touches(prev_day: date, proj_day: date, anchor_close: float, 
                                anchor_time: datetime, es_spx_offset: float) -> pd.DataFrame:
    """Detect ES touches of fan levels overnight, converted to SPX frame."""
    
    # Get ES overnight data
    es_overnight = fetch_es_overnight(prev_day, proj_day)
    if es_overnight.empty:
        return pd.DataFrame()
    
    # Convert ES to SPX frame
    spx_equiv = es_overnight.copy()
    for col in ["Open", "High", "Low", "Close"]:
        if col in spx_equiv.columns:
            spx_equiv[col] = spx_equiv[col] - es_spx_offset
    
    # Calculate fan levels for each overnight period
    touch_results = []
    top_slope, bottom_slope = get_current_slopes()
    
    for timestamp, bar in spx_equiv.iterrows():
        # Calculate fan levels at this time
        blocks_from_anchor = count_effective_blocks(anchor_time, timestamp)
        fan_top = anchor_close + (top_slope * blocks_from_anchor)
        fan_bottom = anchor_close - (bottom_slope * blocks_from_anchor)
        
        # Check for touches
        bar_high = float(bar["High"])
        bar_low = float(bar["Low"])
        bar_close = float(bar["Close"])
        
        touch_type = None
        if bar_high >= fan_top:
            touch_type = "TOP"
        elif bar_low <= fan_bottom:
            touch_type = "BOTTOM"
        
        if touch_type:
            # Determine bias and entry signal
            bias = determine_bias(bar_close, fan_top, fan_bottom)
            entry_signal = generate_entry_signal(bar_close, fan_top, fan_bottom, bias, touch_type)
            
            touch_results.append({
                "Time": timestamp.strftime("%H:%M"),
                "DateTime": timestamp,
                "SPX_Equiv_Price": round(bar_close, 2),
                "Fan_Top": round(fan_top, 2),
                "Fan_Bottom": round(fan_bottom, 2),
                "Touch_Type": touch_type,
                "Bias": bias,
                "Entry_Signal": entry_signal,
                "High": round(bar_high, 2),
                "Low": round(bar_low, 2)
            })
    
    return pd.DataFrame(touch_results)

def generate_entry_signal(price: float, top: float, bottom: float, bias: str, touch_type: str = None) -> str:
    if touch_type == "TOP":
        if price > top:
            return "Short from above fan top"
        else:
            return "Short rejection at fan top"
    elif touch_type == "BOTTOM":
        if price < bottom:
            return "Long from below fan bottom"
        else:
            return "Long bounce at fan bottom"
    else:
        # Regular RTH signals
        if bias == "UP":
            return "Long on dip to bottom" if price > top else "Long breakout above fan"
        elif bias == "DOWN":
            return "Short on rally to top" if price < bottom else "Short breakdown below fan"
        elif bias == "NEUTRAL":
            return "Range-bound - wait for breakout"
        else:
            return "—"

def build_spx_strategy_table(anchor_close: float, anchor_time: datetime, 
                            target_day: date, prev_day: date, 
                            spx_rth_data: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    
    # Build fan projections
    fan_df = project_fan_levels(anchor_close, anchor_time, target_day)
    
    # Get overnight touches
    es_spx_offset = calculate_es_spx_offset_230pm(prev_day)
    overnight_touches = pd.DataFrame()
    
    if es_spx_offset is not None:
        overnight_touches = detect_overnight_fan_touches(
            prev_day, target_day, anchor_close, anchor_time, es_spx_offset
        )
    
    # Build RTH strategy table
    strategy_rows = []
    neutral_band = float(st.session_state.get("neutral_band_pct", NEUTRAL_BAND_DEFAULT))
    
    for _, row in fan_df.iterrows():
        slot_time = row["Time"]
        top_level = row["Top"]
        bottom_level = row["Bottom"]
        fan_width = row["Fan_Width"]
        
        actual_price = None
        if spx_rth_data is not None and not spx_rth_data.empty:
            slot_datetime = row["DateTime"]
            if slot_datetime in spx_rth_data.index:
                actual_price = float(spx_rth_data.loc[slot_datetime, "Close"])
        
        if actual_price is not None:
            bias = determine_bias(actual_price, top_level, bottom_level, neutral_band)
            price_display = f"{actual_price:.2f}"
            entry_signal = generate_entry_signal(actual_price, top_level, bottom_level, bias)
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
    
    return pd.DataFrame(strategy_rows), overnight_touches

# ═══════════════════════════════════════════════════════════════════════════════
# BC FORECAST LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def project_contract_line(bounce1_time: datetime, bounce1_price: float,
                         bounce2_time: datetime, bounce2_price: float,
                         target_day: date, line_label: str) -> Tuple[pd.DataFrame, float]:
    effective_blocks = count_effective_blocks(bounce1_time, bounce2_time)
    slope = (bounce2_price - bounce1_price) / effective_blocks if effective_blocks > 0 else 0.0
    
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
    duration1 = count_effective_blocks(bounce1_time, high1_time)
    duration2 = count_effective_blocks(bounce2_time, high2_time)
    
    durations = [d for d in [duration1, duration2] if d > 0]
    if not durations:
        return "N/A"
    
    median_duration = int(np.median(durations))
    exit_candidate = bounce2_time
    blocks_added = 0
    
    while blocks_added < median_duration:
        exit_candidate += timedelta(minutes=30)
        if not is_maintenance(exit_candidate) and not in_weekend_gap(exit_candidate):
            blocks_added += 1
    
    rth_slots = rth_slots_ct(target_day)
    for slot in rth_slots:
        if slot >= exit_candidate:
            return slot.strftime("%H:%M")
    
    return "After RTH"

# ═══════════════════════════════════════════════════════════════════════════════
# UI COMPONENT BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def create_metric_card(title: str, value: str, subtext: str = "", icon: str = "📊", 
                      card_type: str = "primary") -> str:
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
    return f'<span class="status-badge badge-{status}">{text}</span>'

def create_header_section(title: str, subtitle: str = "") -> str:
    return f"""
    <div class="main-header animate-slide-in">
        <h1 class="header-title">{title}</h1>
        {f'<p class="header-subtitle">{subtitle}</p>' if subtitle else ''}
    </div>
    """

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN INTERFACE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def render_main_header():
    current_time = datetime.now(CT_TZ)
    
    st.markdown(create_header_section(
        "⚡ SPX Prophet",
        "Enterprise Trading Analytics Platform - SPX Anchors | BC Forecast | Plan Card"
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
        status_subtext = "RTH: 08:30-14:30 CT"
        
        st.markdown(create_metric_card(
            "Market Status",
            status_text,
            status_subtext,
            "📊",
            status_type
        ), unsafe_allow_html=True)
    
    with col3:
        top_slope, bottom_slope = get_current_slopes()
        slope_text = f"+{top_slope:.3f}"
        override_active = ("top_slope_per_block" in st.session_state or 
                          "bottom_slope_per_block" in st.session_state)
        slope_subtext = f"Bot: -{bottom_slope:.3f}"
        slope_type = "warning" if override_active else "neutral"
        
        st.markdown(create_metric_card(
            "SPX Slopes /30m",
            slope_text,
            slope_subtext,
            "📐",
            slope_type
        ), unsafe_allow_html=True)
    
    with col4:
        try:
            test_data = fetch_intraday("^GSPC", current_time.date() - timedelta(days=1), 
                                     current_time.date(), "30m")
            connectivity = "CONNECTED" if not test_data.empty else "LIMITED"
            conn_type = "success" if not test_data.empty else "warning"
            conn_subtext = f"{len(test_data)} bars" if not test_data.empty else "Check source"
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

def render_sidebar_controls():
    st.sidebar.title("🎛️ Controls")
    
    today_ct = datetime.now(CT_TZ).date()
    
    prev_day = st.sidebar.date_input(
        "Previous Trading Day",
        value=get_previous_trading_day(today_ct),
        help="Day to get SPX anchor close ≤ 3:00 PM CT"
    )
    
    proj_day = st.sidebar.date_input(
        "Projection Day", 
        value=today_ct,
        help="Target day for RTH projections"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("✍️ Manual Anchor")
    
    use_manual = st.sidebar.checkbox(
        "Override with manual 3:00 PM close",
        value=False,
        help="Use custom anchor instead of fetched ^GSPC data"
    )
    
    manual_value = st.sidebar.number_input(
        "Manual Anchor Close",
        value=6400.00,
        step=0.25,
        format="%.2f",
        disabled=not use_manual,
        help="SPX close price for anchor calculations"
    )
    
    st.sidebar.markdown("---")
    
    refresh_anchors = st.sidebar.button(
        "🔮 Refresh SPX Anchors",
        type="primary",
        use_container_width=True,
        help="Rebuild fan projections and overnight analysis"
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
        <h2 style="margin-top: 0; display: flex; align-items: center; gap: 12px;">
            🎯 SPX Anchors - Fan Analysis & Overnight Touches
        </h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">
            Previous day anchor projection with overnight ES touch detection converted to SPX frame
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if controls["refresh_anchors"] or "anchors_data" not in st.session_state:
        with st.spinner("Building SPX anchor analysis with overnight touches..."):
            try:
                if controls["use_manual"]:
                    anchor_close = float(controls["manual_value"])
                    anchor_time = fmt_ct(datetime.combine(controls["prev_day"], time(15, 0)))
                    anchor_label = " (Manual)"
                    estimated = False
                else:
                    anchor_close, anchor_time, estimated = get_spx_anchor_3pm(controls["prev_day"])
                    if anchor_close is None:
                        st.error("❌ Could not resolve SPX anchor for previous day")
                        return
                    anchor_label = " (Estimated)" if estimated else ""
                
                # Get RTH SPX data
                spx_rth_data = fetch_intraday("^GSPC", controls["proj_day"], controls["proj_day"], "30m")
                spx_rth_data = between_time(spx_rth_data, RTH_START, RTH_END) if not spx_rth_data.empty else pd.DataFrame()
                
                # Build strategy table with overnight touches
                strategy_df, overnight_touches = build_spx_strategy_table(
                    anchor_close, anchor_time, controls["proj_day"], controls["prev_day"], spx_rth_data
                )
                
                # Calculate offset used
                es_spx_offset = calculate_es_spx_offset_230pm(controls["prev_day"])
                
                st.session_state["anchors_data"] = {
                    "anchor_close": anchor_close,
                    "anchor_time": anchor_time,
                    "anchor_label": anchor_label,
                    "strategy_df": strategy_df,
                    "overnight_touches": overnight_touches,
                    "es_spx_offset": es_spx_offset,
                    "spx_data": spx_rth_data,
                    "estimated": estimated
                }
                
            except Exception as e:
                st.error(f"Error building anchor analysis: {str(e)}")
                return
    
    if "anchors_data" in st.session_state:
        data = st.session_state["anchors_data"]
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(create_metric_card(
                "Anchor Close",
                f"{data['anchor_close']:.2f}",
                f"3:00 PM CT{data['anchor_label']}",
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
            touch_count = len(data['overnight_touches']) if not data['overnight_touches'].empty else 0
            st.markdown(create_metric_card(
                "Overnight Touches",
                str(touch_count),
                "ES converted to SPX",
                "🌙",
                "success" if touch_count > 0 else "neutral"
            ), unsafe_allow_html=True)
        
        with col4:
            offset = data.get('es_spx_offset', 0) or 0
            st.markdown(create_metric_card(
                "ES-SPX Offset",
                f"{offset:+.2f}",
                "2:30 PM calculation",
                "🔗",
                "neutral"
            ), unsafe_allow_html=True)
        
        # Overnight touches table
        if not data['overnight_touches'].empty:
            st.markdown("### 🌙 Overnight Fan Touches (ES → SPX)")
            st.dataframe(
                data['overnight_touches'][["Time", "SPX_Equiv_Price", "Fan_Top", "Fan_Bottom", "Touch_Type", "Bias", "Entry_Signal"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Time": st.column_config.TextColumn("Time", width="small"),
                    "SPX_Equiv_Price": st.column_config.NumberColumn("SPX Equiv", width="medium", format="%.2f"),
                    "Fan_Top": st.column_config.NumberColumn("Fan Top", width="medium", format="%.2f"),
                    "Fan_Bottom": st.column_config.NumberColumn("Fan Bottom", width="medium", format="%.2f"),
                    "Touch_Type": st.column_config.TextColumn("Touch", width="small"),
                    "Bias": st.column_config.TextColumn("Bias", width="small"),
                    "Entry_Signal": st.column_config.TextColumn("Entry Signal", width="large")
                }
            )
        else:
            st.info("No overnight fan touches detected (ES data may be unavailable)")
        
        st.markdown("### 📊 RTH Trading Strategy Table")
        
        if not data['strategy_df'].empty:
            st.dataframe(
                data['strategy_df'],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Slot": st.column_config.TextColumn("", width="small"),
                    "Time": st.column_config.TextColumn("Time", width="small"),
                    "Price": st.column_config.TextColumn("SPX Price", width="medium"),
                    "Bias": st.column_config.TextColumn("Bias", width="small"),
                    "Top": st.column_config.NumberColumn("Top", width="medium", format="%.2f"),
                    "Bottom": st.column_config.NumberColumn("Bottom", width="medium", format="%.2f"),
                    "Width": st.column_config.NumberColumn("Width", width="small", format="%.1f"),
                    "Entry_Signal": st.column_config.TextColumn("Entry Signal", width="large")
                }
            )
    
    else:
        st.info("👆 Click 'Refresh SPX Anchors' in the sidebar to begin analysis")

def render_bc_forecast_tab(controls: Dict):
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
    
    # Handle Friday to Monday gap for overnight session slots
    if controls["prev_day"].weekday() == 4 and controls["proj_day"].weekday() == 0:  # Friday to Monday
        asia_start = fmt_ct(datetime.combine(controls["prev_day"], time(19, 0)))
        europe_end = fmt_ct(datetime.combine(controls["proj_day"], time(7, 0)))
    else:
        asia_start = fmt_ct(datetime.combine(controls["prev_day"], time(19, 0)))
        europe_end = fmt_ct(datetime.combine(controls["proj_day"], time(7, 0)))
    
    session_slots = []
    current_slot = asia_start
    while current_slot <= europe_end:
        session_slots.append(current_slot)
        current_slot += timedelta(minutes=30)
    
    slot_options = [dt.strftime("%Y-%m-%d %H:%M") for dt in session_slots]
    
    with st.form("bc_forecast_form", clear_on_submit=False):
        st.markdown("### 📍 Underlying Bounces (Exactly 2 Required)")
        
        bounce_col1, bounce_col2 = st.columns(2)
        
        with bounce_col1:
            st.markdown("**Bounce #1**")
            b1_time = st.selectbox("Time (30m slot)", options=slot_options, index=0, key="b1_time")
            b1_price = st.number_input("SPX Price", value=6500.00, step=0.25, format="%.2f", key="b1_price")
        
        with bounce_col2:
            st.markdown("**Bounce #2**")
            b2_time = st.selectbox("Time (30m slot)", options=slot_options, index=min(6, len(slot_options)-1), key="b2_time")
            b2_price = st.number_input("SPX Price", value=6512.00, step=0.25, format="%.2f", key="b2_price")
        
        st.markdown("---")
        st.markdown("### 📋 Contract A (Required)")
        
        ca_col1, ca_col2 = st.columns(2)
        
        with ca_col1:
            ca_symbol = st.text_input("Contract Symbol", value="6525c", key="ca_symbol")
            ca_b1_price = st.number_input("Price at Bounce #1", value=10.00, step=0.05, format="%.2f", key="ca_b1_price")
            ca_b2_price = st.number_input("Price at Bounce #2", value=12.50, step=0.05, format="%.2f", key="ca_b2_price")
        
        with ca_col2:
            st.markdown("**Exit Reference Points**")
            ca_h1_time = st.selectbox("High after Bounce #1 - Time", options=slot_options, index=min(2, len(slot_options)-1), key="ca_h1_time")
            ca_h1_price = st.number_input("High after Bounce #1 - Price", value=14.00, step=0.05, format="%.2f", key="ca_h1_price")
            ca_h2_time = st.selectbox("High after Bounce #2 - Time", options=slot_options, index=min(8, len(slot_options)-1), key="ca_h2_time")
            ca_h2_price = st.number_input("High after Bounce #2 - Price", value=16.00, step=0.05, format="%.2f", key="ca_h2_price")
        
        submitted = st.form_submit_button("🚀 Generate NY Session Projections", type="primary", use_container_width=True)
    
    if submitted:
        try:
            b1_dt = fmt_ct(datetime.strptime(st.session_state["b1_time"], "%Y-%m-%d %H:%M"))
            b2_dt = fmt_ct(datetime.strptime(st.session_state["b2_time"], "%Y-%m-%d %H:%M"))
            
            if b2_dt <= b1_dt:
                st.error("❌ Bounce #2 must occur after Bounce #1")
                return
            
            underlying_df, underlying_slope = project_contract_line(
                b1_dt, st.session_state["b1_price"], b2_dt, st.session_state["b2_price"],
                controls["proj_day"], "SPX_Projected"
            )
            
            underlying_df.insert(0, "Slot", underlying_df["Time"].apply(lambda x: "⭐ 8:30" if x == "08:30" else ""))
            
            ca_entry_df, ca_entry_slope = project_contract_line(
                b1_dt, st.session_state["ca_b1_price"], b2_dt, st.session_state["ca_b2_price"],
                controls["proj_day"], f"{st.session_state['ca_symbol']}_Entry"
            )
            
            ca_h1_dt = fmt_ct(datetime.strptime(st.session_state["ca_h1_time"], "%Y-%m-%d %H:%M"))
            ca_h2_dt = fmt_ct(datetime.strptime(st.session_state["ca_h2_time"], "%Y-%m-%d %H:%M"))
            
            ca_exit_df, ca_exit_slope = project_contract_line(
                ca_h1_dt, st.session_state["ca_h1_price"], ca_h2_dt, st.session_state["ca_h2_price"],
                controls["proj_day"], f"{st.session_state['ca_symbol']}_Exit"
            )
            
            ca_expected_exit = calculate_expected_exit_time(b1_dt, ca_h1_dt, b2_dt, ca_h2_dt, controls["proj_day"])
            
            result_df = underlying_df.merge(ca_entry_df, on="Time").merge(ca_exit_df, on="Time")
            result_df[f"{st.session_state['ca_symbol']}_Spread"] = (
                result_df[f"{st.session_state['ca_symbol']}_Exit"] - result_df[f"{st.session_state['ca_symbol']}_Entry"]
            )
            
            st.session_state["bc_results"] = {
                "table": result_df,
                "underlying_slope": underlying_slope,
                "ca_symbol": st.session_state['ca_symbol'],
                "ca_entry_slope": ca_entry_slope,
                "ca_exit_slope": ca_exit_slope,
                "ca_expected_exit": ca_expected_exit
            }
            
        except Exception as e:
            st.error(f"❌ Error generating BC forecast: {str(e)}")
            return
    
    if "bc_results" in st.session_state:
        results = st.session_state["bc_results"]
        
        st.markdown("### 📈 Projection Summary")
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.markdown(create_metric_card("Underlying Slope", f"{results['underlying_slope']:+.3f}", "SPX points per 30m", "📐", "primary"), unsafe_allow_html=True)
        
        with metric_col2:
            st.markdown(create_metric_card(f"{results['ca_symbol']} Entry", f"{results['ca_entry_slope']:+.3f}", f"Exit: {results['ca_exit_slope']:+.3f}", "📊", "success"), unsafe_allow_html=True)
        
        with metric_col3:
            st.markdown(create_metric_card("Contracts", "1", "Single contract analysis", "📋", "neutral"), unsafe_allow_html=True)
        
        with metric_col4:
            st.markdown(create_metric_card("Expected Exit", results['ca_expected_exit'], f"Contract A timing", "⏰", "warning"), unsafe_allow_html=True)
        
        st.markdown("### 🎯 NY Session Projections")
        st.dataframe(results['table'], use_container_width=True, hide_index=True, 
                    column_config={"Slot": st.column_config.TextColumn("", width="small"), "Time": st.column_config.TextColumn("Time", width="small")})
    
    else:
        st.info("👆 Fill out the form above and click 'Generate NY Session Projections'")

def render_plan_card_tab():
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
    
    has_anchors = "anchors_data" in st.session_state
    has_bc = "bc_results" in st.session_state
    
    if not has_anchors:
        st.warning("⚠️ SPX Anchors data required. Please refresh SPX Anchors first.")
        return
    
    anchors = st.session_state["anchors_data"]
    bc = st.session_state.get("bc_results", None)
    
    st.markdown("### 🎯 Session Overview")
    
    plan_col1, plan_col2, plan_col3, plan_col4 = st.columns(4)
    
    with plan_col1:
        st.markdown(create_metric_card("Anchor Close", f"{anchors['anchor_close']:.2f}", f"3PM{anchors['anchor_label']}", "⚓", "primary"), unsafe_allow_html=True)
    
    with plan_col2:
        strategy_df = anchors['strategy_df']
        width_830 = strategy_df[strategy_df['Time'] == '08:30']['Width'].iloc[0] if not strategy_df.empty else 0
        st.markdown(create_metric_card("Fan Width @ 8:30", f"{width_830:.2f}", "Key decision zone", "📏", "neutral"), unsafe_allow_html=True)
    
    with plan_col3:
        touch_count = len(anchors.get('overnight_touches', [])) 
        st.markdown(create_metric_card("Overnight Touches", str(touch_count), "Fan interactions", "🌙", "success" if touch_count > 0 else "neutral"), unsafe_allow_html=True)
    
    with plan_col4:
        readiness_score = 90 if (has_anchors and bc and touch_count > 0) else 75 if (has_anchors and bc) else 60 if has_anchors else 25
        readiness_type = "success" if readiness_score >= 80 else "warning" if readiness_score >= 60 else "danger"
        st.markdown(create_metric_card("Readiness", f"{readiness_score}%", "Plan completeness", "🎯", readiness_type), unsafe_allow_html=True)
    
    plan_left, plan_right = st.columns(2)
    
    with plan_left:
        st.markdown("""<div class="enterprise-card"><h3 style="margin-top: 0;">🎯 Primary Setup (SPX Anchors)</h3></div>""", unsafe_allow_html=True)
        
        row_830 = strategy_df[strategy_df['Time'] == '08:30']
        if not row_830.empty:
            setup = row_830.iloc[0]
            st.markdown(f"""
            **8:30 AM Key Levels:**
            - **Bias:** {create_status_badge(setup['Bias'], 'up' if setup['Bias'] == 'UP' else 'down' if setup['Bias'] == 'DOWN' else 'neutral')}
            - **Fan Top:** {setup['Top']:.2f}
            - **Fan Bottom:** {setup['Bottom']:.2f}
            - **Entry Signal:** {setup['Entry_Signal']}
            """, unsafe_allow_html=True)
            
            # Overnight touches summary
            overnight_touches = anchors.get('overnight_touches', pd.DataFrame())
            if not overnight_touches.empty:
                latest_touch = overnight_touches.iloc[-1]
                st.markdown(f"""
                **Latest Overnight Touch:**
                - **Time:** {latest_touch['Time']} ({latest_touch['Touch_Type']})
                - **SPX Equiv:** {latest_touch['SPX_Equiv_Price']:.2f}
                - **Signal:** {latest_touch['Entry_Signal']}
                """)
        else:
            st.info("8:30 AM data not available")
    
    with plan_right:
        st.markdown("""<div class="enterprise-card"><h3 style="margin-top: 0;">💼 Contract Strategy (BC Forecast)</h3></div>""", unsafe_allow_html=True)
        
        if bc:
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
        else:
            st.info("Set up BC Forecast for contract projections")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    try:
        if "app_initialized" not in st.session_state:
            st.session_state["app_initialized"] = True
            st.session_state["neutral_band_pct"] = NEUTRAL_BAND_DEFAULT
        
        render_main_header()
        controls = render_sidebar_controls()
        
        tab_anchors, tab_bc, tab_plan = st.tabs(["🎯 SPX Anchors", "🔮 BC Forecast", "📝 Plan Card"])
        
        with tab_anchors:
            render_spx_anchors_tab(controls)
        
        with tab_bc:
            render_bc_forecast_tab(controls)
        
        with tab_plan:
            render_plan_card_tab()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: var(--text-tertiary); font-size: 0.8rem; padding: 16px;">
            <p><strong>SPX Prophet</strong> - Professional Trading Analytics Platform</p>
            <p>⚠️ <strong>Risk Disclaimer:</strong> Educational purposes only. Trading involves substantial risk.</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page and try again.")

if __name__ == "__main__":
    main()