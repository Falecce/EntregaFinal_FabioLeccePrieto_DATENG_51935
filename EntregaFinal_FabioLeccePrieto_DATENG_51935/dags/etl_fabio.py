# Este es el DAG que orquesta el ETL de la tabla users

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import smtplib
from email import message

QUERY_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS vehiculos_producidos_vs_exportados2 (
    date_from VARCHAR(10),
    vehiculos_producidos decimal(10),
    vehiculos_exportados decimal(10),
    diferencia decimal (10),
    porcentaje_exportacion decimal(6),
    frequency varchar(12),
    process_date VARCHAR(10) distkey
) sortkey(process_date);
"""

QUERY_CLEAN_PROCESS_DATE = """
DELETE FROM users WHERE process_date = '{{ ti.xcom_pull(key="process_date") }}';
"""


# create function to get process_date and push it to xcom
def get_process_date(**kwargs):
    # If process_date is provided take it, otherwise take today
    if (
        "process_date" in kwargs["dag_run"].conf
        and kwargs["dag_run"].conf["process_date"] is not None
    ):
        process_date = kwargs["dag_run"].conf["process_date"]
    else:
        process_date = kwargs["dag_run"].conf.get(
            "process_date", datetime.now().strftime("%Y-%m-%d")
        )
    kwargs["ti"].xcom_push(key="process_date", value=process_date)

defaul_args = {
    "owner": "Fabio Lecce",
    "start_date": datetime(2023, 7, 1),
    "retries": 0,
    "retry_delay": timedelta(seconds=5),
}

with DAG(
    dag_id="etl_fabio",
    default_args=defaul_args,
    description="ETL de la tabla importaciones autos",
    schedule_interval="@daily",
    catchup=False,
) as dag:
    
    # Tareas
    get_process_date_task = PythonOperator(
        task_id="get_process_date",
        python_callable=get_process_date,
        provide_context=True,
        dag=dag,
    )

    create_table = SQLExecuteQueryOperator(
        task_id="create_table",
        conn_id="redshift_default",
        sql=QUERY_CREATE_TABLE,
        dag=dag,
    )

    clean_process_date = SQLExecuteQueryOperator(
        task_id="clean_process_date",
        conn_id="redshift_default",
        sql=QUERY_CLEAN_PROCESS_DATE,
        dag=dag,
    )

    spark_etl_fabio = SparkSubmitOperator(
        task_id="spark_etl_fabio",
        application=f'{Variable.get("spark_scripts_dir")}/fabio.py',
        conn_id="spark_default",
        dag=dag,
        driver_class_path=Variable.get("driver_class_path"),
    )

    get_process_date_task >> create_table >> clean_process_date >> spark_etl_fabio
