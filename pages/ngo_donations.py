import streamlit as st
import pandas as pd
from backened.db import connect_db

st.set_page_config(page_title="NGO Management", page_icon="🏢", layout="wide")

st.markdown("<h1>🏢 NGO Management System</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#AAB7B8;'>Add, view, and manage registered NGOs</p>", unsafe_allow_html=True)
st.markdown("---")

conn = connect_db()
if conn is None:
    st.error("❌ Could not connect to the database.")
    st.stop()

tab1, tab2 = st.tabs(["➕ Add New NGO", "📋 Manage Existing NGOs"])

# ---------------- TAB 1: ADD NGO ----------------
with tab1:
    st.subheader("Register a New NGO")

    with st.form("add_ngo_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("NGO Name*")
            category = st.selectbox(
                "Category",
                ["Education", "Health", "Environment", "Poverty Relief", "Disaster Relief", "Animal Welfare", "Other"]
            )
            registration_number = st.text_input("Government Registration Number*")
            contact_email = st.text_input("Contact Email*")
        with col2:
            contact_phone = st.text_input("Contact Phone")
            services = st.text_area("Services Offered (comma-separated)", placeholder="e.g., Child Education, Medical Camps, Food Distribution")
            description = st.text_area("Short Description", placeholder="What does this NGO do? Their mission, past work, etc.")

        submitted = st.form_submit_button("✅ Register NGO", use_container_width=True)

    if submitted:
        if not (name and registration_number and contact_email):
            st.error("⚠️ Please fill all required fields (marked with *).")
        else:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM ngos WHERE registration_number=%s", (registration_number,))
                if cursor.fetchone():
                    st.error("❌ An NGO with this registration number already exists.")
                else:
                    cursor.execute("""
                        INSERT INTO ngos (name, category, registration_number, contact_email, contact_phone, services, description)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (name, category, registration_number, contact_email, contact_phone, services, description))
                    conn.commit()
                    st.success(f"✅ '{name}' has been registered successfully!")
            except Exception as e:
                st.error(f"Database error: {e}")
            finally:
                cursor.close()
               

             

# ---------------- TAB 2: MANAGE NGOs ----------------
with tab2:
    st.subheader("All Registered NGOs")

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ngos ORDER BY created_at DESC")
    ngos = cursor.fetchall()
    cursor.close()

    if not ngos:
        st.info("No NGOs registered yet. Add one from the 'Add New NGO' tab.")
    else:
        search = st.text_input("🔍 Search NGO by name")
        filtered = [n for n in ngos if search.lower() in n["name"].lower()] if search else ngos

        for ngo in filtered:
            status = "🚩 Flagged" if ngo["flagged"] else "✅ Active"
            with st.expander(f"{ngo['name']} — {ngo['category']} — {status}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Registration No.:** {ngo['registration_number']}")
                    st.write(f"**Email:** {ngo['contact_email']}")
                    st.write(f"**Phone:** {ngo['contact_phone'] or 'N/A'}")
                    st.write(f"**Transparency Score:** {ngo['transparency_score']}")
                with c2:
                    st.write(f"**Services:** {ngo['services'] or 'N/A'}")
                    st.write(f"**Total Received:** ₹{ngo['total_received']:,.0f}")
                    st.write(f"**Description:** {ngo['description'] or 'N/A'}")

                st.markdown("---")
                b1, b2, b3 = st.columns(3)

                with b1:
                    new_score = st.number_input(
                        "Update Score", min_value=0, max_value=100,
                        value=ngo["transparency_score"], key=f"score_{ngo['id']}"
                    )
                    if st.button("💾 Save Score", key=f"save_{ngo['id']}"):
                        cur = conn.cursor()
                        cur.execute("UPDATE ngos SET transparency_score=%s WHERE id=%s", (new_score, ngo["id"]))
                        conn.commit()
                        cur.close()
                        st.success("Score updated.")
                        st.rerun()

                with b2:
                    if ngo["flagged"]:
                        if st.button("✅ Unflag NGO", key=f"unflag_{ngo['id']}"):
                            cur = conn.cursor()
                            cur.execute("UPDATE ngos SET flagged=FALSE, flag_reason=NULL WHERE id=%s", (ngo["id"],))
                            conn.commit()
                            cur.close()
                            st.rerun()
                    else:
                        reason = st.text_input("Flag reason", key=f"reason_{ngo['id']}")
                        if st.button("🚩 Flag NGO", key=f"flag_{ngo['id']}"):
                            cur = conn.cursor()
                            cur.execute("UPDATE ngos SET flagged=TRUE, flag_reason=%s WHERE id=%s", (reason, ngo["id"]))
                            conn.commit()
                            cur.close()
                            st.rerun()

                with b3:
                    if st.button("🗑️ Delete NGO", key=f"delete_{ngo['id']}"):
                        cur = conn.cursor()
                        cur.execute("DELETE FROM ngos WHERE id=%s", (ngo["id"],))
                        conn.commit()
                        cur.close()
                        st.success(f"Deleted {ngo['name']}.")
                        st.rerun()

conn.close()