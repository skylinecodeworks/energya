from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import logging
from fastapi.middleware.cors import CORSMiddleware

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Cargar modelo entrenado
MODEL_PATH = "models/energy_price_model.pkl"
try:
    model, scaler = joblib.load(MODEL_PATH)
    logger.info("Modelo cargado exitosamente.")
except Exception as e:
    logger.error(f"Error al cargar el modelo: {e}")
    raise RuntimeError("No se pudo cargar el modelo. Asegúrate de que el archivo existe y es válido.")

# Inicializar FastAPI
app = FastAPI(title="Energy Price Prediction API", description="API para predecir el precio de la energía basado en datos climáticos.", version="1.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir acceso desde cualquier dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo de datos de entrada
class EnergyPredictionRequest(BaseModel):
    temperature: float
    humidity: float
    precipitation: float
    rain: float
    snowfall: float
    surface_pressure: float
    cloud_cover: float
    wind_speed_10m: float
    wind_speed_100m: float
    wind_direction_10m: float
    wind_direction_100m: float
    days_since_start: int  # Representa la distancia en días desde el inicio del dataset

@app.post("/predict/", summary="Realizar predicción de precios de energía", response_model=dict)
def predict(data: EnergyPredictionRequest):
    """ Recibe datos climáticos y predice el precio de la energía en EUR/MWh. """
    try:
        # Convertir entrada en array de numpy
        features = np.array([
            [
                data.temperature, data.humidity, data.precipitation, data.rain, data.snowfall,
                data.surface_pressure, data.cloud_cover, data.wind_speed_10m, data.wind_speed_100m,
                data.wind_direction_10m, data.wind_direction_100m, data.days_since_start
            ]
        ])

        # Normalizar los datos de entrada
        features_scaled = scaler.transform(features)

        # Realizar predicción
        prediction = model.predict(features_scaled)

        # Responder con el resultado
        response = {
            "predicted_price": round(float(prediction[0]), 2),
            "unit": "EUR/MWh",
            "input_data": data.dict()
        }
        logger.info(f"Predicción realizada: {response}")
        return response
    except Exception as e:
        logger.error(f"Error en la predicción: {e}")
        raise HTTPException(status_code=500, detail=f"Error al realizar la predicción: {e}")

@app.get("/healthcheck/", summary="Verificar el estado del servicio", response_model=dict)
def healthcheck():
    """ Verifica si la API está funcionando correctamente. """
    return {"status": "ok", "message": "API en funcionamiento."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
