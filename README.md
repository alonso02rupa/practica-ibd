# practica-ibd
Repositorio para la práctica IBD
Práctica realizada con participación a partes iguales por Marcos Erans Batista, Juan Moreno Segura y Alonso Ruiz Palomo
La forma en la que funciona es la siguiente, utilizamos nuestras propias imagenes creadas en las carpetas que podrás ver en el repositorio. Usamos la misma imagen para diferentes tipos de sensor, a los que pasamos por linea de comando o el docker-compose como se deben comportar. Estos actuan como publishers a una API, que manda los mensajes a un exchange, el cual, viendo de donde provienen, los manda a una cola (si no existe, la crea). Estas colas llevan a unos consumidores que están escuchando en la cola y pasan todos los mensajes a un csv. 
