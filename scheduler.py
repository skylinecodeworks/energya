import sys
import os
import time
import datetime
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

sys.stdout.reconfigure(line_buffering=True)  # 🚀 Forzar salida inmediata de logs


# Configuración de tiempos de ejecución desde variables de entorno
EXTRACTION_INTERVAL = int(os.getenv("EXTRACTION_INTERVAL", 3600))  # 1 hora por defecto
TRAINING_INTERVAL = int(os.getenv("TRAINING_INTERVAL", 86400))  # 24 horas por defecto

scheduler = BackgroundScheduler()


def run_extraction():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚀 [{now}] Ejecutando extracción de datos...")
    try:
        subprocess.run(["python", "src/data_ingestion.py"], check=True)
        subprocess.run(["python", "src/data_ingestion_meteo.py"], check=True)
        print(f"✅ [{now}] Extracción completada con éxito")
    except subprocess.CalledProcessError as e:
        print(f"❌ [{now}] Error en extracción: {e}")


def run_training():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"📊 [{now}] Ejecutando entrenamiento del modelo...")
    try:
        subprocess.run(["python", "src/train_model_batch.py"], check=True)
        print(f"✅ [{now}] Entrenamiento completado con éxito")
    except subprocess.CalledProcessError as e:
        print(f"❌ [{now}] Error en entrenamiento: {e}")


# Programar las tareas con margen de gracia para evitar saltos
scheduler.add_job(run_extraction, IntervalTrigger(seconds=EXTRACTION_INTERVAL),
                  id="extraction", replace_existing=True, misfire_grace_time=60)
scheduler.add_job(run_training, IntervalTrigger(seconds=TRAINING_INTERVAL),
                  id="training", replace_existing=True, misfire_grace_time=60)

if __name__ == "__main__":
    print("\n🎯 Iniciando Scheduler con APScheduler")
    print("🕒 Tareas programadas:")
    print(f"   - Extracción cada {EXTRACTION_INTERVAL} segundos")
    print(f"   - Entrenamiento cada {TRAINING_INTERVAL} segundos")
    print("========================================\n")

    scheduler.start()
    time.sleep(2)  # Pequeña pausa para asegurarnos de que las tareas se programan

    # Verificar que las tareas están programadas correctamente
    job_extraction = scheduler.get_job("extraction")
    job_training = scheduler.get_job("training")

    if not job_extraction or not job_training:
        print("❌ Error: No se programaron correctamente las tareas en el scheduler.")
        exit(1)

    print(f"✅ Próxima ejecución de extracción: {job_extraction.next_run_time}")
    print(f"✅ Próxima ejecución de entrenamiento: {job_training.next_run_time}\n")

    try:
        while True:
            now = datetime.datetime.now(datetime.timezone.utc)  # Tiempo actual en UTC

            next_run_extraction = job_extraction.next_run_time
            next_run_training = job_training.next_run_time

            remaining_extraction = (next_run_extraction - now).total_seconds() if next_run_extraction else "N/A"
            remaining_training = (next_run_training - now).total_seconds() if next_run_training else "N/A"

            print(f"⏳ Próxima extracción en {int(remaining_extraction)}s | Próximo entrenamiento en {int(remaining_training)}s")

            time.sleep(60)  # Muestra información cada minuto

    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Deteniendo el scheduler...")
        scheduler.shutdown()
