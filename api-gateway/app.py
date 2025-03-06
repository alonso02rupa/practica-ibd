from flask import Flask, request, jsonify
import pika
import os
import importlib

app = Flask(__name__)

# Configuración de RabbitMQ
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
EXCHANGE_NAME = "sensor_exchange"

# Conexión persistente a RabbitMQ para mejorar rendimiento
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()

# Declarar el exchange como "direct"
channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct")

def ensure_queue_exists(sensor_type):
    """Declara una cola para el tipo de sensor si aún no existe."""
    channel.queue_declare(queue=sensor_type, durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=sensor_type, routing_key=sensor_type)

def send_to_exchange(sensor_type, message):
    """Envía el mensaje a RabbitMQ asegurando que la cola existe."""
    ensure_queue_exists(sensor_type)
    channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=sensor_type, body=message)

@app.route('/api/exchange', methods=['POST'])
def receive_sensor_data():
    """Recibe datos de sensores simulados y los envía a RabbitMQ."""
    sensor_type = request.headers.get('Sensor-Type')
    sensor_data = request.json

    if not sensor_type:
        return jsonify({'error': "Encabezado 'Sensor-Type' requerido"}), 400

    if not sensor_data:
        return jsonify({'error': 'Datos del sensor faltantes'}), 400

    try:
        send_to_exchange(sensor_type, str(sensor_data))
        return jsonify({'message': 'Datos enviados correctamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor-data', methods=['GET'])
def handle_service_request():
    """Redirige la petición GET a un microservicio basado en el encabezado."""
    service_name = request.headers.get('Service-Name')

    if not service_name:
        return jsonify({'error': "Encabezado 'Service-Name' requerido"}), 400

    try:
        # Importar dinámicamente el módulo del servicio
        service_module = importlib.import_module(f"sensor-data.{service_name}")
        
        # Ejecutar la función `handle_request` del servicio
        return service_module.handle_request(request)
    
    except ModuleNotFoundError:
        return jsonify({'error': f"Servicio '{service_name}' no encontrado"}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
