import streamlit as st
from geopy.geocoders import Nominatim

# -----------------------
# Config
# -----------------------
st.set_page_config(
    page_title="Dashboard Météo",
    page_icon="🌤️",
    layout="wide"
)

# ------------------------
# VILLES PRÉDEFINIES
# ------------------------
VILLES_PREDEFINIES = {
    "Paris": (48.8566, 2.3522),
    "Londres": (51.5074, -0.1278),
    "New York": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503),
    "Berlin": (52.5200, 13.4050),
    "Madrid": (40.4168, -3.7038),
    "Rome": (41.9028, 12.4964),
    "Sydney": (-33.8688, 151.2093),
}

def geocode_city(city_name):
    try:
        geolocator = Nominatim(user_agent="weather_app")
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        return None
    except Exception as e:
        st.error(f"Erreur géocodage : {e}")
        return None


# ------------------------
# PAGE ACCUEIL MODERNE
# ------------------------
st.title("🌤️ Dashboard Météo")
st.markdown("---")

# 🔍 Recherche principale
st.markdown("## 🔎 Rechercher une ville")

ville_input = st.text_input(
    "Rechercher une ville",
    placeholder="Entrez une ville... (ex : Marseille, Tokyo, Montréal...)",
    label_visibility="collapsed"
)

latitude = None
longitude = None
ville_selectionnee = None

# --------------------------------------------------------
# 1️⃣ Si l'utilisateur tape une ville → Géocodage automatique
# --------------------------------------------------------
if ville_input:
    with st.spinner("Recherche de la ville..."):
        coords = geocode_city(ville_input)

    if coords:
        latitude, longitude = coords
        ville_selectionnee = ville_input
        st.success(f"✔ Ville trouvée : **{ville_selectionnee}**")
    else:
        st.error("❌ Ville introuvable.")


# --------------------------------------------------------
# 2️⃣ VILLES PRÉDEFINIES — sous forme de boutons modernes
# --------------------------------------------------------
st.markdown("### ⭐ Villes populaires")

cols = st.columns(4)

for i, (ville, coords) in enumerate(VILLES_PREDEFINIES.items()):
    with cols[i % 4]:
        if st.button(ville):
            ville_selectionnee = ville
            latitude, longitude = coords
            st.session_state.latitude = latitude
            st.session_state.longitude = longitude
            st.session_state.ville_selectionnee = ville
            st.success(f"✔ Ville sélectionnée : **{ville}**")


# --------------------------------------------------------
# 3️⃣ AFFICHAGE CARTE METEOBLUE (pas cliquable)
# --------------------------------------------------------
st.markdown("---")
st.markdown("## 🛰 Carte météo")

iframe_code = """
<iframe width="100%" height="700" src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=°C&metricWind=km/h&zoom=4&overlay=wind&product=ecmwf&level=surface&lat=37.44&lon=6.24&detailLat=43.197&detailLon=4.042&detail=true" frameborder="0"></iframe>
"""
st.components.v1.html(iframe_code, height=700)


# --------------------------------------------------------
# 4️⃣ Si une ville a été trouvée → Affichage + enregistrement
# --------------------------------------------------------
if latitude and longitude:
    st.markdown("---")
    st.subheader("📍 Ville sélectionnée")

    c1, c2, c3 = st.columns(3)
    c1.metric("🏙️ Ville", ville_selectionnee)
    c2.metric("📐 Latitude", f"{latitude:.4f}")
    c3.metric("📐 Longitude", f"{longitude:.4f}")

    # Sauvegarde globale
    st.session_state.latitude = latitude
    st.session_state.longitude = longitude
    st.session_state.ville_selectionnee = ville_selectionnee

    st.success("✔ Coordonnées enregistrées ! Ouvrez la page **Données météo** dans le menu à gauche.")
