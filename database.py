"""IPO Intelligence - mobile-first Streamlit dashboard.
Run with: streamlit run app/dashboard.py

NOTE ON IMPORTS: this file uses flat imports (e.g. `import db`, not
`from ipo_ai import db`) because the deployed repo has all ipo_ai/*.py
files alongside app files at the repo root rather than in nested
packages. If you later restructure into proper packages, switch these
back to package-relative imports.
"""
import datetime
import streamlit as st
import pandas as pd

import db
from pipeline import refresh_all
from gmp import summarize_gmp, indicative_listing
from subscription import format_multiple, history_series
from scoring import score_ipo
from ai_summary import make_summary
from quality import field_quality
from verify import verify as verify_field

st.set_page_config(page_title='IPO Intelligence', page_icon='\u20B9', layout='centered', initial_sidebar_state='collapsed')
db.init_db()

# ============================================================
# Design system: "verification ledger" theme
# Deep navy + IBM Plex type family, colour used only to encode
# data-provenance status (FACT / CROSS-CHECKED / CONFLICT / UNVERIFIED)
# ============================================================
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
html, body, [class*="css"] { font-family:"IBM Plex Sans",-apple-system,sans-serif; }
.stApp{ background:
  radial-gradient(1200px 500px at 50% -10%, #14203A 0%, rgba(20,32,58,0) 60%), var(--bg); }
.block-container{ padding-top:1rem; padding-left:.9rem; padding-right:.9rem; max-width:560px; }
h1,h2,h3{ font-family:"IBM Plex Serif" !important; color:var(--text) !important; }
p, span, div, label{ color:var(--text); }
.stCaption, small{ color:var(--muted) !important; }

div.stButton > button{
  width:100%; background:linear-gradient(180deg,#4C7CF3,#3D68DE) !important;
  border:1px solid #5D8AFF33 !important; color:#fff !important;
  font-weight:600 !important; font-size:15px !important; padding:12px 16px !important;
  border-radius:11px !important; box-shadow:0 6px 18px rgba(76,124,243,.28) !important;
}

.mono{ font-family:"IBM Plex Mono",monospace; }
.status-row{ font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--muted); display:flex; align-items:center; gap:8px; margin:2px 0 12px; }
.pulse{ width:6px; height:6px; border-radius:50%; background:var(--good); box-shadow:0 0 0 3px var(--good-soft); }

.chip-row{ display:flex; gap:8px; overflow-x:auto; padding:4px 0 14px; }
.chip{ font-family:"IBM Plex Mono",monospace; font-size:11px; font-weight:500; padding:6px 11px;
  border-radius:20px; border:1px solid var(--line); color:var(--muted); background:var(--card); white-space:nowrap; }
.chip.active{ background:var(--brand-soft); border-color:#3E5AA0; color:#BFD0FF; }

.section-label{ font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.8px; text-transform:uppercase;
  color:var(--faint); margin:20px 2px 10px; }

.card{ position:relative; background:var(--card); border:1px solid var(--line); border-radius:14px;
  margin-bottom:14px; overflow:hidden; box-shadow:0 10px 24px -14px rgba(0,0,0,.6); padding:16px 16px 15px 21px; }
.ledger{ position:absolute; left:0; top:0; bottom:0; width:7px; display:flex; flex-direction:column; }
.ledger i{ flex:1; }
.ledger i.fact{ background:var(--good); } .ledger i.cross{ background:#2B8F5B; }
.ledger i.conflict{ background:var(--bad); } .ledger i.unverified{ background:var(--gray); }

.card-top{ display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
.co-name{ font-family:"IBM Plex Serif"; font-weight:600; font-size:17px; line-height:1.28; color:var(--text); }
.co-meta{ margin-top:6px; display:flex; align-items:center; gap:7px; flex-wrap:wrap; }
.tag{ font-family:"IBM Plex Mono",monospace; font-size:10px; font-weight:500; padding:3px 8px; border-radius:5px; }
.tag.mainboard{ background:var(--brand-soft); color:#9FB8F5; }
.tag.sme{ background:#332F14; color:#E4CE6D; }
.tag.q-high{ background:var(--good-soft); color:#63E39F; }
.tag.q-partial{ background:var(--warn-soft); color:#F5C071; }
.tag.q-limited{ background:var(--gray-soft); color:#9AA8C2; }
.tag.q-conflict{ background:var(--bad-soft); color:#F58E8E; }

.ring-wrap{ position:relative; width:58px; height:58px; flex:none; }
.ring-hole{ position:absolute; inset:6px; border-radius:50%; background:var(--card); border:1px dashed #33436B;
  display:flex; flex-direction:column; align-items:center; justify-content:center; }
.ring-hole b{ font-family:"IBM Plex Mono",monospace; font-size:16px; font-weight:600; color:var(--text); line-height:1; }
.ring-hole span{ font-family:"IBM Plex Mono",monospace; font-size:7.5px; color:var(--faint); letter-spacing:.5px; margin-top:1px; }

.stat-grid{ display:grid; grid-template-columns:1fr 1fr; gap:10px 14px; margin-top:15px; padding-top:14px; border-top:1px solid var(--line-soft); }
.stat .k{ font-family:"IBM Plex Mono",monospace; font-size:10px; color:var(--faint); letter-spacing:.4px; text-transform:uppercase; }
.stat .v{ font-family:"IBM Plex Mono",monospace; font-size:14px; font-weight:600; margin-top:3px; color:var(--text); }
.stat .v.good{ color:var(--good); } .stat .v.warn{ color:var(--warn); }
.gmp-flag{ display:inline-flex; align-items:center; gap:4px; margin-left:6px; font-family:"IBM Plex Mono",monospace;
  font-size:9px; font-weight:600; color:var(--bad); background:var(--bad-soft); padding:2px 6px; border-radius:4px; }

.verdict{ margin-top:15px; padding:12px 13px; border-radius:10px; background:var(--good-soft); border:1px solid #1E4A31; }
.verdict.mixed{ background:var(--warn-soft); border-color:#4A3A18; }
.verdict.weak{ background:var(--bad-soft); border-color:#4A1E1E; }
.verdict-head{ display:flex; align-items:center; gap:7px; font-weight:600; font-size:13.5px; color:#8CE8B4; }
.verdict.mixed .verdict-head{ color:#F5C071; } .verdict.weak .verdict-head{ color:#F58E8E; }
.verdict-dot{ width:7px; height:7px; border-radius:50%; background:var(--good); }
.verdict.mixed .verdict-dot{ background:var(--warn); } .verdict.weak .verdict-dot{ background:var(--bad); }
.verdict ul{ margin:9px 0 0; padding-left:16px; font-size:12.5px; color:#C9D6E8; line-height:1.55; }
.verdict .lbl{ font-family:"IBM Plex Mono",monospace; font-size:9.5px; color:var(--faint); letter-spacing:.5px; text-transform:uppercase; margin-top:10px; display:block; }
.verdict .lbl:first-of-type{ margin-top:0; }

.insufficient{ display:flex; align-items:flex-start; gap:10px; padding:13px; border-radius:10px;
  background:var(--gray-soft); border:1px dashed #3A4864; margin-top:15px; }
.insufficient p{ margin:0; font-size:12px; color:var(--muted); line-height:1.55; }
.insufficient b{ color:var(--text); display:block; font-size:13px; margin-bottom:3px; }

.gmp-box{ background:var(--card-2); border:1px solid var(--line); border-radius:10px; padding:12px 13px; margin-top:6px; }
.gmp-box .range{ font-family:"IBM Plex Mono",monospace; font-size:19px; font-weight:600; color:var(--text); }
.gmp-box .range small{ font-size:11px; color:var(--muted); font-weight:500; }
.gmp-box .note{ font-size:11.5px; color:var(--muted); margin-top:6px; line-height:1.5; }
.gmp-box .sources{ margin-top:9px; display:flex; gap:6px; flex-wrap:wrap; }
.src-chip{ font-family:"IBM Plex Mono",monospace; font-size:9.5px; color:var(--faint); border:1px solid var(--line); padding:3px 7px; border-radius:5px; }
.src-chip b{ color:var(--muted); }

.status-pill{ font-family:"IBM Plex Mono",monospace; font-size:8.5px; font-weight:600; padding:2px 6px; border-radius:4px; margin-left:7px; }
.status-pill.fact{ background:var(--good-soft); color:#63E39F; }
.status-pill.cross{ background:#12301F; color:#4FBE84; }
.status-pill.conflict{ background:var(--bad-soft); color:#F58E8E; }
.status-pill.unverified{ background:var(--gray-soft); color:#9AA8C2; }

.risk-tags{ display:flex; gap:7px; flex-wrap:wrap; }
.risk-tag{ font-size:11.5px; padding:6px 10px; border-radius:8px; background:var(--card-2);
  border:1px solid var(--line); color:var(--muted); display:flex; align-items:center; gap:6px; }
.risk-tag .dot{ width:5px; height:5px; border-radius:50%; background:var(--warn); }
.risk-tag.high .dot{ background:var(--bad); }

.a-title{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.6px; text-transform:uppercase;
  color:var(--faint); margin:14px 0 8px; }

.legend{ margin:26px 2px 6px; padding:14px 15px; border-radius:12px; background:var(--card); border:1px solid var(--line); }
.legend-title{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.6px; text-transform:uppercase; color:var(--faint); margin-bottom:10px; }
.legend-row{ display:flex; align-items:center; gap:8px; font-size:11.5px; color:var(--muted); padding:4px 0; }
.legend-row i{ width:8px; height:8px; border-radius:50%; }
.legend-row i.fact{ background:var(--good); } .legend-row i.cross{ background:#2B8F5B; }
.legend-row i.conflict{ background:var(--bad); } .legend-row i.unverified{ background:var(--gray); }

/* Streamlit chrome: tabs, expanders, dataframes styled to match */
.stTabs [data-baseweb="tab-list"]{ gap:4px; }
.stTabs [data-baseweb="tab"]{ font-family:"IBM Plex Mono",monospace !important; font-size:12px !important; color:var(--muted) !important; }
div[data-testid="stExpander"]{ background:var(--card-2) !important; border:1px solid var(--line) !important; border-radius:10px !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Helpers
# ============================================================

def score_ring_svg(score, size=58):
    if score is None:
        return f'''<div class="ring-wrap"><svg viewBox="0 0 58 58" width="{size}" height="{size}">
        <circle cx="29" cy="29" r="25" fill="none" stroke="#1C2740" stroke-width="5"/></svg>
        <div class="ring-hole"><b>&mdash;</b><span>SCORE</span></div></div>'''
    color = '#34C77B' if score >= 65 else ('#F0A93E' if score >= 45 else '#EF5B5B')
    circumference = 157
    offset = circumference - (circumference * score / 100)
    return f'''<div class="ring-wrap"><svg viewBox="0 0 58 58" width="{size}" height="{size}">
    <circle cx="29" cy="29" r="25" fill="none" stroke="#1C2740" stroke-width="5"/>
    <circle cx="29" cy="29" r="25" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"
      stroke-dasharray="{circumference}" stroke-dashoffset="{offset}" transform="rotate(-90 29 29)"/></svg>
    <div class="ring-hole"><b>{score}</b><span>SCORE</span></div></div>'''


def quality_tag(status):
    m = {'HIGH': ('q-high', '\U0001F7E2 HIGH CONFIDENCE'), 'PARTIAL': ('q-partial', '\U0001F7E1 PARTIAL'),
         'LIMITED': ('q-limited', '\U0001F7E0 LIMITED'), 'CONFLICT': ('q-conflict', '\U0001F534 CONFLICT')}
    cls, label = m.get(status, ('q-limited', status))
    return f'<span class="tag {cls}">{label}</span>'


def ledger_strip(obs):
    """Renders the signature verification-ledger strip from real observation statuses."""
    order = ['fact', 'cross', 'conflict', 'unverified']
    status_map = {'FACT': 'fact', 'CROSS_CHECKED': 'cross', 'CONFLICT': 'conflict', 'UNVERIFIED': 'unverified'}
    ticks = [status_map.get(o.get('status', 'UNVERIFIED'), 'unverified') for o in obs] or ['unverified'] * 6
    ticks = ticks[:8] if len(ticks) >= 8 else (ticks * (8 // max(len(ticks), 1) + 1))[:8]
    return '<div class="ledger">' + ''.join(f'<i class="{t}"></i>' for t in ticks) + '</div>'


def render_card(ipo: dict):
    ipo_id = ipo['id']
    obs = db.get_observations(ipo_id)
    by_field = {}
    for o in obs:
        by_field.setdefault(o['field'], []).append(o)

    facts = {}
    for field, rows in by_field.items():
        v = verify_field(field, rows)
        if v['status'] in ('VERIFIED', 'CROSS_CHECKED'):
            try:
                facts[field] = float(v['value'])
            except (TypeError, ValueError):
                facts[field] = v['value']

    gmp_hist = db.gmp_history(ipo_id)
    gmp_obs = [{'source': g['source_name'], 'value': g['gmp_value'], 'observed_at': g['observed_at']} for g in gmp_hist]
    gmp = summarize_gmp(gmp_obs)
    if gmp['low'] is not None and ipo.get('price_high'):
        facts['gmp_pct'] = (gmp['low'] + gmp['high']) / 2 / ipo['price_high'] * 100

    sub_hist = db.subscription_history(ipo_id)
    facts['subscription_total'] = sub_hist[-1]['total'] if sub_hist else None

    score = score_ipo(facts, category=ipo.get('category', 'MAINBOARD'))
    summary = make_summary(facts, score)
    dq = field_quality(obs)

    overall = score['overall']
    cat_cls = 'sme' if ipo.get('category') == 'SME' else 'mainboard'

    gmp_stat_html = 'NOT VERIFIED'
    if gmp['low'] is not None:
        rng = f"₹{gmp['low']:g}" if gmp['low'] == gmp['high'] else f"₹{gmp['low']:g}\u2013₹{gmp['high']:g}"
        flag = '<span class="gmp-flag">\u26A0 CONFLICT</span>' if gmp['status'] == 'CONFLICT' else ''
        gmp_stat_html = f'{rng}{flag}'

    st.markdown(f'''
    <div class="card">
      {ledger_strip(obs)}
      <div class="card-top">
        <div>
          <div class="co-name">{ipo['ipo_name']}</div>
          <div class="co-meta"><span class="tag {cat_cls}">{ipo.get('category','MAINBOARD')}</span>{quality_tag(dq['status'])}</div>
        </div>
        {score_ring_svg(overall)}
      </div>
      <div class="stat-grid">
        <div class="stat"><div class="k">Price band</div><div class="v">{('₹%g–₹%g' % (ipo['price_low'], ipo['price_high'])) if ipo.get('price_low') else 'NOT VERIFIED'}</div></div>
        <div class="stat"><div class="k">GMP (unofficial)</div><div class="v warn">{gmp_stat_html}</div></div>
        <div class="stat"><div class="k">Subscription</div><div class="v good">{format_multiple(facts.get('subscription_total'))}</div></div>
        <div class="stat"><div class="k">Risk score</div><div class="v">{(str(score['risk_score'])+' / 100') if score['risk_score'] is not None else 'NOT VERIFIED'}</div></div>
      </div>
    ''', unsafe_allow_html=True)

    if summary['verdict'].startswith('\u26A0'):
        st.markdown(f'''<div class="insufficient"><p><b>Insufficient verified data</b>
        Critical fields (financial strength / valuation) aren't verified yet — no strong verdict is shown until they are.</p></div>''',
                     unsafe_allow_html=True)
    else:
        vclass = 'mixed' if 'MIXED' in summary['verdict'] else ('weak' if 'WEAK' in summary['verdict'] else '')
        why = ''.join(f'<li>{s}</li>' for s in summary['strengths']) or '<li>No strengths verified yet</li>'
        watch = ''.join(f'<li>{c}</li>' for c in summary['concerns']) or '<li>No concerns flagged yet</li>'
        st.markdown(f'''
        <div class="verdict {vclass}">
          <div class="verdict-head"><span class="verdict-dot"></span> {summary['verdict']}</div>
          <span class="lbl">Why</span><ul>{why}</ul>
          <span class="lbl">Watch</span><ul>{watch}</ul>
        </div>''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander('FULL ANALYSIS'):
        st.markdown('<div class="a-title">Score breakdown</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([
            {'Section': k.replace('_', ' ').title(), 'Score': v['score'], 'Weight %': v['weight_pct']}
            for k, v in score['sections'].items()
        ]), hide_index=True, use_container_width=True)

        if gmp['low'] is not None:
            st.markdown('<div class="a-title">GMP — grey market, unofficial</div>', unsafe_allow_html=True)
            il = indicative_listing(ipo.get('price_high'), gmp['low'], gmp['high'])
            note = ''
            if il:
                note = f"Indicative listing: ₹{il['price_range'][0]:g}\u2013₹{il['price_range'][1]:g} \u2014 <b>indicative only, not guaranteed.</b>"
            src_chips = ''.join(f'<span class="src-chip"><b>{s}</b></span>' for s in gmp['sources'])
            st.markdown(f'''<div class="gmp-box">
              <div class="range">{gmp_stat_html}<small> / issue price ₹{ipo.get('price_high','?'):g}</small></div>
              <div class="note">{note}</div>
              <div class="sources">{src_chips}</div>
            </div>''', unsafe_allow_html=True)

        if sub_hist:
            st.markdown('<div class="a-title">Subscription trend</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(history_series(sub_hist)), hide_index=True, use_container_width=True)

        st.markdown('<div class="a-title">Sources for this IPO</div>', unsafe_allow_html=True)
        if obs:
            st.dataframe(pd.DataFrame([
                {'Field': o['field'], 'Value': o['value_json'], 'Source': o['source_name'],
                 'Fetched': o['fetched_at'], 'Status': o['status']}
                for o in obs
            ]), hide_index=True, use_container_width=True)
        else:
            st.caption('No field-level sources recorded yet for this IPO.')


# ============================================================
# Header
# ============================================================
st.markdown('<div style="display:flex;align-items:center;gap:9px;">'
            '<div style="width:26px;height:26px;border-radius:7px;background:linear-gradient(155deg,#4C7CF3,#2C4FBE);'
            'display:flex;align-items:center;justify-content:center;font-family:\'IBM Plex Mono\';font-weight:600;'
            'font-size:13px;color:#fff;">\u20B9</div>'
            '<div><div style="font-family:\'IBM Plex Serif\';font-weight:600;font-size:16.5px;color:#EDF1F7;">IPO Intelligence</div>'
            '<div style="font-family:\'IBM Plex Mono\';font-weight:500;font-size:9.5px;color:#5C6C88;letter-spacing:.6px;'
            'text-transform:uppercase;">Official-first \u00b7 No-guess policy</div></div></div>', unsafe_allow_html=True)

last = db.last_successful_refresh()
status_text = f"Last verified <b>{last['finished_at'][:16].replace('T',' ')}</b> \u00b7 {last['sources_ok']}/{last['sources_ok']+last['sources_failed']} sources OK" if last else 'No refresh has completed yet'
st.markdown(f'<div class="status-row"><div class="pulse"></div>{status_text}</div>', unsafe_allow_html=True)

if 'result' not in st.session_state:
    st.session_state.result = None

if st.button('\u27F3  REFRESH DATA'):
    with st.spinner('Fetching public IPO sources and validating source health\u2026'):
        st.session_state.result = refresh_all()
    st.success('Refresh completed. Only successfully fetched public data is considered.')

result = st.session_state.result

tab_dashboard, tab_sources, tab_about = st.tabs(['Dashboard', 'Source Health', 'Rules'])

with tab_dashboard:
    ipos = db.list_ipos()
    if not ipos:
        st.info('No confirmed IPOs yet. Run `python scripts/seed_sample_data.py` to see the dashboard '
                 'populated with a labelled synthetic example, or press REFRESH DATA and confirm a '
                 'discovered candidate against a primary source.')
    else:
        today = datetime.date.today().isoformat()
        sections = {
            '\U0001F525 Open IPOs': [i for i in ipos if i.get('open_date') and i.get('close_date') and i['open_date'] <= today <= i['close_date']],
            '\U0001F4C5 Upcoming IPOs': [i for i in ipos if i.get('open_date') and i['open_date'] > today],
            '\U0001F4CC Closing Today': [i for i in ipos if i.get('close_date') == today],
            '\U0001F4CA Recently Listed': [i for i in ipos if i.get('listing_date') and i['listing_date'] <= today],
        }
        for title, group in sections.items():
            if not group:
                continue
            st.markdown(f'<div class="section-label">{title} ({len(group)})</div>', unsafe_allow_html=True)
            for ipo in group:
                render_card(ipo)

    st.markdown('''<div class="legend">
      <div class="legend-title">Verification ledger \u2014 what the strip on each card means</div>
      <div class="legend-row"><i class="fact"></i> FACT \u2014 direct from an official source (SEBI / NSE / BSE / RHP)</div>
      <div class="legend-row"><i class="cross"></i> CROSS-CHECKED \u2014 confirmed by 2+ independent sources</div>
      <div class="legend-row"><i class="conflict"></i> CONFLICT \u2014 sources disagree; shown as a range, never averaged</div>
      <div class="legend-row"><i class="unverified"></i> UNVERIFIED \u2014 not enough evidence yet; never guessed</div>
    </div>''', unsafe_allow_html=True)

    if result:
        st.markdown('<div class="section-label">IPO Candidate Discovery (this refresh)</div>', unsafe_allow_html=True)
        st.caption('Candidates are leads only \u2014 not treated as verified IPO facts until a primary/exchange source confirms them.')
        st.dataframe(result['candidates'][:100], use_container_width=True, hide_index=True)

with tab_sources:
    if not result:
        st.info('Press REFRESH DATA to see source health.')
    else:
        snapshots = result['snapshots']
        good = [x for x in snapshots if 'error' not in x]
        bad = [x for x in snapshots if 'error' in x]
        a, b = st.columns(2)
        a.metric('Sources OK', len(good))
        b.metric('Sources failed', len(bad))
        st.dataframe([{
            'Source': x.get('source', 'unknown'), 'Tier': x.get('tier', ''),
            'Status': 'OK' if 'error' not in x else 'ERROR', 'HTTP': x.get('status_code', ''),
            'Fetched': x.get('fetched_at', ''), 'Error': x.get('error', '')[:120],
        } for x in snapshots], use_container_width=True, hide_index=True)
        with st.expander('Raw source snapshots (for auditing)'):
            for x in snapshots:
                st.markdown(f"**{x.get('source', 'unknown')}**")
                st.json(x)

with tab_about:
    st.markdown('''
- Official filing/exchange data outranks secondary research sites.
- Missing values are never guessed \u2014 shown as `NOT VERIFIED`.
- Conflicting values are shown as a range with a `DATA CONFLICT` flag, never averaged.
- GMP is unofficial and always labelled as such; it never drives the fundamental score.
- Every observation keeps its source, URL and fetch timestamp.
- Calculations are deterministic Python; AI only summarizes already-verified facts.
- Mainboard and SME IPOs use separate scoring weights.
- No CAPTCHA / login / paywall / robots-restriction is ever bypassed.
''')
