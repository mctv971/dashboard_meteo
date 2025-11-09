import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry
import json
from datetime import datetime
import requests
from googletrans import Translator
import asyncio
from blagues_api import BlaguesAPI
from blagues_api import BlagueType

def get_weather_data(latitude, longitude):
    """
    Récupère les données météorologiques pour une localisation donnée et les sauvegarde en JSON.
    
    Parameters:
    latitude (float): Latitude de la localisation
    longitude (float): Longitude de la localisation
    
    Returns:
    dict: Dictionnaire contenant les chemins des fichiers JSON créés
    """
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ["sunrise", "sunset", "daylight_duration", "sunshine_duration"],
        "hourly": ["temperature_2m", "rain", "precipitation", "precipitation_probability", "apparent_temperature", "relative_humidity_2m", "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m", "weather_code", "cloud_cover", "visibility", "showers", "snowfall", "uv_index", "uv_index_clear_sky", "is_day"],
        "current": ["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "precipitation", "rain", "showers", "snowfall", "temperature_2m", "apparent_temperature", "relative_humidity_2m", "is_day", "weather_code", "cloud_cover", "pressure_msl", "surface_pressure"],
        "timezone": "auto",
    }
    responses = openmeteo.weather_api(url, params=params)

    print(responses)

    print("\n✅ Requête effectuée avec succès")

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process current data. The order of variables needs to be the same as requested.
    current = response.Current()
    current_wind_speed_10m = current.Variables(0).Value()
    current_wind_direction_10m = current.Variables(1).Value()
    current_wind_gusts_10m = current.Variables(2).Value()
    current_precipitation = current.Variables(3).Value()
    current_rain = current.Variables(4).Value()
    current_showers = current.Variables(5).Value()
    current_snowfall = current.Variables(6).Value()
    current_temperature_2m = current.Variables(7).Value()
    current_apparent_temperature = current.Variables(8).Value()
    current_relative_humidity_2m = current.Variables(9).Value()
    current_is_day = current.Variables(10).Value()
    current_weather_code = current.Variables(11).Value()
    current_cloud_cover = current.Variables(12).Value()
    current_pressure_msl = current.Variables(13).Value()
    current_surface_pressure = current.Variables(14).Value()

    # Save current data to JSON
    current_data = {
        "timestamp": str(current.Time()),
        "location": {
            "latitude": float(response.Latitude()),
            "longitude": float(response.Longitude()),
            "elevation": float(response.Elevation()),
            "timezone": str(response.Timezone())
        },
        "wind_speed_10m": float(current_wind_speed_10m) if current_wind_speed_10m is not None else None,
        "wind_direction_10m": float(current_wind_direction_10m) if current_wind_direction_10m is not None else None,
        "wind_gusts_10m": float(current_wind_gusts_10m) if current_wind_gusts_10m is not None else None,
        "precipitation": float(current_precipitation) if current_precipitation is not None else None,
        "rain": float(current_rain) if current_rain is not None else None,
        "showers": float(current_showers) if current_showers is not None else None,
        "snowfall": float(current_snowfall) if current_snowfall is not None else None,
        "temperature_2m": float(current_temperature_2m) if current_temperature_2m is not None else None,
        "apparent_temperature": float(current_apparent_temperature) if current_apparent_temperature is not None else None,
        "relative_humidity_2m": float(current_relative_humidity_2m) if current_relative_humidity_2m is not None else None,
        "is_day": int(current_is_day) if current_is_day is not None else None,
        "weather_code": int(current_weather_code) if current_weather_code is not None else None,
        "cloud_cover": float(current_cloud_cover) if current_cloud_cover is not None else None,
        "pressure_msl": float(current_pressure_msl) if current_pressure_msl is not None else None,
        "surface_pressure": float(current_surface_pressure) if current_surface_pressure is not None else None
    }

    with open('current_weather.json', 'w', encoding='utf-8') as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)


    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_rain = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(3).ValuesAsNumpy()
    hourly_apparent_temperature = hourly.Variables(4).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(5).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(6).ValuesAsNumpy()
    hourly_wind_gusts_10m = hourly.Variables(7).ValuesAsNumpy()
    hourly_wind_direction_10m = hourly.Variables(8).ValuesAsNumpy()
    hourly_weather_code = hourly.Variables(9).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(10).ValuesAsNumpy()
    hourly_visibility = hourly.Variables(11).ValuesAsNumpy()
    hourly_showers = hourly.Variables(12).ValuesAsNumpy()
    hourly_snowfall = hourly.Variables(13).ValuesAsNumpy()
    hourly_uv_index = hourly.Variables(14).ValuesAsNumpy()
    hourly_uv_index_clear_sky = hourly.Variables(15).ValuesAsNumpy()
    hourly_is_day = hourly.Variables(16).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["rain"] = hourly_rain
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["apparent_temperature"] = hourly_apparent_temperature
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["wind_gusts_10m"] = hourly_wind_gusts_10m
    hourly_data["wind_direction_10m"] = hourly_wind_direction_10m
    hourly_data["weather_code"] = hourly_weather_code
    hourly_data["cloud_cover"] = hourly_cloud_cover
    hourly_data["visibility"] = hourly_visibility
    hourly_data["showers"] = hourly_showers
    hourly_data["snowfall"] = hourly_snowfall
    hourly_data["uv_index"] = hourly_uv_index
    hourly_data["uv_index_clear_sky"] = hourly_uv_index_clear_sky
    hourly_data["is_day"] = hourly_is_day

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # Convert numpy types to native Python types for JSON serialization
    hourly_dataframe_json = hourly_dataframe.copy()
    for col in hourly_dataframe_json.columns:
        if col != 'date':
            hourly_dataframe_json[col] = hourly_dataframe_json[col].astype(float)

    # Save hourly data to JSON
    hourly_dataframe_json.to_json('hourly_weather.json', orient='records', date_format='iso', indent=2)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_sunrise = daily.Variables(0).ValuesInt64AsNumpy()
    daily_sunset = daily.Variables(1).ValuesInt64AsNumpy()
    daily_daylight_duration = daily.Variables(2).ValuesAsNumpy()
    daily_sunshine_duration = daily.Variables(3).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end =  pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}

    daily_data["sunrise"] = daily_sunrise
    daily_data["sunset"] = daily_sunset
    daily_data["daylight_duration"] = daily_daylight_duration
    daily_data["sunshine_duration"] = daily_sunshine_duration

    daily_dataframe = pd.DataFrame(data = daily_data)


    # Convert numpy types to native Python types for JSON serialization
    daily_dataframe_json = daily_dataframe.copy()
    for col in daily_dataframe_json.columns:
        if col != 'date':
            if col in ['sunrise', 'sunset']:
                # Convert timestamp to readable format
                daily_dataframe_json[col] = pd.to_datetime(daily_dataframe_json[col], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                daily_dataframe_json[col] = daily_dataframe_json[col].astype(float)

    # Save daily data to JSON
    daily_dataframe_json.to_json('daily_weather.json', orient='records', date_format='iso', indent=2)
    
    return {
        "current": "current_weather.json",
        "hourly": "hourly_weather.json", 
        "daily": "daily_weather.json"
    }

def get_saints_data():
    """
    Récupère les données des saints du jour depuis l'API Nominis et les sauvegarde en JSON.
    
    Returns:
    str: Chemin du fichier JSON créé
    """
    url = "https://nominis.cef.fr/json/nominis.php"
    
    try:
        # Récupération des données depuis l'API
        response = requests.get(url)
        response.raise_for_status()  # Lève une exception en cas d'erreur HTTP
        data = response.json()
        
        # Extraction des saints majeurs
        saints_majeurs = []
        
        if "response" in data and "saints" in data["response"] and "majeurs" in data["response"]["saints"]:
            majeurs = data["response"]["saints"]["majeurs"]
            
            for saint in majeurs:
                print(f"saint data: {saint}")
                saint_info = {
                    "valeur": majeurs[saint].get("valeur", ""),
                    "resume": majeurs[saint].get("resume", ""),
                    "lien": majeurs[saint].get("lien", "")
                }
                saints_majeurs.append(saint_info)
                
            print(f"📖 {len(saints_majeurs)} saints majeurs trouvés")
        else:
            print("⚠️ Aucun saint majeur trouvé dans la réponse")
        
        # Sauvegarde des données
        saints_data = {
            "date_recuperation": datetime.now().isoformat(),
            "nombre_saints": len(saints_majeurs),
            "saints_majeurs": saints_majeurs
        }
        
        with open('saints_du_jour.json', 'w', encoding='utf-8') as f:
            json.dump(saints_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Données des saints sauvegardées dans 'saints_du_jour.json'")
        return "saints_du_jour.json"
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des données : {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur lors du décodage JSON : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return None

def get_horoscope_data(sign):
    """
    Récupère les données d'horoscope quotidien depuis l'API Prokerala et les sauvegarde en JSON.
    Utilise l'authentification OAuth en deux étapes.
    
    Parameters:
    sign (str): Signe astrologique (aries, taurus, gemini, cancer, leo, virgo, 
                libra, scorpio, sagittarius, capricorn, aquarius, pisces)
    
    Returns:
    str: Chemin du fichier JSON créé
    
    Note: La fonction utilise automatiquement la date et heure actuelles au format ISO 8601.
    """
    # URLs pour l'authentification et l'API
    token_url = "https://api.prokerala.com/token"
    horoscope_url = "https://api.prokerala.com/v2/horoscope/daily"
        # Remplacez par vos vrais identifiants Prokerala
    client_id = "1b2a34cf-e918-422f-9a9b-50ea6a1db24e"  # À remplacer
    client_secret = "k03lTb4mfWoepIyaVWXIxsBQLzFhMeY64dWK78Z2"  # À remplacer

    
    # Initialisation du traducteur avec gestion d'erreur
    try:
        translator = Translator()
    except Exception as e:
        print(f"⚠️ Erreur initialisation traducteur : {e}")
        translator = None

    try:
        # Étape 1: Obtenir l'access_token
        print("🔐 Récupération de l'access_token...")
        
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        token_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        token_response = requests.post(token_url, data=token_data, headers=token_headers)
        token_response.raise_for_status()
        token_json = token_response.json()
        
        access_token = token_json.get('access_token')
        if not access_token:
            print("❌ Impossible d'obtenir l'access_token")
            return None
            
        print("✅ Access_token obtenu avec succès")
        
        # Étape 2: Utiliser l'access_token pour récupérer l'horoscope
        # Format datetime pour l'API (ISO 8601 avec encodage URL pour +)
        current_datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")

        params = {
            "sign": sign,
            "datetime": current_datetime
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.get(horoscope_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"data received: {data}")
                
        # Extraction des données d'horoscope
        horoscope_info = {}
        
        if "data" in data and "daily_prediction" in data["data"]:
            daily_prediction = data["data"]["daily_prediction"]
            
            # Récupération des prédictions
            prediction = daily_prediction.get("prediction", "")
            sign_name = daily_prediction.get("sign_name", "")
            date = daily_prediction.get("date", "")
            sign_id = daily_prediction.get("sign_id", "")
            
            # Traduction en français
            try:
                if prediction and translator:
                    # Utilisation synchrone de googletrans
                    translated_prediction = translator.translate(prediction, src='en', dest='fr')
                    print(f"Traduction effectuée : {translated_prediction}")
                    prediction_fr = translated_prediction.text
                elif prediction:
                    # Fallback si pas de traducteur
                    print("⚠️ Traducteur non disponible, utilisation du texte original")
                    prediction_fr = prediction
                else:
                    prediction_fr = ""
                    
                print(f"🔮 Horoscope pour {sign_name} ({sign}) récupéré et traduit")
                
            except Exception as translate_error:
                print(f"⚠️ Erreur de traduction, utilisation du texte original : {translate_error}")
                prediction_fr = prediction
            
            horoscope_info = {
                "sign_id": sign_id,
                "sign_name": sign_name,
                "signe_demande": sign,
                "date": date,
                "prediction_originale": prediction,
                "prediction_francaise": prediction_fr,
                "date_recuperation": datetime.now().isoformat()
            }
            
        else:
            print("⚠️ Aucune donnée d'horoscope trouvée dans la réponse")
            horoscope_info = {
                "signe_demande": sign,
                "erreur": "Aucune donnée disponible",
                "date_recuperation": datetime.now().isoformat()
            }
        
        # Sauvegarde des données
        filename = f'horoscope_{sign}_daily.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(horoscope_info, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Horoscope sauvegardé dans '{filename}'")
        return filename
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération de l'horoscope : {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur lors du décodage JSON : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return None

def get_blague_data():
    """
    Récupère une blague aléatoire depuis l'API Blagues et la sauvegarde en JSON.
    
    Parameters:
    token (str): Token de l'API Blagues
    
    Returns:
    str: Chemin du fichier JSON créé
    """
    try:
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjkwNTE1NTk3ODI5NzM0NDMwIiwibGltaXQiOjEwMCwia2V5IjoiZWIwcVdQNHBUeHR1b2JZSElsOUhaQmhGcVNkOUE4SFJVU0EyaTNqM25XVEIwQlZYcXoiLCJjcmVhdGVkX2F0IjoiMjAyNS0xMS0wOVQxNzo0MTo0MyswMDowMCIsImlhdCI6MTc2MjcxMDEwM30.LCYQKX_9o1OSgk7BSTp8mslyRfWublIN5n4VL9CQ1WM"
        # Création de l'instance BlaguesAPI
        blagues = BlaguesAPI(token)
        
        print("😄 Récupération d'une blague aléatoire...")
        
        # Fonction asynchrone pour récupérer la blague
        async def get_random_joke():
            blague = await blagues.random(disallow=[ BlagueType.LIMIT
            ])
            return blague
        
        # Exécution de la fonction asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        blague = loop.run_until_complete(get_random_joke())
        loop.close()
        
        # Extraction des données de la blague
        blague_data = {
            "id": blague.id,
            "type": blague.type,
            "joke": blague.joke,
            "answer": blague.answer,
            "date_recuperation": datetime.now().isoformat()
        }
        
        print(f"🎭 Blague récupérée (Type: {blague.type})")
        print(f"Question: {blague.joke}")
        print(f"Réponse: {blague.answer}")
        
        # Sauvegarde des données
        filename = 'blague_du_jour.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(blague_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Blague sauvegardée dans '{filename}'")
        return filename
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la blague : {e}")
        return None



# Exemple d'utilisation
if __name__ == "__main__":
    # Coordonnées de Berlin (exemple par défaut)
    latitude = 52.52
    longitude = 13.41
    
    # Configuration pour l'horoscope et les blagues
    signe_astrologique = "leo"  # Changez selon votre signe
    # IMPORTANT: Remplacez par votre vrai token Blagues API

    
    print("🌤️  Récupération des données météo...")
    # Appel de la fonction météo
    weather_files_created = get_weather_data(latitude, longitude)
    
    print("\n📿 Récupération des données des saints...")
    # Appel de la fonction saints
    saints_file_created = get_saints_data()
    
    print(f"\n🔮 Récupération de l'horoscope pour {signe_astrologique}...")
    # Appel de la fonction horoscope
    horoscope_file_created = get_horoscope_data(signe_astrologique)
    
    print(f"\n😄 Récupération d'une blague du jour...")
    # Appel de la fonction blague
    blague_file_created = get_blague_data()
    
    print(f"\n🎉 Traitement terminé !")
    print(f"📁 Fichiers météo créés : {weather_files_created}")
    if saints_file_created:
        print(f"📁 Fichier saints créé : {saints_file_created}")
    else:
        print("❌ Échec de création du fichier saints")
        
    if horoscope_file_created:
        print(f"📁 Fichier horoscope créé : {horoscope_file_created}")
    else:
        print("❌ Échec de création du fichier horoscope")
        
    if blague_file_created:
        print(f"📁 Fichier blague créé : {blague_file_created}")
    else:
        print("❌ Échec de création du fichier blague")
        
    print("\n💡 Note: Pour l'horoscope, assurez-vous d'avoir un client_id et client_secret Prokerala valides")
        
    print("\n💡 Note: Pour l'horoscope, assurez-vous d'avoir un client_id et client_secret Prokerala valides")
        
    print("\n💡 Note: Pour l'horoscope, assurez-vous d'avoir une clé API Prokerala valide")