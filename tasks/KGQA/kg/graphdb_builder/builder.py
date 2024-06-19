"""
    The module loads all the entities and relationships defined in the importer files. It
    calls Cypher queries defined in the cypher.py module. Further, it generates an hdf object
    with the number of enities and relationships loaded for each Database and Ontology.
"""

import os
from urllib.parse import quote, unquote
import sys
import re
from datetime import datetime
from src.kg import kg_utils
from src.kg.graphdb_connector import connector


START_TIME = datetime.now()

try:
    kg_config = kg_utils.read_kg_config()
    cwd = os.path.dirname(os.path.abspath(__file__))
    log_config = kg_config['graphdb_builder_log']
    logger = kg_utils.setup_logging(log_config, key="loader")
    config = kg_utils.setup_config('builder')
except Exception as err:
    logger.error("Reading configuration > {}.".format(err))


def remove_repeated_lines(file_path):
    """
    Remove repeated lines of .tsv files, which are to loaded into kg.
    """
    with open(file_path, 'r') as f:
        header = f.readline()
        lines = f.readlines()
    lines_seen = set()
    lines_seen.add(header)
    for line in lines:
        if line not in lines_seen:
            lines_seen.add(line)
    with open(file_path, 'w') as f:
        f.write(header)
        for line in lines_seen:
            f.write(line)


def load_into_database(driver, queries, requester):
    """
    This function runs the queries provided in the graph database using a neo4j driver.

    :param driver: neo4j driver, which provides the connection to the neo4j graph database.
    :type driver: neo4j driver
    :param list[dict] queries: list of queries to be passed to the database.
    :param str requester: identifier of the query.
    """
    regex = r"file:\/\/\/(.+\.tsv)"
    result = None
    for query in queries:
        try:
            if "file" in query:
                matches = re.search(regex, query)
                if matches:
                    file_path = matches.group(1)
                    if os.path.isfile(unquote(file_path)):
                        result = connector.commitQuery(driver, query+";")
                        record = result.single()
                        if record is not None and 'c' in record:
                            counts = record['c']
                            if counts == 0:
                                logger.warning("{} - No data was inserted in query: {}.\n results: {}".format(requester, query, counts))
                            else:
                                logger.info("{} - Query: {}.\n results: {}".format(requester, query, counts))
                        else:
                            logger.info("{} - cypher query: {}".format(requester, query))
                    else:
                        logger.error("Error loading: File does not exist. Query: {}".format(query))
            else:
                result = connector.commitQuery(driver, query+";")
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error("Loading: {}, file: {}, line: {} - query: {}".format(err, fname, exc_tb.tb_lineno, query))

    return result


def updateDB(driver, imports=None, specific=[]):
    """
    Populates the graph database with information for each Database or Ontology \
    specified in imports. If imports is not defined, the function populates the entire graph \
    database based on the graph variable defined in the grapher_config.py module. \
    This function also updates the graph stats object with numbers from the loaded entities and \
    relationships.

    :param driver: neo4j driver, which provides the connection to the neo4j graph database.
    :type driver: neo4j driver
    :param list imports: a list of entities to be loaded into the graph.
    """
    if imports is None:
        imports = config["graph"]
    try:
        cypher_queries = kg_utils.get_queries(os.path.join(cwd, config['cypher_queries_file']))
    except Exception as err:
        logger.error("Reading queries file > {}.".format(err))

    for i in imports:
        queries = []
        logger.info("Loading {} into the database".format(i))
        try:
            import_dir = quote(kg_config['imports_databases_directory'], safe='/:')
            if i == "ontologies":
                entities = [e.lower() for e in config["ontology_entities"]]
                if len(specific) > 0:
                    entities = list(set(entities).intersection([s.lower() for s in specific]))
                import_dir = quote(kg_config['imports_ontologies_directory'], safe='/:')
                ontologyDataImportCode = cypher_queries['IMPORT_ONTOLOGY_DATA']['query']
                for entity in entities:
                    queries.extend(ontologyDataImportCode.replace("ENTITY", entity.capitalize()).replace("IMPORTDIR", import_dir).split(';')[0:-1])
                print('Done Loading ontologies')
            elif i == "genes":
                code = cypher_queries['IMPORT_GENE_DATA']['query']
                queries = code.replace("IMPORTDIR", import_dir).split(';')[0:-1]
                print('Done Loading genes')
            elif i == "proteins":
                code = cypher_queries['IMPORT_PROTEIN_DATA']['query']
                queries = code.replace("IMPORTDIR", import_dir).split(';')[0:-1]
                print('Done Loading proteins')
            elif i == "annotations":
                code = cypher_queries['IMPORT_PROTEIN_ANNOTATIONS']['query']
                queries = code.replace("IMPORTDIR", import_dir).split(';')[0:-1]
                print('Done Loading annotations')
            elif i == "modified_proteins":
                code = cypher_queries['IMPORT_MODIFIED_PROTEINS']['query']
                for resource in config["modified_proteins_resources"]:
                    queries.extend(code.replace("IMPORTDIR", import_dir).replace("RESOURCE", resource.lower()).split(';')[0:-1])
                print('Done Loading modified_proteins')
            elif i == "ppi":
                code = cypher_queries['IMPORT_CURATED_PPI_DATA']['query']
                for resource in config["curated_PPI_resources"]:
                    queries.extend(code.replace("IMPORTDIR", import_dir).replace("RESOURCE", resource.lower()).split(';')[0:-1])
                code = cypher_queries['IMPORT_PPI_ACTION']['query']
                for resource in config["PPI_action_resources"]:
                    queries.extend(code.replace("IMPORTDIR", import_dir).replace("RESOURCE", resource.lower()).split(';')[0:-1])
                print('Done Loading ppi')
            elif i == "protein_structure":
                code = cypher_queries['IMPORT_PROTEIN_STRUCTURES']['query']
                queries = code.replace("IMPORTDIR", import_dir).split(';')[0:-1]
                print('Done Loading protein_structure')
            elif i == "diseases":
                code = cypher_queries['IMPORT_DISEASE_DATA']['query']
                for entity, resource in config["disease_resources"]:
                    queries.extend(code.replace("IMPORTDIR", import_dir).replace("ENTITY", entity).replace("RESOURCE", resource.lower()).split(';')[0:-1])
                print('Done Loading diseases')
            elif i == 'pathway':
                code = cypher_queries['IMPORT_PATHWAY_DATA']['query']
                for resource in config["pathway_resources"]:
                    queries.extend(code.replace("IMPORTDIR", import_dir).replace("RESOURCE", resource.lower()).split(';')[0:-1])
                print('Done Loading pathway')
            elif i == "jensenlab":
                code = cypher_queries['IMPORT_JENSENLAB_DATA']['query']
                for (entity1, entity2) in config["jensenlabEntities"]:
                    queries.extend(code.replace("IMPORTDIR", import_dir).replace("ENTITY1", entity1).replace("ENTITY2", entity2).split(';')[0:-1])
                print('Done Loading jensenlab')
            else:
                logger.error("Non-existing dataset. The dataset you are trying to load does not exist: {}.".format(i))
            load_into_database(driver, queries, i)
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error("Loading: {}: {}, file: {}, line: {}".format(i, err, fname, exc_tb.tb_lineno))


def SkgBuild(imports):
    """
    Build a small customize KG, a subgraph of clinical knowledge graph (CKG).
    """
    driver = connector.getGraphDatabaseConnectionConfiguration()
    updateDB(driver, imports)


if __name__ == '__main__':
    SkgBuild()
