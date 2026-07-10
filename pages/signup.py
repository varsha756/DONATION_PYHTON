import streamlit as st
import bcrypt
import random
import smtplib, ssl
from email.mime.text import MIMEText
from backened.db import connect_db

st.set_page_config(page_title="Sign Up - Transparency Checker", page_icon="📝", layout="centered")

st.markdown("<h2 style='text-align:center;color:#2E86C1;'>📝 Create Account</h2>", unsafe_allow_html=True)


def send_verification_email(email, code):
    sender = "your_real_gmail@gmail.com"
    app_password = "abcdefghijklmnop"  # the 16-char app password, no spaces"
    msg = MIMEText(f"Your Transparency Checker verification code is: {code}")
    msg["Subject"] = "Email Verification"
    msg["From"] = sender
    msg["To"] = email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, app_password)
        server.sendmail(sender, email, msg.as_string())


username = st.text_input("👤 Username")
email = st.text_input("📧 Gmail Address")
password = st.text_input("🔑 Password", type="password")
confirm_password = st.text_input("🔑 Confirm Password", type="password")
role = st.selectbox("Select Role", ["Donor", "NGO Admin"])

if st.button("Sign Up"):
    if not (username and email and password and confirm_password):
        st.error("⚠️ Please fill all fields.")
    elif password != confirm_password:
        st.error("❌ Passwords do not match.")
    elif len(password) < 6:
        st.error("❌ Password must be at least 6 characters.")
    else:
        conn = connect_db()
        if conn is None:
            st.error("❌ Could not connect to the database.")
        else:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
                if cursor.fetchone():
                    st.error("❌ An account with this email already exists.")
                else:
                    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
                    code = str(random.randint(100000, 999999))

                    cursor.execute(
                        "INSERT INTO users (username, email, password, role, is_verified, verification_code) VALUES (%s,%s,%s,%s,%s,%s)",
                        (username, email, hashed_pw.decode("utf-8"), role, False, code)
                    )
                    conn.commit()

                    try:
                        send_verification_email(email, code)
                        st.success("✅ Account created! Check your Gmail for the verification code, then go to Login to verify.")
                    except Exception:
                        st.warning(f"⚠️ Account created, but email sending failed. DEBUG OTP: {code}")

            except Exception as e:
                st.error(f"Database error: {e}")
            finally:
                cursor.close()
                conn.close()

st.markdown("<p style='text-align:center;'>Already have an account?</p>", unsafe_allow_html=True)
if st.button("Go to Login"):
    st.switch_page("pages/login.py")