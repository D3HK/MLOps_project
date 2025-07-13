from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    "dvc_pipeline",
    start_date=datetime(2025, 7, 13),
    schedule_interval=None,  # Ручной запуск
    # schedule_interval="@daily", # @weekly
    catchup=False,
) as dag:

    import_data = BashOperator(
        task_id="import_data",
        bash_command="cd /opt/airflow/project && dvc repro import_data",
    )

    preprocess = BashOperator(
        task_id="preprocess",
        bash_command="cd /opt/airflow/project && dvc repro preprocess",
    )

    train = BashOperator(
        task_id="train",
        bash_command="cd /opt/airflow/project && dvc repro train --force",
    )

    evaluate = BashOperator(
        task_id="evaluate",
        bash_command="cd /opt/airflow/project && dvc repro evaluate",
    )

    import_data >> preprocess >> train >> evaluate