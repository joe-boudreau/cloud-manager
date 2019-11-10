import mysql.connector
from flask import g
from src import config


def get_manager_db():
    db = getattr(g, '_manager_db', None)
    if db is None:
        db = g._manager_db = connect_to_manager_db()
    return db


def get_worker_db():
    db = getattr(g, '_worker_db', None)
    if db is None:
        db = g._worker_db = connect_to_worker_db()
    return db


def connect_to_manager_db():
    dbip, dbport = get_rds_info()

    return mysql.connector.connect(
        user=config.manager_db_config['user'],
        password=config.manager_db_config['password'],
        db=config.manager_db_config['database'],
        host=dbip,
        port=dbport)


def connect_to_worker_db():
    dbip, dbport = get_rds_info()

    return mysql.connector.connect(
        user=config.worker_db_config['user'],
        password=config.worker_db_config['password'],
        db=config.worker_db_config['database'],
        host=dbip,
        port=dbport)


def get_rds_info():
    rds = config.get_boto_session().client('rds')
    dbs = rds.describe_db_instances()['DBInstances']
    if len(dbs) == 0:
        print("Warning: No database instances within RDS")
        raise EnvironmentError("No RDS instances configured!!!!")
    else:
        # assuming we only have one rds instance
        dbe = dbs[0]['Endpoint']
        dbip = dbe['Address']
        dbport = dbe['Port']
        return dbip, dbport


# gets the dictionary for lower and upper cpu thresholds
# and scaling factors
def get_manager_config(db=None):
    man_db = get_manager_db() if db is None else db

    cursor = man_db.cursor()
    cursor.execute("select * from config")
    records = cursor.fetchall()

    result = None

    # since there would only be one row anyway, break after iteration
    for row in records:
        result = {'upper_threshold': row[1], 'lower_threshold': row[2], 'shrink_ratio': row[3], 'expand_ratio': row[4]}
        break

    cursor.close()

    return result


def update_manager_config(lower_threshold=None, upper_threshold=None, shrink_ratio=None, expand_ratio=None):
    update_stmt = "update config set "

    if lower_threshold is not None: update_stmt += "lower_threshold = {},".format(lower_threshold)
    if upper_threshold is not None: update_stmt += "upper_threshold = {},".format(upper_threshold)
    if shrink_ratio is not None: update_stmt += "shrink_ratio = {},".format(shrink_ratio)
    if expand_ratio is not None: update_stmt += "expand_ratio = {},".format(expand_ratio)

    update_stmt = update_stmt.strip(',')  # Strip last comma

    db = get_manager_db()
    cursor = db.cursor()
    cursor.execute(update_stmt)
    db.commit()


def initialize_config():
    if get_manager_config() is None:
        insert_stmt = '''
            INSERT INTO config (lower_threshold, upper_threshold, shrink_ratio, expand_ratio)
            VALUES (40.0, 80.0, 0.5, 2.0);
        '''
        db = get_manager_db()
        cursor = db.cursor()
        cursor.execute(insert_stmt)
        db.commit()
