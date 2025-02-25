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
