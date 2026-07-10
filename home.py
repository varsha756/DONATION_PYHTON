import streamlit as st
from streamlit_lottie import st_lottie
import requests

st.set_page_config(page_title="Donation Transparency Checker", page_icon="🌍", layout="wide")





# Hide sidebar + its collapse arrow, only on this page
st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    [data-testid="collapsedControl"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ... rest of your welcome page code (title, lottie animation, button, etc.)
# Hide default Streamlit menu/footer for a cleaner look
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(15px);}
        to {opacity: 1; transform: translateY(0);}
    }
    .fadeIn {
        animation-name: fadeIn;
        animation-duration: 1.2s;
        animation-fill-mode: both;
    }
    .title-text {
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #2E86C1, #58D68D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle-text {
        text-align: center;
        font-size: 1.2rem;
        color: #AAB7B8;
        margin-bottom: 2rem;
    }
    div.stButton > button {
        display: block;
        margin: 0 auto;
        background-color: #2E86C1;
        color: white;
        font-size: 1.1rem;
        padding: 0.6em 2em;
        border-radius: 12px;
        border: none;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #58D68D;
        transform: scale(1.05);
    }
    </style>

    <h1 class="fadeIn title-text">Donation Transparency Checker</h1>
    <p class="fadeIn subtitle-text">Ensuring NGO accountability with AI-powered transparency analysis</p>
""", unsafe_allow_html=True)


def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except requests.exceptions.RequestException:
        return None


lottie_animation = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if lottie_animation:
        st_lottie(lottie_animation, height=300, key="welcome")
    else:
        st.info("🌍 Transparency you can trust.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 plz login "):
        st.switch_page("pages/login.py")   # match the EXACT filename casing on disk