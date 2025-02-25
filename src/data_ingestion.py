import os
import time
import logging
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
from web_scrapper import navigate_and_extract

# Cargar variables desde .env
load_dotenv()

# Configuración desde .env
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")
COUNTRY = os.getenv("COUNTRY", "de")  # Alemania por defecto
BIDDING_ZONE = os.getenv("BIDDING_ZONE", "DE-LU")  # Alemania-Luxemburgo por defecto

# Configurar logging
log_file = "logs/daily_data_ingestion.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Conectar a MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

def log_message(message):
    """Registrar mensaje en log y consola"""
    logging.info(message)
    print(message)

# Obtener la última fecha registrada en MongoDB para la bidding zone específica
latest_entry = collection.find_one({"bidding_zone": BIDDING_ZONE}, sort=[("timestamp", -1)])

if latest_entry:
    START_DATE = latest_entry["timestamp"].strftime("%Y-%m-%d")
else:
    START_DATE = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")  # Si no hay datos, toma ayer

END_DATE = datetime.today().strftime("%Y-%m-%d")

def store_prices_in_mongo(data):
    """Almacena los datos en MongoDB evitando duplicados."""
    if data and "unix_seconds" in data and "price" in data and "unit" in data:
        timestamps = data["unix_seconds"]
        prices = data["price"]
        currency = data["unit"]

        if len(timestamps) != len(prices):
            log_message(f"Error: Desajuste entre timestamps ({len(timestamps)}) y precios ({len(prices)}).")
            return

        processed_data = []
        for ts, price in zip(timestamps, prices):
            record = {
                "timestamp": datetime.utcfromtimestamp(ts),
                "price": price,
                "currency": currency,
                "country": COUNTRY,
                "bidding_zone": BIDDING_ZONE
            }

            # Evitar duplicados
            if not collection.find_one({"timestamp": record["timestamp"], "bidding_zone": BIDDING_ZONE}):
                processed_data.append(record)

        if processed_data:
            collection.insert_many(processed_data)
            log_message(f"Datos insertados correctamente ({len(processed_data)} registros).")
        else:
            log_message("No hay datos nuevos para insertar.")
    else:
        log_message("Estructura de datos inesperada. No se insertaron registros.")

if __name__ == "__main__":
    log_message(f"Descargando datos diarios para {COUNTRY} ({BIDDING_ZONE}) desde {START_DATE} hasta {END_DATE}...")

    # **Usar el Web Scraper en lugar de la API directa**
    energy_prices = navigate_and_extract(BIDDING_ZONE, START_DATE, END_DATE)

    store_prices_in_mongo(energy_prices)
    log_message("Descarga diaria completada.")
