# Energy Price Prediction

## INFORMACION PREVIA:

La separación entre **país** y **bidding zone** en la industria de la energía se debe a la forma en que funcionan los mercados eléctricos en Europa y en otras regiones del mundo. Aquí te explico las razones principales:

---

### **1. Los mercados eléctricos no siempre siguen las fronteras nacionales**
Los mercados de energía en Europa están organizados en **bidding zones** (zonas de oferta) que no necesariamente coinciden con los límites geográficos de los países. 

- Algunos países tienen **varias bidding zones** debido a limitaciones en su red de transmisión eléctrica.  
  - Ejemplo: **Italia** tiene varias zonas de oferta (`IT-North`, `IT-South`, `IT-Sicily`, etc.).
- Otros países **comparten una misma bidding zone** con países vecinos.  
  - Ejemplo: **Alemania y Luxemburgo** están en la misma zona de oferta `DE-LU`.

---

### **2. ¿Qué es una Bidding Zone?**
Una **bidding zone** es un área dentro de un mercado eléctrico donde los precios de la electricidad son homogéneos porque no hay restricciones internas significativas en la red de transmisión.  

- **Si un país tiene suficiente capacidad de transmisión interna**, todo el país puede ser una única bidding zone (ej. España `ES`).  
- **Si un país tiene cuellos de botella o congestión en la red de transmisión**, se divide en múltiples zonas de oferta para reflejar las diferencias en precios y oferta/demanda (ej. Italia).  
- **Si dos países tienen redes eléctricas bien integradas**, pueden compartir la misma zona de oferta (ej. Alemania y Luxemburgo).

---

### **3. Impacto en la Fijación de Precios**
Los precios de la electricidad dentro de una misma **bidding zone** son generalmente los mismos, mientras que diferentes zonas pueden tener precios distintos debido a factores como:

- **Capacidad de transmisión**: Si una región genera más energía renovable pero no puede enviarla a otra región con alta demanda, los precios bajarán en la primera y subirán en la segunda.
- **Demanda y oferta local**: Algunas zonas tienen más generación de energía eólica, solar o nuclear que otras.
- **Interconexiones con otros mercados**: Una zona con muchas conexiones internacionales puede tener precios más estables.

---

### **Ejemplo Práctico**
Supongamos que quieres analizar los precios de la electricidad en Alemania (`de`):

- Si consultas por **país (`COUNTRY=de`)**, podrías estar incluyendo datos generales que no reflejan la variabilidad regional.
- Si consultas por **bidding zone (`BIDDING_ZONE=DE-LU`)**, estarás obteniendo datos más específicos del mercado real en el que opera Alemania junto con Luxemburgo.

Lo mismo aplica para otros países con múltiples bidding zones, como Italia, Suecia y Noruega.

---

### **Conclusión**
El **país (`COUNTRY`)** en la API puede representar una agregación de datos de todo el país, mientras que la **bidding zone (`BIDDING_ZONE`)** refleja mejor los precios reales dentro del mercado eléctrico. **Es importante usar `BIDDING_ZONE` si se quiere hacer predicciones precisas de precios de energía.**

---

Si tienes más dudas sobre esto, dime y lo analizamos más a fondo antes de seguir con el desarrollo. 🚀

## EJECUCION DE LA PLATAFORMA:

## **Paso 1: Crear el Script de Descarga Diaria**
Vamos a estructurar el script `src/daily_update.py`, que se encargará de:

1. **Ejecutar la ingesta de datos** (`data_ingestion.py`).
2. **Re-entrenar el modelo** (`model_training.py`).
3. **Registrar logs de cada ejecución**.

### **1.1 Crear `src/daily_update.py`**
Edita o crea el archivo `src/daily_update.py` con el siguiente contenido:

```python
import subprocess
import datetime

LOG_FILE = "logs/daily_update.log"

def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{timestamp} - {message}\n")
    print(message)

def run_ingestion():
    log_message("Iniciando ingesta de datos...")
    result = subprocess.run(["python", "src/data_ingestion.py"], capture_output=True, text=True)
    log_message(result.stdout if result.stdout else "Error en la ingesta")

def run_training():
    log_message("Iniciando re-entrenamiento del modelo...")
    result = subprocess.run(["python", "src/model_training.py"], capture_output=True, text=True)
    log_message(result.stdout if result.stdout else "Error en el entrenamiento")

if __name__ == "__main__":
    log_message("=== Inicio del proceso diario ===")
    run_ingestion()
    run_training()
    log_message("=== Fin del proceso diario ===")
```

---

## **Paso 2: Programar la Ejecución Automática**
Tienes dos opciones: **cronjob (local, simple)** o **Celery + Redis (escalable, en producción)**.

### **Opción 1: Usar Cronjob en Linux**
Para ejecutar el script todos los días a las 03:00 AM, sigue estos pasos:

1. Abre el editor de cron:
   ```bash
   crontab -e
   ```

2. Agrega esta línea al final del archivo:
   ```bash
   0 3 * * * /usr/bin/python3 /ruta/del/proyecto/src/daily_update.py >> /ruta/del/proyecto/logs/cron.log 2>&1
   ```

   - `0 3 * * *` → Ejecutar a las 03:00 AM todos los días.
   - `/usr/bin/python3` → Ruta de Python (confirma con `which python3`).
   - `>> logs/cron.log 2>&1` → Guarda la salida en un archivo de log.

3. Guarda y cierra el archivo. Para verificar los cronjobs activos:
   ```bash
   crontab -l
   ```

---

### **Opción 2: Usar Celery + Redis (Para Producción)**
Si planeas ejecutar tareas en la nube con mayor control y escalabilidad, usa **Celery**.

1. **Instalar Celery y Redis**
   ```bash
   pip install celery redis
   ```

2. **Levantar un contenedor Redis con Docker**
   ```bash
   docker run -d --name redis -p 6379:6379 redis
   ```

3. **Crear `src/tasks.py` para definir las tareas**
   ```python
   from celery import Celery
   import subprocess

   app = Celery("tasks", broker="redis://localhost:6379/0")

   @app.task
   def run_ingestion():
       subprocess.run(["python", "src/data_ingestion.py"])

   @app.task
   def run_training():
       subprocess.run(["python", "src/model_training.py"])
   ```

4. **Ejecutar el worker de Celery**
   ```bash
   celery -A src.tasks worker --loglevel=info
   ```

5. **Ejecutar tareas automáticamente cada día**
   En `src/celery_schedule.py`:
   ```python
   from celery.schedules import crontab
   from src.tasks import app, run_ingestion, run_training

   app.conf.beat_schedule = {
       "daily-ingestion": {
           "task": "src.tasks.run_ingestion",
           "schedule": crontab(hour=3, minute=0),
       },
       "daily-training": {
           "task": "src.tasks.run_training",
           "schedule": crontab(hour=4, minute=0),
       },
   }
   ```

6. **Ejecutar Celery Beat (scheduler)**
   ```bash
   celery -A src.tasks beat --loglevel=info
   ```

