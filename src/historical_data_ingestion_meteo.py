import os
import time
import logging
import requests
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar configuración desde .env
load_dotenv()

# Configuración de Open-Meteo
METEO_API_URL = os.getenv("METEO_API_URL")
LATITUDE = os.getenv("METEO_LATITUDE")
LONGITUDE = os.getenv("METEO_LONGITUDE")
HISTORICAL_START_DATE = os.getenv("METEO_HISTORICAL_START_DATE")

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION_METEO = os.getenv("MONGO_COLLECTION_METEO")

# Conectar a MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION_METEO]

# Configurar logging
log_file = "logs/historical_data_meteo.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_message(message):
    """Registrar mensaje en log y consola"""
    logging.info(message)
    print(message)

def fetch_historical_weather_data(start_date, end_date):
    """Solicita datos meteorológicos a Open-Meteo."""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,surface_pressure,cloud_cover,wind_speed_10m,wind_speed_100m,wind_direction_10m,wind_direction_100m",
    }
    try:
        response = requests.get(METEO_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log_message(f"Error al obtener datos de Open-Meteo ({start_date} - {end_date}): {e}")
        return None

def transform_weather_data(data):
    """Transforma los datos de Open-Meteo en formato MongoDB."""
    transformed_data = []
    hourly_data = data.get("hourly", {})
    times = hourly_data.get("time", [])
    for i, timestamp in enumerate(times):
        record = {
            "timestamp": datetime.strptime(timestamp, "%Y-%m-%dT%H:%M"),
            "temperature": hourly_data.get("temperature_2m", [None])[i],
            "humidity": hourly_data.get("relative_humidity_2m", [None])[i],
            "precipitation": hourly_data.get("precipitation", [None])[i],
            "rain": hourly_data.get("rain", [None])[i],
            "snowfall": hourly_data.get("snowfall", [None])[i],
            "surface_pressure": hourly_data.get("surface_pressure", [None])[i],
            "cloud_cover": hourly_data.get("cloud_cover", [None])[i],
            "wind_speed_10m": hourly_data.get("wind_speed_10m", [None])[i],
            "wind_speed_100m": hourly_data.get("wind_speed_100m", [None])[i],
            "wind_direction_10m": hourly_data.get("wind_direction_10m", [None])[i],
            "wind_direction_100m": hourly_data.get("wind_direction_100m", [None])[i],
        }
        transformed_data.append(record)
    return transformed_data

def load_weather_data(data):
    """Inserta los datos transformados en MongoDB evitando duplicados."""
    if data:
        collection.insert_many(data)
        log_message(f"{len(data)} registros meteorológicos insertados en MongoDB.")

def download_historical_meteo_data():
    """Descarga datos históricos en lotes de 30 días."""
    start_date = datetime.strptime(HISTORICAL_START_DATE, "%Y-%m-%d")
    end_date = datetime.today()

    while start_date < end_date:
        next_date = start_date + timedelta(days=30)
        if next_date > end_date:
            next_date = end_date

        log_message(f"Descargando datos meteorológicos desde {start_date.strftime('%Y-%m-%d')} hasta {next_date.strftime('%Y-%m-%d')}...")
        raw_data = fetch_historical_weather_data(start_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d"))

        if raw_data:
            transformed_data = transform_weather_data(raw_data)
            load_weather_data(transformed_data)
        else:
            log_message(f"No se obtuvieron datos para {start_date.strftime('%Y-%m-%d')} - {next_date.strftime('%Y-%m-%d')}.")

        log_message("Esperando 10 segundos antes de la próxima solicitud...")
        time.sleep(10)

        start_date = next_date + timedelta(days=1)

if __name__ == "__main__":
    log_message("Iniciando descarga histórica de datos meteorológicos...")
    download_historical_meteo_data()
    log_message("Descarga histórica completada.")
