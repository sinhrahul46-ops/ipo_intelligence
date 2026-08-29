import streamlit as st
from pipeline import run_refresh
from database import get_ipos, get_latest_gmp, init_db
from datetime import datetime

# Auto-initialize DB to prevent errors
init_db()

# Page config for mobile layout
st.set_page_config(page_title="IPO Intelligence", layout="centered", initial_sidebar_state="collapsed")

# Injecting the Dark Premium CSS from your HTML
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#0B1220; --card:#121B2E; --card-2:#17213A; --line:#243052; --line-soft:#1C2740;
    --text:#EDF1F7; --muted:#8FA0BC; --faint:#5C6C88; --brand:#4C7CF3; --brand-soft:#1C2A4D;
    --good:#34C77B; --good-soft:#12301F; --warn:#F0A93E; --warn-soft:#332512;
    --bad:#EF5B5B; --bad-soft:#331616; --gray:#57667F; --gray-soft:#1B2438;
  }
  
  /* Background & Base Font */
  .stApp { 
    background: radial-gradient(1200px 500px at 50% -10%, #14203A 0%, rgba(20,32,58,0) 60%), var(--bg); 
    color: var(--text); font-family: "IBM Plex Sans", -apple-system, sans-serif; 
  }
  
  /* Hide Streamlit Header */
  header[data-testid="stHeader"] { display: none; }
  .block-container { padding-top: 20px; padding-bottom: 20px; max-width: 430px; } /* Mobile width limit */

  /* App Header Styling */
  .brand-row { display:flex; align-items:center; gap:9px; margin-bottom: 20px;}
  .brand-mark { width:26px; height:26px; border-radius:7px; background:linear-gradient(155deg,#4C7CF3,#2C4FBE); display:flex; align-items:center; justify-content:center; font-family:"IBM Plex Mono"; font-weight:600; font-size:13px; color:#fff; box-shadow:0 2px 10px rgba(76,124,243,.35); }
  .brand-text { font-family:"IBM Plex Serif"; font-weight:600; font-size:18px; color: #fff; letter-spacing:.1px; line-height: 1.1;}
  .brand-text small { display:block; font-family:"IBM Plex Mono"; font-weight:500; font-size:9.5px; color:var(--faint); letter-spacing:.6px; text-transform:uppercase; margin-top:1px;}

  /* Card Styling */
  .card { position:relative; background:var(--card); border:1px solid var(--line); border-radius:14px; margin-bottom:14px; overflow:hidden; box-shadow:0 10px 24px -14px rgba(0,0,0,.6); padding:16px 16px 15px 21px; }
  .ledger { position:absolute; left:0; top:0; bottom:0; width:7px; display:flex; flex-direction:column; }
  .ledger i { flex:1; } 
  .ledger i.fact { background:var(--good); } .ledger i.cross { background:#2B8F5B; } .ledger i.conflict { background:var(--bad); } .ledger i.unverified { background:var(--gray); }
  
  .card-top { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
  .co-name { font-family:"IBM Plex Serif"; font-weight:600; font-size:17px; line-height:1.28; color:#fff;}
  .tag { font-family:"IBM Plex Mono"; font-size:10px; font-weight:500; padding:3px 8px; border-radius:5px; margin-right: 5px;}
  .tag.mainboard { background:var(--brand-soft); color:#9FB8F5; }
  .tag.sme { background:#332F14; color:#E4CE6D; }
  
  /* SVG Score Ring */
  .ring-wrap { position:relative; width:58px; height:58px; flex:none; }
  .ring-hole { position:absolute; inset:6px; border-radius:50%; background:var(--card); border:1px dashed #33436B; display:flex; flex-direction:column; align-items:center; justify-content:center; }
  .ring-hole b { font-family:"IBM Plex Mono"; font-size:16px; font-weight:600; line-height:1; color:#fff;}
  .ring-hole span { font-family:"IBM Plex Mono"; font-size:7.5px; color:var(--faint); letter-spacing:.5px; margin-top:1px; }

  /* Stats Grid */
  .stat-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px 14px; margin-top:15px; padding-top:14px; border-top:1px solid var(--line-soft); }
  .stat .k { font-family:"IBM Plex Mono"; font-size:10px; color:var(--faint); letter-spacing:.4px; text-transform:uppercase; }
  .stat .v { font-family:"IBM Plex Mono"; font-size:14px; font-weight:600; margin-top:3px; color:#fff;}
  .stat .v.good { color:var(--good); } .stat .v.warn { color:var(--warn); }
  
  /* Streamlit Expander Overrides (To match dark theme) */
  [data-testid="stExpander"] { background-color: var(--card-2) !important; border: 1px solid var(--line) !important; border-radius: 10px !important; margin-top: -5px; margin-bottom: 20px;}
  [data-testid="stExpander"] p, [data-testid="stExpander"] li { color: var(--muted) !important; font-size: 13px;}
  [data-testid="stExpander"] h3 { font-family: "IBM Plex Sans", sans-serif !important; font-size: 15px !important; color: #fff !important; margin-bottom: 5px; border-bottom: 1px solid var(--line-soft); padding-bottom: 5px;}
  [data-testid="stExpander"] strong { color: var(--text) !important; }
</style>
""", unsafe_allow_html=True)

# Custom Header
st.markdown("""
<div class="brand-row">
  <div class="brand-mark">₹</div>
  <div class="brand-text">IPO Intelligence<small>Official-first · No-guess policy</small></div>
</div>
""", unsafe_allow_html=True)

# Refresh Button
if st.button("🔄 REFRESH DATA", use_container_width=True):
    with st.spinner("Fetching official filings & checking GMP..."):
        run_refresh()
        st.success(f"Last verified: {datetime.now().strftime('%I:%M %p')} · Sources OK")

ipos = get_ipos()

if not ipos:
    st.info("No data available. Press 'Refresh Data'.")

for ipo in ipos:
    # Fetch GMP Data
    gmp_data = get_latest_gmp(ipo['id'])
    gmp_val = gmp_data['gmp'] if gmp_data['gmp'] else 0
    indicative_listing = (ipo['price_high'] or 0) + gmp_val
    
    # Calculate SVG Ring values
    score = ipo.get('overall_score', 0) or 0
    score_color = "#34C77B" if score >= 70 else ("#F0A93E" if score >= 45 else "#EF5B5B")
    offset = 157 - (157 * score / 100)

    # Fetch Dates (Defaults to TBA if not in DB)
    open_date = ipo.get('open_date', 'TBA') or 'TBA'
    close_date = ipo.get('close_date', 'TBA') or 'TBA'
    listing_date = ipo.get('listing_date', 'TBA') or 'TBA'
    
    type_class = 'sme' if ipo['type'] == 'SME' else 'mainboard'

    # Build the HTML Card
    html_card = f"""
    <div class="card">
      <div class="ledger">
        <i class="fact"></i><i class="cross"></i><i class="fact"></i><i class="fact"></i>
      </div>
      <div class="card-top">
        <div>
          <div class="co-name">{ipo['name']}</div>
          <div style="margin-top:6px;">
            <span class="tag {type_class}">{ipo['type']}</span>
            <span class="tag" style="background:var(--gray-soft); color:#9AA8C2;">{ipo['data_confidence']}</span>
          </div>
        </div>
        <div class="ring-wrap">
          <svg viewBox="0 0 58 58" width="58" height="58">
            <circle cx="29" cy="29" r="25" fill="none" stroke="#1C2740" stroke-width="5"/>
            <circle cx="29" cy="29" r="25" fill="none" stroke="{score_color}" stroke-width="5" stroke-linecap="round" stroke-dasharray="157" stroke-dashoffset="{offset}" transform="rotate(-90 29 29)"/>
          </svg>
          <div class="ring-hole"><b>{int(score)}</b><span>SCORE</span></div>
        </div>
      </div>
      
      <div class="stat-grid">
        <div class="stat"><div class="k">Price Band</div><div class="v">₹{ipo['price_low']}–{ipo['price_high']}</div></div>
        <div class="stat"><div class="k">GMP (Grey Market)</div><div class="v warn">₹{gmp_val}</div></div>
        <div class="stat"><div class="k">Est. Listing Price</div><div class="v good">₹{indicative_listing}</div></div>
        <div class="stat"><div class="k">Issue Size</div><div class="v">₹{ipo['issue_size']} Cr</div></div>
      </div>
    </div>
    """
    
    st.markdown(html_card, unsafe_allow_html=True)
    
    # Expandable Details with Dates
    with st.expander("📑 View Dates & Full AI Analysis"):
        st.markdown(f"""
### 📅 IPO Timeline
*   **Issue Opens:** {open_date}
*   **Issue Closes:** {close_date}
*   **Basis of Allotment:** 1 Day after close (Est.)
*   **Listing Date:** {listing_date}

### 📊 AI Summary
{ipo['ai_summary']}
        """)
