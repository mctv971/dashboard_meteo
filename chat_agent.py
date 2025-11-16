import os
from typing import Optional, List, Dict, Any
import requests

from dotenv import load_dotenv

# LangChain / LangGraph
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_agent  # <<< NEW

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
    Utilise l'API de géocodage Nominatim pour obtenir les coordonnées d'une ville.
    Retourne (latitude, longitude) ou None si échec.
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": city_name,
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "MeteoBot/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            return lat, lon
    except Exception as e:
        print(f"Erreur géocodage pour '{city_name}': {e}")
    return None


class WeatherArgs(BaseModel):
    city: str = Field(
        ...,
        description="Nom de la ville pour laquelle récupérer la météo. OBLIGATOIRE : demander à l'utilisateur si non fourni."
    )


@tool("get_weather", args_schema=WeatherArgs)
def tool_get_weather(city: str) -> Dict[str, Any]:
    """
    Récupère toutes les données météo pour une ville donnée.
    Le paramètre 'city' est OBLIGATOIRE. Si l'utilisateur ne fournit pas de ville,
    l'agent doit lui demander avant d'appeler cet outil.
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
    preview = []
    for row in hourly[:6]:  # prochaines ~6 heures
        preview.append({
            "date": str(row.get("date")),
            "t": row.get("temperature_2m"),
            "pp": row.get("precipitation_probability"),
        })

    return {
        "ok": True,
        "current": {
            "temperature_2m": current.get("temperature_2m"),
            "relative_humidity_2m": current.get("relative_humidity_2m"),
            "wind_speed_10m": current.get("wind_speed_10m"),
            "weather_code": current.get("weather_code"),
        },
        "next_hours": preview,
        "lat": lat,
        "lon": lon,
    }



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

    tools = [tool_get_weather, tool_get_saints, tool_get_horoscope, tool_get_blague]

    system_prompt = (
        "Tu es MeteoBot, un assistant météo francophone. Réponds de manière concise, "
        "et cite les unités. Utilise les outils si nécessaire (météo, saints, horoscope, blague). "
        "IMPORTANT : Pour la météo, le nom de la ville est OBLIGATOIRE. Si l'utilisateur ne mentionne pas "
        "de ville, demande-lui d'abord quelle ville l'intéresse avant d'appeler l'outil get_weather."
        "SI L'UTILISATEUR ABORDE UN AUTRE SUJET, INDIQUE LUI QUE TU NE PEUX RÉPONDRE QU'AUX QUESTIONS LIÉES À LA MÉTÉO, MERCI."
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
