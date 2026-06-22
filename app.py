import streamlit as st
import anthropic

st.title("🌍 Mon Organisateur de Voyage")
st.write("Dis moi où tu veux aller, et je t'organise ton voyage !")

destination = st.text_input("Quelle est ta destination ?")
jours = st.slider("Combien de jours ?", 1, 14, 5)
budget = st.selectbox("Ton budget ?", ["Petit budget", "Moyen", "Confortable"])

if st.button("Organise mon voyage !"):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Organise moi un voyage de {jours} jours à {destination} avec un budget {budget}. Fais un itinéraire jour par jour en français."}]
    )
    st.write(message.content[0].text)
