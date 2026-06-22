import streamlit as st
from groq import Groq

st.title("🌍 Mon Organisateur de Voyage")
st.write("Dis moi où tu veux aller, et je t'organise ton voyage !")

destination = st.text_input("Quelle est ta destination ?")
jours = st.number_input("Combien de jours ?", min_value=1, value=5)
budget = st.selectbox("Ton budget ?", ["Petit budget", "Moyen", "Confortable"])

if "historique" not in st.session_state:
    st.session_state.historique = []

if st.button("Organise mon voyage !"):
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
    st.write(reponse)

if st.session_state.get("historique"):
    st.divider()
    question_suivi = st.text_input("Tu as une question sur ce voyage ?")
    if st.button("Poser ma question"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        st.session_state.historique.append({"role": "user", "content": question_suivi})
        with st.spinner("Je réfléchis à ta question... 💭"):
            response
