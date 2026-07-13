import streamlit as st
import os
import io
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from backened.db import connect_db

st.set_page_config(page_title="Make a Donation", page_icon="💝", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("⚠️ Please log in to make a donation.")
    st.stop()

UPLOAD_DIR = "uploads/payment_proofs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.markdown("""
    <style>
    .donate-header {
        text-align: center; font-size: 2.5rem; font-weight: 800;
        background: linear-gradient(90deg, #E74C3C, #F39C12);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .score-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.85rem; font-weight: 600; background-color: #27AE60; color: white;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #E74C3C, #F39C12);
        color: white; border: none; border-radius: 10px; padding: 0.6em 2em; font-weight: 600;
    }
    </style>
    <h1 class="donate-header">💝 Make a Donation</h1>
""", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#AAB7B8;'>Every contribution is tracked for full transparency</p>", unsafe_allow_html=True)
st.markdown("---")

conn = connect_db()
if conn is None:
    st.error("❌ Could not connect to the database.")
    st.stop()

cursor = conn.cursor()
cursor.execute("SELECT id, name, category, transparency_score, image_path, upi_id FROM ngos ORDER BY transparency_score DESC")
ngos = cursor.fetchall()
cursor.close()

if not ngos:
    st.info("No NGOs available yet.")
    st.stop()

# ---------- STEP 1: Choose NGO ----------
st.subheader("1️⃣ Choose an NGO")
cols = st.columns(4)
if "selected_ngo_id" not in st.session_state:
    st.session_state.selected_ngo_id = ngos[0]["id"]

for i, ngo in enumerate(ngos):
    with cols[i % 4]:
        with st.container(border=True):
            if ngo["image_path"] and os.path.exists(ngo["image_path"]):
                st.image(ngo["image_path"], use_container_width=True)
            else:
                st.markdown("🏢")
            st.markdown(f"**{ngo['name']}**")
            st.caption(ngo["category"])
            st.markdown(f"<span class='score-badge'>Score: {ngo['transparency_score']}</span>", unsafe_allow_html=True)
            if st.button("Select", key=f"select_{ngo['id']}", use_container_width=True):
                st.session_state.selected_ngo_id = ngo["id"]

selected_ngo = next(n for n in ngos if n["id"] == st.session_state.selected_ngo_id)
st.success(f"Selected NGO: **{selected_ngo['name']}**")

st.markdown("---")

# ---------- STEP 2: Enter amount + show QR ----------
st.subheader("2️⃣ Enter Amount & Pay via QR")
col1, col2 = st.columns([1, 1])

with col1:
    amount = st.number_input("Donation Amount (₹)", min_value=1.0, step=100.0)
    note = st.text_input("Note (optional)", placeholder="e.g., For flood relief campaign")

with col2:
    upi_id = selected_ngo["upi_id"] or "demo@upi"
    upi_string = f"upi://pay?pa={upi_id}&pn={selected_ngo['name'].replace(' ', '%20')}&am={amount:.2f}&cu=INR&tn=Donation"

    qr_img = qrcode.make(upi_string)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    st.image(buf.getvalue(), width=220, caption=f"Scan to pay ₹{amount:,.0f} to {selected_ngo['name']}")
    st.caption(f"UPI ID: {upi_id}")
    st.caption("⚠️ Demo QR — verify UPI ID is real before relying on it for actual payments.")

proof = st.file_uploader("Upload Payment Screenshot (after paying)", type=["png", "jpg", "jpeg"])
if proof:
    st.image(proof, width=180, caption="Proof Preview")

st.markdown("---")

# ---------- STEP 3: Confirm + generate receipt ----------
st.subheader("3️⃣ Confirm Payment & Get Receipt")

def build_receipt_pdf(donor_name, donor_email, ngo, amount, note, receipt_no):
    buf = io.BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#1B4332"), alignment=TA_CENTER)
    sub_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=14)
    section = ParagraphStyle("Sec", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#1B4332"), spaceBefore=10, spaceAfter=6)
    normal = ParagraphStyle("N", parent=styles["Normal"], fontSize=10.5, leading=15)

    story = []
    story.append(Paragraph(ngo["name"], title_style))
    story.append(Paragraph(ngo["category"] or "", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#1B4332")))
    story.append(Spacer(1, 10))
    story.append(Paragraph("DONATION RECEIPT", ParagraphStyle("RT", parent=styles["Heading1"], fontSize=15, alignment=TA_CENTER, spaceAfter=14)))

    meta = Table([["Receipt No.:", receipt_no, "Date:", datetime.now().strftime("%d %b %Y")]],
                 colWidths=[70*mm, 50*mm, 30*mm, 40*mm])
    meta.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 10.5), ("FONTNAME", (0,0), (0,0), "Helvetica-Bold"), ("FONTNAME", (2,0), (2,0), "Helvetica-Bold")]))
    story.append(meta)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Donor Details", section))
    donor_table = Table([["Name:", donor_name], ["Email:", donor_email]], colWidths=[40*mm, 130*mm])
    donor_table.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 10.5), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold")]))
    story.append(donor_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Donation Details", section))
    donation_table = Table([["Description", "Amount (INR)"], [note or "General Donation", f"Rs. {amount:,.2f}"]], colWidths=[130*mm, 40*mm])
    donation_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1B4332")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10.5),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(donation_table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"Thank you for your generous contribution to {ngo['name']}. This receipt confirms the above donation has been recorded.",
        normal
    ))

    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
    doc.build(story)
    buf.seek(0)
    return buf


if st.button("✅ I've Paid — Confirm Donation", use_container_width=True):
    if amount <= 0:
        st.error("⚠️ Please enter a valid donation amount.")
    else:
        proof_path = None
        if proof:
            file_ext = proof.name.split(".")[-1]
            safe_email = st.session_state["user_email"].replace("@", "_at_")
            proof_path = os.path.join(UPLOAD_DIR, f"{safe_email}_{selected_ngo['id']}_{amount}.{file_ext}")
            with open(proof_path, "wb") as f:
                f.write(proof.getbuffer())

        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO donations (donor_email, ngo_id, amount, payment_proof_path, note)
                VALUES (?,?,?,?,?)
            """, (st.session_state["user_email"], selected_ngo["id"], amount, proof_path, note))
            conn.commit()
            donation_id = cur.lastrowid
            cur.execute("UPDATE ngos SET total_received = total_received + ? WHERE id=?", (amount, selected_ngo["id"]))
            conn.commit()
            cur.close()

            st.success(f"✅ Donation recorded! ₹{amount:,.0f} to {selected_ngo['name']}.")
            st.balloons()

            receipt_no = f"DON-{donation_id:05d}"
            pdf_buf = build_receipt_pdf(
                st.session_state["user_email"].split("@")[0].title(),
                st.session_state["user_email"],
                selected_ngo, amount, note, receipt_no
            )
            st.download_button(
                "📄 Download Receipt (PDF)",
                data=pdf_buf,
                file_name=f"receipt_{receipt_no}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Database error: {e}")

conn.close()