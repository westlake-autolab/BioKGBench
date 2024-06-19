import sys
import os
import json
import neo4j
import yaml
import pandas as pd
import logging
import logging.config


def setup_logging(path='log.config', key=None):
    """
    Setup logging configuration.

    :param str path: path to file containing configuration for logging file.
    :param str key: name of the logger.
    :return: Logger with the specified name from 'key'. If key is *None*, returns a logger which is \
                the root logger of the hierarchy.
    """
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        try:
            logging.config.dictConfig(config)
        except Exception:
            logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(key)

    return logger


def read_yaml(yaml_file):
    content = None
    with open(yaml_file, 'r') as stream:
        try:
            content = yaml.safe_load(stream)
        except yaml.YAMLError as err:
            raise yaml.YAMLError("The yaml file {} could not be parsed. {}".format(yaml_file, err))
    return content



def read_ckg_config(key=None):
    cwd = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(cwd, 'config/ckg_config.yml')
    content = read_yaml(config_file)
    if key is not None:
        if key in content:
            return content[key]

    return content



def get_configuration(configuration_file):
    configuration = None
    if configuration_file.endswith("yml"):
        configuration = read_yaml(configuration_file)
    else:
        raise Exception("The format specified in the configuration file {} is not supported. {}".format(configuration_file))

    return configuration


def read_config():
    cwd = os.path.dirname(os.path.abspath(__file__))
    print("!!!!!",os.path.join(cwd, 'connector_config.yml'))
    logger = setup_logging()
    try:
        ckg_config = read_ckg_config()
        cwd = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(cwd, 'connector_config.yml')
        config = get_configuration(path)
        log_config = ckg_config['graphdb_connector_log']
        logger = setup_logging(log_config, key="connector")
        
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


def connectToDB(host="localhost", port=7687, user="neo4j", password="password"):
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


# def removeRelationshipDB(entity1, entity2, relationship):
#     driver = getGraphDatabaseConnectionConfiguration()
#     countCy = cy.COUNT_RELATIONSHIPS
#     deleteCy = cy.REMOVE_RELATIONSHIPS
#     countst = countCy.replace('ENTITY1', entity1).replace('ENTITY2', entity2).replace('RELATIONSHIP', relationship)
#     deletest = deleteCy.replace('ENTITY1', entity1).replace('ENTITY2', entity2).replace('RELATIONSHIP', relationship)
#     print("Removing %d entries in the database" % sendQuery(driver, countst).data()[0]['count'])
#     sendQuery(driver, deletest)
#     print("Existing entries after deletion: %d" % sendQuery(driver, countst).data()[0]['count'])


# def modifyEntityProperty(parameters):
#     '''parameters: tuple with entity name, entity id, property name to modify, and value'''

#     driver = getGraphDatabaseConnectionConfiguration()
#     entity, entityid, attribute, value = parameters

#     try:
#         queries_path = "./queries.yml"
#         project_cypher = ckg_utils.get_queries(os.path.join(cwd, queries_path))
#         for query_name in project_cypher:
#             title = query_name.lower().replace('_', ' ')
#             if title == 'modify':
#                 query = project_cypher[query_name]['query'] % (entity, entityid, attribute, value)
#                 sendQuery(driver, query)
#                 print("Property successfully modified")
#     except Exception as err:
#         exc_type, exc_obj, exc_tb = sys.exc_info()
#         fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
#         logger.error("Error: {}. Reading queries from file {}: {}, file: {},line: {}".format(err, queries_path, sys.exc_info(), fname, exc_tb.tb_lineno))


def do_cypher_tx(tx, cypher, parameters):
    result = tx.run(cypher, **parameters)
    values = result.data()
    return values


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


def find_node(driver, node_type, parameters={}):
    query = "MATCH (n:TYPE) WHERE RETURN n".replace('TYPE', node_type)
    where_clause = ''
    if len(parameters) > 0:
        where_clause = "WHERE "+'AND '.join(["n.{}='{}'".format(k,v) for k, v in parameters.items()])
    query = query.replace("WHERE", where_clause)
    query_result = sendQuery(driver, query)
    
    result = None
    if len(query_result) > 0:
        query_result = query_result.pop()
        if 'n' in query_result:
            result = query_result['n']
    
    return result


def find_nodes(driver, node_type, parameters={}):
    query = "MATCH (n:TYPE) WHERE RETURN n".replace('TYPE', node_type)
    where_clause = ''
    if len(parameters) > 0:
        where_clause = "WHERE "+'AND '.join(["n.{}='{}'".format(k,v) for k, v in parameters.items()])
    query = query.replace("WHERE", where_clause)
    result = sendQuery(driver, query)

    return result


def run_query(query, parameters={}):
    driver = getGraphDatabaseConnectionConfiguration(configuration=None, database=None)
    data = getCursorData(driver, query, parameters=parameters)

    return data


def generate_virtual_graph(graph_json):
    query = "CALL apoc.graph.fromDocument('JSON', {write:false}) YIELD graph RETURN *".replace("JSON", json.dumps(graph_json))
    #driver = getGraphDatabaseConnectionConfiguration()
    #neo4j = sendQuery(driver, query)
    return query
