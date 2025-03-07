from flask import Flask, request, jsonify
import pika
import os
import time
import requests
import json  # Añadimos esta importación

app = Flask(__name__)

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
EXCHANGE_FOLDER = os.getenv("EXCHANGE_FOLDER", "exchange")
SERVICES_FOLDER = os.getenv("SERVICES_FOLDER", "services")

# Variables globales para la conexión
connection = None
channel = None

def connect_to_rabbitmq():
    """Establece o reestablece la conexión con RabbitMQ."""
    global connection, channel
    max_retries = 10
    retry_delay = 5  # segundos
    for attempt in range(max_retries):
        try:
            if connection is not None and not connection.is_closed:
                connection.close()
            credentials = pika.PlainCredentials('guest', 'guest')
            parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials, heartbeat=600)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange=EXCHANGE_FOLDER, exchange_type="direct")
            print("[*] Conexión a RabbitMQ establecida", flush=True)
            return True
        except Exception as e:
            print(f"[!] Intento {attempt + 1}/{max_retries} fallido al conectar con RabbitMQ: {e}", flush=True)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    print("[!] No se pudo conectar a RabbitMQ después de varios intentos", flush=True)
    return False

print("[*] Iniciando API Gateway...", flush=True)
connect_to_rabbitmq()

def ensure_queue_exists(sensor_type):
    """Declara una cola para el tipo de sensor si aún no existe."""
    global channel
    try:
        if channel is None or channel.is_closed:
            connect_to_rabbitmq()
        channel.queue_declare(queue=sensor_type, durable=True)
        channel.queue_bind(exchange=EXCHANGE_FOLDER, queue=sensor_type, routing_key=sensor_type)
        print(f"[*] Cola '{sensor_type}' asegurada", flush=True)
    except Exception as e:
        print(f"[!] Error al asegurar cola para '{sensor_type}': {e}, reconectando...", flush=True)
        connect_to_rabbitmq()
        channel.queue_declare(queue=sensor_type, durable=True)
        channel.queue_bind(exchange=EXCHANGE_FOLDER, queue=sensor_type, routing_key=sensor_type)
        print(f"[*] Cola '{sensor_type}' asegurada tras reconexión", flush=True)

def send_to_exchange(sensor_type, message):
    """Envía el mensaje a RabbitMQ asegurando que la cola existe."""
    global channel
    try:
        if channel is None or channel.is_closed or connection is None or connection.is_closed:
            connect_to_rabbitmq()
        ensure_queue_exists(sensor_type)
        # Convertimos el diccionario a JSON válido antes de enviarlo
        message_json = json.dumps(message)
        channel.basic_publish(exchange=EXCHANGE_FOLDER, routing_key=sensor_type, body=message_json.encode('utf-8'))
        print(f"[*] Mensaje enviado a RabbitMQ: {message_json}", flush=True)
    except Exception as e:
        print(f"[!] Error al enviar mensaje a RabbitMQ: {e}, reconectando...", flush=True)
        connect_to_rabbitmq()
        ensure_queue_exists(sensor_type)
        message_json = json.dumps(message)
        channel.basic_publish(exchange=EXCHANGE_FOLDER, routing_key=sensor_type, body=message_json.encode('utf-8'))
        print(f"[*] Mensaje enviado tras reconexión: {message_json}", flush=True)

@app.route(f'/api/{EXCHANGE_FOLDER}', methods=['POST'])
def receive_sensor_data():
    """Recibe datos de sensores simulados y los envía a RabbitMQ."""
    print(f"[*] Recibiendo solicitud en /api/{EXCHANGE_FOLDER}", flush=True)
    sensor_data = request.json
    print(f"[*] Datos recibidos: {sensor_data}", flush=True)

    if not sensor_data or 'sensor' not in sensor_data:
        return jsonify({'error': 'Datos del sensor o campo "sensor" faltantes'}), 400

    sensor_type = sensor_data['sensor']
    try:
        send_to_exchange(sensor_type, sensor_data)  # Pasamos el diccionario directamente
        return jsonify({'message': 'Datos enviados correctamente'}), 200
    except Exception as e:
        print(f"[!] Error al enviar datos a RabbitMQ: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route(f'/api/{SERVICES_FOLDER}', methods=['GET'])
def handle_service_request():
    print(f"[*] Recibiendo solicitud en /api/{SERVICES_FOLDER}", flush=True)
    service_name = request.headers.get('Service-Name')

    if not service_name:
        return jsonify({'error': "Encabezado 'Service-Name' requerido"}), 400

    try:
        # Apuntar al nombre del servicio correcto y al puerto 5000 con el endpoint /api
        response = requests.post(f"http://{service_name}:5000/api")
        print(f"[*] Respuesta recibida de {service_name}: {response.json()}", flush=True)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"[!] Error al conectar con el servicio '{service_name}': {str(e)}", flush=True)
        return jsonify({'error': f"Error al conectar con el servicio '{service_name}': {str(e)}"}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
