import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from datetime import datetime
import os
import sys

# Ajouter le répertoire courant au path pour importer requete_page1
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import requete_page1

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Météo & Bien-être",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un look magnifique
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .weather-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        padding: 1.5rem;
        border-radius: 20px;
        color: white;
        margin: 1rem 0;
    }
    
    .saint-card {
        background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%);
        padding: 1.5rem;
        border-radius: 20px;
        color: white;
        margin: 1rem 0;
    }
    
    .horoscope-card {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        padding: 1.5rem;
        border-radius: 20px;
        color: white;
        margin: 1rem 0;
    }
    
    .joke-card {
        background: linear-gradient(135deg, #55a3ff 0%, #003d82 100%);
        padding: 1.5rem;
        border-radius: 20px;
        color: white;
        margin: 1rem 0;
    }
    
    .sidebar .element-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_coordinates_from_city(city_name):
    """
    Récupère les coordonnées GPS d'une ville via l'API OpenStreetMap Nominatim
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
        headers = {'User-Agent': 'WeatherDashboard/1.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon, data[0]['display_name']
        return None, None, None
    except:
        return None, None, None

def load_json_file(filename):
    """Charge un fichier JSON s'il existe"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return None

def display_weather_data():
    """Affiche les données météorologiques"""
    st.markdown('<div class="weather-card">', unsafe_allow_html=True)
    st.markdown("### 🌤️ Données Météorologiques Actuelles")
    
    current_weather = load_json_file('current_weather.json')
    print("-------------------------")
    print(current_weather)
    print("-------------------------")
    if current_weather:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = current_weather.get('temperature_2m', 'N/A')
            st.metric("🌡️ Température", f"{temp}°C" if temp != 'N/A' else "N/A")
            
        with col2:
            humidity = current_weather.get('relative_humidity_2m', 'N/A')
            st.metric("💧 Humidité", f"{humidity}%" if humidity != 'N/A' else "N/A")
            
        with col3:
            wind_speed = current_weather.get('wind_speed_10m', 'N/A')
            st.metric("💨 Vent", f"{wind_speed} km/h" if wind_speed != 'N/A' else "N/A")
            
        with col4:
            pressure = current_weather.get('pressure_msl', 'N/A')
            st.metric("📊 Pression", f"{pressure} hPa" if pressure != 'N/A' else "N/A")
        
        # Localisation
        if 'location' in current_weather:
            loc = current_weather['location']
            st.write(f"📍 **Localisation:** {loc.get('latitude', 'N/A')}°N, {loc.get('longitude', 'N/A')}°E")
            st.write(f"🏔️ **Altitude:** {loc.get('elevation', 'N/A')} m")
    else:
        st.warning("❌ Données météo actuelles non disponibles")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_weather_charts():
    """Affiche les graphiques météorologiques"""
    hourly_weather = load_json_file('hourly_weather.json')
    if hourly_weather:
        df = pd.DataFrame(hourly_weather)
        df['date'] = pd.to_datetime(df['date'])
        
        # Limiter aux prochaines 24 heures pour la lisibilité
        df_24h = df.head(24).copy()
        
        # Nettoyage des données - remplacer les NaN par 0 et s'assurer que c'est numérique
        numeric_columns = ['temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'precipitation']
        for col in numeric_columns:
            if col in df_24h.columns:
                df_24h[col] = pd.to_numeric(df_24h[col], errors='coerce').fillna(0)
        
        print("Données nettoyées:")
        print(df_24h[['date', 'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'precipitation']].head(10))
        print(f"Min temp: {df_24h['temperature_2m'].min()}, Max temp: {df_24h['temperature_2m'].max()}")
        
        # Créer 4 graphiques séparés en colonnes
        col1, col2 = st.columns(2)
        
        with col1:
            # Graphique température
            if 'temperature_2m' in df_24h.columns:
                fig_temp = go.Figure()
                fig_temp.add_trace(
                    go.Scatter(
                        x=df_24h['date'], 
                        y=df_24h['temperature_2m'],
                        mode='lines+markers',
                        name='Température',
                        line=dict(color='#ff6b6b', width=3),
                        marker=dict(size=8, color='#ff6b6b')
                    )
                )
                fig_temp.update_layout(
                    title="🌡️ Température (24h)",
                    xaxis_title="Heure",
                    yaxis_title="Température (°C)",
                    height=300,
                    showlegend=False
                )
                st.plotly_chart(fig_temp, use_container_width=True)
            
            # Graphique vent
            if 'wind_speed_10m' in df_24h.columns:
                fig_wind = go.Figure()
                fig_wind.add_trace(
                    go.Scatter(
                        x=df_24h['date'], 
                        y=df_24h['wind_speed_10m'],
                        mode='lines+markers',
                        name='Vent',
                        line=dict(color='#45b7d1', width=3),
                        marker=dict(size=8, color='#45b7d1')
                    )
                )
                fig_wind.update_layout(
                    title="💨 Vitesse du vent (24h)",
                    xaxis_title="Heure",
                    yaxis_title="Vitesse (km/h)",
                    height=300,
                    showlegend=False
                )
                st.plotly_chart(fig_wind, use_container_width=True)
        
        with col2:
            # Graphique humidité
            if 'relative_humidity_2m' in df_24h.columns:
                fig_humidity = go.Figure()
                fig_humidity.add_trace(
                    go.Scatter(
                        x=df_24h['date'], 
                        y=df_24h['relative_humidity_2m'],
                        mode='lines+markers',
                        name='Humidité',
                        line=dict(color='#4ecdc4', width=3),
                        marker=dict(size=8, color='#4ecdc4')
                    )
                )
                fig_humidity.update_layout(
                    title="💧 Humidité relative (24h)",
                    xaxis_title="Heure",
                    yaxis_title="Humidité (%)",
                    height=300,
                    showlegend=False
                )
                st.plotly_chart(fig_humidity, use_container_width=True)
            
            # Graphique précipitations
            if 'precipitation' in df_24h.columns:
                fig_precip = go.Figure()
                fig_precip.add_trace(
                    go.Bar(
                        x=df_24h['date'], 
                        y=df_24h['precipitation'],
                        name='Précipitations',
                        marker_color='#74b9ff'
                    )
                )
                fig_precip.update_layout(
                    title="🌧️ Précipitations (24h)",
                    xaxis_title="Heure",
                    yaxis_title="Précipitations (mm)",
                    height=300,
                    showlegend=False
                )
                st.plotly_chart(fig_precip, use_container_width=True)
        
        # Afficher un tableau de debug si nécessaire
        if st.checkbox("🔍 Afficher les données détaillées"):
            st.dataframe(df_24h[['date', 'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'precipitation']])
            
    else:
        st.warning("❌ Données horaires non disponibles")

def display_saints_data():
    """Affiche les données des saints"""
    st.markdown('<div class="saint-card">', unsafe_allow_html=True)
    st.markdown("### 📿 Saints du Jour")
    
    saints_data = load_json_file('saints_du_jour.json')
    if saints_data:
        st.write(f"**Nombre de saints:** {saints_data.get('nombre_saints', 0)}")
        
        if 'saints_majeurs' in saints_data:
            for i, saint in enumerate(saints_data['saints_majeurs'], 1):
                with st.expander(f"🙏 {saint.get('valeur', f'Saint {i}')}"):
                    if saint.get('resume'):
                        st.write(f"**Résumé:** {saint['resume']}")
                    if saint.get('lien'):
                        st.write(f"**Plus d'infos:** [Lien externe]({saint['lien']})")
    else:
        st.warning("❌ Données des saints non disponibles")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_horoscope_data():
    """Affiche les données d'horoscope"""
    st.markdown('<div class="horoscope-card">', unsafe_allow_html=True)
    st.markdown("### 🔮 Horoscope du Jour")
    
    # Chercher le fichier d'horoscope (il peut avoir différents noms selon le signe)
    horoscope_files = [f for f in os.listdir('.') if f.startswith('horoscope_') and f.endswith('_daily.json')]
    
    if horoscope_files:
        horoscope_data = load_json_file(horoscope_files[0])
        if horoscope_data:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.write(f"**Signe:** {horoscope_data.get('sign_name', 'N/A')}")
                st.write(f"**Date:** {horoscope_data.get('date', 'N/A')}")
            
            with col2:
                st.write("**Prédiction en français:**")
                prediction_fr = horoscope_data.get('prediction_francaise', horoscope_data.get('prediction_originale', 'N/A'))
                st.write(f"*{prediction_fr}*")
                
                if horoscope_data.get('prediction_originale') != prediction_fr:
                    with st.expander("Voir la version originale (anglais)"):
                        st.write(horoscope_data.get('prediction_originale', 'N/A'))
    else:
        st.warning("❌ Données d'horoscope non disponibles")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_joke_data():
    """Affiche la blague du jour"""
    st.markdown('<div class="joke-card">', unsafe_allow_html=True)
    st.markdown("### 😄 Blague du Jour")
    
    joke_data = load_json_file('blague_du_jour.json')
    if joke_data:
        st.write(f"**Type:** {joke_data.get('type', 'N/A')}")
        st.write(f"**Question:** {joke_data.get('joke', 'N/A')}")
        st.write(f"**Réponse:** {joke_data.get('answer', 'N/A')}")
        st.write(f"*Blague #{joke_data.get('id', 'N/A')}*")
    else:
        st.warning("❌ Blague du jour non disponible")
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # En-tête principal
    st.markdown('<h1 class="main-header">🌤️ Dashboard Météo & Bien-être 🌟</h1>', unsafe_allow_html=True)
    
    # Sidebar pour les paramètres
    st.sidebar.markdown("## ⚙️ Configuration")
    
    # Input ville
    city = st.sidebar.text_input("🏙️ Entrez votre ville:", value="Paris", help="Entrez le nom de votre ville pour obtenir les données météo")
    
    # Sélection signe astrologique
    signes = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
              "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    
    signe_names = {
        "aries": "♈ Bélier", "taurus": "♉ Taureau", "gemini": "♊ Gémeaux",
        "cancer": "♋ Cancer", "leo": "♌ Lion", "virgo": "♍ Vierge",
        "libra": "♎ Balance", "scorpio": "♏ Scorpion", "sagittarius": "♐ Sagittaire",
        "capricorn": "♑ Capricorne", "aquarius": "♒ Verseau", "pisces": "♓ Poissons"
    }
    
    selected_sign = st.sidebar.selectbox(
        "🔮 Choisissez votre signe astrologique:",
        signes,
        format_func=lambda x: signe_names[x],
        index=4  # Leo par défaut
    )
    
    # Bouton pour récupérer les données
    if st.sidebar.button("🚀 Récupérer toutes les données", type="primary"):
        with st.spinner("📡 Récupération des données en cours..."):
            
            # Obtenir les coordonnées de la ville
            lat, lon, display_name = get_coordinates_from_city(city)
            
            if lat is not None and lon is not None:
                st.sidebar.success(f"📍 Ville trouvée: {display_name}")
                
                # Créer une barre de progression
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # 1. Données météo
                    status_text.text("🌤️ Récupération des données météo...")
                    progress_bar.progress(25)
                    st.sidebar.info(f"🌤️ Récupération des données météo pour {city} ({lat}, {lon})")


                    weather_files = requete_page1.get_weather_data(lat, lon)
                    
                    # 2. Saints
                    status_text.text("📿 Récupération des saints du jour...")
                    progress_bar.progress(50)
                    saints_file = requete_page1.get_saints_data()
                    
                    # 3. Horoscope
                    status_text.text("🔮 Récupération de l'horoscope...")
                    progress_bar.progress(75)
                    horoscope_file = requete_page1.get_horoscope_data(selected_sign)
                    
                    # 4. Blague
                    status_text.text("😄 Récupération de la blague du jour...")
                    progress_bar.progress(100)
                    joke_file = requete_page1.get_blague_data()
                    
                    status_text.text("✅ Toutes les données ont été récupérées!")
                    st.sidebar.success("🎉 Données mises à jour avec succès!")
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Erreur lors de la récupération: {str(e)}")
                    
            else:
                st.sidebar.error(f"❌ Impossible de trouver les coordonnées pour '{city}'")
    
    # Informations sur les dernières données
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 État des données")
    
    files_status = {
        "Météo actuelle": "current_weather.json",
        "Prévisions horaires": "hourly_weather.json",
        "Prévisions quotidiennes": "daily_weather.json",
        "Saints du jour": "saints_du_jour.json",
        "Horoscope": next((f for f in os.listdir('.') if f.startswith('horoscope_')), None),
        "Blague du jour": "blague_du_jour.json"
    }
    
    for name, filename in files_status.items():
        if filename and os.path.exists(filename):
            mod_time = datetime.fromtimestamp(os.path.getmtime(filename))
            st.sidebar.write(f"✅ {name}: {mod_time.strftime('%H:%M:%S')}")
        else:
            st.sidebar.write(f"❌ {name}: Non disponible")
    
    # Affichage principal
    st.markdown("---")
    
    # Section météo
    display_weather_data()
    display_weather_charts()
    
    # Colonnes pour saints et horoscope
    col1, col2 = st.columns(2)
    
    with col1:
        display_saints_data()
    
    with col2:
        display_horoscope_data()
    
    # Blague en bas
    display_joke_data()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
        🌟 Dashboard créé avec ❤️ en Python & Streamlit<br>
        📡 Données provenant de Open-Meteo, Nominis, Prokerala et Blagues-API
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()