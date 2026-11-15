
def extraire_etapes_circuit(client, destination, jours, type_voyage, nb_villes):
    """Récupère et nettoie les étapes du circuit générées par Groq."""

    if type_voyage == "Road trip (plusieurs villes)":
        consigne_type = (
            f"Le circuit doit traverser {int(nb_villes)} villes différentes "
            f"dans la région ou le pays : {destination}. "
            "Répartis les visites dans un ordre géographique logique."
        )
        nombre_lieux = max(8, min(18, int(jours) * 2))
    else:
        consigne_type = (
            f"Tous les lieux doivent se trouver à {destination} "
            "ou à proximité."
        )
        nombre_lieux = max(5, min(12, int(jours) + 3))

    prompt = f"""
Tu es un guide touristique professionnel.

Crée un circuit touristique de {nombre_lieux} lieux réels
pour un voyage de {int(jours)} jours à {destination}.

{consigne_type}

Réponds uniquement avec du JSON valide.
N'ajoute aucune phrase avant ou après le JSON.
N'utilise pas de balises Markdown.

Respecte exactement cette structure :

{{
  "etapes": [
    {{
      "jour": 1,
      "ville": "Paris",
      "lieu": "Tour Eiffel",
      "description": "Monument emblématique de Paris"
    }}
  ]
}}

Chaque étape doit avoir les quatre champs :
jour, ville, lieu et description.
Les lieux doivent être réels et visitables.
Respecte l'ordre logique du circuit.
"""

    contenu = demander_a_groq(
        client,
        [{"role": "user", "content": prompt}]
    )

    if not contenu:
        return []

    try:
        # Nettoyage de la réponse
        contenu = contenu.strip()
        contenu = re.sub(r"```(?:json)?", "", contenu)
        contenu = contenu.replace("```", "").strip()

        # Recherche du début du JSON
        debut = contenu.find("{")
        if debut == -1:
            debut = contenu.find("[")

        if debut == -1:
            raise ValueError("Aucun JSON trouvé dans la réponse de Groq.")

        # Lecture du premier objet ou tableau JSON valide
        donnees, _ = json.JSONDecoder().raw_decode(contenu[debut:])

        # Accepte un objet ou directement une liste
        if isinstance(donnees, list):
            etapes_brutes = donnees
        elif isinstance(donnees, dict):
            etapes_brutes = (
                donnees.get("etapes")
                or donnees.get("steps")
                or donnees.get("places")
                or []
            )
        else:
            etapes_brutes = []

        etapes = []

        for e in etapes_brutes:
            if not isinstance(e, dict):
                continue

            lieu = (
                e.get("lieu")
                or e.get("name")
                or e.get("nom")
                or e.get("place")
            )

            ville = (
                e.get("ville")
                or e.get("city")
                or destination
            )

            if not lieu:
                continue

            try:
                jour = int(e.get("jour", e.get("day", 1)))
            except (ValueError, TypeError):
                jour = 1

            etapes.append({
                "jour": jour,
                "ville": str(ville),
                "lieu": str(lieu),
                "description": str(
                    e.get("description", e.get("details", "Lieu touristique à visiter"))
                )
            })

        if not etapes:
            st.warning(
                "L'IA a répondu, mais aucun lieu exploitable n'a été trouvé."
            )
            st.caption("Réponse reçue : " + contenu[:1000])
            return []

        return etapes

    except Exception as exc:
        st.error("Impossible de lire les étapes générées par l'IA.")
        st.caption(f"Erreur technique : {exc}")
        st.caption("Réponse reçue : " + contenu[:1000])
        return []
