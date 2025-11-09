import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# Ajouter le répertoire courant au chemin Python pour importer requete_page1
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from requete_page1 import get_weather_data, get_saints_data, get_horoscope_data, get_blague_data
except ImportError as e:
    st.error(f"Erreur d'importation : {e}")
    st.stop()

def show_data_page():
    """Page de données avec météo, horoscope, saints et blague"""
    
    # Vérifier si nous avons les données de la ville
    if "latitude" not in st.session_state or "longitude" not in st.session_state:
        st.error("❌ Aucune ville sélectionnée. Retournez à la page d'accueil.")
        if st.button("🏠 Retour à l'accueil"):
            st.session_state.page = "accueil"
            st.rerun()
        return
    
    # En-tête de la page
    st.title(f"📊 Données pour {st.session_state.ville_selectionnee}")
    st.markdown(f"**📍 Coordonnées :** {st.session_state.latitude:.4f}, {st.session_state.longitude:.4f}")
    
    # Bouton de retour
    if st.button("🏠 Retour à l'accueil"):
        st.session_state.page = "accueil"
        st.rerun()
    
    st.markdown("---")
    
    # Section de récupération des données
    st.subheader("🔄 Récupération des données")
    
    if st.button("🚀 Récupérer toutes les données", type="primary"):
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Colonnes pour afficher les données
        col1, col2 = st.columns(2)
        
        try:
            # 1. Données météo
            status_text.text("🌤️ Récupération des données météo...")
            progress_bar.progress(25)
            
            weather_data = get_weather_data(st.session_state.latitude, st.session_state.longitude)
            
            with col1:
                with st.expander("🌤️ Données Météo", expanded=True):
                    if weather_data:
                        st.success("✅ Données météo récupérées")
                        
                        # Données actuelles
                        if "current" in weather_data:
                            st.subheader("🌡️ Météo actuelle")
                            current = weather_data["current"]
                            
                            metric_cols = st.columns(3)
                            with metric_cols[0]:
                                st.metric("Température", f"{current.get('temperature_2m', 'N/A')}°C")
                            with metric_cols[1]:
                                st.metric("Humidité", f"{current.get('relative_humidity_2m', 'N/A')}%")
                            with metric_cols[2]:
                                st.metric("Vent", f"{current.get('wind_speed_10m', 'N/A')} km/h")
                        
                        # Données horaires (aperçu)
                        if "hourly" in weather_data and len(weather_data["hourly"]) > 0:
                            st.subheader("⏰ Prévisions horaires (24h)")
                            hourly_df = pd.DataFrame(weather_data["hourly"][:24])  # Premières 24h
                            st.dataframe(hourly_df[["date", "temperature_2m", "precipitation_probability"]].head(8))
                        
                    else:
                        st.error("❌ Échec de récupération des données météo")
            
            # 2. Saints du jour
            status_text.text("📿 Récupération des saints du jour...")
            progress_bar.progress(50)
            
            saints_data = get_saints_data()
            
            with col2:
                with st.expander("📿 Saints du jour", expanded=True):
                    if saints_data:
                        st.success("✅ Données des saints récupérées")
                        st.write(f"**Nombre de saints :** {saints_data.get('nombre_saints', 0)}")
                        
                        if saints_data.get("saints_majeurs"):
                            for i, saint in enumerate(saints_data["saints_majeurs"][:3]):  # Afficher max 3
                                st.write(f"**{i+1}. {saint.get('valeur', 'N/A')}**")
                                if saint.get('resume'):
                                    st.write(saint['resume'][:200] + "..." if len(saint['resume']) > 200 else saint['resume'])
                    else:
                        st.error("❌ Échec de récupération des saints")
            
            # 3. Horoscope
            status_text.text("🔮 Récupération de l'horoscope...")
            progress_bar.progress(75)
            
            # Sélection du signe astrologique
            signes = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
                     "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
            signe_selectionne = st.selectbox("Choisissez votre signe astrologique:", signes, index=4)  # Leo par défaut
            
            horoscope_data = get_horoscope_data(signe_selectionne)
            
            with col1:
                with st.expander("🔮 Horoscope du jour", expanded=True):
                    if horoscope_data:
                        st.success("✅ Horoscope récupéré")
                        st.write(f"**Signe :** {horoscope_data.get('sign_name', 'N/A')}")
                        if horoscope_data.get('prediction_francaise'):
                            st.write("**Prédiction :**")
                            st.write(horoscope_data['prediction_francaise'])
                    else:
                        st.error("❌ Échec de récupération de l'horoscope")
            
            # 4. Blague du jour
            status_text.text("😄 Récupération de la blague du jour...")
            progress_bar.progress(100)
            
            blague_data = get_blague_data()
            
            with col2:
                with st.expander("😄 Blague du jour", expanded=True):
                    if blague_data:
                        st.success("✅ Blague récupérée")
                        st.write(f"**Type :** {blague_data.get('type', 'N/A')}")
                        st.write(f"**Question :** {blague_data.get('joke', 'N/A')}")
                        st.write(f"**Réponse :** {blague_data.get('answer', 'N/A')}")
                    else:
                        st.error("❌ Échec de récupération de la blague")
            
            # Finalisation
            status_text.text("✅ Toutes les données ont été récupérées !")
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération des données : {e}")
    
    # Section d'informations supplémentaires
    st.markdown("---")
    st.subheader("ℹ️ Informations détaillées")
    
    with st.expander("🛠️ Données techniques"):
        st.write(f"**Ville :** {st.session_state.ville_selectionnee}")
        st.write(f"**Latitude :** {st.session_state.latitude}")
        st.write(f"**Longitude :** {st.session_state.longitude}")
        st.write(f"**Timestamp :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with st.expander("📋 Instructions"):
        st.markdown("""
        - Cliquez sur "Récupérer toutes les données" pour lancer la récupération
        - Les données s'afficheront dans les sections expandables
        - Vous pouvez sélectionner votre signe astrologique pour l'horoscope
        - Utilisez le bouton "Retour à l'accueil" pour changer de ville
        """)

if __name__ == "__main__":
    show_data_page()