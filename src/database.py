import boto3
import mysql.connector
from flask import g
from src import config


def connect_to_db():
    rds = boto3.client('rds')
    dbs = rds.describe_db_instances()['DBInstances']

    if len(dbs) == 0:
        print("Warning: No database instances within RDS")
    else:
        # assuming we only have one rds instance
        dbe = dbs[0]['Endpoint']
        dbip = dbe['Address']
        dbport = dbe['Port']

    worker_db = getattr(g, '_worker_db', None)
    if worker_db is None:
        g._worker_db = mysql.connector.connect(
                user=config.worker_db_config['user'],
                password=config.worker_db_config['password'],
                db=config.worker_db_config['database'],
                host=dbip,
                port=dbport)

    manager_db = getattr(g, '_manager_db', None)
    if manager_db is None:
        g._manager_db = mysql.connector.connect(
                user=config.manager_db_config['user'],
                password=config.manager_db_config['password'],
                db=config.manager_db_config['database'],
                host=dbip,
                port=dbport)
