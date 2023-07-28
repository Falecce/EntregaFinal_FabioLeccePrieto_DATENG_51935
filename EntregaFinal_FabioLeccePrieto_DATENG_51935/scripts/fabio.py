# Este script está pensado para correr en Spark y hacer el proceso de ETL de la tabla users

import requests
import urllib.parse
from datetime import datetime, timedelta
from os import environ as env
from pyspark.sql.functions import concat, col, lit, when, expr, to_date, monotonically_increasing_id
from commons import ETL_Spark
import smtplib
from airflow.models import DAG, Variable
from airflow.operators.python_operator import PythonOperator
from email.mime.text import MIMEText

def send_email(subject, body, recipients):
    # Código para enviar el correo electrónico, similar al ejemplo anterior
    sender_email = Variable.get('SMTP_EMAIL_FROM')
    password = Variable.get('SMTP_PASSWORD')
    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipients

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, recipients, message.as_string())
        server.quit()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print("Error al enviar el correo:", str(e))

class ETL_Fabio(ETL_Spark):
        def __init__(self, job_name=None):
            super().__init__(job_name)
            self.process_date = datetime.now().strftime("%Y-%m-%d")

        def run(self):
            process_date = "2023-07-09"  # datetime.now().strftime("%Y-%m-%d")
            self.execute(process_date)

        def extract(self):
            """
            Extrae datos de la API
            """
            print(">>> [E] Extrayendo datos de la API...")

            def get_api_call(ids, **kwargs):
                API_BASE_URL = "https://apis.datos.gob.ar/series/api/"
                kwargs["ids"] = ",".join(ids)
                
                return "{}{}?{}".format(API_BASE_URL, "series", urllib.parse.urlencode(kwargs))
            
            api_call = get_api_call(["Automotriz_produccion_s2nqOo,Automotriz_expos_ItCfsr"])
            result = requests.get(api_call).json()
            df = self.spark.createDataFrame(result['data'], ["date_from", "vehiculos_producidos", "vehiculos_exportados"])
            df.printSchema()
            df.show()

            return df

        def transform(self, df_original):
            """
            Transforma los datos
            """
            print(">>> [T] Transformando datos...")
            #Eliminamos duplicados

            df = df_original.withColumn(
                'Diferencia', df_original.vehiculos_producidos - df_original.vehiculos_exportados
            )

            df = df.withColumn(
                'Porcentaje_exportacion', 100 * df_original.vehiculos_exportados / df_original.vehiculos_producidos
            )

            df = df.orderBy(col("date_from").asc())

            df = df.withColumn('frequency', lit('Mensual'))

            df.printSchema()
            df.show()

            return df

        def send_email_alert(self):
            subject = "Alerta: Valores de Porcentaje de Exportación anormales"
            body = "Los siguientes meses tienen un porcentaje de exportación mayor al 100%:\n\n"
            
            # Obtener los registros que cumplen la condición
            df_alert = self.df_final.filter(col("Porcentaje_exportacion") > 100)

            for row in df_alert.collect():
                # Formatear los datos y agregarlos al cuerpo del correo
                body += f"Date: {row['date_from']}, Porcentaje_exportacion: {row['Porcentaje_exportacion']}\n"
            
            recipients = Variable.get('SMTP_EMAIL_TO')
            send_email(subject, body, recipients)

        def load(self, df_final):
            """
            Carga los datos transformados en Redshift
            """
            print(">>> [L] Cargando datos en Redshift...")

            # add process_date column
            df_final = df_final.withColumn("process_date", lit(self.process_date))

            df_final.write \
                .format("jdbc") \
                .option("url", env['REDSHIFT_URL']) \
                .option("dbtable", f"{env['REDSHIFT_SCHEMA']}.vehiculos_producidos_vs_exportados2") \
                .option("user", env['REDSHIFT_USER']) \
                .option("password", env['REDSHIFT_PASSWORD']) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            self.df_final = df_final
            # Verificar si hay registros que cumplan la condición
            df_alert = df_final.filter(col("Porcentaje_exportacion") > 50)
            if not df_alert.isEmpty():
                self.send_email_alert()
            
            print(">>> [L] Datos cargados exitosamente")

if __name__ == "__main__":
    print("Corriendo script")
    etl = ETL_Fabio()
    etl.run()