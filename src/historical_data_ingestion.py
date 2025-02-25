import os
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
from web_scrapper import navigate_and_extract  # Importar el web scraper

# Cargar configuración desde .env
load_dotenv()

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")
COUNTRY = os.getenv("COUNTRY", "de")
BIDDING_ZONE = os.getenv("BIDDING_ZONE", "DE-LU")
HISTORICAL_START_DATE = os.getenv("HISTORICAL_START_DATE", "2016-01-01")
SLEEP_TIME = int(os.getenv("SLEEP_TIME", 5))  # Espera entre requests (en segundos)
DAYS_PER_REQUEST = int(os.getenv("DAYS_PER_REQUEST", 7))  # Intervalo de descarga
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))  # Máximo de reintentos en caso de error

# Configurar logging
log_file = "logs/historical_data.log"
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

def store_prices_in_mongo(data):
    """Almacena los datos extraídos en MongoDB, incluyendo los precios."""
    if data and "unix_seconds" in data and "price" in data and "unit" in data:
        timestamps = data["unix_seconds"]
        prices = data["price"]
        currency = data["unit"]  # Guardar la unidad (ej. "EUR / MWh")

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


def download_historical_data():
    """Descargar datos históricos usando el web scraper con fechas dinámicas."""
    start_date = datetime.strptime(HISTORICAL_START_DATE, "%Y-%m-%d")

    log_message(
        f"Iniciando descarga histórica para {COUNTRY} ({BIDDING_ZONE}) desde {HISTORICAL_START_DATE} hasta hoy.")

    while start_date < datetime.today():
        next_date = start_date + timedelta(days=DAYS_PER_REQUEST)

        # **Si la siguiente fecha es mayor que hoy, limitarla a la fecha actual**
        today = datetime.today()
        if next_date > today:
            next_date = today

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = next_date.strftime("%Y-%m-%d")

        log_message(f"Descargando datos desde {start_str} hasta {end_str}...")

        # **Llamar al Web Scraper con parámetros de búsqueda**
        data = navigate_and_extract(BIDDING_ZONE, start_str, end_str)

        if data:
            store_prices_in_mongo(data)
        else:
            log_message(f"No se pudo obtener datos del web scraper para {start_str} - {end_str}")

        # **Detener el bucle si ya hemos llegado a la fecha actual**
        if next_date >= today:
            log_message("Se alcanzó la fecha actual. Finalizando descarga histórica.")
            break

        # Esperar antes de la siguiente solicitud
        log_message(f"Esperando {SLEEP_TIME} segundos antes de la siguiente extracción...")
        time.sleep(SLEEP_TIME)

        # **Actualizar `start_date` correctamente**
        start_date = next_date

    log_message("Descarga histórica completada.")


if __name__ == "__main__":
    download_historical_data()
