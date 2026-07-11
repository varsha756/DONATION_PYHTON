import streamlit as st
import pandas as pd
import plotly.express as px
from backened.rules import check_transparency
from backened.ai_api import ai_reasoning
from backened.db import connect_db

st.set_page_config(page_title="Transparency Analysis", page_icon="🔍", layout="wide")
st.title("🔍 Transparency Analysis")

REPORT_CATEGORIES = ["Medical/Health", "Education", "Food & Nutrition", "Infrastructure", "Salaries/Admin", "Disaster Relief", "Other"]


def get_data_from_db():
    """Fetches and aggregates promised vs. actual spending, and recent NGO report text."""
    conn = connect_db()
    cursor = conn.cursor()

    # --- Promised (from donor pledges) ---
    cursor.execute("SELECT promised_category, SUM(promised_amount) FROM pledges GROUP BY promised_category")
    promised_data = cursor.fetchall()
    promised = {category: float(amount) for category, amount in promised_data}

    # --- Actual (from NGO-submitted fund utilization reports) ---
    cursor.execute("SELECT category, SUM(amount_utilized) FROM fund_reports GROUP BY category")
    actual_data = cursor.fetchall()
    actual = {category: float(amount) for category, amount in actual_data}

    # Make sure every known category appears in both dicts, even if zero
    for cat in REPORT_CATEGORIES:
        promised.setdefault(cat, 0.0)
        actual.setdefault(cat, 0.0)

    # --- Receipt text for AI analysis: pull real, recent NGO report descriptions ---
    cursor.execute("""
        SELECT n.name, fr.description
        FROM fund_reports fr
        JOIN ngos n ON fr.ngo_id = n.id
        ORDER BY fr.report_date DESC
        LIMIT 20
    """)
    report_rows = cursor.fetchall()
    if report_rows:
        receipt_text = "\n".join(f"{name}: {desc}" for name, desc in report_rows)
    else:
        receipt_text = "No fund utilization reports submitted yet."

    cursor.close()
    conn.close()
    return promised, actual, receipt_text


def save_analysis_log(rule_result, ai_explanation):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO analysis_log (rule_result, ai_result) VALUES (%s,%s)",
        ("; ".join(rule_result), ai_explanation)
    )
    conn.commit()
    cursor.close()
    conn.close()


if st.button("▶️ Run Analysis", use_container_width=True):
    promised, actual, receipt_text = get_data_from_db()
    rule_result = check_transparency(promised, actual)
    ai_result = ai_reasoning(receipt_text)

    st.markdown("---")

    # ---------- Promised vs Actual chart ----------
    st.subheader("📊 Promised vs. Actual Spending by Category")
    df = pd.DataFrame({
        "Category": list(promised.keys()),
        "Promised": [promised[c] for c in promised],
        "Actual": [actual.get(c, 0.0) for c in promised],
    })
    fig = px.bar(df, x="Category", y=["Promised", "Actual"], barmode="group")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

    # ---------- Rule-based findings ----------
    st.subheader("🔍 Rule-Based Findings")
    if not rule_result:
        st.info("No rule-based findings returned.")
    else:
        for issue in rule_result:
            if "mismatch" in issue.lower():
                st.warning(f"⚠️ {issue}")
            else:
                st.success(f"✅ {issue}")

    # ---------- AI reasoning ----------
    st.subheader("🤖 AI Reasoning")
    st.info(ai_result.get("explanation", "No explanation returned."))

    with st.expander("📄 Source text analyzed by AI"):
        st.text(receipt_text)

    # ---------- Persist this run ----------
    save_analysis_log(rule_result, ai_result.get("explanation", ""))
    st.caption("✅ This analysis run was logged.")

st.markdown("---")

# ---------- Past analysis runs ----------
st.subheader("🧾 Past Analysis Runs")
conn = connect_db()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM analysis_log ORDER BY run_at DESC LIMIT 10")
logs = cursor.fetchall()
cursor.close()
conn.close()

if not logs:
    st.caption("No past analysis runs yet.")
else:
    for log in logs:
        with st.expander(f"Run at {log['run_at'].strftime('%d %b %Y, %I:%M %p')}"):
            st.write("**Rule-based:**", log["rule_result"])
            st.write("**AI Reasoning:**", log["ai_result"])