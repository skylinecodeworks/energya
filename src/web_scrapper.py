import os
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Cargar configuración desde .env
load_dotenv()

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")
COUNTRY = os.getenv("COUNTRY", "de")
BIDDING_ZONE = os.getenv("BIDDING_ZONE", "DE-LU")
SWAGGER_URL = os.getenv("SWAGGER_URL", "https://api.energy-charts.info/")

# Configurar logging
log_file = "logs/web_scraper.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# **Conectar a MongoDB** y hacer accesible la colección
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

# Configuración de Selenium en modo headless
options = Options()
options.headless = True
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Inicializar el navegador
browser = webdriver.Chrome(options=options)

def log_message(message):
    """Registrar mensaje en log y consola"""
    logging.info(message)
    print(message)

def navigate_and_extract(bidding_zone, start_date, end_date):
    """Navega el Swagger UI y extrae los datos de energía usando los parámetros recibidos."""
    options = Options()
    options.headless = True  # Modo sin interfaz gráfica
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    browser = None

    try:
        # **Inicializar el navegador para cada solicitud**
        browser = webdriver.Chrome(options=options)

        swagger_url = "https://api.energy-charts.info/"
        api_url = f"{swagger_url}price?bzn={bidding_zone}&start={start_date}&end={end_date}"

        log_message(f"Navegando a {swagger_url} para obtener datos de {bidding_zone} entre {start_date} y {end_date}")
        browser.get(api_url)

        # **Esperar hasta que el contenido JSON esté disponible**
        WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.TAG_NAME, "pre")))

        # Extraer el HTML resultante y buscar el JSON de respuesta
        soup = BeautifulSoup(browser.page_source, "html.parser")
        json_data = soup.find("pre")

        if json_data:
            log_message("Datos obtenidos correctamente desde Swagger UI.")
            return json.loads(json_data.text)  # Convertir el JSON a un diccionario
        else:
            log_message("No se encontraron datos en la página.")
            return None

    except Exception as e:
        log_message(f"Error durante la navegación: {str(e)}")
        return None

    finally:
        if browser:
            browser.quit()  # Cerrar el navegador correctamente



def store_prices_in_mongo(data):
    """Almacenar los datos extraídos en MongoDB."""
    if data and "unix_seconds" in data:
        processed_data = []
        timestamps = data["unix_seconds"]

        for ts in timestamps:
            record = {
                "timestamp": datetime.utcfromtimestamp(ts),
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
    log_message("Iniciando scraper de Swagger UI...")
    energy_data = navigate_and_extract()
    if energy_data:
        store_prices_in_mongo(energy_data)
    log_message("Proceso completado.")
