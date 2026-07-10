import streamlit as st
import pandas as pd
import plotly.express as px
import os
from backened.db import connect_db

st.set_page_config(page_title="My Donations", page_icon="📜", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("⚠️ Please log in to view your donations.")
    st.stop()

st.markdown("""
    <style>
    .history-header {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        color: #58D68D;
    }
    .metric-card {
        background-color: #1E2130;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #58D68D; }
    .metric-label { font-size: 0.9rem; color: #AAB7B8; }
    </style>
    <h1 class="history-header">📜 My Donations</h1>
""", unsafe_allow_html=True)
st.markdown("---")

conn = connect_db()
cursor = conn.cursor(dictionary=True)
cursor.execute("""
    SELECT d.id, n.name AS ngo_name, n.category, d.amount, d.note, d.payment_proof_path, d.created_at
    FROM donations d
    JOIN ngos n ON d.ngo_id = n.id
    WHERE d.donor_email = %s
    ORDER BY d.created_at DESC
""", (st.session_state["user_email"],))
rows = cursor.fetchall()
cursor.close()
conn.close()

if not rows:
    st.info("You haven't made any donations yet. Head to the Donate page to get started!")
    st.stop()

df = pd.DataFrame(rows)
total_given = df["amount"].sum()
ngo_count = df["ngo_name"].nunique()

col1, col2, col3 = st.columns(3)
for col, value, label in zip(
    [col1, col2, col3],
    [f"₹{total_given:,.0f}", ngo_count, len(df)],
    ["Total Donated", "NGOs Supported", "Total Donations Made"]
):
    with col:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("###")

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.subheader("📈 Donations Over Time")
    time_df = df.groupby(df["created_at"].dt.date)["amount"].sum().reset_index()
    fig = px.line(time_df, x="created_at", y="amount", markers=True)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("🥧 Donations by NGO")
    ngo_df = df.groupby("ngo_name")["amount"].sum().reset_index()
    fig2 = px.pie(ngo_df, names="ngo_name", values="amount", hole=0.4)
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.subheader("🧾 Donation History")

for r in rows:
    with st.expander(f"₹{r['amount']:,.0f} → {r['ngo_name']} ({r['category']}) — {r['created_at'].strftime('%d %b %Y')}"):
        st.write(f"**Note:** {r['note'] or 'None'}")
        if r["payment_proof_path"] and os.path.exists(r["payment_proof_path"]):
            if r["payment_proof_path"].lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(r["payment_proof_path"], width=250)
            else:
                st.write(f"📄 Proof: {r['payment_proof_path']}")
        else:
            st.caption("No proof uploaded.")