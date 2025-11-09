import streamlit as st
from geopy.geocoders import Nominatim
import time

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Météo",
    page_icon="🌤️",
    layout="wide"
)

# Dictionnaire des villes avec leurs coordonnées
VILLES_PREDEFINIES = {
    "Paris": (48.8566, 2.3522),
    "Londres": (51.5074, -0.1278),
    "New York": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503),
    "Berlin": (52.5200, 13.4050),
    "Madrid": (40.4168, -3.7038),
    "Rome": (41.9028, 12.4964),
    "Moscou": (55.7558, 37.6176),
    "Sydney": (-33.8688, 151.2093),
    "São Paulo": (-23.5505, -46.6333)
}

def geocode_city(city_name):
    """
    Convertit le nom d'une ville en coordonnées géographiques.
    
    Parameters:
    city_name (str): Nom de la ville
    
    Returns:
    tuple: (latitude, longitude) ou None si non trouvé
    """
    try:
        geolocator = Nominatim(user_agent="weather_app")
        location = geolocator.geocode(city_name)
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        st.error(f"Erreur lors de la géolocalisation : {e}")
        return None

def main():
    """Page d'accueil du dashboard"""
    
    # En-tête
    st.title("🌤️ Dashboard Météo")
    st.markdown("---")
    
    # Introduction
    st.markdown("""
    ### Bienvenue sur votre dashboard météo personnalisé !
    
    Sélectionnez une ville ci-dessous pour accéder aux données météorologiques, 
    horoscope, saints du jour et blague quotidienne.
    """)
    
    # Section de sélection de ville
    st.subheader("🏙️ Sélection de la ville")
    
    # Options de sélection
    option = st.radio(
        "Comment souhaitez-vous sélectionner votre ville ?",
        ["Villes prédéfinies", "Recherche personnalisée"],
        horizontal=True
    )
    
    latitude, longitude, ville_selectionnee = None, None, None
    
    if option == "Villes prédéfinies":
        # Sélection parmi les villes prédéfinies
        ville_selectionnee = st.selectbox(
            "Choisissez une ville :",
            list(VILLES_PREDEFINIES.keys()),
            index=0
        )
        latitude, longitude = VILLES_PREDEFINIES[ville_selectionnee]
        
    else:
        # Recherche personnalisée
        ville_personnalisee = st.text_input(
            "Entrez le nom de votre ville :",
            placeholder="Ex: Marseille, Barcelona, etc."
        )
        
        if ville_personnalisee:
            with st.spinner("Recherche des coordonnées..."):
                coords = geocode_city(ville_personnalisee)
                if coords:
                    latitude, longitude = coords
                    ville_selectionnee = ville_personnalisee
                    st.success(f"✅ Ville trouvée : {ville_personnalisee}")
                    st.info(f"📍 Coordonnées : {latitude:.4f}, {longitude:.4f}")
                else:
                    st.error("❌ Ville non trouvée. Veuillez vérifier l'orthographe.")
    
    # Affichage des informations de la ville sélectionnée
    if latitude and longitude and ville_selectionnee:
        
        st.markdown("---")
        st.subheader("📍 Ville sélectionnée")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🏙️ Ville", ville_selectionnee)
        
        with col2:
            st.metric("📐 Latitude", f"{latitude:.4f}")
        
        with col3:
            st.metric("📐 Longitude", f"{longitude:.4f}")
        
        # Sauvegarder dans la session state
        st.session_state.latitude = latitude
        st.session_state.longitude = longitude
        st.session_state.ville_selectionnee = ville_selectionnee
        
        # Bouton pour aller à la page de données
        st.markdown("---")
        
        if st.button("🚀 Voir les données météo et plus", type="primary", use_container_width=True):
            st.session_state.page = "donnees"
            st.rerun()
    
    # Informations supplémentaires
    st.markdown("---")
    st.subheader("ℹ️ Informations")
    
    with st.expander("🌟 Fonctionnalités disponibles"):
        st.markdown("""
        - **🌤️ Météo** : Données météorologiques actuelles, horaires et quotidiennes
        - **🔮 Horoscope** : Prédictions astrologiques quotidiennes
        - **📿 Saints du jour** : Informations sur les saints du calendrier
        - **😄 Blague du jour** : Une blague aléatoire pour commencer la journée
        """)
    
    with st.expander("🛠️ Comment utiliser"):
        st.markdown("""
        1. Sélectionnez une ville dans la liste ou recherchez-en une personnalisée
        2. Vérifiez que les coordonnées sont correctes
        3. Cliquez sur "Voir les données météo et plus"
        4. Profitez de toutes les informations disponibles !
        """)

if __name__ == "__main__":
    # Initialiser la session state
    if "page" not in st.session_state:
        st.session_state.page = "accueil"
    
    # Navigation simple
    if st.session_state.page == "accueil":
        main()
    elif st.session_state.page == "donnees":
        # Import et redirection vers la page de données
        import donnees_page
        donnees_page.show_data_page()