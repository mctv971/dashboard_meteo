"""
Générateur de recommandations intelligent basé sur l'IA
Utilise le modèle LLM pour créer des recommandations personnalisées
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def generate_recommendations(weather_data: dict, ville: str) -> dict:
    """
    Génère des recommandations intelligentes basées sur la météo et la ville.
    
    Args:
        weather_data: Dictionnaire contenant les données météo (current, hourly, daily)
        ville: Nom de la ville
        
    Returns:
        dict: Dictionnaire avec les sections de recommandations
    """
    try:
        # Récupérer le modèle
        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            return {"error": "GROQ_API_KEY manquant"}
        
        llm = ChatGroq(
            model=model_name,
            temperature=0.7,  # Plus créatif pour les recommandations
            max_tokens=2000,
            timeout=60,
            groq_api_key=api_key,
        )
        
        # Extraire les données pertinentes
        current = weather_data.get("current", {})
        hourly = weather_data.get("hourly", [])[:24]
        daily = weather_data.get("daily", [])[:7]
        
        # Données actuelles complètes
        temp = current.get("temperature_2m", 20)
        apparent_temp = current.get("apparent_temperature", temp)
        humidity = current.get("relative_humidity_2m", 50)
        wind = current.get("wind_speed_10m", 0)
        wind_gusts = current.get("wind_gusts_10m", wind)
        cloud_cover = current.get("cloud_cover", 0)
        pressure = current.get("pressure_msl", 1013)
        visibility = current.get("visibility", 10000) / 1000 if current.get("visibility") else None  # en km
        is_day = current.get("is_day", 1)
        precipitation = current.get("precipitation", 0)
        snowfall = current.get("snowfall", 0)
        
        # Statistiques horaires (24h)
        rain_probs = []
        uv_values = []
        temps_hourly = []
        wind_speeds = []
        cloud_covers = []
        
        if hourly:
            for h in hourly:
                if h.get("precipitation_probability") is not None:
                    rain_probs.append(h.get("precipitation_probability"))
                if h.get("uv_index") is not None:
                    uv_values.append(h.get("uv_index"))
                if h.get("temperature_2m") is not None:
                    temps_hourly.append(h.get("temperature_2m"))
                if h.get("wind_speed_10m") is not None:
                    wind_speeds.append(h.get("wind_speed_10m"))
                if h.get("cloud_cover") is not None:
                    cloud_covers.append(h.get("cloud_cover"))
        
        rain_prob_max = max(rain_probs) if rain_probs else 0
        rain_prob_avg = sum(rain_probs) / len(rain_probs) if rain_probs else 0
        uv_max = max(uv_values) if uv_values else 0
        temp_max_24h = max(temps_hourly) if temps_hourly else temp
        temp_min_24h = min(temps_hourly) if temps_hourly else temp
        wind_max = max(wind_speeds) if wind_speeds else wind
        cloud_avg = sum(cloud_covers) / len(cloud_covers) if cloud_covers else cloud_cover
        
        # Données journalières (aujourd'hui)
        today = daily[0] if daily else {}
        temp_max = today.get("temperature_2m_max", temp)
        temp_min = today.get("temperature_2m_min", temp)
        sunrise = today.get("sunrise", "")
        sunset = today.get("sunset", "")
        sunshine_duration = today.get("sunshine_duration", 0) / 3600 if today.get("sunshine_duration") else 0  # en heures
        daylight_duration = today.get("daylight_duration", 0) / 3600 if today.get("daylight_duration") else 0  # en heures
        precip_sum = today.get("precipitation_sum", 0)
        
        # Tendances sur 3-7 jours
        temps_next_days = []
        rain_next_days = []
        uv_next_days = []
        
        for day in daily[1:4]:  # J+1 à J+3
            if day.get("temperature_2m_max") is not None:
                temps_next_days.append(day.get("temperature_2m_max"))
            if day.get("precipitation_probability_max") is not None:
                rain_next_days.append(day.get("precipitation_probability_max"))
            if day.get("uv_index_max") is not None:
                uv_next_days.append(day.get("uv_index_max"))
        
        temp_trend = "stable"
        if temps_next_days and len(temps_next_days) >= 2:
            if temps_next_days[-1] > temps_next_days[0] + 3:
                temp_trend = "hausse"
            elif temps_next_days[-1] < temps_next_days[0] - 3:
                temp_trend = "baisse"
        
        # Construire le prompt
        system_prompt = """Tu es un assistant météo expert qui génère des recommandations personnalisées et créatives.
        
Tu dois créer des recommandations DÉTAILLÉES et PRATIQUES en format markdown structuré.

IMPORTANT : 
- Sois SPÉCIFIQUE à la ville mentionnée (événements, lieux, culture locale)
- Sois CRÉATIF et ENGAGEANT dans tes suggestions
- Donne des HORAIRES précis quand pertinent
- Mentionne des LIEUX CONCRETS de la ville
- Adapte tes conseils au CONTEXTE LOCAL (saison, jour de la semaine si pertinent)

Structure OBLIGATOIRE de ta réponse (utilise exactement ces titres avec emojis) :

### 🏃 Activités sportives recommandées
[2-4 activités avec lieux précis et horaires conseillés]

### 🌱 Jardinage & Plantes
[Conseils adaptés à la météo et à la saison]

### 🚗 Entretien & Pratique
[Conseils voiture, vélo, etc.]

### 👕 Vie quotidienne
[Séchage linge, choix vestimentaires, etc.]

### 🎭 Sorties & Loisirs
[3-5 suggestions avec lieux précis de la ville]

### 🍽️ Gastronomie locale
[Suggestions de restaurants, terrasses, spécialités selon la météo]

### 📋 Synthèse de la journée
[Un paragraphe d'ambiance générale avec conseils principaux]

Utilise des **gras**, des emojis, et sois ENTHOUSIASTE !"""

        # Construire des descriptions contextuelles
        time_of_day = "☀️ journée" if is_day else "🌙 soirée/nuit"
        sky_condition = "☁️ nuageux" if cloud_avg > 70 else ("⛅ partiellement nuageux" if cloud_avg > 30 else "☀️ dégagé")
        wind_condition = "💨 venteux" if wind > 25 else ("🍃 léger vent" if wind > 10 else "😌 calme")
        
        precip_text = ""
        if snowfall > 0:
            precip_text = f"❄️ Neige en cours ({snowfall:.1f} mm)"
        elif precipitation > 0:
            precip_text = f"🌧️ Pluie en cours ({precipitation:.1f} mm)"
        
        visibility_text = f"👁️ Visibilité : {visibility:.1f} km" if visibility else ""
        
        user_prompt = f"""Génère des recommandations personnalisées pour **{ville}** avec ces conditions météo :

📊 **Conditions actuelles ({time_of_day}) :**
- 🌡️ Température : {temp:.1f}°C (ressenti : {apparent_temp:.1f}°C)
- 🌡️ Min/Max aujourd'hui : {temp_min:.1f}°C / {temp_max:.1f}°C
- 💧 Humidité : {humidity:.0f}%
- 💨 Vent : {wind:.1f} km/h (rafales jusqu'à {wind_gusts:.1f} km/h)
- {sky_condition} (couverture : {cloud_cover:.0f}%)
- 🌧️ Probabilité de pluie (24h) : {rain_prob_max:.0f}% (moyenne : {rain_prob_avg:.0f}%)
- ☀️ Indice UV max : {uv_max:.1f}
- 🌅 Lever : {sunrise} | Coucher : {sunset}
- ☀️ Ensoleillement prévu : {sunshine_duration:.1f}h sur {daylight_duration:.1f}h de jour
- 📊 Pression : {pressure:.0f} hPa
{visibility_text}
{precip_text}

📈 **Prévisions & Tendances (3 prochains jours) :**
- 🌡️ Températures : {temps_next_days[0]:.1f}°C → {temps_next_days[-1]:.1f}°C (tendance : {temp_trend})
- 🌧️ Risque de pluie moyen : {sum(rain_next_days)/len(rain_next_days) if rain_next_days else 0:.0f}%
- ☀️ UV moyen : {sum(uv_next_days)/len(uv_next_days) if uv_next_days else 0:.1f}
- 💧 Précipitations totales attendues : {precip_sum:.1f} mm

🎯 **Mission :** Crée des recommandations DÉTAILLÉES, LOCALISÉES et CRÉATIVES pour cette ville.
Mentionne des LIEUX RÉELS, des ÉVÉNEMENTS possibles, et des CONSEILS PRATIQUES adaptés à TOUTES ces données météo.
Utilise les tendances pour conseiller sur les prochains jours aussi !

Réponds UNIQUEMENT avec le contenu structuré (commence directement par "### 🏃")."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Appeler le LLM
        response = llm.invoke(messages)
        
        return {
            "success": True,
            "content": response.content,
            "ville": ville,
            "temp": temp,
            "apparent_temp": apparent_temp,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "humidity": humidity,
            "wind": wind,
            "wind_gusts": wind_gusts,
            "cloud_cover": cloud_cover,
            "cloud_avg": cloud_avg,
            "pressure": pressure,
            "visibility": visibility,
            "rain_prob": rain_prob_max,
            "rain_prob_avg": rain_prob_avg,
            "uv": uv_max,
            "precipitation": precipitation,
            "snowfall": snowfall,
            "sunrise": sunrise,
            "sunset": sunset,
            "sunshine_duration": sunshine_duration,
            "daylight_duration": daylight_duration,
            "precip_sum": precip_sum,
            "is_day": is_day,
            "temp_trend": temp_trend,
            "temps_next_days": temps_next_days,
            "rain_next_days": rain_next_days
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def format_recommendations_for_display(reco_data: dict) -> str:
    """
    Formate les recommandations pour l'affichage Streamlit.
    
    Args:
        reco_data: Données retournées par generate_recommendations
        
    Returns:
        str: Contenu formaté en markdown
    """
    if not reco_data.get("success"):
        return f"⚠️ Erreur lors de la génération : {reco_data.get('error', 'Inconnue')}"
    
    content = reco_data.get("content", "")
    
    # Ajouter un en-tête
    header = f"""
🎯 **Recommandations générées par IA pour {reco_data.get('ville', 'votre ville')}**

*Basées sur les conditions météorologiques actuelles et les prévisions*

---

"""
    
    return header + content
