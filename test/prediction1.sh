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

