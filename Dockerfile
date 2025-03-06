FROM python:3.9-slim

WORKDIR /app

# Copiar el archivo de requerimientos e instalar las dependencias
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar el código de la aplicación
COPY app.py .

# Variables de entorno por defecto (se pueden sobrescribir desde docker-compose o al ejecutar el contenedor)
ENV API_GATEWAY_URL=http://api-gateway:8080/api/sensor-data
ENV SENSOR_TYPE=generic_sensor
ENV TIME_SLEEP=30
ENV SENSOR_CONFIG=""

CMD ["python","app.py"]
