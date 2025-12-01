import streamlit as st
from geopy.geocoders import Nominatim
from styles import GLOBAL_STYLE

# -----------------------
# Config
# -----------------------
st.set_page_config(
    page_title="Dashboard Météo",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Appliquer le style global
st.markdown(GLOBAL_STYLE, unsafe_allow_html=True)

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
st.markdown('<h1 class="animate-fade-in">🌤️ Dashboard Météo Professionnel</h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 1.2rem; opacity: 0.8; text-align: center;">Explorez les données météorologiques en temps réel avec un design moderne et intuitif</p>', unsafe_allow_html=True)
st.markdown("---")

# 🔍 Recherche principale avec style amélioré
st.markdown('<div class="weather-card animate-fade-in">', unsafe_allow_html=True)
st.markdown("## 🔎 Rechercher une ville")
st.markdown('<p style="opacity: 0.8;">Entrez le nom d\'une ville pour obtenir les prévisions météorologiques détaillées</p>', unsafe_allow_html=True)

ville_input = st.text_input(
    "Rechercher une ville",
    placeholder="🌍 Entrez une ville... (ex : Marseille, Tokyo, Montréal...)",
    label_visibility="collapsed",
    key="city_search"
)
st.markdown('</div>', unsafe_allow_html=True)

latitude = None
longitude = None
ville_selectionnee = None

# --------------------------------------------------------
# 1️⃣ Si l'utilisateur tape une ville → Géocodage automatique
# --------------------------------------------------------
if ville_input:
    with st.spinner("🔍 Recherche de la ville en cours..."):
        coords = geocode_city(ville_input)

    if coords:
        latitude, longitude = coords
        ville_selectionnee = ville_input
        # Sauvegarde dans la session
        st.session_state.latitude = latitude
        st.session_state.longitude = longitude
        st.session_state.ville_selectionnee = ville_selectionnee
        
        st.success(f"✅ Ville trouvée : **{ville_selectionnee}** ({latitude:.4f}, {longitude:.4f})")
        st.info("🚀 Redirection vers les données météo...")
        
        # Redirection automatique
        import time
        time.sleep(1.5)
        st.switch_page("pages/1_Données météo.py")
    else:
        st.error("❌ Impossible de trouver cette ville. Vérifiez l'orthographe.")


# --------------------------------------------------------
# 2️⃣ VILLES PRÉDEFINIES — sous forme de boutons modernes
# --------------------------------------------------------
st.markdown("---")
st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)
st.markdown("### ⭐ Villes populaires")
st.markdown('<p style="opacity: 0.8; margin-bottom: 1.5rem;">Sélectionnez rapidement une ville parmi nos destinations les plus consultées</p>', unsafe_allow_html=True)

cols = st.columns(4)

city_emojis = {
    "Paris": "🗼", "Londres": "🏰", "New York": "🗽", "Tokyo": "🗾",
    "Berlin": "🏛️", "Madrid": "⚽", "Rome": "🏛️", "Sydney": "🦘"
}

for i, (ville, coords) in enumerate(VILLES_PREDEFINIES.items()):
    with cols[i % 4]:
        emoji = city_emojis.get(ville, "🌆")
        if st.button(f"{emoji} {ville}", key=f"city_{ville}", use_container_width=True):
            ville_selectionnee = ville
            latitude, longitude = coords
            st.session_state.latitude = latitude
            st.session_state.longitude = longitude
            st.session_state.ville_selectionnee = ville
            st.success(f"✅ **{ville}** sélectionnée !")
            st.info("🚀 Redirection vers les données météo...")
            
            # Redirection automatique vers la page Données météo
            import time
            time.sleep(1)
            st.switch_page("pages/1_Données météo.py")

st.markdown('</div>', unsafe_allow_html=True)


# --------------------------------------------------------
# 3️⃣ AFFICHAGE CARTE METEOBLUE (pas cliquable)
# --------------------------------------------------------
st.markdown("---")
st.markdown('<div class="animate-fade-in">', unsafe_allow_html=True)
st.markdown("## 🛰️ Carte météo interactive")
st.markdown('<p style="opacity: 0.8; margin-bottom: 1rem;">Explorez les conditions météorologiques en temps réel à travers le monde</p>', unsafe_allow_html=True)

iframe_code = """
<div style="border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);">
    <iframe width="100%" height="700" src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=°C&metricWind=km/h&zoom=4&overlay=wind&product=ecmwf&level=surface&lat=37.44&lon=6.24&detailLat=43.197&detailLon=4.042&detail=true" frameborder="0"></iframe>
</div>
"""
st.components.v1.html(iframe_code, height=720)
st.markdown('</div>', unsafe_allow_html=True)


# --------------------------------------------------------
# 4️⃣ Si une ville a été trouvée → Affichage + enregistrement
# --------------------------------------------------------
if latitude and longitude:
    st.markdown("---")
    st.markdown('<div class="weather-card animate-fade-in">', unsafe_allow_html=True)
    st.markdown("## 📍 Ville sélectionnée")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<p class="metric-label">🏙️ Ville</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{ville_selectionnee}</p>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<p class="metric-label">📐 Latitude</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{latitude:.4f}°</p>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<p class="metric-label">📐 Longitude</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{longitude:.4f}°</p>', unsafe_allow_html=True)

    # Sauvegarde globale
    st.session_state.latitude = latitude
    st.session_state.longitude = longitude
    st.session_state.ville_selectionnee = ville_selectionnee

    st.markdown('<br>', unsafe_allow_html=True)
    st.success("✅ Coordonnées enregistrées avec succès !")
    st.info("👈 **Ouvrez la page Données météo** dans le menu latéral pour voir les prévisions complètes")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer moderne
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem 0; opacity: 0.7;">
    <p style="font-size: 0.9rem;">
        🌤️ Dashboard Météo Professionnel | Powered by Open-Meteo API<br>
        Made with ❤️ using Streamlit
    </p>
</div>
""", unsafe_allow_html=True)
