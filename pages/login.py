import streamlit as st
import random
import bcrypt
import smtplib, ssl
from email.mime.text import MIMEText
from backened.db import connect_db

st.set_page_config(page_title="Login - Transparency Checker", page_icon="🔐", layout="centered")

st.markdown("<h2 style='text-align:center;color:#2E86C1;'>🔐 User Login</h2>", unsafe_allow_html=True)

# Gmail verification function
def send_verification_email(email, code):
    sender = st.secrets["email"]["sender"]
    password = st.secrets["email"]["app_password"]
    msg = MIMEText(f"Your Transparency Checker verification code is: {code}")
    msg["Subject"] = "Email Verification"
    msg["From"] = sender
    msg["To"] = email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, email, msg.as_string())

# Login form
username = st.text_input("👤 Username")
email = st.text_input("📧 Gmail Address")
password = st.text_input("🔑 Password", type="password")
role = st.selectbox("Select Role", ["Donor", "NGO Admin"])

if st.button("Register"):
    if username and email and password:
        conn = connect_db()
        cursor = conn.cursor()

        # Generate verification code
        code = str(random.randint(100000, 999999))
        st.write("DEBUG OTP:", code)   # temporary, shows OTP in Streamlit

        try:
            hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (username,email,password,role,verification_code) VALUES (?,?,?,?,?)",
                (username, email, hashed_pw.decode("utf-8"), role, code)
            )
            conn.commit()

            send_verification_email(email, code)
            st.success("✅ Registered successfully! Check your Gmail for verification code.")
        except Exception as e:
            st.error(f"Database error: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        st.error("⚠️ Please fill all fields.")


# Verification step
verification_code = st.text_input("Enter Verification Code")
if st.button("Verify Email"):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE email=? AND verification_code=?",
            (email, verification_code)
        )
        user = cursor.fetchone()

        if user:
            cursor.execute("UPDATE users SET is_verified=1 WHERE email=?", (email,))
            conn.commit()
            st.success("Email verified successfully!")
        else:
            st.error("Invalid verification code.")
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")