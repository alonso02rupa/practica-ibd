import os
import time
import json
import random
import requests

# Esperar a que el API Gateway esté listo
time.sleep(10)

# Variables de entorno
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8080/api/sensor-data")
sensor_type = os.getenv("SENSOR_TYPE", "generic_sensor")
time_sleep = float(os.getenv("TIME_SLEEP", 30))
sensor_config_str = os.getenv("SENSOR_CONFIG", "{}")

try:
    sensor_config_all = json.loads(sensor_config_str)
except json.JSONDecodeError:
    print("Error al decodificar SENSOR_CONFIG")
    sensor_config_all = {}

# Obtener la configuración específica para el sensor actual
sensor_config = sensor_config_all.get(sensor_type, {})

if not sensor_config:
    print(f"No se encontró configuración para el sensor: {sensor_type}")
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
    for field, config in sensor_config.items():
        data[field] = generate_value(config)
    return data

# Definir los headers para la petición (incluye el tipo de sensor)
headers = {
    "Sensor-Type": sensor_type,
    "Content-Type": "application/json"
}

print(f"[*] Sensor '{sensor_type}' iniciado. Enviando datos cada {time_sleep} segundos a {API_GATEWAY_URL}")

try:
    while True:
        sensor_data = generate_sensor_data()
        try:
            response = requests.post(API_GATEWAY_URL, headers=headers, json=sensor_data)
            print(f"[x] Enviado: {sensor_data}. Respuesta: {response.status_code} - {response.text}")
        except Exception as e:
            print("Error al enviar datos:", e)
        time.sleep(time_sleep)
except KeyboardInterrupt:
    print("Sensor detenido.")
