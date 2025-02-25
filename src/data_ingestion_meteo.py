import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from pymongo import MongoClient

from historical_data_ingestion_meteo import fetch_historical_weather_data, transform_weather_data

# Cargar configuración desde .env
load_dotenv()

# Configuración de Open-Meteo
METEO_API_URL = os.getenv("METEO_API_URL")
LATITUDE = os.getenv("METEO_LATITUDE")
LONGITUDE = os.getenv("METEO_LONGITUDE")

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION_METEO = os.getenv("MONGO_COLLECTION_METEO")

# Conectar a MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION_METEO]

# Configurar logging
log_file = "logs/daily_data_meteo.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_message(message):
    """Registrar mensaje en log y consola"""
    logging.info(message)
    print(message)

def fetch_daily_weather_data():
    """Solicita los datos del día anterior a Open-Meteo."""
    start_date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    return fetch_historical_weather_data(start_date, start_date)

def load_weather_data_filtered(data):
    """Carga datos en MongoDB solo si no existen."""
    inserted_count = 0
    for record in data:
        existing_entry = collection.find_one({"timestamp": record["timestamp"]})
        if not existing_entry:
            collection.insert_one(record)
            inserted_count += 1

    if inserted_count > 0:
        log_message(f"✅ {inserted_count} registros nuevos insertados en MongoDB.")
    else:
        log_message("⚠️ No se insertaron datos. Todos los registros ya existían.")

if __name__ == "__main__":
    log_message("📡 Descargando datos meteorológicos diarios...")

    data = fetch_daily_weather_data()
    if data:
        transformed_data = transform_weather_data(data)
        load_weather_data_filtered(transformed_data)
        log_message("📡 Descarga diaria completada.")
    else:
        log_message("⚠️ No se obtuvieron datos meteorológicos hoy.")
