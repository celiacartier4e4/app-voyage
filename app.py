import streamlit as st
from groq import Groq

st.title("🌍 Mon Organisateur de Voyage")
st.write("Dis moi où tu veux aller, et je t'organise ton voyage !")

destination = st.text_input("Quelle est ta destination ?")
jours = st.slider("Combien de jours ?", 1, 14, 5)
budget = st.selectbox("Ton budget ?", ["Petit budget", "Moyen", "Confortable"])

if st.button("Organise mon voyage !"):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": f"Organise moi un voyage de {jours} jours à {destination} avec un budget {budget}. Fais un itinéraire jour par jour en français."}]
    )
    st.write(response.choices[0].message.content)
