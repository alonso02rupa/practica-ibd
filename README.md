# 🛠️ Plataforma de Recolección de Datos de Sensores IoT

## 🔖 Repositorio de la Práctica IBD

Repositorio para la práctica de Infraestructura de Bases de Datos.

Práctica realizada con participación a partes iguales por:
- **Marcos Erans Batista**
- **Juan Moreno Segura**
- **Alonso Ruiz Palomo**

---

## 📚 Introducción

Este proyecto implementa una plataforma escalable y robusta para la recolección de datos de sensores IoT en un edificio inteligente. La plataforma maneja datos provenientes de diferentes tipos de sensores:

- 🌡️ **Temperatura / Humedad**
- 🛏️ **Ocupación**
- 💪 **Consumo de Energía**
- 👁️ **Cámaras de Seguridad**

Cada tipo de sensor está containerizado usando **Docker**, asegurando aislamiento y facilidad de despliegue. El sistema utiliza una cola de mensajes (**RabbitMQ**) para gestionar el flujo de datos, con una **API REST** (desarrollada con **Flask**) actuando como punto de entrada para los datos de los sensores. Los consumidores procesan los datos desde las colas y los almacenan en archivos **CSV** para garantizar persistencia.

Esta arquitectura asegura un manejo eficiente de diferentes tipos de datos, frecuencias y volúmenes, manteniendo **escalabilidad** y **tolerancia a fallos**.

---

## 🛠️ Tecnologías Utilizadas

- **Docker**: Para la containerización de sensores, API gateway y consumidores.
- **Python**: Para la simulación de sensores, la API gateway y el procesamiento de datos.
- **RabbitMQ**: Para la gestión de colas de mensajes y enrutamiento.
- **Flask**: Para construir la API REST.
- **CSV**: Para el almacenamiento persistente de datos.

---

## 🏢 Arquitectura del Sistema

### 🛠️ Sensores

- Cada tipo de sensor se implementa como un **contenedor Docker independiente**.
- Generan datos a tasas configurables y los envían a la API Gateway mediante **solicitudes HTTP POST**.
- Se usa una **única imagen Docker** para todos los sensores, controlando su comportamiento mediante **variables de entorno**.

### 🌐 API Gateway

- Una API REST basada en **Flask** que recibe los datos de los sensores.
- Verifica el tipo de sensor a partir de las cabeceras de las solicitudes y **publica los datos en RabbitMQ**.
- Proporciona endpoints para recuperar todas las mediciones de cada tipo de sensor.

### 🛏️ Cola de Mensajes (**RabbitMQ**)

- El **exchange** enruta los mensajes a colas específicas según el tipo de sensor (ejemplo: `temperature_queue`, `occupancy_queue`, etc.).
- Las colas se crean **dinámicamente** si no existen previamente.

### 💡 Consumidores

- Múltiples contenedores de consumidores se suscriben a cada cola específica de sensor.
- Procesan los mensajes y añaden los datos a archivos **CSV segregados**, almacenados en un volumen Docker compartido.

---

## 🛠️ Instalación y Configuración

### 🔗 Prerrequisitos

Asegúrate de tener instaladas las siguientes herramientas:

- **Docker** ➔ [Instalar Docker](https://www.docker.com/get-started)
- **Git** ➔ [Instalar Git](https://git-scm.com/downloads)

### 📂 Clonar el Repositorio

```bash
git clone https://github.com/alonso02rupa/practica-ibd.git
cd practica-ibd
```

### 🌐 Configurar y Ejecutar los Contenedores

El proyecto usa **Docker Compose** para gestionar múltiples contenedores.

#### ♻️ Crear la red externa

```bash
docker network create sensor_network
```

#### ⚙️ Lanzar la infraestructura base

```bash
docker-compose up --build
```

#### 🔄 Lanzar los sensores

```bash
docker-compose -f docker-compose-sensors.yml up --build \
  --scale sensor_temperature=4 \
  --scale sensor_power=7 \
  --scale sensor_camera=3 \
  --scale sensor_occupancy=6
```

#### 📊 Solicitar datos con GET

```bash
curl -X GET "http://localhost:8080/api/services" -H "Service-Name: consumer_temperature"
```

> **Nota:** La API se ejecuta en el **puerto 5000** por defecto. Asegúrate de que este puerto esté accesible en tu máquina.

---

## 📚 Persistencia de Datos

- Los datos de los sensores se almacenan en **archivos CSV** dentro de un volumen Docker compartido (`sensor_data_volume`).
- Cada tipo de sensor tiene su propio archivo CSV (`temperature.csv`, `occupancy.csv`, etc.).
- Puedes acceder a los archivos CSV montando el volumen en tu máquina local o ejecutando comandos dentro de los contenedores de consumidores.

---

## 🚀 Despliegue y Escalabilidad

- Toda la infraestructura está virtualizada con **Docker**.
- Los contenedores se descargan automáticamente desde **Docker Hub** durante la ejecución.
- Gracias a la arquitectura desacoplada, el sistema maneja tasas y volúmenes de datos variables, asegurando persistencia incluso si los contenedores se reinician.

---


🎉 **¡Gracias por visitar nuestro repositorio!** 🎉

