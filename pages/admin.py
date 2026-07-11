import streamlit as st
import pandas as pd
import plotly.express as px
import bcrypt
from datetime import date
from backened.db import connect_db

st.set_page_config(page_title="Admin Dashboard", page_icon="🛠️", layout="wide")

st.markdown("""
    <style>
    .admin-header { text-align:center; font-size:2.4rem; font-weight:800; color:#2E86C1; }
    .section-header { font-size:1.6rem; font-weight:700; color:#58D68D; margin-top:10px; }
    .metric-card {
        background-color:#1E2130; padding:20px; border-radius:12px;
        text-align:center; box-shadow:0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-value { font-size:1.9rem; font-weight:700; color:#58D68D; }
    .metric-label { font-size:0.9rem; color:#AAB7B8; }
    </style>
    <h1 class="admin-header">🛠️ Admin Dashboard</h1>
""", unsafe_allow_html=True)
st.caption("Overview, transparency analytics, reports, and user management")
st.markdown("---")

conn = connect_db()
if conn is None:
    st.error("❌ Could not connect to the database.")
    st.stop()


def load_data():
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM ngos ORDER BY transparency_score DESC")
    ngos = pd.DataFrame(cursor.fetchall())

    cursor.execute("SELECT user_id, username, email, role, is_verified FROM users")
    users = pd.DataFrame(cursor.fetchall())

    cursor.execute("""
        SELECT d.id, d.donor_email, d.amount, d.note, d.created_at, n.name AS ngo_name, n.category
        FROM donations d JOIN ngos n ON d.ngo_id = n.id
    """)
    donations = pd.DataFrame(cursor.fetchall())

    cursor.execute("""
        SELECT fr.id, fr.title, fr.category, fr.amount_utilized, fr.description,
               fr.status, fr.report_date, n.name AS ngo_name, n.id AS ngo_id
        FROM fund_reports fr JOIN ngos n ON fr.ngo_id = n.id
    """)
    reports = pd.DataFrame(cursor.fetchall())

    try:
        cursor.execute("SELECT promised_category, SUM(promised_amount) AS total FROM pledges GROUP BY promised_category")
        pledges = pd.DataFrame(cursor.fetchall())
    except Exception:
        pledges = pd.DataFrame()

    cursor.close()

    if not ngos.empty:
        ngos["total_received"] = ngos["total_received"].astype(float)
        ngos["transparency_score"] = ngos["transparency_score"].astype(float)
    if not donations.empty:
        donations["amount"] = donations["amount"].astype(float)
        donations["created_at"] = pd.to_datetime(donations["created_at"])
    if not reports.empty:
        reports["amount_utilized"] = reports["amount_utilized"].astype(float)
        reports["report_date"] = pd.to_datetime(reports["report_date"])
    if not pledges.empty:
        pledges["total"] = pledges["total"].astype(float)

    return ngos, users, donations, reports, pledges


ngo_df, user_df, donation_df, report_df, pledge_df = load_data()

# ==================== TOP METRICS ====================
total_ngos = len(ngo_df)
total_donors = int((user_df["role"] == "Donor").sum()) if not user_df.empty else 0
total_ngo_admins = int((user_df["role"] == "NGO Admin").sum()) if not user_df.empty else 0
total_auditors = int((user_df["role"] == "Auditor").sum()) if not user_df.empty else 0
total_raised = ngo_df["total_received"].sum() if not ngo_df.empty else 0
flagged_count = int(ngo_df["flagged"].sum()) if not ngo_df.empty else 0
avg_score = ngo_df["transparency_score"].mean() if not ngo_df.empty else 0
pending_reports = int((report_df["status"] == "pending").sum()) if not report_df.empty else 0

metrics = [
    (total_ngos, "NGOs Registered"), (total_donors, "Donors"),
    (total_ngo_admins, "NGO Admins"), (total_auditors, "Auditors"),
    (f"₹{total_raised:,.0f}", "Total Raised"), (f"{avg_score:.0f}", "Avg. Transparency Score"),
    (flagged_count, "🚩 Flagged NGOs"), (pending_reports, "⏳ Pending Approvals"),
]
cols = st.columns(4)
for i, (value, label) in enumerate(metrics):
    with cols[i % 4]:
        st.markdown(f"""<div class="metric-card"><div class="metric-value">{value}</div>
                     <div class="metric-label">{label}</div></div>""", unsafe_allow_html=True)
    if i % 4 == 3 and i != len(metrics) - 1:
        cols = st.columns(4)

st.markdown("###")
st.markdown("---")

# ==================== SECTION: DONATIONS OVERVIEW ====================
st.markdown('<p class="section-header">💰 Donations — Filterable</p>', unsafe_allow_html=True)

if donation_df.empty:
    st.info("No donations yet.")
else:
    f1, f2, f3 = st.columns(3)
    with f1:
        date_range = st.date_input(
            "Date range",
            value=(donation_df["created_at"].min().date(), donation_df["created_at"].max().date())
        )
    with f2:
        donor_options = ["All"] + sorted(donation_df["donor_email"].unique().tolist())
        donor_filter = st.selectbox("Donor", donor_options)
    with f3:
        ngo_options = ["All"] + sorted(donation_df["ngo_name"].unique().tolist())
        ngo_filter = st.selectbox("NGO / Project", ngo_options)

    filtered = donation_df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[(filtered["created_at"].dt.date >= start) & (filtered["created_at"].dt.date <= end)]
    if donor_filter != "All":
        filtered = filtered[filtered["donor_email"] == donor_filter]
    if ngo_filter != "All":
        filtered = filtered[filtered["ngo_name"] == ngo_filter]

    st.metric("Total (filtered)", f"₹{filtered['amount'].sum():,.0f}", f"{len(filtered)} donations")
    st.dataframe(
        filtered[["donor_email", "ngo_name", "category", "amount", "note", "created_at"]]
        .rename(columns={"donor_email": "Donor", "ngo_name": "NGO", "category": "Category", "amount": "Amount (₹)", "note": "Note", "created_at": "Date"}),
        use_container_width=True, hide_index=True
    )

st.markdown("---")

# ==================== SECTION: TRANSPARENCY SCORE SUMMARY ====================
st.markdown('<p class="section-header">🏆 Transparency Score Summary</p>', unsafe_allow_html=True)
if not ngo_df.empty:
    s1, s2, s3 = st.columns(3)
    s1.metric("Highest Score", f"{ngo_df['transparency_score'].max():.0f}", ngo_df.loc[ngo_df['transparency_score'].idxmax(), 'name'])
    s2.metric("Lowest Score", f"{ngo_df['transparency_score'].min():.0f}", ngo_df.loc[ngo_df['transparency_score'].idxmin(), 'name'])
    s3.metric("Average Score", f"{avg_score:.1f}")

    board = ngo_df[["name", "category", "transparency_score", "total_received", "flagged"]].copy()
    board.insert(0, "Rank", range(1, len(board) + 1))
    board["flagged"] = board["flagged"].map({1: "🚩 Flagged", 0: "✅ Active"})
    board = board.rename(columns={
        "name": "NGO", "category": "Category", "transparency_score": "Score",
        "total_received": "Total Received (₹)", "flagged": "Status"
    })
    st.dataframe(board, use_container_width=True, hide_index=True)

    fig = px.bar(board.head(10), x="NGO", y="Score", color="Status",
                 color_discrete_map={"✅ Active": "#58D68D", "🚩 Flagged": "#E74C3C"},
                 title="Top 10 NGOs by Transparency Score")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No NGOs registered yet.")

st.markdown("---")

# ==================== SECTION: PENDING APPROVALS ====================
st.markdown('<p class="section-header">⏳ Pending Approvals — Fund Utilization Reports</p>', unsafe_allow_html=True)
if report_df.empty or pending_reports == 0:
    st.success("✅ No pending fund reports.")
else:
    pending = report_df[report_df["status"] == "pending"]
    for _, r in pending.iterrows():
        with st.expander(f"{r['ngo_name']} — {r['title']} — ₹{r['amount_utilized']:,.0f} ({r['category']})"):
            st.write(r["description"])
            c1, c2 = st.columns(2)
            if c1.button("✅ Approve", key=f"approve_{r['id']}"):
                cur = conn.cursor()
                cur.execute("UPDATE fund_reports SET status='approved' WHERE id=%s", (r["id"],))
                conn.commit()
                cur.close()
                st.rerun()
            if c2.button("❌ Reject", key=f"reject_{r['id']}"):
                cur = conn.cursor()
                cur.execute("UPDATE fund_reports SET status='rejected' WHERE id=%s", (r["id"],))
                conn.commit()
                cur.close()
                st.rerun()

st.markdown("---")

# ==================== SECTION: FLAGGED NGOS ====================
st.markdown('<p class="section-header">🚩 Flagged NGOs</p>', unsafe_allow_html=True)
if not ngo_df.empty and flagged_count > 0:
    st.dataframe(
        ngo_df[ngo_df["flagged"] == 1][["name", "category", "flag_reason", "transparency_score"]]
        .rename(columns={"name": "NGO", "category": "Category", "flag_reason": "Reason", "transparency_score": "Score"}),
        use_container_width=True, hide_index=True
    )
else:
    st.success("✅ No flagged NGOs.")

st.markdown("---")

# ==================== SECTION: ANALYTICS ====================
st.markdown('<p class="section-header">📊 Platform Analytics</p>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Fund Distribution by Category (Actual Spending)**")
    if report_df.empty:
        st.info("No fund reports yet.")
    else:
        fd = report_df.groupby("category")["amount_utilized"].sum().reset_index()
        fig = px.pie(fd, names="category", values="amount_utilized", hole=0.4)
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("**Promised vs. Actual by Category**")
    if pledge_df.empty and report_df.empty:
        st.info("No pledge or report data yet.")
    else:
        actual_cat = report_df.groupby("category")["amount_utilized"].sum() if not report_df.empty else pd.Series(dtype=float)
        promised_cat = pledge_df.set_index("promised_category")["total"] if not pledge_df.empty else pd.Series(dtype=float)
        all_cats = sorted(set(actual_cat.index) | set(promised_cat.index))
        comp = pd.DataFrame({
            "Category": all_cats,
            "Promised": [promised_cat.get(c, 0) for c in all_cats],
            "Actual": [actual_cat.get(c, 0) for c in all_cats],
        })
        fig = px.bar(comp, x="Category", y=["Promised", "Actual"], barmode="group")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.markdown("**Transparency Score Comparison**")
    if not ngo_df.empty:
        fig = px.bar(ngo_df.sort_values("transparency_score", ascending=False).head(10),
                     x="name", y="transparency_score", color="flagged",
                     color_discrete_map={0: "#58D68D", 1: "#E74C3C"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with c4:
    st.markdown("**User Base: Donors vs. NGO Admins vs. Auditors**")
    if not user_df.empty:
        role_counts = user_df["role"].value_counts().reset_index()
        role_counts.columns = ["Role", "Count"]
        fig = px.pie(role_counts, names="Role", values="Count", hole=0.4)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("**Donations Over Time**")
if not donation_df.empty:
    time_df = donation_df.groupby(donation_df["created_at"].dt.date)["amount"].sum().reset_index()
    fig = px.line(time_df, x="created_at", y="amount", markers=True)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==================== SECTION: MONTHLY / ANNUAL REPORT ====================
st.markdown('<p class="section-header">🗓️ Generate Transparency Report</p>', unsafe_allow_html=True)

period_type = st.radio("Report period", ["Monthly", "Annual"], horizontal=True)
today = date.today()

if period_type == "Monthly":
    year = st.selectbox("Year", list(range(today.year, today.year - 5, -1)))
    month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1)
    d_mask = (donation_df["created_at"].dt.year == year) & (donation_df["created_at"].dt.month == month) if not donation_df.empty else pd.Series(dtype=bool)
    r_mask = (report_df["report_date"].dt.year == year) & (report_df["report_date"].dt.month == month) if not report_df.empty else pd.Series(dtype=bool)
    period_label = f"{year}-{month:02d}"
else:
    year = st.selectbox("Year", list(range(today.year, today.year - 5, -1)), key="ann_year")
    d_mask = (donation_df["created_at"].dt.year == year) if not donation_df.empty else pd.Series(dtype=bool)
    r_mask = (report_df["report_date"].dt.year == year) if not report_df.empty else pd.Series(dtype=bool)
    period_label = str(year)

period_donations = donation_df[d_mask] if not donation_df.empty else pd.DataFrame()
period_reports = report_df[r_mask] if not report_df.empty else pd.DataFrame()

st.markdown(f"#### Report: {period_label}")
r1, r2, r3 = st.columns(3)
r1.metric("Total Donations", f"₹{period_donations['amount'].sum():,.0f}" if not period_donations.empty else "₹0")
r2.metric("Total Utilized", f"₹{period_reports['amount_utilized'].sum():,.0f}" if not period_reports.empty else "₹0")
utilization_rate = (period_reports['amount_utilized'].sum() / period_donations['amount'].sum() * 100) if not period_donations.empty and period_donations['amount'].sum() > 0 else 0
r3.metric("Utilization Rate", f"{utilization_rate:.1f}%")

if not period_reports.empty:
    cat_summary = period_reports.groupby("category")["amount_utilized"].sum().reset_index()
    fig = px.bar(cat_summary, x="category", y="amount_utilized", title="Spending by Category — " + period_label)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(fig, use_container_width=True)

dl1, dl2 = st.columns(2)
if not period_donations.empty:
    csv = period_donations.to_csv(index=False).encode("utf-8")
    dl1.download_button("📥 Download Donations CSV", csv, file_name=f"donations_{period_label}.csv", mime="text/csv")
if not period_reports.empty:
    csv2 = period_reports.to_csv(index=False).encode("utf-8")
    dl2.download_button("📥 Download Fund Reports CSV", csv2, file_name=f"fund_reports_{period_label}.csv", mime="text/csv")

if period_donations.empty and period_reports.empty:
    st.info("No data for this period.")

st.markdown("---")

# ==================== SECTION: USER MANAGEMENT ====================
st.markdown('<p class="section-header">👥 Manage Users</p>', unsafe_allow_html=True)

if not user_df.empty:
    st.dataframe(
        user_df.rename(columns={"username": "Username", "email": "Email", "role": "Role", "is_verified": "Verified"}),
        use_container_width=True, hide_index=True
    )

st.markdown("#### ➕ Add New Account")
with st.form("add_user_form", clear_on_submit=True):
    new_username = st.text_input("Username")
    new_email = st.text_input("Email")
    new_password = st.text_input("Temporary Password", type="password")
    new_role = st.selectbox("Role", ["Donor", "NGO Admin", "Auditor"])
    submitted = st.form_submit_button("Create Account")

    if submitted:
        if not (new_username and new_email and new_password):
            st.error("⚠️ Fill all fields.")
        else:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE email=%s", (new_email,))
            if cur.fetchone():
                st.error("❌ An account with this email already exists.")
            else:
                hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
                cur.execute(
                    "INSERT INTO users (username, email, password, role, is_verified, verification_code) VALUES (%s,%s,%s,%s,%s,%s)",
                    (new_username, new_email, hashed.decode("utf-8"), new_role, True, "000000")
                )
                conn.commit()
                st.success(f"✅ Account created for {new_email} as {new_role}.")
            cur.close()
            st.rerun()

st.markdown("#### 🔧 Edit / Remove Account")
if not user_df.empty:
    target_email = st.selectbox("Select account", user_df["email"].tolist(), key="edit_target")
    target_row = user_df[user_df["email"] == target_email].iloc[0]

    e1, e2 = st.columns(2)
    with e1:
        new_role_edit = st.selectbox("Change role", ["Donor", "NGO Admin", "Auditor"],
                                      index=["Donor", "NGO Admin", "Auditor"].index(target_row["role"]) if target_row["role"] in ["Donor", "NGO Admin", "Auditor"] else 0,
                                      key="role_edit")
        if st.button("💾 Update Role"):
            cur = conn.cursor()
            cur.execute("UPDATE users SET role=%s WHERE user_id=%s", (new_role_edit, int(target_row["user_id"])))
            conn.commit()
            cur.close()
            st.success("Role updated.")
            st.rerun()

    with e2:
        st.write("")
        st.write("")
        if st.button("🗑️ Delete Account", type="primary"):
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE user_id=%s", (int(target_row["user_id"]),))
            conn.commit()
            cur.close()
            st.success(f"Deleted {target_email}.")
            st.rerun()

st.markdown("---")

# ==================== SECTION: ALL NGOS ====================
st.markdown('<p class="section-header">🏢 All NGOs</p>', unsafe_allow_html=True)
if ngo_df.empty:
    st.info("No NGOs registered yet.")
else:
    cols_show = ["name", "category", "registration_number", "contact_email", "contact_phone", "transparency_score", "total_received", "flagged"]
    cols_show = [c for c in cols_show if c in ngo_df.columns]
    st.dataframe(
        ngo_df[cols_show].rename(columns={
            "name": "Name", "category": "Category", "registration_number": "Reg. No.",
            "contact_email": "Email", "contact_phone": "Phone",
            "transparency_score": "Score", "total_received": "Total Received (₹)", "flagged": "Flagged"
        }),
        use_container_width=True, hide_index=True
    )

st.markdown("#### 🔗 Link NGO Admins Missing a Profile")
cursor = conn.cursor(dictionary=True)
cursor.execute("""
    SELECT u.user_id, u.username, u.email FROM users u
    LEFT JOIN ngos n ON u.email = n.contact_email
    WHERE u.role = 'NGO Admin' AND n.id IS NULL
""")
unlinked = cursor.fetchall()
cursor.execute("SELECT id, name FROM ngos ORDER BY name")
all_ngos = cursor.fetchall()
cursor.close()

if not unlinked:
    st.success("✅ Every NGO Admin is linked.")
else:
    for u in unlinked:
        with st.expander(f"{u['username']} — {u['email']}"):
            if all_ngos:
                chosen = st.selectbox("Link to NGO", options=[n["id"] for n in all_ngos],
                                       format_func=lambda x: next(n["name"] for n in all_ngos if n["id"] == x),
                                       key=f"sel_{u['user_id']}")
                if st.button("🔗 Link", key=f"lnk_{u['user_id']}"):
                    cur = conn.cursor()
                    cur.execute("UPDATE ngos SET contact_email=%s WHERE id=%s", (u["email"], chosen))
                    conn.commit()
                    cur.close()
                    st.rerun()

conn.close()