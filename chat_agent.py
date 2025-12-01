import os
from typing import Optional, List, Dict, Any
import requests
from datetime import datetime

from dotenv import load_dotenv

# LangChain / LangGraph
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_agent  # <<< NEW


from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.retrievers import WikipediaRetriever


# App tools
from requete_page1 import (
    get_weather_data,
    get_saints_data,
    get_horoscope_data,
    get_blague_data,
)


load_dotenv()


def _get_city_coords(city_name: str) -> Optional[tuple[float, float]]:
    """
    Utilise l'API de géocodage Photon pour obtenir les coordonnées d'une ville.
    Photon est plus fiable que Nominatim pour les déploiements cloud.
    Retourne (latitude, longitude) ou None si échec.
    """
    try:
        url = "https://photon.komoot.io/api/"
        params = {
            "q": city_name,
            "limit": 1,
            "lang": "fr"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("features") and len(data["features"]) > 0:
            coordinates = data["features"][0]["geometry"]["coordinates"]
            # Photon renvoie [longitude, latitude], on inverse
            lon, lat = coordinates[0], coordinates[1]
            return lat, lon
    except Exception as e:
        print(f"Erreur géocodage pour '{city_name}': {e}")
    return None


def _aggregate_hourly_by_period(hourly_data: List[Dict], date_str: str) -> Dict[str, Any]:
    """
    Agrège les données horaires par période de la journée (nuit, matin, après-midi, soir).
    Retourne les moyennes et min/max pour chaque période.
    """
    from datetime import datetime
    
    periods = {
        "nuit": [],      # 0h-6h
        "matin": [],     # 6h-12h
        "apres_midi": [], # 12h-18h
        "soir": []       # 18h-24h
    }
    
    for row in hourly_data:
        try:
            row_date = datetime.fromisoformat(str(row.get("date")).replace('Z', '+00:00'))
            row_date_str = row_date.strftime('%Y-%m-%d')
            
            if row_date_str != date_str:
                continue
                
            hour = row_date.hour
            
            if 0 <= hour < 6:
                periods["nuit"].append(row)
            elif 6 <= hour < 12:
                periods["matin"].append(row)
            elif 12 <= hour < 18:
                periods["apres_midi"].append(row)
            else:
                periods["soir"].append(row)
        except Exception:
            continue
    
    result = {}
    for period_name, period_data in periods.items():
        if not period_data:
            continue
            
        temps = [r.get("temperature_2m") for r in period_data if r.get("temperature_2m") is not None]
        precip_prob = [r.get("precipitation_probability") for r in period_data if r.get("precipitation_probability") is not None]
        wind = [r.get("wind_speed_10m") for r in period_data if r.get("wind_speed_10m") is not None]
        
        result[period_name] = {
            "temperature_avg": round(sum(temps) / len(temps), 1) if temps else None,
            "temperature_min": round(min(temps), 1) if temps else None,
            "temperature_max": round(max(temps), 1) if temps else None,
            "precipitation_probability_avg": round(sum(precip_prob) / len(precip_prob), 1) if precip_prob else None,
            "wind_speed_avg": round(sum(wind) / len(wind), 1) if wind else None,
        }
    
    return result


class WeatherArgs(BaseModel):
    city: str = Field(
        ...,
        description="Nom de la ville pour laquelle récupérer la météo. OBLIGATOIRE : demander à l'utilisateur si non fourni."
    )
    days: str = Field(
        default="today",
        description=(
            "Jours pour lesquels récupérer les prévisions. Options: "
            "'today' (aujourd'hui uniquement), "
            "'tomorrow' (demain uniquement), "
            "'week' (les 7 prochains jours), "
            "ou un nombre spécifique comme '3' pour les 3 prochains jours. "
            "Par défaut: 'today'"
        )
    )


@tool("get_weather", args_schema=WeatherArgs)
def tool_get_weather(city: str, days: str = "today") -> Dict[str, Any]:
    """
    Récupère les données météo pour une ville donnée avec filtrage flexible des jours.
    
    Le paramètre 'city' est OBLIGATOIRE. Si l'utilisateur ne fournit pas de ville,
    l'agent doit lui demander avant d'appeler cet outil.
    
    Le paramètre 'days' permet de filtrer les prévisions:
    - 'today': données actuelles + prévisions par période (nuit, matin, après-midi, soir)
    - 'tomorrow': prévisions pour demain avec moyennes par période
    - 'week': prévisions pour les 7 prochains jours avec moyennes quotidiennes
    - un nombre (ex: '3'): prévisions pour les N prochains jours avec moyennes quotidiennes
    
    Retourne des données agrégées pour éviter la surcharge de contexte.
    """
    coords = _get_city_coords(city)
    if not coords:
        return {"ok": False, "message": f"Impossible de trouver les coordonnées de '{city}'"}
    
    lat, lon = coords
    data = get_weather_data(lat, lon)
    if not data:
        return {"ok": False, "message": "Données météo indisponibles"}

    current = data.get("current", {})
    hourly = data.get("hourly", [])
    daily = data.get("daily", [])
    
    # Déterminer combien de jours inclure
    if days == "today":
        num_days = 1
        include_current = True
        include_periods = True
    elif days == "tomorrow":
        num_days = 1
        daily = daily[1:2] if len(daily) > 1 else []
        include_current = False
        include_periods = True
    elif days == "week":
        num_days = 7
        include_current = True
        include_periods = False
    else:
        # Essayer de parser comme un nombre
        try:
            num_days = int(days)
            num_days = min(max(1, num_days), 7)  # Limiter entre 1 et 7
            include_current = True
            include_periods = False
        except ValueError:
            num_days = 1
            include_current = True
            include_periods = True
    
    result = {"ok": True, "lat": lat, "lon": lon}
    
    # Inclure les données actuelles si demandé
    if include_current and days != "tomorrow":
        result["current"] = {
            "temperature_2m": current.get("temperature_2m"),
            "relative_humidity_2m": current.get("relative_humidity_2m"),
            "wind_speed_10m": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
        }
    
    # Prévisions quotidiennes avec agrégation intelligente
    daily_forecast = []
    for i, day in enumerate(daily[:num_days]):
        day_data = {
            "date": str(day.get("date")),
            "temperature_max": day.get("temperature_2m_max"),
            "temperature_min": day.get("temperature_2m_min"),
            "precipitation_sum": day.get("precipitation_sum"),
            "precipitation_probability_max": day.get("precipitation_probability_max"),
            "weather_code": day.get("weather_code"),
            "wind_speed_max": day.get("wind_speed_10m_max"),
            "uv_index_max": day.get("uv_index_max"),
        }
        
        # Ajouter les détails par période si demandé (today ou tomorrow uniquement)
        if include_periods and i < 2:  # Seulement pour les 2 premiers jours max
            try:
                date_obj = datetime.fromisoformat(str(day.get("date")).replace('Z', '+00:00'))
                date_str = date_obj.strftime('%Y-%m-%d')
                periods = _aggregate_hourly_by_period(hourly, date_str)
                if periods:
                    day_data["periods"] = periods
            except Exception as e:
                print(f"Erreur agrégation périodes: {e}")
        
        daily_forecast.append(day_data)
    
    if daily_forecast:
        result["daily_forecast"] = daily_forecast
    
    return result



@tool("get_saints")
def tool_get_saints() -> Dict[str, Any]:
    """
    Récupère les saints du jour (majeurs) depuis l'API Nominis et retourne un résumé concis.
    """
    data = get_saints_data()
    if not data:
        return {"ok": False, "message": "Données saints indisponibles"}
    saints = data.get("saints_majeurs", [])
    return {
        "ok": True,
        "count": len(saints),
        "top": saints[:3],
    }


class HoroscopeArgs(BaseModel):
    sign: str = Field(..., description="Signe astrologique en anglais (ex: leo, aries, virgo)")


@tool("get_horoscope", args_schema=HoroscopeArgs)
def tool_get_horoscope(sign: str) -> Dict[str, Any]:
    """
    Récupère l'horoscope du jour pour un signe donné et renvoie la version française si disponible.
    """
    data = get_horoscope_data(sign)
    if not data:
        return {"ok": False, "message": "Horoscope indisponible"}
    return {
        "ok": True,
        "sign": data.get("sign_name") or sign,
        "prediction_fr": data.get("prediction_francaise") or data.get("prediction_originale"),
        "date": data.get("date"),
    }


@tool("get_blague")
def tool_get_blague() -> Dict[str, Any]:
    """
    Récupère une blague courte (question/réponse) et la renvoie.
    """
    data = get_blague_data()
    if not data:
        return {"ok": False, "message": "Blague indisponible"}
    return {
        "ok": True,
        "type": data.get("type"),
        "joke": data.get("joke"),
        "answer": data.get("answer"),
    }

class SearchWebArgs(BaseModel):
    query: str = Field(..., description="Requête de recherche web à effectuer")


@tool("search_web", args_schema=SearchWebArgs)
def tool_search_web(query: str) -> Dict[str, Any]:
    """
    Utilise cet outil pour effectuer des recherches web autour du sujet de la ville.
    Effectue une recherche web via DuckDuckGo et retourne les résultats.
    """
    try:
        search = DuckDuckGoSearchResults()
        results = search.run(query)
        return {
            "ok": True,
            "results": results  # DuckDuckGoSearchResults retourne déjà une chaîne formatée
        }
    except Exception as e:
        return {"ok": False, "message": f"Erreur de recherche: {str(e)}"}


class WikiLookupArgs(BaseModel):
    topic: str = Field(..., description="Sujet à rechercher sur Wikipedia")


@tool("wiki_lookup", args_schema=WikiLookupArgs)
def tool_wiki_lookup(topic: str) -> Dict[str, Any]:
    """
    Utilise cet outil pour rechercher des informations sur des articles liés à la ville, ca peut être des monuments, histoire, culture, etc.
    Recherche un sujet sur Wikipedia et retourne un résumé concis.
    """
    try:
        retriever = WikipediaRetriever()
        docs = retriever.get_relevant_documents(topic)
        if not docs:
            return {"ok": False, "message": f"Aucun résultat Wikipedia pour '{topic}'"}
        
        summary = docs[0].page_content[:500] if docs else "Aucun contenu trouvé."  # Limite à 500 caractères
        return {
            "ok": True,
            "summary": summary
        }
    except Exception as e:
        return {"ok": False, "message": f"Erreur Wikipedia: {str(e)}"}

def build_agent():
    """Create a LangChain/LangGraph agent wired with our tools and a Groq LLM."""
    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY manquant. Définissez-le dans .env")

    llm = ChatGroq(
        model=model_name,
        temperature=0.2,
        max_tokens=None,
        timeout=60,
        groq_api_key=api_key,
    )

    tools = [tool_get_weather, tool_get_saints, tool_get_horoscope, tool_get_blague, tool_search_web, tool_wiki_lookup]

    system_prompt = (
        "Tu es MeteoBot, un assistant météo francophone intelligent et informatif. "
        "Réponds de manière concise et cite les unités. "
        "\n\n"
        "IMPORTANT : Pour la météo, le nom de la ville est OBLIGATOIRE. Si l'utilisateur ne mentionne pas "
        "de ville, demande-lui d'abord quelle ville l'intéresse avant d'appeler l'outil get_weather. "
        "\n\n"
        "ENRICHISSEMENT DES RÉPONSES : "
        "Quand tu donnes la météo d'une ville, n'hésite pas à ENRICHIR ta réponse avec des informations contextuelles "
        "pertinentes sur la ville en utilisant les outils search_web et wiki_lookup. Par exemple : "
        "- Des faits intéressants sur la ville "
        "- Des monuments ou attractions en lien avec la météo annoncée "
        "- Des événements locaux si pertinent "
        "- Des conseils d'activités adaptés à la météo "
        "\n\n"
        "Cela rendra tes réponses plus utiles et engageantes pour l'utilisateur. "
        "\n\n"
        "RESTRICTIONS : "
        "Si l'utilisateur aborde un sujet complètement hors météo (politique, cuisine, sport non lié à la météo, etc.), "
        "indique-lui poliment que tu es spécialisé dans la météo et les informations liées aux villes."
    )

    # 👉 Nouveau : on utilise create_agent (LangChain) qui tourne sur LangGraph
    graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )
    return graph


def _to_lc_messages(history: List[Dict[str, str]]):
    msgs = []
    for m in history:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            msgs.append(AIMessage(content=content))
        elif role == "system":
            msgs.append(SystemMessage(content=content))
    return msgs


def run_agent(user_input: str, history: Optional[List[Dict[str, str]]] = None) -> str:
    """Invoke the agent with optional history and return assistant text."""
    graph = build_agent()
    messages = _to_lc_messages(history or []) + [HumanMessage(content=user_input)]
    result = graph.invoke({"messages": messages})
    # result["messages"] est une liste de BaseMessage ; on récupère le dernier AIMessage
    out_msgs = result.get("messages", [])
    last_ai = next((m for m in reversed(out_msgs) if isinstance(m, AIMessage)), None)
    return last_ai.content if last_ai else "(Aucune réponse)"
