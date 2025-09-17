# app.py — Contract Calculator (SPX options style)
# ═══════════════════════════════════════════════════════════════════════════════
# Rules baked in:
# • Default contract slope: −0.33 per 30m (descending)
# • Valid blocks: 3:00→3:30 PM = 1 block; skip 3:30→7:00 PM; then 7:00 PM→ forward in 30m steps
# • 3:00 PM → 8:30 AM = 28 valid blocks
# • Optional BC Fit: choose two 30m timestamps in [3:30 PM (prev) .. 8:00 AM (today)] with their prices
#   → slope = (P2 − P1) / (# of 30m steps), direction included
# • Outputs 8:30 AM contract value and full RTH (08:30–14:30) table

import streamlit as st
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, date, time, timedelta
from typing import List

# ───────────────────────────────────────────────────────────────────────────────
# Basic setup
# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Contract Calculator", page_icon="📉", layout="wide")
CT = pytz.timezone("America/Chicago")

SLOPE_CONTRACT_DEFAULT = -0.33  # per 30m, descending by default
RTH_START = time(8,30)
RTH_END   = time(14,30)

# ───────────────────────────────────────────────────────────────────────────────
# Time helpers
# ───────────────────────────────────────────────────────────────────────────────
def fmt_ct(dt: datetime) -> datetime:
    if dt.tzinfo is None: return CT.localize(dt)
    return dt.astimezone(CT)

def rth_slots_ct(day: date) -> List[datetime]:
    start = fmt_ct(datetime.combine(day, RTH_START))
    end   = fmt_ct(datetime.combine(day, RTH_END))
    out, cur = [], start
    while cur <= end:
        out.append(cur)
        cur += timedelta(minutes=30)
    return out

def blocks_simple_30m(d1: datetime, d2: datetime) -> int:
    d1, d2 = fmt_ct(d1), fmt_ct(d2)
    if d2 <= d1: return 0
    return int((d2 - d1).total_seconds() // (30*60))

def count_blocks_contract(anchor_day: date, target_dt: datetime) -> int:
    """
    Contract valid blocks from 3 PM anchor-day to target:
    - Count 3:00→3:30 PM = 1
    - Skip 3:30→7:00 PM
    - Count 7:00 PM → target in 30m steps
    (3 PM → 8:30 AM = 28 blocks)
    """
    target_dt = fmt_ct(target_dt)
    d3  = fmt_ct(datetime.combine(anchor_day, time(15,0)))
    d33 = fmt_ct(datetime.combine(anchor_day, time(15,30)))
    d7  = fmt_ct(datetime.combine(anchor_day, time(19,0)))
    if target_dt <= d3: 
        return 0
    blocks = 1 if target_dt >= d33 else 0  # 3:00→3:30
    if target_dt > d7:
        blocks += blocks_simple_30m(d7, target_dt)
    return blocks

# ───────────────────────────────────────────────────────────────────────────────
# Styling
# ───────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root { --border:#e2e8f0; --muted:#f8fafc; --text:#0f172a; --sub:#475569; }
html, body { background: var(--muted); color: var(--text); }
.card { background:#fff; border:1px solid var(--border); border-radius:16px; padding:16px; box-shadow:0 10px 26px rgba(2,6,23,.06); }
.metric { font-size:1.6rem; font-weight:700; }
.kicker { color:var(--sub); font-size:.9rem; }
.dataframe { border-radius:12px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# Sidebar Inputs
# ───────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🔧 Contract Calculator")

today_ct = fmt_ct(datetime.now()).date()
prev_day = st.sidebar.date_input("Previous Trading Day", value=today_ct - timedelta(days=1))
proj_day = st.sidebar.date_input("Projection Day", value=prev_day + timedelta(days=1))

contract_3pm = st.sidebar.number_input("Contract Price @ 3:00 PM", value=20.00, step=0.05, format="%.2f")
default_slope = st.sidebar.number_input("Default Slope (per 30m)", value=float(SLOPE_CONTRACT_DEFAULT), step=0.01, format="%.2f",
                                        help="Used unless you re-fit from two bounce points below.")

st.sidebar.markdown("---")
use_bc = st.sidebar.checkbox("Use BC Fit (re-fit slope from two points)", value=False)

# Build bounce slot list: 15:30 (prev) → 08:00 (today) in 30m steps
start_b = fmt_ct(datetime.combine(prev_day, time(15,30)))
end_b   = fmt_ct(datetime.combine(proj_day, time(8,0)))
b_slots, cur = [], start_b
while cur <= end_b:
    b_slots.append(cur)
    cur += timedelta(minutes=30)
b_slot_labels = [dt.strftime("%Y-%m-%d %H:%M") for dt in b_slots]

# ───────────────────────────────────────────────────────────────────────────────
# Forms to avoid full reruns while typing
# ───────────────────────────────────────────────────────────────────────────────
st.header("📉 Contract Calculator")

colA, colB = st.columns([1.2,1])

with colA:
    with st.form("calc_form", clear_on_submit=False):
        st.subheader("Projection Inputs")
        st.caption("Use either the default slope (left) or re-fit with BC below.")
        submitted = st.form_submit_button("Compute Projections")

with colB:
    with st.form("bc_form", clear_on_submit=False):
        st.subheader("BC Fit (optional)")
        st.caption("Pick two 30-min timestamps between 3:30 PM (prev) and 8:00 AM (today).")
        c1, c2 = st.columns(2)
        with c1:
            b1_sel = st.selectbox("Bounce #1 (CT)", b_slot_labels, index=0, key="b1")
            p1 = st.number_input("Contract @ Bounce #1", value=contract_3pm, step=0.05, format="%.2f", key="p1")
        with c2:
            b2_sel = st.selectbox("Bounce #2 (CT)", b_slot_labels, index=min(8, len(b_slot_labels)-1), key="b2")
            p2 = st.number_input("Contract @ Bounce #2", value=contract_3pm, step=0.05, format="%.2f", key="p2")
        fit_clicked = st.form_submit_button("Fit Slope from BC")

# Persist BC fit into session if used
if fit_clicked and use_bc:
    try:
        b1_dt = fmt_ct(datetime.strptime(b1_sel, "%Y-%m-%d %H:%M"))
        b2_dt = fmt_ct(datetime.strptime(b2_sel, "%Y-%m-%d %H:%M"))
        if b2_dt <= b1_dt:
            st.error("Bounce #2 must be after Bounce #1.")
        else:
            steps = blocks_simple_30m(b1_dt, b2_dt)
            if steps <= 0:
                st.error("Bounces must be at least 30 minutes apart.")
            else:
                slope_fit = (float(p2) - float(p1)) / steps
                # Use Bounce #2 as reference for forward projection
                st.session_state["fit"] = {"ref_dt": b2_dt, "ref_px": float(p2), "slope": float(slope_fit)}
                st.success(f"Slope fitted: {slope_fit:+.4f} per 30m (from {b1_sel} → {b2_sel})")
    except Exception as e:
        st.error(f"Fit failed: {e}")

# Decide slope & reference for projections
ref_dt = fmt_ct(datetime.combine(prev_day, time(15,0)))  # default reference = 3:00 PM
ref_px = float(contract_3pm)
slope  = float(default_slope)

if use_bc and "fit" in st.session_state:
    slope  = float(st.session_state["fit"]["slope"])
    ref_dt = st.session_state["fit"]["ref_dt"]
    ref_px = float(st.session_state["fit"]["ref_px"])

# ───────────────────────────────────────────────────────────────────────────────
# Compute projections
# ───────────────────────────────────────────────────────────────────────────────
def proj_at(slot: datetime) -> float:
    """Project contract price for a given slot using rules above."""
    slot = fmt_ct(slot)
    dt_830 = fmt_ct(datetime.combine(proj_day, time(8,30)))

    # If BC fit (ref_dt != 3:00 PM prev_day), just step from ref in 30m
    if not (ref_dt.time() == time(15,0) and ref_dt.date() == prev_day):
        steps = blocks_simple_30m(ref_dt, slot)
        return round(ref_px + slope * steps, 2)

    # Otherwise from 3:00 PM: valid blocks to 8:30, then simple 30m during RTH
    base_blocks = count_blocks_contract(prev_day, min(slot, dt_830))
    if slot <= dt_830:
        total = base_blocks
    else:
        total = base_blocks + blocks_simple_30m(dt_830, slot)
    return round(ref_px + slope * total, 2)

# Always compute once the main form is pressed (or if BC just fitted)
if submitted or (use_bc and "fit" in st.session_state):
    # 8:30 snapshot
    dt_830 = fmt_ct(datetime.combine(proj_day, time(8,30)))
    v_830 = proj_at(dt_830)

    # Header cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><div class='kicker'>Reference</div>"
                    f"<div class='metric'>{ref_px:.2f} @ {ref_dt.strftime('%Y-%m-%d %H:%M CT')}</div></div>",
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div class='kicker'>Slope Used (per 30m)</div>"
                    f"<div class='metric'>{slope:+.4f}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='kicker'>8:30 AM Projection</div>"
                    f"<div class='metric'>{v_830:.2f}</div></div>", unsafe_allow_html=True)

    # Build RTH table
    rows = []
    for slot in rth_slots_ct(proj_day):
        rows.append({
            "⭐": "⭐" if slot.strftime("%H:%M")=="08:30" else "",
            "Time": slot.strftime("%H:%M"),
            "Contract Proj": proj_at(slot)
        })
    st.markdown("### RTH Projection (08:30 → 14:30)")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

else:
    st.info("Set your inputs on the left. Click **Compute Projections** (or fit slope with **BC Fit**) to see results.")