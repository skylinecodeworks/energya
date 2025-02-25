import os
import joblib
import pandas as pd
import numpy as np
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Cargar configuración desde .env
load_dotenv()

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION_ENERGY = os.getenv("MONGO_COLLECTION")  # Datos de energía
MONGO_COLLECTION_METEO = os.getenv("MONGO_COLLECTION_METEO")  # Datos meteorológicos
MODEL_PATH = "models/energy_price_model.pkl"
BATCH_SIZE = 50000  # Tamaño del lote

# Conectar a MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection_energy = db[MONGO_COLLECTION_ENERGY]
collection_meteo = db[MONGO_COLLECTION_METEO]

def fetch_data_in_batches():
    """Generador que obtiene datos de MongoDB en lotes."""
    total_records = collection_energy.count_documents({})
    print(f"🔄 Total de registros en MongoDB: {total_records}")

    for i in range(0, total_records, BATCH_SIZE):
        print(f"🔄 Obteniendo lote {i // BATCH_SIZE + 1}...")

        energy_batch = list(collection_energy.find({}, {"_id": 0, "timestamp": 1, "price": 1})
                            .skip(i).limit(BATCH_SIZE))

        meteo_batch = list(collection_meteo.find({}, {"_id": 0, "timestamp": 1, "temperature": 1, "humidity": 1,
                                                      "precipitation": 1, "rain": 1, "snowfall": 1,
                                                      "surface_pressure": 1, "cloud_cover": 1,
                                                      "wind_speed_10m": 1, "wind_speed_100m": 1,
                                                      "wind_direction_10m": 1, "wind_direction_100m": 1})
                           .skip(i).limit(BATCH_SIZE))

        if not energy_batch or not meteo_batch:
            print("⚠️ No se encontraron más datos en este lote.")
            break  # Salir si no hay más datos

        print(f"✅ Procesando lote con {len(energy_batch)} registros de energía y {len(meteo_batch)} de clima.")

        df_energy = pd.DataFrame(energy_batch)
        df_meteo = pd.DataFrame(meteo_batch)

        df_energy["timestamp"] = pd.to_datetime(df_energy["timestamp"])
        df_meteo["timestamp"] = pd.to_datetime(df_meteo["timestamp"])

        df_merged = pd.merge(df_energy, df_meteo, on="timestamp", how="inner")

        df_merged.dropna(subset=["price"], inplace=True)

        print(f"🔄 Registros después de la fusión: {len(df_merged)}")

        yield df_merged  # Retorna el lote procesado

def train_model():
    """Entrena un modelo con pesos temporales para dar más importancia a los datos recientes."""
    model = RandomForestRegressor(n_estimators=150, max_depth=None, random_state=42, n_jobs=-1)
    scaler = StandardScaler()  # Normalización de datos

    X_total = []
    y_total = []
    time_weights = []

    batch_count = 0  # Contador de lotes

    for df_batch in fetch_data_in_batches():
        batch_count += 1

        # Agregar la variable de tiempo "days_since_start"
        df_batch["days_since_start"] = (df_batch["timestamp"] - df_batch["timestamp"].min()).dt.days

        # Seleccionar todas las características, incluyendo days_since_start
        X = df_batch.drop(columns=["timestamp", "price"])
        y = df_batch["price"]

        if X.isnull().values.any() or y.isnull().values.any():
            print("⚠️ Datos con NaN detectados, eliminando filas con valores faltantes.")
            df_batch.dropna(inplace=True)
            X = df_batch.drop(columns=["timestamp", "price"])
            y = df_batch["price"]

        if X.empty or y.empty:
            print("⚠️ Se detectó un lote vacío después de limpiar NaNs, saltando...")
            continue

        # Acumular datos para el entrenamiento
        X_total.append(X)
        y_total.append(y)
        time_weights.append(df_batch["days_since_start"].to_numpy())

    if batch_count == 0:
        print("⚠️ No se entrenó el modelo porque no se procesaron lotes.")
        return

    # Concatenar todos los datos antes de entrenar el modelo
    X_train = np.vstack([df.to_numpy() for df in X_total])
    y_train = np.hstack([df.to_numpy() for df in y_total])
    time_weights_train = np.hstack(time_weights)  # Unir los pesos temporales

    print(f"🔄 Entrenando modelo final con {len(X_train)} registros...")
    X_train_scaled = scaler.fit_transform(X_train)  # Normalizar datos

    # Entrenar RandomForest con `sample_weight`
    model.fit(X_train_scaled, y_train, sample_weight=time_weights_train)

    # Guardar el modelo entrenado
    os.makedirs("models", exist_ok=True)
    joblib.dump((model, scaler), MODEL_PATH)
    print(f"✅ Modelo entrenado y guardado en {MODEL_PATH} con {batch_count} lotes.")

if __name__ == "__main__":
    print("🚀 Entrenando modelo por lotes con pesos temporales...")
    train_model()
    print("🏁 Entrenamiento finalizado con todos los datos.")
