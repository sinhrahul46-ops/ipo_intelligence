from database import init_db, save_ipo, save_gmp
from collectors import IPOCollector
from analyzer import calculate_scores, generate_ai_summary

def run_refresh():
    init_db()
    collector = IPOCollector()
    ipos = collector.discover_ipos()
    for ipo in ipos:
        gmp_info = collector.fetch_gmp(ipo['id'])
        save_gmp(ipo['id'], gmp_info['raw'], str(gmp_info['raw_sources']))
        financials = collector.verify_financials(ipo['id'])
        scores = calculate_scores(ipo, financials, gmp_info)
        summary = generate_ai_summary(ipo, scores, financials, gmp_info)
        ipo['overall_score'] = scores['overall']
        ipo['risk_score'] = scores['risk']
        ipo['data_confidence'] = "🟢 HIGH CONFIDENCE" if "VERIFIED" in financials['source'] else "🟠 LIMITED"
        ipo['ai_summary'] = summary
        save_ipo(ipo)
    return True
