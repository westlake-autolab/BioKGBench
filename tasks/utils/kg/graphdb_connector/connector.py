import os
import sys
import neo4j
import pandas as pd
import logging

from .. import kg_utils

def commitQuery(driver, query, parameters={}):
    result = None
    try:
        with driver.session() as session:
            result = session.run(query, parameters)
    except neo4j.exceptions.ClientError as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        sys_error = "{}, file: {},line: {}".format(sys.exc_info(), fname, exc_tb.tb_lineno)
        print("Connection error:{}.\n{}".format(err, sys_error))
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        sys_error = "{}, file: {},line: {}".format(sys.exc_info(), fname, exc_tb.tb_lineno)
        raise Exception("Connection error:{}.\n{}".format(err, sys_error))

    return result


def connectToDB(host="localhost", port=7625, user="neo4j", password="password"):
    try:
        uri = "bolt://{}:{}".format(host, port)
        driver = neo4j.GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        sys_error = "{}, file: {},line: {}".format(sys.exc_info(), fname, exc_tb.tb_lineno)
        print("Database is not online")
        #raise Exception("Unexpected error:{}.\n{}".format(err, sys_error))

    return driver

def do_cypher_tx(tx, cypher, parameters):
    result = tx.run(cypher, **parameters)
    values = result.data()
    return values

def sendQuery(driver, query, parameters={}):
    result = None
    try:
        with driver.session() as session:
            result = session.read_transaction(do_cypher_tx, query, parameters)
    except Exception as err:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        sys_error = "{}, file: {},line: {}".format(sys.exc_info(), fname, exc_tb.tb_lineno)
        raise Exception("Connection error:{}.\n{}".format(err, sys_error))

    return result


def getCursorData(driver, query, parameters={}):
    result = sendQuery(driver, query, parameters)
    df = pd.DataFrame(result)

    return df

def read_config():
    try:
        kg_config = kg_utils.read_kg_config()
        cwd = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(cwd, '../../../../config/kg_config.yml')
        config = kg_utils.get_configuration(path)
        log_config = kg_config['graphdb_connector_log']
        # logger = kg_utils.setup_logging(log_config, key="connector")
        logger = logging.getLogger()
        
        return config
    except Exception as err:
        logger.error("Reading configuration > {}.".format(err))


def getGraphDatabaseConnectionConfiguration(configuration=None, database=None):
    driver = None
    if configuration is None:
        configuration = read_config() # TODO this will fail if this function is imported
    host = configuration['db_url']
    port = configuration['db_port']
    user = configuration['db_user']
    password = configuration['db_password']

    if database is not None:
        host = host+'/'+database
    try:
        driver = connectToDB(host, port, user, password)
    except Exception as e:
        print("Database is offline: ", e)

    return driver


if __name__ == '__main__':
    read_config()