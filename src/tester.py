import joblib
import numpy as np

# Cargar el modelo entrenado
model, scaler = joblib.load("models/energy_price_model.pkl")

# Crear un dato de prueba (valores dentro de un rango esperado)
new_data = np.array([[5.0, 80, 0, 0, 0, 1012, 75, 3.5, 10.2, 180, 200]])

# Normalizar los datos con el mismo escalador del entrenamiento
new_data_scaled = scaler.transform(new_data)

# Hacer la predicción
predicted_price = model.predict(new_data_scaled)

print(f"📊 Predicción del precio de la energía: {predicted_price[0]:.2f} EUR/MWh")
