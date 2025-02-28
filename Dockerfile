FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV RABBITMQ_HOST=rabbitmq
ENV RABBITMQ_USERNAME=guest
ENV RABBITMQ_PASSWORD=guest
ENV SENSOR_TYPE=temperature
ENV TIME_SLEEP=10
CMD ["python"]
