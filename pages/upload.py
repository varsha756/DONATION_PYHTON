import streamlit as st
from backened.db import connect_db

st.title("📤 Upload Receipts")

donor = st.text_input("Donor Name")
promised_category = st.text_input("Promised Category")
promised_amount = st.number_input("Promised Amount", min_value=0.0)

if st.button("Save Donation"):
    if donor.strip() == "" or promised_category.strip() == "" or promised_amount <= 0:
        st.error("⚠️ Please fill all fields correctly before saving.")
    else:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO donations (donor_name, promised_category, promised_amount) VALUES (%s,%s,%s)",
            (donor, promised_category, promised_amount)
        )
        conn.commit()
        st.success("✅ Donation saved successfully!")
