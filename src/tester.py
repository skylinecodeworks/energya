from pymongo import MongoClient

MONGO_URI = "mongodb://admin:password@localhost:27017/"
MONGO_DB = "energy_db"  # Ajusta según tu configuración
MONGO_COLLECTION_ENERGY = "energy_prices"
MONGO_COLLECTION_METEO = "weather_data"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

# Contar registros en ambas colecciones
num_energy_records = db[MONGO_COLLECTION_ENERGY].count_documents({})
num_meteo_records = db[MONGO_COLLECTION_METEO].count_documents({})

print(f"⚡ Registros en energy_prices: {num_energy_records}")
print(f"🌤️ Registros en weather_data: {num_meteo_records}")

# Obtener una muestra de 5 registros para inspección
sample_energy = list(db[MONGO_COLLECTION_ENERGY].find().limit(5))
sample_meteo = list(db[MONGO_COLLECTION_METEO].find().limit(5))

print("\n🔍 Muestra de datos de precios de energía:")
for record in sample_energy:
    print(record)

print("\n🔍 Muestra de datos meteorológicos:")
for record in sample_meteo:
    print(record)
