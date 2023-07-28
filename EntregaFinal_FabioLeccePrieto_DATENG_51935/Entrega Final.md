# Entrega Final Fabio Lecce
Aca tenemos todo lo necesario para correr la entrega final de Fabio Lecce Prieto

# Distribución de los archivos
Los archivos a tener en cuenta son:
* `docker_images/`: Contiene los Dockerfiles para crear las imagenes utilizadas de Airflow y Spark.
* `docker-compose.yml`: Archivo de configuración de Docker Compose. Contiene la configuración de los servicios de Airflow y Spark.
* `.env`: Archivo de variables de entorno. Contiene variables de conexión a Redshift y driver de Postgres.
* `dags/`: Carpeta con los archivos de los DAGs.
    * `etl_fabio.py`: DAG principal que ejecuta el pipeline de extracción, transformación y carga de datos de usuarios.
* `logs/`: Carpeta con los archivos de logs de Airflow.
* `plugins/`: Carpeta con los plugins de Airflow.
* `postgres_data/`: Carpeta con los datos de Postgres.
* `scripts/`: Carpeta con los scripts de Spark.
    * `postgresql-42.5.2.jar`: Driver de Postgres para Spark.
    * `common.py`: Script de Spark con funciones comunes.
    * `fabio.py`: Script de Spark que ejecuta el ETL.

# Pasos para ejecutar la entrega final
1. Accede a cuenta gmail, luego ir a Gestionar tu cuenta de Google > Seguridad y activar la verificación de dos pasos para esto seguir los siguientes pasos: `https://support.google.com/accounts/answer/185839?hl=es-419&co=GENIE.Platform%3DDesktop`.
2. Volver a la pestaña seguridad de la cuenta y seleccionar la opción Contraseñas de aplicaciones luego ingresar tu contraseña de login; aparecerá una nueva ventana donde elegir en aplicación correo y en dispositivo el ordenador que estés usando. Al finalizar aparecerá la contraseña de aplicación que se debe guardar (Esta es la contraseña que vamos a utlizar para la variable de ariflow `SMTP_PASSWORD` que configuraremos mas adelante).
3. Posicionarse en la carpeta `EntregaFinal_FabioLeccePrieto_DATENG_51935`. A esta altura debería ver el archivo `docker-compose.yml`.
4. Crear las siguientes carpetas a la misma altura del `docker-compose.yml`.
```bash
mkdir -p dags,logs,plugins,postgres_data,scripts
```
5. Crear un archivo con variables de entorno llamado `.env` ubicado a la misma altura que el `docker-compose.yml`. Cuyo contenido sea:
```bash
REDSHIFT_HOST=...
REDSHIFT_PORT=5439
REDSHIFT_DB=...
REDSHIFT_USER=...
REDSHIFT_SCHEMA=...
REDSHIFT_PASSWORD=...
REDSHIFT_URL="jdbc:postgresql://${REDSHIFT_HOST}:${REDSHIFT_PORT}/${REDSHIFT_DB}?user=${REDSHIFT_USER}&password=${REDSHIFT_PASSWORD}"
DRIVER_PATH=/tmp/drivers/postgresql-42.5.2.jar
```
6. Descargar las imagenes de Airflow y Spark.
```bash
docker-compose pull lucastrubiano/airflow:airflow_2_6_2
docker-compose pull lucastrubiano/spark:spark_3_4_1
```
7. Las imagenes fueron generadas a partir de los Dockerfiles ubicados en `docker_images/`. Si se desea generar las imagenes nuevamente, ejecutar los comandos que están en los Dockerfiles.
8. Ejecutar el siguiente comando para levantar los servicios de Airflow y Spark.
```bash
docker-compose up --build
```
9. Una vez que los servicios estén levantados, ingresar a Airflow en `http://localhost:8080/`.
10. En la pestaña `Admin -> Connections` crear una nueva conexión con los siguientes datos para Redshift:
    * Conn Id: `redshift_default`
    * Conn Type: `Amazon Redshift`
    * Host: `host de redshift`
    * Database: `base de datos de redshift`
    * Schema: `esquema de redshift`
    * User: `usuario de redshift`
    * Password: `contraseña de redshift`
    * Port: `5439`
11. En la pestaña `Admin -> Connections` crear una nueva conexión con los siguientes datos para Spark:
    * Conn Id: `spark_default`
    * Conn Type: `Spark`
    * Host: `spark://spark`
    * Port: `7077`
    * Extra: `{"queue": "default"}`
12. En la pestaña `Admin -> Variables` crear una nueva variable con los siguientes datos:
    * Key: `driver_class_path`
    * Value: `/tmp/drivers/postgresql-42.5.2.jar`
13. En la pestaña `Admin -> Variables` crear una nueva variable con los siguientes datos:
    * Key: `spark_scripts_dir`
    * Value: `/opt/airflow/scripts`
14. En la pestaña `Admin -> Variables` crear una nueva variable con los siguientes datos:
    * Key: `SMTP_EMAIL_FROM`
    * Value: `Escribir el correo que usaremos para enviar el Email`
15. En la pestaña `Admin -> Variables` crear una nueva variable con los siguientes datos:
    * Key: `SMTP_EMAIL_TO`
    * Value: `Escribir el correo a quien le llega el Email`
16. En la pestaña `Admin -> Variables` crear una nueva variable con los siguientes datos:
    * Key: `SMTP_PASSWORD`
    * Value: `Escribir la contraseña, que guardamos anteriormente, del correo que usaremos`
17. Ejecutar el DAG `etl_fabio`.
