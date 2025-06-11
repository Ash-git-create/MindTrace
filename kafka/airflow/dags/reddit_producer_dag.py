from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='reddit_producer_dag',
    default_args=default_args,
    description='Run Reddit Kafka Producer every 15 minutes',
    start_date=datetime(2025, 6, 10),
    schedule_interval='*/15 * * * *',  # every 15 minutes
    catchup=False
) as dag:

    run_reddit_producer = BashOperator(
        task_id='run_reddit_producer',
        bash_command='python /opt/airflow/my_kafka_project/producer/reddit_producer.py'
    )
