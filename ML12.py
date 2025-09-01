# app.py
# ═══════════════════════════════════════════════════════════════════════════════
# 🔮 SPX PROPHET — Full App (SPX Anchors • Stock Anchors • Signals & EMA • Contract Tool)
# - SPX: previous day's exact 3:00 PM CT close as anchor (manual override supported)
# - Fan: Top=+slope per 30m, Bottom=−slope per 30m (default ±0.260), skip 4–5 PM CT + Fri 5 PM → Sun 5 PM
# - Stocks: Mon/Tue swing high/low → two parallel anchor lines by your per-ticker slopes
# - Signals: fan touch + same-bar EMA 8/21 confirmation (1m if recent; otherwise 5m/30m fallback)
# - Contract Tool: two points (0–30 price) → slope → RTH projection
# - Clean light UI, icons, and compact tables
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple

# ───────────────────────────────────────────────────────────────────────────────
# CORE CONFIG
# ───────────────────────────────────────────────────────────────────────────────
CT_TZ = pytz.timezone("America/Chicago")
RTH_START = "08:30"
RTH_END   = "14:30"

# Default slope per 30-minute block (Top +, Bottom −)
SLOPE_PER_BLOCK_DEFAULT = 0.260

# Per-ticker slope magnitudes (your latest set)
STOCK_SLOPES = {
    "TSLA": 0.0285, "NVDA": 0.0860, "AAPL": 0.0155, "MSFT": 0.0541,
    "AMZN": 0.0139, "GOOGL": 0.0122, "META": 0.0674, "NFLX": 0.0230,
}

# ───────────────────────────────────────────────────────────────────────────────
# PAGE & THEME (Enhanced Enterprise Glassmorphism)
# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🔮 SPX Prophet Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  /* Enhanced Color Palette */
  --primary: #1e40af;        /* blue-800 */
  --primary-light: #3b82f6;  /* blue-500 */
  --primary-lighter: #60a5fa; /* blue-400 */
  --secondary: #059669;      /* emerald-600 */
  --secondary-light: #10b981; /* emerald-500 */
  --accent: #7c3aed;         /* violet-600 */
  --accent-light: #8b5cf6;   /* violet-500 */
  
  /* Neutral Palette */
  --surface: #ffffff;
  --surface-elevated: #f8fafc; /* slate-50 */
  --surface-muted: #f1f5f9;    /* slate-100 */
  --background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  
  /* Text Colors */
  --text-primary: #0f172a;   /* slate-900 */
  --text-secondary: #334155; /* slate-700 */
  --text-muted: #64748b;     /* slate-500 */
  --text-light: #94a3b8;     /* slate-400 */
  
  /* Borders & Dividers */
  --border: #e2e8f0;         /* slate-200 */
  --border-light: #f1f5f9;   /* slate-100 */
  
  /* Status Colors */
  --success: #059669;        /* emerald-600 */
  --success-bg: #d1fae5;     /* emerald-100 */
  --warning: #d97706;        /* amber-600 */
  --warning-bg: #fef3c7;     /* amber-100 */
  --danger: #dc2626;         /* red-600 */
  --danger-bg: #fee2e2;      /* red-100 */
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  --shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);
  
  /* Glass Effect */
  --glass-bg: rgba(255, 255, 255, 0.25);
  --glass-border: rgba(255, 255, 255, 0.18);
  --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}

/* Reset and Base Styles */
html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--background);
  color: var(--text-primary);
  line-height: 1.6;
}

.block-container {
  padding-top: 2rem;
  padding-bottom: 2rem;
  max-width: 1400px;
}

/* Typography Enhancements */
h1, h2, h3, h4, h5, h6 {
  color: var(--text-primary);
  font-weight: 600;
  letter-spacing: -0.025em;
}

h1 { font-size: 2.25rem; font-weight: 700; }
h2 { font-size: 1.875rem; }
h3 { font-size: 1.5rem; }

/* Enhanced Card System */
.card, .metric-card {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  padding: 1.5rem;
  box-shadow: var(--glass-shadow);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.card::before, .metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
  opacity: 0.5;
}

.card:hover, .metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px -8px rgba(31, 38, 135, 0.3);
  border-color: rgba(255, 255, 255, 0.3);
}

/* Metric Cards */
.metric-card {
  text-align: center;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
}

.metric-title {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0 0 0.5rem 0;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
  margin: 0.5rem 0;
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.kicker {
  font-size: 0.8rem;
  color: var(--text-light);
  margin-top: 0.25rem;
  font-weight: 400;
}

/* Status Badges */
.badge-open {
  color: var(--success);
  background: var(--success-bg);
  border: 1px solid var(--success);
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
}

.badge-closed {
  color: var(--danger);
  background: var(--danger-bg);
  border: 1px solid var(--danger);
  padding: 0.375rem 0.875rem;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
}

.badge-open::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Override Tags */
.override-tag {
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--border);
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  display: inline-block;
  margin-top: 0.5rem;
  font-weight: 500;
  box-shadow: var(--shadow-sm);
}

/* Dividers */
hr {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 2rem 0;
}

/* Table Styling */
.dataframe {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(8px);
}

.dataframe th {
  background: var(--surface-muted);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dataframe td {
  font-size: 0.9rem;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-light);
}

.dataframe tr:hover {
  background: rgba(59, 130, 246, 0.05);
}

/* Small Notes */
.small-note {
  color: var(--text-light);
  font-size: 0.85rem;
  line-height: 1.4;
}

/* Animation Classes */
.fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.slide-up {
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
""",
    unsafe_allow_html=True,
)
