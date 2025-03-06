from flask import Flask, request, jsonify
import pika
import os
import importlib
import time

app = Flask(__name__)

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
EXCHANGE_NAME = "sensor_exchange"

# Variables globales
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
            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct", durable=True)
            print("[*] Conexión a RabbitMQ establecida", flush=True)
            return True
        except Exception as e:
            print(f"[!] Intento {attempt + 1}/{max_retries} fallido al conectar con RabbitMQ: {e}", flush=True)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    print("[!] No se pudo conectar a RabbitMQ después de varios intentos", flush=True)
    return False

# Conectar al iniciar
print("[*] Iniciando API Gateway...", flush=True)
connect_to_rabbitmq()

def ensure_queue_exists(sensor_type):
    """Declara una cola para el tipo de sensor si aún no existe."""
    global channel
    try:
        if channel is None or channel.is_closed:
            connect_to_rabbitmq()
        channel.queue_declare(queue=sensor_type, durable=True)
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=sensor_type, routing_key=sensor_type)
        print(f"[*] Cola '{sensor_type}' asegurada", flush=True)
    except Exception as e:
        print(f"[!] Error al asegurar cola para '{sensor_type}': {e}, reconectando...", flush=True)
        connect_to_rabbitmq()
        channel.queue_declare(queue=sensor_type, durable=True)
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=sensor_type, routing_key=sensor_type)
        print(f"[*] Cola '{sensor_type}' asegurada tras reconexión", flush=True)

def send_to_exchange(sensor_type, message):
    """Envía el mensaje a RabbitMQ asegurando que la cola existe."""
    global channel
    try:
        if channel is None or channel.is_closed or connection is None or connection.is_closed:
            connect_to_rabbitmq()
        ensure_queue_exists(sensor_type)
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=sensor_type, body=message.encode('utf-8'))
        print(f"[*] Mensaje enviado a RabbitMQ: {message}", flush=True)
    except Exception as e:
        print(f"[!] Error al enviar mensaje a RabbitMQ: {e}, reconectando...", flush=True)
        connect_to_rabbitmq()
        ensure_queue_exists(sensor_type)
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=sensor_type, body=message.encode('utf-8'))
        print(f"[*] Mensaje enviado tras reconexión: {message}", flush=True)

@app.route('/api/exchange', methods=['POST'])
def receive_sensor_data():
    """Recibe datos de sensores simulados y los envía a RabbitMQ."""
    print("[*] Recibiendo solicitud en /api/exchange", flush=True)
    sensor_type = request.headers.get('Sensor-Type')
    sensor_data = request.json
    print(f"[*] Datos recibidos: {sensor_data}", flush=True)

    if not sensor_type:
        return jsonify({'error': "Encabezado 'Sensor-Type' requerido"}), 400
    if not sensor_data:
        return jsonify({'error': 'Datos del sensor faltantes'}), 400

    try:
        send_to_exchange(sensor_type, str(sensor_data))
        return jsonify({'message': 'Datos enviados correctamente'}), 200
    except Exception as e:
        print(f"[!] Error al enviar datos a RabbitMQ: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor-data', methods=['GET', 'POST'])
def handle_sensor_data():
    """Maneja solicitudes GET y POST para datos de sensores."""
    print("[*] Recibiendo solicitud en /api/sensor-data", flush=True)
    if request.method == 'POST':
        sensor_data = request.json
        print(f"[*] Datos recibidos: {sensor_data}", flush=True)
        if not sensor_data or 'sensor' not in sensor_data:
            return jsonify({'error': 'Datos del sensor o campo "sensor" faltantes'}), 400
        
        sensor_type = sensor_data['sensor']
        try:
            send_to_exchange(sensor_type, str(sensor_data))
            return jsonify({'message': 'Datos enviados correctamente'}), 200
        except Exception as e:
            print(f"[!] Error al enviar datos a RabbitMQ: {e}", flush=True)
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'GET':
        service_name = request.headers.get('Service-Name')
        if not service_name:
            return jsonify({'error': "Encabezado 'Service-Name' requerido"}), 400
        
        try:
            service_module = importlib.import_module(f"sensor-data.{service_name}")
            return service_module.handle_request(request)
        except ModuleNotFoundError:
            return jsonify({'error': f"Servicio '{service_name}' no encontrado"}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
