import streamlit as st
from pipeline import run_refresh
from database import get_ipos, get_latest_gmp, init_db
from datetime import datetime

# Auto-initialize DB to prevent errors
init_db()

st.set_page_config(page_title="IPO Intelligence", layout="centered", initial_sidebar_state="collapsed")

st.markdown('''
    <style>
    .ipo-card {
        background-color: #f8f9fa; padding: 15px; border-radius: 12px; margin-bottom: 15px;
        border-left: 5px solid #0052cc; color: #1e1e1e; font-family: sans-serif;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .badge-high { background-color: #d4edda; color: #155724; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }
    .metric-row { display: flex; justify-content: space-between; margin-top: 10px; }
    </style>
''', unsafe_allow_html=True)

st.title("IPO Intelligence 📈")

if st.button("🔄 REFRESH DATA", use_container_width=True):
    with st.spinner("Scanning DRHP, checking GMP conflicts, analyzing..."):
        run_refresh()
        st.success(f"Updated: {datetime.now().strftime('%I:%M %p')}")

ipos = get_ipos()

if not ipos:
    st.info("No data available. Press 'Refresh Data'.")

for ipo in ipos:
    gmp_data = get_latest_gmp(ipo['id'])
    gmp_val = gmp_data['gmp'] if gmp_data['gmp'] else 0
    indicative_listing = ipo['price_high'] + gmp_val
    gmp_pct = (gmp_val / ipo['price_high']) * 100 if ipo['price_high'] else 0

    html_card = f"""
<div class="ipo-card">
    <h3 style="margin:0;">{ipo['name']} <span class="badge-high">{ipo['type']}</span></h3>
    <p style="margin: 2px 0 10px 0; font-size: 0.8em; color: gray;">Accuracy: {ipo['data_confidence']}</p>
    <div class="metric-row">
        <div><b>Price:</b> ₹{ipo['price_high']}</div>
        <div><b>Est. Listing:</b> ₹{indicative_listing}</div>
    </div>
    <div class="metric-row">
        <div><b>GMP:</b> ₹{gmp_val} <span style="color:green;">(+{gmp_pct:.1f}%)</span></div>
        <div><b>Score:</b> {ipo['overall_score']}/100</div>
    </div>
</div>
"""
    with st.container():
        st.markdown(html_card, unsafe_allow_html=True)
        
        with st.expander("📑 Detailed AI Analysis & Sources"):
            st.markdown(ipo['ai_summary'])
