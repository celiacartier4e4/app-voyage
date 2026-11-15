import streamlit as st
import requests
import json
import re
import streamlit.components.v1 as components
from groq import Groq
from groq import APIError

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mon Organisateur de Voyage",
    page_icon="✈️",
    layout="centered"
)

# Modèle de remplacement officiel conseillé par Groq.
# L'ancien modèle llama-3.3-70b-versatile a été arrêté le 16/08/2026.
MODELE_GROQ = "openai/gpt-oss-120b"

st.markdown(
    """
    <style>
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1600');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    h1, h2, h3 { color: white !important; }
    .stButton > button {
        background-color: #ff6b35;
        color: white;
        border-radius: 20px;
        font-size: 18px;
        font-weight: bold;
        border: none;
    }
    .stTextInput input, .stNumberInput input {
        border-radius: 15px;
        background-color: rgba(255,255,255,0.9);
        color: black !important;
    }
    .stSelectbox [data-baseweb="select"] {
        border-radius: 15px;
        background-color: rgba(255,255,255,0.9);
    }
    .boite {
        background: rgba(255, 120, 30, 0.45);
        border-radius: 20px;
        padding: 20px;
        border: 2px solid rgba(255,160,80,0.6);
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='color:white!important'>✈️ Mon Organisateur de Voyage</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<h3 style='color:white!important'>🌍 Dis-moi où tu veux aller, et je t'organise ton voyage !</h3>",
    unsafe_allow_html=True
)
st.markdown("---")


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "historique" not in st.session_state:
    st.session_state.historique = []

if "destination_choisie" not in st.session_state:
    st.session_state.destination_choisie = ""


# ---------------------------------------------------------
# GROQ HELPERS
# ---------------------------------------------------------
@st.cache_resource
def obtenir_client_groq():
    """Crée un client Groq réutilisable pendant la session Streamlit."""
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception as exc:
        raise RuntimeError(
            "La clé GROQ_API_KEY est absente. Ajoute-la dans "
            "Streamlit Cloud > Manage app > Settings > Secrets."
        ) from exc

    if not api_key:
        raise RuntimeError("La clé GROQ_API_KEY est vide.")

    return Groq(api_key=api_key)


def demander_a_groq(client, messages):
    """Envoie une demande à Groq et affiche un message utile en cas d'erreur."""
    try:
        resultat = client.chat.completions.create(
            model=MODELE_GROQ,
            messages=messages
        )
        if not resultat.choices:
            st.error("Groq n'a renvoyé aucune réponse. Réessaie dans quelques instants.")
            return None

        contenu = resultat.choices[0].message.content
        if not contenu:
            st.error("La réponse de l'IA est vide. Réessaie.")
            return None

        return contenu

    except APIError as exc:
        st.error(
            "Groq n'a pas pu traiter la demande. "
            "Vérifie que le modèle est disponible et que ta clé API est valide."
        )
        st.caption(f"Détail technique : {exc}")
        return None

    except Exception as exc:
        st.error("Une erreur inattendue est survenue pendant la communication avec Groq.")
        st.caption(f"Détail technique : {exc}")
        return None



# ---------------------------------------------------------
# CIRCUIT TOURISTIQUE SUR CARTE
# ---------------------------------------------------------
def extraire_etapes_circuit(client, destination, jours, type_voyage, nb_villes):
    """Demande à l'IA une liste structurée de lieux à visiter, dans l'ordre."""
    if type_voyage == "Road trip (plusieurs villes)":
        consigne_type = (
            f"Le circuit doit traverser exactement {int(nb_villes)} villes "
            f"ou étapes urbaines différentes dans la région/pays {destination}. "
            "Répartis les lieux entre ces villes dans un ordre géographique logique."
        )
        nombre_lieux = max(8, min(18, int(jours) * 2))
    else:
        consigne_type = (
            f"Tous les lieux doivent se trouver dans la ville de {destination} "
            "ou à proximité immédiate."
        )
        nombre_lieux = max(5, min(12, int(jours) + 3))

    prompt = f"""
Tu es un organisateur de circuits touristiques. Prépare une liste de {nombre_lieux}
lieux réels et connus à visiter pendant {int(jours)} jours à {destination}.
{consigne_type}

Réponds UNIQUEMENT avec un objet JSON valide, sans Markdown, sous cette forme :
{{
  "etapes": [
    {{
      "jour": 1,
      "ville": "Nom de la ville",
      "lieu": "Nom officiel ou courant du lieu",
      "description": "Description courte du lieu"
    }}
  ]
}}

Règles :
- Respecte l'ordre conseillé de visite.
- Répartis les étapes sur les {int(jours)} jours.
- Utilise des lieux touristiques réels, précis et géocodables.
- Pour un road trip, garde une progression géographique cohérente entre les villes.
- N'ajoute aucune coordonnée GPS.
- Réponds uniquement en français dans les descriptions.
"""
    contenu = demander_a_groq(
        client,
        [{"role": "user", "content": prompt}]
    )
    if not contenu:
        return []

    try:
        # Tolère les éventuelles balises Markdown renvoyées par le modèle.
        contenu = contenu.strip()
        if contenu.startswith("```"):
            contenu = re.sub(r"^```(?:json)?\s*", "", contenu)
            contenu = re.sub(r"\s*```$", "", contenu)
        donnees = json.loads(contenu)
        etapes = donnees.get("etapes", [])
        return [
            e for e in etapes
            if isinstance(e, dict) and e.get("lieu") and e.get("ville")
        ]
    except (json.JSONDecodeError, AttributeError, TypeError):
        st.warning("Je n'ai pas réussi à structurer les lieux du circuit. La carte ne peut pas être créée.")
        return []


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def geocoder_lieu(nom_lieu, ville, destination):
    """Trouve les coordonnées d'un lieu avec le service public OpenStreetMap."""
    requete = f"{nom_lieu}, {ville}, {destination}"
    try:
        resultat = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": requete,
                "format": "jsonv2",
                "limit": 1
            },
            headers={"User-Agent": "MonOrganisateurDeVoyage/1.0"},
            timeout=15
        )
        resultat.raise_for_status()
        elements = resultat.json()
        if not elements:
            # Deuxième essai moins précis si la recherche complète échoue.
            resultat = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": f"{nom_lieu}, {ville}",
                    "format": "jsonv2",
                    "limit": 1
                },
                headers={"User-Agent": "MonOrganisateurDeVoyage/1.0"},
                timeout=15
            )
            resultat.raise_for_status()
            elements = resultat.json()

        if elements:
            return {
                "lat": float(elements[0]["lat"]),
                "lon": float(elements[0]["lon"]),
                "adresse": elements[0].get("display_name", requete)
            }
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return None
    return None


def construire_circuit_carte(etapes, destination):
    """Géocode les étapes puis affiche une carte interactive avec ordre du circuit."""
    etapes_geocodees = []

    progression = st.progress(0, text="Localisation des lieux à visiter...")
    total = len(etapes)

    for index, etape in enumerate(etapes):
        ville = str(etape.get("ville", destination))
        lieu = str(etape.get("lieu", "")).strip()
        coordonnees = geocoder_lieu(lieu, ville, destination)

        if coordonnees:
            etapes_geocodees.append({
                "numero": len(etapes_geocodees) + 1,
                "jour": etape.get("jour", "?"),
                "ville": ville,
                "lieu": lieu,
                "description": str(etape.get("description", "")),
                "lat": coordonnees["lat"],
                "lon": coordonnees["lon"]
            })

        progression.progress(
            (index + 1) / total,
            text=f"Recherche des lieux : {index + 1}/{total}"
        )

    progression.empty()

    if not etapes_geocodees:
        st.warning(
            "Je n'ai pas réussi à localiser les lieux proposés. "
            "Essaie avec une destination plus précise."
        )
        return

    st.markdown("## 🗺️ Ton circuit touristique")
    st.caption(
        "Les numéros indiquent l'ordre conseillé des visites. "
        "Les positions sont issues d'OpenStreetMap."
    )

    # Données JSON échappées pour insertion sûre dans le composant HTML.
    points_json = json.dumps(etapes_geocodees, ensure_ascii=False)
    points_json = points_json.replace("</", "<\\/")

    carte_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
      <style>
        html, body {{ margin:0; padding:0; }}
        #carte {{ height: 540px; width:100%; border-radius:16px; }}
        .numero {{
          background:#ff6b35; color:white; border:2px solid white;
          border-radius:50%; width:30px; height:30px;
          line-height:26px; text-align:center; font-weight:bold;
          box-shadow:0 1px 5px #555;
        }}
        .leaflet-popup-content {{ font-family:Arial,sans-serif; }}
      </style>
    </head>
    <body>
      <div id="carte"></div>
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <script>
        const points = {points_json};
        const carte = L.map('carte');
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
          maxZoom: 19,
          attribution: '&copy; OpenStreetMap'
        }}).addTo(carte);

        const coordonnees = [];
        points.forEach((p) => {{
          const position = [p.lat, p.lon];
          coordonnees.push(position);

          const icone = L.divIcon({{
            className: '',
            html: '<div class="numero">' + p.numero + '</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
          }});

          const popup =
            '<b>Étape ' + p.numero + ' — Jour ' + p.jour + '</b><br>' +
            '<b>' + p.lieu + '</b><br>' +
            p.ville + '<br>' +
            p.description;

          L.marker(position, {{icon: icone}}).addTo(carte).bindPopup(popup);
        }});

        if (coordonnees.length > 1) {{
          L.polyline(coordonnees, {{
            color:'#ff6b35', weight:4, opacity:0.85,
            dashArray:'8, 8'
          }}).addTo(carte);
        }}

        if (coordonnees.length > 0) {{
          carte.fitBounds(coordonnees, {{padding:[30,30] }});
        }} else {{
          carte.setView([20, 0], 2);
        }}
      </script>
    </body>
    </html>
    """
    components.html(carte_html, height=560, scrolling=False)

    st.markdown("### 📍 Les étapes dans l'ordre")
    for point in etapes_geocodees:
        st.markdown(
            f"**{point['numero']}. {point['lieu']}** — "
            f"Jour {point['jour']} · {point['ville']}"
        )
        if point["description"]:
            st.caption(point["description"])

    # Lien Google Maps pour ouvrir le parcours complet.
    if len(etapes_geocodees) >= 2:
        origine = f"{etapes_geocodees[0]['lat']},{etapes_geocodees[0]['lon']}"
        destination_finale = (
            f"{etapes_geocodees[-1]['lat']},{etapes_geocodees[-1]['lon']}"
        )
        intermediaires = "|".join(
            f"{p['lat']},{p['lon']}" for p in etapes_geocodees[1:-1]
        )
        url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={origine}&destination={destination_finale}"
            f"&waypoints={intermediaires}&travelmode=driving"
        )
        st.link_button("🚗 Ouvrir ce circuit dans Google Maps", url)


# ---------------------------------------------------------
# FORMULAIRE DE VOYAGE
# ---------------------------------------------------------
st.markdown("<div class='boite'>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:black!important;font-weight:bold'>🔥 Destinations populaires :</p>",
    unsafe_allow_html=True
)

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

type_voyage = st.selectbox(
    "🚗 Type de voyage",
    ["Une seule ville", "Road trip (plusieurs villes)"]
)

col1, col2 = st.columns(2)

with col1:
    if type_voyage == "Une seule ville":
        destination = st.text_input(
            "📍 Ta destination",
            value=st.session_state.destination_choisie
        )
    else:
        destination = st.text_input(
            "📍 Pays ou région du road trip",
            value=st.session_state.destination_choisie
        )

with col2:
    jours = st.number_input("📅 Nombre de jours", min_value=1, value=5, step=1)

if type_voyage == "Road trip (plusieurs villes)":
    nb_villes = st.number_input(
        "🏙️ Nombre de villes à visiter",
        min_value=2,
        max_value=10,
        value=3,
        step=1
    )
else:
    nb_villes = 1

col3, col4 = st.columns(2)

with col3:
    budget = st.selectbox(
        "💰 Ton budget",
        ["Petit budget", "Moyen", "Confortable"]
    )

with col4:
    nb_adultes = st.number_input(
        "🧑 Nombre d'adultes",
        min_value=0,
        value=1,
        step=1
    )

nb_enfants = st.number_input(
    "👶 Nombre d'enfants",
    min_value=0,
    value=0,
    step=1
)

ages_enfants = []

if nb_enfants > 0:
    st.markdown(
        "<p style='color:black!important;font-weight:bold'>🎂 Âge des enfants</p>",
        unsafe_allow_html=True
    )
    colonnes_ages = st.columns(min(int(nb_enfants), 4))

    for i in range(int(nb_enfants)):
        with colonnes_ages[i % len(colonnes_ages)]:
            age = st.number_input(
                f"Enfant {i + 1}",
                min_value=1,
                max_value=17,
                value=5,
                key=f"age_enfant_{i}"
            )
            ages_enfants.append(age)

col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    bouton = st.button("✈️ Organise mon voyage !", use_container_width=True)

with col_btn2:
    bouton_aventure = st.button("🎒 Mode aventure !", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# GENERATION DU VOYAGE
# ---------------------------------------------------------
def generer_voyage(
    destination,
    jours,
    nb_adultes,
    nb_enfants,
    ages_enfants,
    info_enfants,
    budget,
    type_voyage,
    nb_villes,
    mode_aventure=False
):
    try:
        client = obtenir_client_groq()
    except RuntimeError as exc:
        st.error(str(exc))
        return

    total_personnes = int(nb_adultes) + int(nb_enfants)

    if total_personnes < 1:
        st.warning("Indique au moins une personne pour organiser le voyage.")
        return

    if type_voyage == "Road trip (plusieurs villes)":
        intro = (
            f"Organise-moi un road trip de {int(jours)} jours dans "
            f"{destination}, en visitant {int(nb_villes)} villes différentes."
        )
    else:
        intro = f"Organise-moi un voyage de {int(jours)} jours à {destination}."

    if mode_aventure:
        question = (
            f"{intro} Pour {int(nb_adultes)} adulte(s){info_enfants}, "
            f"avec un budget {budget}. Propose des activités originales, "
            "surprenantes et insolites, adaptées au groupe. "
            f"À la fin, donne le coût total estimé en euros par personne "
            f"et pour tout le groupe de {total_personnes} personne(s). "
            "Précise que les prix sont des estimations à vérifier. "
            "Réponds en français."
        )
    else:
        question = (
            f"{intro} Pour {int(nb_adultes)} adulte(s){info_enfants}, "
            f"avec un budget {budget}. Fais un itinéraire jour par jour "
            "adapté au groupe. "
            f"À la fin, donne le coût total estimé en euros par personne "
            f"et pour tout le groupe de {total_personnes} personne(s). "
            "Précise que les prix sont des estimations à vérifier. "
            "Réponds en français."
        )

    st.session_state.historique = [{"role": "user", "content": question}]

    with st.spinner("Je prépare ton itinéraire... 🌍"):
        reponse = demander_a_groq(client, st.session_state.historique)

    if reponse is None:
        return

    st.session_state.historique.append(
        {"role": "assistant", "content": reponse}
    )

    if mode_aventure:
        st.success("🎒 Voici ton itinéraire aventure ! 🌟")
    else:
        st.success("Voici ton itinéraire ! 🎉")

    st.write(reponse)
    st.markdown("---")

    # Génération de la carte et du circuit ordonné
    with st.spinner("Je prépare le circuit et localise les lieux à visiter... 🗺️"):
        etapes_circuit = extraire_etapes_circuit(
            client, destination, jours, type_voyage, nb_villes
        )
        if etapes_circuit:
            construire_circuit_carte(etapes_circuit, destination)

    st.markdown("---")

    # Avis sur la destination
    with st.spinner("Analyse de la destination... 🌟"):
        q_note = (
            f"Donne une note sur 10 et un avis rapide en 3 lignes sur "
            f"{destination} pour un voyage de {int(jours)} jours "
            f"avec un budget {budget}. Réponds en français."
        )
        r_note = demander_a_groq(
            client,
            [{"role": "user", "content": q_note}]
        )
    if r_note:
        st.info("🌟 " + r_note)

    # Monnaie locale
    with st.spinner("Je cherche la monnaie locale... 💱"):
        q_monnaie = (
            f"Quelle est la monnaie officielle utilisée à {destination} ? "
            "Donne un taux de conversion approximatif par rapport à l'euro "
            "et précise qu'il doit être vérifié. Réponds en français."
        )
        r_monnaie = demander_a_groq(
            client,
            [{"role": "user", "content": q_monnaie}]
        )
    if r_monnaie:
        st.info("💱 " + r_monnaie)

    # Meilleure période
    with st.spinner("Vérification de la meilleure période... 📅"):
        q_periode = (
            f"Quelle est la meilleure saison pour visiter {destination} ? "
            "Indique si la période actuelle est généralement adaptée, "
            "sans prétendre disposer de données météo en temps réel. "
            "Réponds en français en 3 ou 4 lignes."
        )
        r_periode = demander_a_groq(
            client,
            [{"role": "user", "content": q_periode}]
        )
    if r_periode:
        st.info("📅 " + r_periode)

    # Onglets
    tab1, tab3, tab4, tab5, tab6 = st.tabs(
        ["🌤️ Météo", "🧳 Bagages", "🗣️ Phrases", "⚠️ Sécurité", "🍽️ Cuisine"]
    )

    with tab1:
        try:
            geo_response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": destination,
                    "count": 1,
                    "language": "fr",
                    "format": "json"
                },
                timeout=15
            )
            geo_response.raise_for_status()
            geo = geo_response.json()

            if not geo.get("results"):
                st.warning("Je n'ai pas trouvé cette destination pour la météo.")
            else:
                lat = geo["results"][0]["latitude"]
                lon = geo["results"][0]["longitude"]

                meteo_response = requests.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "temperature_2m,wind_speed_10m"
                    },
                    timeout=15
                )
                meteo_response.raise_for_status()
                meteo = meteo_response.json()
                conditions = meteo.get("current", {})

                if "temperature_2m" in conditions:
                    st.markdown(
                        f"### 🌡️ Température actuelle : "
                        f"**{conditions['temperature_2m']} °C**"
                    )
                if "wind_speed_10m" in conditions:
                    st.write(f"💨 Vent : {conditions['wind_speed_10m']} km/h")

        except requests.RequestException:
            st.warning("Météo indisponible pour le moment. Réessaie plus tard.")
        except (KeyError, TypeError, ValueError):
            st.warning("Les données météo reçues sont incomplètes.")

    with tab3:
        with st.spinner("Je prépare ta liste de bagages... 🧳"):
            q_bagages = (
                f"Fais une liste pratique de choses à emporter pour un voyage "
                f"de {int(jours)} jours à {destination}, avec un budget {budget}"
                f"{info_enfants}. Réponds en français."
            )
            r_bagages = demander_a_groq(
                client,
                [{"role": "user", "content": q_bagages}]
            )
        if r_bagages:
            st.write(r_bagages)

    with tab4:
        with st.spinner("Je cherche les phrases utiles... 🗣️"):
            q_phrases = (
                f"Donne 15 phrases utiles pour un voyage à {destination}, "
                "avec la traduction française et une prononciation simplifiée. "
                "Réponds en français."
            )
            r_phrases = demander_a_groq(
                client,
                [{"role": "user", "content": q_phrases}]
            )
        if r_phrases:
            st.write(r_phrases)

    with tab5:
        with st.spinner("Vérification des conseils de sécurité... ⚠️"):
            q_securite = (
                f"Donne des conseils généraux de sécurité pour un voyage à "
                f"{destination}. Pour les vaccins, les formalités et les "
                "recommandations officielles, invite à consulter les autorités "
                "sanitaires et diplomatiques officielles. Réponds en français."
            )
            r_securite = demander_a_groq(
                client,
                [{"role": "user", "content": q_securite}]
            )
        if r_securite:
            st.write(r_securite)

    with tab6:
        with st.spinner("Je cherche les spécialités culinaires... 🍽️"):
            q_cuisine = (
                f"Quelles sont les spécialités culinaires incontournables à "
                f"{destination} ? Donne 10 plats ou boissons à découvrir. "
                "Réponds en français."
            )
            r_cuisine = demander_a_groq(
                client,
                [{"role": "user", "content": q_cuisine}]
            )
        if r_cuisine:
            st.write(r_cuisine)

    # Hôtels
    with st.spinner("Recherche des idées d'hébergement... 🏨"):
        q_hotels = (
            f"Propose 5 hébergements à rechercher pour un voyage à {destination} "
            f"avec un budget {budget}. Donne le nom ou le type, une courte "
            "description et une fourchette de prix approximative par nuit en euros. "
            "Précise que les disponibilités et tarifs doivent être vérifiés "
            "sur les sites des établissements. Réponds en français."
        )
        r_hotels = demander_a_groq(
            client,
            [{"role": "user", "content": q_hotels}]
        )

    if r_hotels:
        st.markdown("---")
        st.markdown("### 🏨 Recommandations d'hébergements")
        st.write(r_hotels)


# ---------------------------------------------------------
# ACTION DES BOUTONS
# ---------------------------------------------------------
if bouton or bouton_aventure:
    if destination.strip():
        info_enfants = ""

        if ages_enfants:
            ages_formates = ", ".join(
                [f"{int(age)} ans" for age in ages_enfants]
            )
            info_enfants = (
                f" et {int(nb_enfants)} enfant(s) âgé(s) de {ages_formates}"
            )

        generer_voyage(
            destination=destination.strip(),
            jours=jours,
            nb_adultes=nb_adultes,
            nb_enfants=nb_enfants,
            ages_enfants=ages_enfants,
            info_enfants=info_enfants,
            budget=budget,
            type_voyage=type_voyage,
            nb_villes=nb_villes,
            mode_aventure=bouton_aventure
        )
    else:
        st.warning("Entre une destination d'abord ! 📍")


# ---------------------------------------------------------
# QUESTIONS COMPLEMENTAIRES
# ---------------------------------------------------------
if st.session_state.get("historique"):
    st.markdown("---")
    st.markdown(
        "<div class='boite'>"
        "<p style='color:black!important;font-weight:bold;font-size:20px'>"
        "💬 Tu as une question sur ce voyage ?</p></div>",
        unsafe_allow_html=True
    )

    question_suivi = st.text_input(
        "Pose ta question ici...",
        key="question_suivi"
    )

    if st.button("📨 Poser ma question"):
        if not question_suivi.strip():
            st.warning("Écris une question avant de l'envoyer.")
        else:
            try:
                client = obtenir_client_groq()
                st.session_state.historique.append(
                    {"role": "user", "content": question_suivi.strip()}
                )

                with st.spinner("Je réfléchis à ta question... 💭"):
                    reponse_suivi = demander_a_groq(
                        client,
                        st.session_state.historique
                    )

                if reponse_suivi:
                    st.session_state.historique.append(
                        {"role": "assistant", "content": reponse_suivi}
                    )
                    st.write(reponse_suivi)

            except RuntimeError as exc:
                st.error(str(exc))
