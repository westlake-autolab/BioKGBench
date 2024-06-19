import os
import yaml
import json
import logging
import logging.config


def read_yaml(yaml_file):
    content = None
    with open(yaml_file, 'r') as stream:
        try:
            content = yaml.safe_load(stream)
        except yaml.YAMLError as err:
            raise yaml.YAMLError("The yaml file {} could not be parsed. {}".format(yaml_file, err))
        return content
    

def read_kg_config(key=None):
    cwd = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(cwd, 'config/kg_config.yml')
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


def setup_config(data_type="databases"):
    """
    Reads YAML configuration file and converts it into a Python dictionary.

    :param data_type: configuration type ('databases', 'ontologies', 'experiments' or 'builder').
    :return: Dictionary.

    .. note:: This function should be used to obtain the configuration for databases_controller.py, \
                ontologies_controller.py, experiments_controller.py and builder.py.
    """
    try:
        dirname = os.path.join(read_kg_config(key='kg_directory'), 'graphdb_builder')
        file_name = '{}_config.yml'.format(data_type)
        config = get_configuration(os.path.join(dirname, file_name))
    except Exception as err:
        raise Exception("builder_utils - Reading configuration > {}.".format(err))

    return config


def get_queries(queries_file):
    queries = None
    if queries_file.endswith("yml"):
        queries = read_yaml(queries_file)
    else:
        raise Exception("The format specified in the queries file {} is not supported. {}".format(queries_file))
    return queries


if __name__ == '__main__':
    # read_kg_config()
    setup_config('builder')