FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia el código fuente del API Gateway
COPY app.py .

# Variables de entorno necesarias
ENV RABBITMQ_HOST=rabbitmq

# Expone el puerto que utiliza la API (por defecto 8080)
EXPOSE 8080

# Inicia la aplicación
CMD ["python", "app.py"]

