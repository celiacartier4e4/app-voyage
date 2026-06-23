import streamlit as st
from groq import Groq
import requests

st.set_page_config(page_title="Mon Organisateur de Voyage", page_icon="✈️", layout="centered")

st.markdown("<style>.stApp {background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600'); background-size: cover; background-position: center;} h1, h2, h3 {color: white !important;} .stButton>button {background-color: #ff6b35; color: white; border-radius: 20px; font-size: 18px; font-weight: bold; border: none;} .stTextInput>div>input {border-radius: 15px; background-color: rgba(255,255,255,0.9); color: black !important;} .stSelectbox>div>div {border-radius: 15px; background-color: rgba(255,255,255,0.9); color: black !important;} .stNumberInput>div>div>input {border-radius: 15px; background-color: rgba(255,255,255,0.9); color: black !important;} .boite {background: rgba(255, 120, 30, 0.45); border-radius: 20px; padding: 30px; border: 2px solid rgba(255,160,80,0.6); margin-bottom: 20px;} * {color: black !important;} h1, h2, h3 {color: white !important;}</style>", unsafe_allow_html=True)

st.markdown("<h1 style='color:white!important'>✈️ Mon Organisateur de Voyage</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='color:white!important'>🌍 Dis moi où tu veux aller, et je t'organise ton voyage !</h3>", unsafe_allow_html=True)
st.markdown("---")

if "historique" not in st.session_state:
    st.session_state.historique = []
if "destination_choisie" not in st.session_state:
    st.session_state.destination_choisie = ""

st.markdown("<div class='boite'>", unsafe_allow_html=True)

st.markdown("<p style='color:black!important;font-weight:bold'>🔥 Destinations populaires :</p>", unsafe_allow_html=True)
col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.button("🍁 Montréal"):
        st.session_state.destination_choisie = "Montréal"
with col_b:
    if st.button("🗼 Tokyo"):
        st.session_state.destination_choisie = "Tokyo"
with col_c:
    if st.button("🌴 Bali"):
        st.session_state.destination_choisie = "Bali"

col1, col2 = st.columns(2)
with col1:
    destination = st.text_input("📍 Ta destination", value=st.session_state.destination_choisie)
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
    st.markdown("<p style='color:black!important;font-weight:bold'>🎂 Age des enfants</p>", unsafe_allow_html=True)
    cols = st.columns(int(nb_enfants))
    for i in range(int(nb_enfants)):
        with cols[i]:
            age = st.number_input(f"Enfant {i+1}", min_value=1, max_value=16, value=5)
            ages_enfants.append(age)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    bouton = st.button("✈️ Organise mon voyage !")
with col_btn2:
    bouton_aventure = st.button("🎒 Mode aventure !")
st.markdown("</div>", unsafe_allow_html=True)

def generer_voyage(destination, jours, nb_adultes, info_enfants, budget, mode_aventure=False):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    if mode_aventure:
        question = f"Organise moi un itineraire SURPRENANT et ORIGINAL de {jours} jours a {destination} pour {int(nb_adultes)} adulte(s){info_enfants} avec un budget {budget}. Propose des activites insolites et hors des sentiers battus. Precise les prix en euros et en monnaie locale. Reponds en francais."
    else:
        question = f"Organise moi un voyage de {jours} jours a {destination} pour {int(nb_adultes)} adulte(s){info_enfants} avec un budget {budget}. Fais un itineraire jour par jour en francais adapte au groupe. Precise les prix en euros et en monnaie locale."

    st.session_state.historique = [{"role": "user", "content": question}]
    response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.historique)
    reponse = response.choices[0].message.content
    st.session_state.historique.append({"role": "assistant", "content": reponse})

    if mode_aventure:
        st.success("🎒 Voici ton itineraire aventure ! 🌟")
    else:
        st.success("Voici ton itineraire ! 🎉")
    st.write(reponse)

    st.markdown("---")

    with st.spinner("Analyse de la destination... 🌟"):
        q_note = f"Donne une note sur 10 et un avis rapide en 3 lignes sur {destination} pour un voyage de {jours} jours avec un budget {budget}. Reponds en francais."
        r_note = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_note}])
        st.info("🌟 " + r_note.choices[0].message.content)

    with st.spinner("Je cherche la monnaie locale... 💱"):
        q_monnaie = f"Quelle est la monnaie officielle utilisee a {destination} ? Donne le taux de conversion approximatif par rapport a l'euro. Reponds en 2-3 lignes en francais."
        r_monnaie = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_monnaie}])
        st.info("💱 " + r_monnaie.choices[0].message.content)

    with st.spinner("Verification de la meilleure periode... 📅"):
        q_periode = f"Est-ce que c'est une bonne periode pour visiter {destination} en ce moment ? Quelle est la meilleure saison pour y aller ? Reponds en francais en 3-4 lignes."
        r_periode = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_periode}])
        st.info("📅 " + r_periode.choices[0].message.content)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🌤️ Météo", "🗺️ Carte", "🧳 Bagages", "🗣️ Phrases", "⚠️ Sécurité", "🍽️ Cuisine"])

    with tab1:
        try:
            geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={destination}&count=1&language=fr").json()
            lat = geo["results"][0]["latitude"]
            lon = geo["results"][0]["longitude"]
            meteo = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&temperature_unit=celsius").json()
            temp = meteo["current_weather"]["temperature"]
            vent = meteo["current_weather"]["windspeed"]
            st.markdown(f"<p style='font-size:24px'>🌡️ Température actuelle : <b>{temp}°C</b></p>", unsafe_allow_html=True)
            st.markdown(f"<p>💨 Vent : {vent} km/h</p>", unsafe_allow_html=True)
        except:
            st.warning("Météo indisponible pour cette destination.")

    with tab2:
        st.markdown(f"<iframe src='https://maps.google.com/maps?q={destination}&output=embed' width='100%' height='400' style='border-radius:15px;border:none;'></iframe>", unsafe_allow_html=True)

    with tab3:
        with st.spinner("Je prépare ta liste de bagages... 🧳"):
            q_bagages = f"Fais moi une liste de choses a emporter pour un voyage de {jours} jours a {destination} avec un budget {budget}{info_enfants}. Sois pratique et adapte a la destination. Reponds en francais."
            r_bagages = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_bagages}])
            st.write(r_bagages.choices[0].message.content)

    with tab4:
        with st.spinner("Je cherche les phrases utiles... 🗣️"):
            q_phrases = f"Donne moi 15 phrases utiles pour un voyage a {destination}, avec la traduction en francais et la prononciation. Reponds en francais."
            r_phrases = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_phrases}])
            st.write(r_phrases.choices[0].message.content)

    with tab5:
        with st.spinner("Verification de la securite... ⚠️"):
            q_securite = f"Donne moi les conseils de securite importants pour un voyage a {destination} : vaccins recommandes, zones a eviter, numeros d'urgence, dangers eventuels. Reponds en francais."
            r_securite = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_securite}])
            st.write(r_securite.choices[0].message.content)

    with tab6:
        with st.spinner("Je cherche les specialites culinaires... 🍽️"):
            q_cuisine = f"Quelles sont les specialites culinaires incontournables a {destination} ? Donne moi les 10 plats ou boissons a absolument gouter. Reponds en francais."
            r_cuisine = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_cuisine}])
            st.write(r_cuisine.choices[0].message.content)

    with st.spinner("Recherche des hotels... 🏨"):
        q_hotels = f"Recommande moi 5 hotels pour un voyage a {destination} avec un budget {budget}. Donne le nom, une description courte et le prix approximatif par nuit en euros. Reponds en francais."
        r_hotels = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_hotels}])
        st.markdown("---")
        st.markdown("### 🏨 Recommendations d'hôtels")
        st.write(r_hotels.choices[0].message.content)

if bouton or bouton_aventure:
    if destination:
        info_enfants = ""
        if ages_enfants:
            info_enfants = f" et {int(nb_enfants)} enfant(s) ages de {', '.join([str(a) + ' ans' for a in ages_enfants])}"
        with st.spinner("Je prepare ton voyage... 🌍"):
            generer_voyage(destination, jours, nb_adultes, info_enfants, budget, mode_aventure=bouton_aventure)
    else:
        st.warning("Entre une destination d'abord ! 📍")

if st.session_state.get("historique"):
    st.markdown("---")
    st.markdown("<div class='boite'>", unsafe_allow_html=True)
    st.markdown("<p style='color:black!important;font-weight:bold;font-size:20px'>💬 Tu as une question sur ce voyage ?</p>", unsafe_allow_html=True)
    question_suivi = st.text_input("Pose ta question ici...")
    bouton2 = st.button("📨 Poser ma question")
    st.markdown("</div>", unsafe_allow_html=True)
    if bouton2:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        st.session_state.historique.append({"role": "user", "content": question_suivi})
        with st.spinner("Je reflechis a ta question... 💭"):
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.historique)
        reponse = response.choices[0].message.content
        st.session_state.historique.append({"role": "assistant", "content": reponse})
        st.write(reponse)
