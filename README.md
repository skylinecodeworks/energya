### **📘 Energy Price Prediction - Documentation**  
**Version:** 1.0 | **Last Updated:** 25/02/2025  

---

# **1. Executive Overview**  

## **1.1 Introduction**  
**Energy Price Prediction** is a data-driven system designed to predict electricity prices using historical energy prices and meteorological data. The system continuously ingests and processes energy market and climate data, applies an ETL pipeline, and trains a machine learning model to generate accurate price predictions.  

The project is fully **containerized with Docker**, orchestrated via **APScheduler**, and provides an API for real-time price forecasting.  

---

## **1.2 Key Features**  
✔ **Automated Data Ingestion** – Retrieves real-time and historical data from energy markets and weather APIs.  
✔ **Scalable Data Processing** – Efficient ETL pipeline using MongoDB for structured data storage.  
✔ **Machine Learning Predictions** – Uses `RandomForestRegressor` to forecast energy prices.  
✔ **REST API with FastAPI** – Provides real-time predictions and integrates with external applications.  
✔ **Fully Dockerized** – Managed via `docker-compose` for seamless deployment.  
✔ **Task Scheduler** – Uses `APScheduler` to automate data ingestion, ETL, and model training.  

---

## **1.3 System Architecture**  

```
                     +----------------------------+
                     |    Energy Price API        |
                     |  (FastAPI & ML Model)      |
                     +------------+--------------+
                                  |
                                  v
                     +----------------------------+
                     |      MongoDB Database      |
                     | Stores Energy & Weather   |
                     +------------+--------------+
                                  |
          +-----------------------+----------------------+
          |                       |                      |
          v                       v                      v
  +--------------+      +-----------------+      +--------------+
  |  Data Ingestion  |  |  ETL Processing  |  | Model Training |
  |  (Energy & Weather) |  | (Data Cleaning &  |  |  (RandomForest)  |
  +--------------+      |  Merging)         |      +--------------+
                        +-----------------+      

```

- **Energy Data:** Collected from `energy-charts.info` (historical and real-time).  
- **Weather Data:** Collected from `open-meteo.com`.  
- **Data Storage:** Stored in MongoDB for efficient processing.  
- **Machine Learning:** Uses RandomForest for training and prediction.  
- **APScheduler:** Manages periodic data extraction and model retraining.  
- **REST API:** Provides an endpoint for energy price predictions.  

---

# **2. Technical Documentation**  

## **2.1 Project Structure**  

```
.
├── docker-compose.yml          # Defines services and dependencies
├── DockerfileApi               # API container setup
├── DockerfileScheduler         # Scheduler container setup
├── main.py                     # FastAPI main entry point
├── model_validation_results.csv # Model evaluation results
├── README.md                   # Project documentation
├── requirements.txt            # Dependencies
├── scheduler.py                # APScheduler task manager
├── src/                        # Source code
│   ├── api.py                  # API for predictions
│   ├── data_ingestion.py        # Energy price data ingestion
│   ├── data_ingestion_meteo.py  # Weather data ingestion
│   ├── historical_data_ingestion.py  # Historical energy data
│   ├── historical_data_ingestion_meteo.py  # Historical weather data
│   ├── quality_tester.py        # Model evaluation
│   ├── train_model_batch.py     # Batch training script
│   ├── web_scrapper.py          # Web scraper for API data
└── test/                        # Test scripts
    └── prediction1.sh           # API test using `curl`
```

---

## **2.2 Installation & Deployment**  

### **1️⃣ Prerequisites**  
- **Docker & Docker Compose** installed.  
- `.env` file configured with API keys and database settings.  

### **2️⃣ Build the Containers**  
```bash
docker-compose build
```

### **3️⃣ Start the Services**  
```bash
docker-compose up -d
```
This will start:
- **MongoDB**
- **Scheduler (APScheduler)**
- **API (FastAPI)**

### **4️⃣ Check Running Containers**  
```bash
docker ps
```

---

## **2.3 Environment Variables**  

### **Configuration in `.env`**
```ini
# Example configuration, take a look at the actual .env file to observe the complete list of parameters

# MongoDB Database
MONGO_URI=mongodb://mongo:27017/
MONGO_DB=energy
MONGO_COLLECTION_ENERGY=energy_prices
MONGO_COLLECTION_METEO=weather_data

# Energy Data API (Energy-Charts)
COUNTRY=ro
BIDDING_ZONE=RO

# Weather API (Open-Meteo)
METEO_LATITUDE=51.1657
METEO_LONGITUDE=10.4515

# Execution Intervals
EXTRACTION_INTERVAL=43200  # Every hour
TRAINING_INTERVAL=86400    # Every 24 hours
```

---

## **2.4 Services Overview**  

### **1️⃣ Scheduler (`scheduler.py`)**  
- Runs **data ingestion**, **ETL**, and **training** periodically.
- Uses **APScheduler** to schedule tasks.

**Example Log Output:**
```
🚀 [2025-02-25 12:00:00] Running data extraction...
✅ [2025-02-25 12:00:10] Extraction completed
📊 [2025-02-25 12:00:30] Running model training...
✅ [2025-02-25 12:01:50] Training completed
```

---

### **2️⃣ API Service (`api.py`)**  
Provides **energy price predictions** based on weather conditions.

#### **Endpoint: `/predict/`**  
```http
POST /predict/
```

📌 **Example Request (`curl`):**
```bash
curl -X POST "http://localhost:8000/predict/" \
-H "Content-Type: application/json" \
-d '{
  "temperature": 5.0,
  "humidity": 80,
  "precipitation": 0.0,
  "rain": 0.0,
  "snowfall": 0.0,
  "surface_pressure": 1012.0,
  "cloud_cover": 75.0,
  "wind_speed_10m": 3.5,
  "wind_speed_100m": 10.2,
  "wind_direction_10m": 180,
  "wind_direction_100m": 200,
  "days_since_start": 3650
}'
```

📌 **Example Response:**
```json
{
  "predicted_price": 102.5,
  "unit": "EUR/MWh",
  "input_data": { ... }
}
```

📌 **Swagger UI is available at:**  
👉 `http://localhost:8000/docs`

---

## **2.5 Machine Learning Model**  

### **1️⃣ Training Script (`train_model_batch.py`)**  
- **Uses `RandomForestRegressor`**
- **Trains on batched data from MongoDB**
- **Handles missing data and scaling**

**Model Parameters:**
```python
model = RandomForestRegressor(n_estimators=150, max_depth=None, random_state=42, n_jobs=-1)
```

### **2️⃣ Model Evaluation (`quality_tester.py`)**  
Runs evaluation using **Mean Absolute Error (MAE)**.

**Example Execution:**
```bash
python src/quality_tester.py
```

**Expected Output:**
```
📊 Evaluation completed. MAE: 11.87 EUR/MWh
📂 Results saved in 'model_validation_results.csv'
```

---

## **2.6 Stopping the Services**  
To stop all containers:
```bash
docker-compose down
```

## **4. Contact**  
📧 **Support:** tom@skylinecodew.com 

