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
    task_id='import_data',
    bash_command='cd /opt/airflow/project && dvc repro --no-commit import_data'
    )

    preprocess = BashOperator(
    task_id='preprocess',
    bash_command='''
    cd /opt/airflow/project && \
    mkdir -p /tmp/dvc_cache && \
    dvc config cache.dir /tmp/dvc_cache && \
    dvc repro --no-commit preprocess
    ''',
    dag=dag
)

    train = BashOperator(
    task_id='train',
    bash_command='''
    cd /opt/airflow/project && \
    export MLFLOW_ARTIFACT_ROOT=/tmp/mlflow && \
    dvc repro train --force
    ''',
    dag=dag
)

    evaluate = BashOperator(
        task_id="evaluate",
        bash_command="cd /opt/airflow/project && dvc repro evaluate",
    )

    import_data >> preprocess >> train >> evaluate