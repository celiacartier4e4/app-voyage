import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="Mon Organisateur de Voyage",
    page_icon="✈️",
    layout="centered"
)

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #f093fb 50%, #f5576c 100%);
    }
    h1, h2, h3, p, label {
        color: white !important;
    }
    .stButton>button {
        background-color: #ff6b35;
        color: white;
        border-radius: 20px;
        padding: 10px 25px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
    }
    .stButton>button:hover {
        background-color: #ffcc00;
        color: black;
    }
    .stTextInput>div>input {
        border-radius: 15px;
        border: 2px solid white;
        background-color: rgba(255,255,255,0.9);
        font-size: 16px;
    }
    .stSelectbox>div>div {
        border-radius: 15px;
        background-color: rgba(255,255,255,0.9);
    }
    .stNumberInput>div>div>input {
        border-radius: 15px;
        background-color: rgba(255,255,255,0.9);
    }
    .stSuccess {
        background-color: rgba(255,255,255,0.2) !important;
        border-radius: 15px;
    }
    .stSpinner {
        color: white !important;
    }
    div[data-testid="stMarkdownContainer"] p {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("# ✈️ Mon Organisateur de Voyage")
st.markdown("### 🌍 Dis moi où tu veux aller, et je t'organise ton voyage !")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    destination = st.text_input("📍 Ta destination")

with col2:
    jours = st.number_input("📅 Nombre de jours", min_value=1, value=5)

with col3:
    budget = st.selectbox("💰 Ton budget", ["Petit budget", "Moyen", "Confortable"])

st.markdown("---")

if "historique" not in st.session_state:
    st.session_state.historique = []

if st.button("✈️ Organise mon voyage !"):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    question = f"Organise moi un voyage de {jours} jours à {destination} avec un budget {budget}. Fais un itinéraire jour par jour en français."
    st.session_state.historique = [{"role": "user", "content": question}]
    with st.spinner("Je prépare ton voyage... 🌍"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.historique
        )
    reponse = response.choices[0].message.content
    st.session_state.historique.append({"role": "assistant", "content": reponse})
    st.success("Voici ton itinéraire ! 🎉")
    st.write(reponse)

if st.session_state.get("historique"):
    st.markdown("---")
    st.markdown("### 💬 Tu as une question sur ce voyage ?")
    question_suivi = st.text_input("Pose ta question ici...")
    if st.button("📨 Poser ma question"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        st.session_state.historique.append({"role": "user", "content": question_suivi})
        with st.spinner("Je réfléchis à ta question... 💭"):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.historique
            )
        reponse = response.choices[0].message.content
        st.session_state.historique.append({"role": "assistant", "content": reponse})
        st.write(reponse)
