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
        background-image: url("https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600");
        background-size: cover;
        background-position: center;
