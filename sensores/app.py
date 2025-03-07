import os
import time
import json
import random
import requests

print("[*] Iniciando sensor...", flush=True)

# Esperar a que el API Gateway esté listo
time.sleep(10)

# Variables de entorno
API_GATEWAY_URL_BASE = os.getenv("API_GATEWAY_URL", "http://api-gateway:8080")  # Base URL
EXCHANGE_FOLDER = os.getenv("EXCHANGE_FOLDER", "exchange")                      # Parte dinámica del endpoint
sensor_type = os.getenv("SENSOR_TYPE", "generic_sensor")
time_sleep = float(os.getenv("TIME_SLEEP", 30))
sensor_config_str = os.getenv("SENSOR_CONFIG", "{}")

# Construir la URL completa dinámicamente
API_GATEWAY_URL = f"{API_GATEWAY_URL_BASE}/api/{EXCHANGE_FOLDER}"

headers = {"Content-Type": "application/json"}

try:
    sensor_config_all = json.loads(sensor_config_str)
    print(f"[*] Configuración cargada: {sensor_config_all}", flush=True)
except json.JSONDecodeError as e:
    print(f"[!] Error al decodificar SENSOR_CONFIG: {e}", flush=True)
    sensor_config_all = {}

# No usamos sensor_config aquí porque queremos generar todos los atributos
if not sensor_config_all:
    print(f"[!] No se encontró configuración en SENSOR_CONFIG. Terminando...", flush=True)
    exit(1)

def generate_value(field_config):
    """Genera un valor aleatorio según el tipo y rango definido en field_config."""
    field_type = field_config.get("type")
    if field_type == "int":
        low, high = field_config.get("range", [0, 100])
        return random.randint(low, high)
    elif field_type == "float":
        low, high = field_config.get("range", [0.0, 1.0])
        return round(random.uniform(low, high), 2)
    elif field_type == "categorical":
        values = field_config.get("values", [])
        return random.choice(values) if values else None
    else:
        return None

def generate_sensor_data():
    """Genera un diccionario con los datos aleatorios del sensor."""
    data = {"sensor": sensor_type, "timestamp": time.time()}
    # Iterar sobre todos los campos definidos en sensor_config_all
    for field, config in sensor_config_all.items():
        if isinstance(config, dict):
            print(f"Procesando campo: {field} con configuración: {config}", flush=True)
            data[field] = generate_value(config)
        else:
            print(f"Error: La configuración para el campo '{field}' no es un diccionario: {config}", flush=True)
            data[field] = None
    return data

print(f"[*] Sensor '{sensor_type}' iniciado. Enviando datos cada {time_sleep} segundos a {API_GATEWAY_URL}", flush=True)

time.sleep((int(time_sleep / 5)) * 2)

try:
    while True:
        sensor_data = generate_sensor_data()
        try:
            response = requests.post(API_GATEWAY_URL, headers=headers, json=sensor_data)
            if response.status_code == 200:
                print(f"[x] Enviado: {sensor_data}. Respuesta: {response.status_code} - {response.text}", flush=True)
            else:
                print(f"[!] Error al enviar datos: {response.status_code} - {response.text}", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"[!] Error de conexión: {e}", flush=True)

        time.sleep(time_sleep)

except KeyboardInterrupt:
    print("[*] Proceso interrumpido por el usuario.", flush=True)
