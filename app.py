import streamlit as st
from groq import Groq

st.set_page_config(page_title="Mon Organisateur de Voyage", page_icon="✈️", layout="centered")

st.markdown("<style>.stApp {background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600'); background-size: cover; background-position: center;} h1, h2, h3 {color: white !important;} p {color: white !important;} label {color: black !important; font-weight: bold;} div[data-testid='stWidgetLabel'] p {color: black !important;} div[data-testid='stWidgetLabel'] label {color: black !important;} .stButton>button {background-color: #ff6b35; color: white; border-radius: 20px; font-size: 18px; font-weight: bold; border: none;} .stTextInput>div>input {border-radius: 15px; background-color: rgba(255,255,255,0.9); color: black !important;} .stSelectbox>div>div {border-radius: 15px; background-color: rgba(255,255,255,0.9); color: black !important;} .stNumberInput>div>div>input {border-radius: 15px; background-color: rgba(255,255,255,0.9); color: black !important;} .boite {background: rgba(255, 120, 30, 0.45); border-radius: 20px; padding: 30px; border: 2px solid rgba(255,160,80,0.6); margin-bottom: 20px;}</style>", unsafe_allow_html=True)

st.markdown("# ✈️ Mon Organisateur de Voyage")
st.markdown("### 🌍 Dis moi où tu veux aller, et je t'organise ton voyage !")
st.markdown("---")

if "historique" not in st.session_state:
    st.session_state.historique = []

st.markdown("<div class='boite'>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    destination = st.text_input("📍 Ta destination")
with col2:
    jours = st.number_input("📅 Nombre de jours", min_value=1, value=5)

col3, col4 = st.columns(2)
with col3:
    budget = st.selectbox("💰 Ton budget", ["Petit budget", "Moyen", "Confortable"])
with col4:
    nb_adultes = st.number_input("🧑 Nombre d'adultes", min_value=0, value=1)

nb_enfants = st.number_input("👶 Nombre d'enfants", min_value=0, value=0)

ages_enfants = []
if nb_enfants > 0:
    st.markdown("<p style='color:black !important; font-weight:bold;'>🎂 Age des enfants</p>", unsafe_allow_html=True)
    cols = st.columns(int(nb_enfants))
    for i in range(int(nb_enfants)):
        with cols[i]:
            age = st.number_input(f"Enfant {i+1}", min_value=1, max_value=16, value=5)
            ages_enfants.append(age)

bouton = st.button("✈️ Organise mon voyage !")
st.markdown("</div>", unsafe_allow_html=True)

if bouton:
    if destination:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        info_enfants = ""
        if ages_enfants:
            info_enfants = f" et {int(nb_enfants)} enfant(s) ages de {', '.join([str(a) + ' ans' for a in ages_enfants])}"
        question = f"Organise moi un voyage de {jours} jours a {destination} pour {int(nb_adultes)} adulte(s){info_enfants} avec un budget {budget}. Fais un itineraire jour par jour en francais adapte au groupe."
        st.session_state.historique = [{"role": "user", "content": question}]
        with st.spinner("Je prepare ton voyage... 🌍"):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.historique
            )
        reponse = response.choices[0].message.content
        st.session_state.historique.append({"role": "assistant", "content": reponse})
        st.success("Voici ton itineraire ! 🎉")
        st.write(reponse)
    else:
        st.warning("Entre une destination d'abord ! 📍")

if st.session_state.get("historique"):
    st.markdown("---")
    st.markdown("<div class='boite'>", unsafe_allow_html=True)
    st.markdown("<p style='color:black !important; font-weight:bold; font-size:20px;'>💬 Tu as une question sur ce voyage ?</p>", unsafe_allow_html=True)
    question_suivi = st.text_input("Pose ta question ici...")
    bouton2 = st.button("📨 Poser ma question")
    st.markdown("</div>", unsafe_allow_html=True)
    if bouton2:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        st.session_state.historique.append({"role": "user", "content": question_suivi})
        with st.spinner("Je reflechis a ta question... 💭"):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.historique
            )
        reponse = response.choices[0].message.content
        st.session_state.historique.append({"role": "assistant", "content": reponse})
        st.write(reponse)
