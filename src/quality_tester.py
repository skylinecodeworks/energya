import joblib
import numpy as np
import pandas as pd
from pymongo import MongoClient
from sklearn.metrics import mean_absolute_error

# Conectar a MongoDB
MONGO_URI = "mongodb://mongo:27017/"
MONGO_DB = "energy_db"  # Reemplázalo con el nombre real de tu BD
MONGO_COLLECTION_ENERGY = "energy_prices"
MONGO_COLLECTION_METEO = "weather_data"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection_energy = db[MONGO_COLLECTION_ENERGY]
collection_meteo = db[MONGO_COLLECTION_METEO]

# Cargar el modelo entrenado
MODEL_PATH = "models/energy_price_model.pkl"
model, scaler = joblib.load(MODEL_PATH)

# Número de registros a evaluar
SAMPLE_SIZE = 500

# Obtener datos históricos de MongoDB
energy_data = list(collection_energy.find({}, {"_id": 0, "timestamp": 1, "price": 1}).limit(SAMPLE_SIZE))
meteo_data = list(collection_meteo.find({}, {"_id": 0, "timestamp": 1, "temperature": 1, "humidity": 1,
                                              "precipitation": 1, "rain": 1, "snowfall": 1, "surface_pressure": 1,
                                              "cloud_cover": 1, "wind_speed_10m": 1, "wind_speed_100m": 1,
                                              "wind_direction_10m": 1, "wind_direction_100m": 1}).limit(SAMPLE_SIZE))

# Convertir a DataFrame
df_energy = pd.DataFrame(energy_data)
df_meteo = pd.DataFrame(meteo_data)

# Asegurar que los timestamps sean datetime para la fusión
df_energy["timestamp"] = pd.to_datetime(df_energy["timestamp"])
df_meteo["timestamp"] = pd.to_datetime(df_meteo["timestamp"])

# Fusionar datos de precios y meteorológicos por timestamp
df_merged = pd.merge(df_energy, df_meteo, on="timestamp", how="inner")

# Asegurar que haya datos después de la fusión
if df_merged.empty:
    print("⚠️ No hay datos disponibles después de la fusión. Abortando.")
    exit()

# Calcular "days_since_start" usando el mismo método que en el entrenamiento
df_merged["days_since_start"] = (df_merged["timestamp"] - df_merged["timestamp"].min()).dt.days

# Separar X (variables predictoras) e y (precio real)
X = df_merged.drop(columns=["timestamp", "price"])
y_real = df_merged["price"]

# Asegurar que las características coincidan con el entrenamiento
expected_features = scaler.n_features_in_
if X.shape[1] != expected_features:
    raise ValueError(f"El modelo espera {expected_features} características, pero se encontraron {X.shape[1]}.")

# Normalizar X usando el mismo scaler del entrenamiento
X_scaled = scaler.transform(X)

# Realizar predicciones
y_pred = model.predict(X_scaled)

# Calcular el error absoluto medio (MAE)
mae = mean_absolute_error(y_real, y_pred)

# Mostrar los resultados
result_df = pd.DataFrame({
    "timestamp": df_merged["timestamp"],
    "price_real": y_real,
    "price_predicho": y_pred,
    "error": abs(y_real - y_pred)
})

# Guardar los resultados en un archivo CSV
result_df.to_csv("model_validation_results.csv", index=False)

print(f"📊 Evaluación completada. Error absoluto medio (MAE): {mae:.2f} EUR/MWh")
print("📂 Resultados guardados en 'model_validation_results.csv'")
