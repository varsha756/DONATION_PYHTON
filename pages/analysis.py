import streamlit as st
from backened.rules import check_transparency
from backened.ai_api import ai_reasoning
from backened.db import connect_db

from backened.db import connect_db

conn = connect_db()
if conn:
    cursor = conn.cursor()
    # ... do your query
    cursor.close()
    conn.close()
else:
    st.error("Could not connect to the database.")
    
st.title("🔍 Transparency Analysis")

def get_data_from_db():
    """Fetches and aggregates donation data from the database."""
    conn = connect_db()
    cursor = conn.cursor()

    # --- Promised Donations ---
    # Fetches all donations and aggregates them by category
    cursor.execute("SELECT promised_category, SUM(promised_amount) FROM donations GROUP BY promised_category")
    promised_data = cursor.fetchall()
    promised = {category: float(amount) for category, amount in promised_data}

    # --- Actual Spending (Placeholder) ---
    # In a real application, this data would come from another table
    # where the NGO records its expenses.
    # For now, we'll use a hardcoded example.
    actual = {"Education": 4500, "Healthcare": 2800, "Logistics": 500}

    # --- Receipt Text for AI Analysis (Placeholder) ---
    # This would likely be fetched from a database field linked to expenses.
    receipt_text = "Expense report: consultancy fees for project setup, and miscellaneous office supplies."

    conn.close()
    return promised, actual, receipt_text


if st.button("Run Analysis"):
    promised, actual, receipt_text = get_data_from_db()
    rule_result = check_transparency(promised, actual)
    ai_result = ai_reasoning(receipt_text)
    st.write("Rule-based Check:", rule_result)
    st.write("AI Reasoning:", ai_result["explanation"])
