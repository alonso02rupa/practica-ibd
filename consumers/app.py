import pika
import os
import csv
import json
import signal
import threading
from flask import Flask, jsonify, request

# Configuración del servicio
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
EXCHANGE_FOLDER = os.getenv("EXCHANGE_FOLDER", "exchange")
SENSOR_NAME = os.getenv("SENSOR_NAME")

if not SENSOR_NAME:
    raise ValueError("Debe definir la variable de entorno SENSOR_NAME.")

CSV_DIR = f"sensor_data/{SENSOR_NAME}"
CSV_FILE = os.path.join(CSV_DIR, f"{SENSOR_NAME}.csv")
os.makedirs(CSV_DIR, exist_ok=True)

# Flask App para exponer los datos
app = Flask(__name__)

@app.route(f'/api/{SENSOR_NAME}', methods=['GET'])
def get_sensor_data():
    """Devuelve los datos del sensor almacenados en el CSV."""
    if not os.path.exists(CSV_FILE):
        return jsonify({'error': f"Archivo CSV para el sensor '{SENSOR_NAME}' no encontrado"}), 404

    try:
        with open(CSV_FILE, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': f"Error al leer el archivo CSV: {str(e)}"}), 500

# Conectar a RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
channel = connection.channel()

channel.exchange_declare(exchange=EXCHANGE_FOLDER, exchange_type="direct")
channel.queue_declare(queue=SENSOR_NAME, durable=True)
channel.queue_bind(exchange=EXCHANGE_FOLDER, queue=SENSOR_NAME, routing_key=SENSOR_NAME)

def callback(ch, method, properties, body):
    """Procesa mensajes y los guarda en un CSV."""
    try:
        print(f"[{SENSOR_NAME}] Mensaje recibido desde RabbitMQ", flush=True)
        data = json.loads(body.decode('utf-8'))
        write_header = not os.path.exists(CSV_FILE)

        with open(CSV_FILE, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(data)
            print(f"[{SENSOR_NAME}] Datos escritos en {CSV_FILE}: {data}", flush=True)
    except json.JSONDecodeError as e:
        print(f"[{SENSOR_NAME}] Error al decodificar el mensaje JSON: {e} - Mensaje crudo: {body.decode('utf-8')}", flush=True)
    except Exception as e:
        print(f"[{SENSOR_NAME}] Error al procesar el mensaje: {e}", flush=True)

# Configurar el consumidor RabbitMQ
channel.basic_consume(queue=SENSOR_NAME, on_message_callback=callback, auto_ack=True)

# Manejar señales de terminación
def stop_rabbitmq(signalnum, frame):
    print(f"[{SENSOR_NAME}] Cerrando conexión RabbitMQ...", flush=True)
    channel.stop_consuming()
    connection.close()
    exit(0)

signal.signal(signal.SIGINT, stop_rabbitmq)
signal.signal(signal.SIGTERM, stop_rabbitmq)

def start_rabbitmq_consumer():
    """Ejecuta el consumidor RabbitMQ en un hilo separado."""
    print(f"[{SENSOR_NAME}] Iniciando consumidor RabbitMQ...", flush=True)
    channel.start_consuming()

if __name__ == "__main__":
    print(f"[{SENSOR_NAME}] Servicio iniciado. Esperando mensajes y sirviendo API...", flush=True)
    # Iniciar el consumidor RabbitMQ en un hilo separado
    consumer_thread = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
    consumer_thread.start()
    # Iniciar Flask en el hilo principal
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
