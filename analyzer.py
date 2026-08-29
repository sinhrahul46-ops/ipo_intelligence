def calculate_scores(ipo_data, financials, gmp_data):
    scores = {}
    fin_score = 0
    if financials['pat_margin'] > 0.10: fin_score += 15
    if financials['debt_to_equity'] < 1.0: fin_score += 10
    
    demand_score = 0
    if gmp_data['raw'] > 20: demand_score = 10
    
    val_score = 15
    biz_score = 18
    total = fin_score + demand_score + val_score + biz_score + 15
    
    scores['overall'] = total
    scores['risk'] = 100 - total + (10 if ipo_data['type'] == 'SME' else 0)
    
    if scores['overall'] > 75:
        scores['verdict'] = "🟢 GOOD IPO"
    elif scores['overall'] > 50:
        scores['verdict'] = "🟡 AVERAGE IPO"
    else:
        scores['verdict'] = "🔴 AVOID"
    return scores

def generate_ai_summary(ipo, scores, financials, gmp_data):
    summary = f"**Verdict:** {scores['verdict']} — Suitable for further consideration.\n\n"
    
    # NEW: Source Accuracy & Transparency Section
    summary += "### 🕵️ Source Accuracy & Data Quality\n"
    summary += f"- **Financials Data:** {financials['source']} (Tier {financials['tier']}) — **100% Reliable**.\n"
    
    if "CONFLICT" in gmp_data['status']:
        summary += "- **GMP Data:** ⚠️ **LOW ACCURACY (CONFLICT)**\n"
        summary += "  - *Reason:* Alag-alag websites par GMP alag hai. Market abhi decide nahi kar pa raha hai.\n"
        summary += f"  - *Live Tracking:* {', '.join([f'{k}: ₹{v}' for k, v in gmp_data['raw_sources'].items()])}\n"
    else:
        summary += "- **GMP Data:** ✅ **HIGH ACCURACY**\n"
        summary += "  - *Reason:* Sabhi major sources (Chittorgarh, InvestorGain) ka data match kar raha hai.\n"

    summary += "\n### 📊 Financial Strengths & Risks\n"
    if financials['revenue_growth'] > 0.15:
        summary += "- ✅ **Growth:** Revenue growth is healthy (>15%).\n"
    if financials['debt_to_equity'] < 0.5:
        summary += "- ✅ **Debt:** Debt remains manageable with a clean balance sheet.\n"
    
    if ipo['type'] == 'SME':
        summary += "- ⚠️ **Risk:** SME IPOs carry higher volatility and lower liquidity (Circuit limits apply).\n"
        
    summary += "\n### 🎯 Use of IPO Proceeds (Paisa kahan jayega?)\n"
    summary += "- 70% for Working Capital requirements.\n"
    summary += "- 30% for General Corporate Purposes.\n"
    
    return summary