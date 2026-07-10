import streamlit as st
import os
import pandas as pd
import plotly.express as px
from datetime import date
from backened.db import connect_db

st.set_page_config(page_title="Fund Utilization Reports", page_icon="📊", layout="wide")

if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "NGO Admin":
    st.warning("⚠️ This page is only for NGO Admins. Please log in with an NGO account.")
    st.stop()

UPLOAD_DIR = "uploads/fund_report_proofs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.markdown("""
    <style>
    .fr-header {
        text-align: center; font-size: 2.3rem; font-weight: 800; color: #2E86C1;
    }
    .metric-card {
        background-color: #1E2130; padding: 20px; border-radius: 12px;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-value { font-size: 1.7rem; font-weight: 700; color: #58D68D; }
    .metric-label { font-size: 0.9rem; color: #AAB7B8; }
    div.stButton > button {
        background: linear-gradient(90deg, #2E86C1, #58D68D);
        color: white; border: none; border-radius: 10px; padding: 0.6em 2em; font-weight: 600;
    }
    </style>
    <h1 class="fr-header">📊 Fund Utilization Reports</h1>
""", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#AAB7B8;'>Show donors exactly how their contributions were used</p>", unsafe_allow_html=True)
st.markdown("---")

conn = connect_db()
if conn is None:
    st.error("❌ Could not connect to the database.")
    st.stop()

cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT id, name, total_received FROM ngos WHERE contact_email=%s", (st.session_state["user_email"],))
ngo = cursor.fetchone()
cursor.close()

if not ngo:
    st.error("❌ No NGO profile linked to this account. Please contact the platform admin.")
    st.stop()

tab1, tab2 = st.tabs(["➕ Submit New Report", "📋 View Past Reports & Utilization"])

# ---------------- TAB 1: SUBMIT REPORT ----------------
with tab1:
    st.subheader(f"Submit a Fund Utilization Report — {ngo['name']}")

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Report Title*", placeholder="e.g., Q2 2026 Medical Camp Expenses")
        category = st.selectbox("Category", ["Medical/Health", "Education", "Food & Nutrition", "Infrastructure", "Salaries/Admin", "Disaster Relief", "Other"])
        amount_utilized = st.number_input("Amount Utilized (₹)*", min_value=1.0, step=100.0)
        report_date = st.date_input("Report Date", value=date.today())
    with col2:
        description = st.text_area("Description*", placeholder="Explain what this money was spent on, how many people benefited, etc.")
        proof_doc = st.file_uploader("Upload Proof (bills, photos, invoices)", type=["pdf", "png", "jpg", "jpeg"])
        if proof_doc and proof_doc.type.startswith("image"):
            st.image(proof_doc, width=200, caption="Preview")
        elif proof_doc:
            st.write(f"📄 {proof_doc.name} attached")

    if st.button("✅ Submit Report", use_container_width=True):
        if not (title and description and amount_utilized > 0):
            st.error("⚠️ Please fill all required fields (marked with *).")
        else:
            proof_path = None
            if proof_doc:
                file_ext = proof_doc.name.split(".")[-1]
                safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
                proof_path = os.path.join(UPLOAD_DIR, f"{ngo['id']}_{safe_title}.{file_ext}")
                with open(proof_path, "wb") as f:
                    f.write(proof_doc.getbuffer())

            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO fund_reports (ngo_id, title, category, amount_utilized, description, proof_document_path, report_date)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (ngo["id"], title, category, amount_utilized, description, proof_path, report_date))
                conn.commit()
                cur.close()
                st.success("✅ Fund utilization report submitted successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Database error: {e}")

# ---------------- TAB 2: VIEW REPORTS ----------------
with tab2:
    st.subheader(f"Utilization Summary — {ngo['name']}")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fund_reports WHERE ngo_id=%s ORDER BY report_date DESC", (ngo["id"],))
    reports = cursor.fetchall()
    cursor.close()

    total_received = float(ngo["total_received"] or 0)
    total_utilized = sum(float(r["amount_utilized"]) for r in reports) if reports else 0
    utilization_pct = (total_utilized / total_received * 100) if total_received > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Received", f"₹{total_received:,.0f}")
    col2.metric("📤 Total Reported as Utilized", f"₹{total_utilized:,.0f}")
    col3.metric("📊 Utilization Rate", f"{utilization_pct:.1f}%")

    if total_received > 0:
        if utilization_pct < 30:
            st.warning("⚠️ Low utilization reporting — consider submitting more fund usage reports to maintain donor trust.")
        elif utilization_pct > 100:
            st.error("🚩 Reported utilization exceeds total funds received — please review your entries for accuracy.")
        else:
            st.success("✅ Utilization reporting looks healthy.")

    st.markdown("###")

    if not reports:
        st.info("No fund utilization reports submitted yet.")
    else:
        df = pd.DataFrame(reports)

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("📈 Utilization by Category")
            cat_df = df.groupby("category")["amount_utilized"].sum().reset_index()
            fig = px.pie(cat_df, names="category", values="amount_utilized", hole=0.4)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            st.subheader("📅 Utilization Over Time")
            time_df = df.groupby("report_date")["amount_utilized"].sum().reset_index()
            fig2 = px.bar(time_df, x="report_date", y="amount_utilized")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.subheader("🧾 Report History")
        for r in reports:
            with st.expander(f"{r['title']} — ₹{r['amount_utilized']:,.0f} ({r['category']}) — {r['report_date']}"):
                st.write(f"**Description:** {r['description']}")
                if r["proof_document_path"] and os.path.exists(r["proof_document_path"]):
                    if r["proof_document_path"].lower().endswith((".png", ".jpg", ".jpeg")):
                        st.image(r["proof_document_path"], width=250)
                    else:
                        st.write(f"📄 Proof document: {r['proof_document_path']}")
                else:
                    st.caption("No proof document uploaded.")

conn.close()