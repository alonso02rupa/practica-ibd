FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
COPY app.py .
RUN pip install --no-cache-dir -r requirements.txt
ENV RABBITMQ_HOST=rabbitmq \
    EXCHANGE_FOLDER=exchange \
    SENSOR_NAME=default_sensor
EXPOSE 5000
CMD ["python", "app.py"]
