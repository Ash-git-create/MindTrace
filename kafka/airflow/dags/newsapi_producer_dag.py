from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='newsapi_producer_dag',
    default_args=default_args,
    description='Run NewsAPI Kafka Producer every 15 minutes',
    start_date=datetime(2025, 6, 10),
    schedule_interval='*/15 * * * *',
    catchup=False
) as dag:

    run_newsapi_producer = BashOperator(
        task_id='run_newsapi_producer',
        bash_command='python /opt/airflow/my_kafka_project/producer/newsapi_producer.py'
    )
