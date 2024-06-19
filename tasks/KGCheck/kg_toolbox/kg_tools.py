from langchain.tools import tool

from .graphdb_connector import connector


driver = connector.getGraphDatabaseConnectionConfiguration()

def query_node_existence_(type, id) -> str:
    '''Determine whether the node with the given type and ID exists in the knowledge graph.
      Args:
          type (str): the type of the query node
          id (int or str): the id of the query node
      Returns:
          str: A description of whether the node with given type and id exists in the knowledge graph.'''
    type = str(type).replace("'","").replace("\"","")
    id = str(id).replace("'","").replace("\"","")
    cypher = f'''MATCH (n:{type}{{id:'{id}'}}) RETURN n'''
    res = connector.getCursorData(driver, cypher)
    if res.empty:
        return f"The node with type {type} and id {id} doesn't exist in the knowledge graph."
    else:
        return f"The node with type {type} and id {id} exists in the knowledge graph."

@tool
def query_node_existence(type, id) -> str:
    '''Determine whether the node with the given type and ID exists in the knowledge graph.
      Args:
          type (str): the type of the query node
          id (int or str): the id of the query node
      Returns:
          str: A description of whether the node with given type and id exists in the knowledge graph.'''
    type = str(type).replace("'","").replace("\"","")
    id = str(id).replace("'","").replace("\"","")
    cypher = f'''MATCH (n:{type}{{id:'{id}'}}) RETURN n'''
    res = connector.getCursorData(driver, cypher)
    if res.empty:
        return f"The node with type {type} and id {id} doesn't exist in the knowledge graph."
    else:
        return f"The node with type {type} and id {id} exists in the knowledge graph."

@tool
def query_node_attribute(type, id, attr) -> str:
    '''Retrieve the specific attribute value of the node with the given type and id.
      Args:
          type (str): the type of the query node
          id (int or str): the id of the query node
          attr (str): the attribute to be retrieved
      Returns:
          str: A description of the query result'''
    type = str(type).replace("'","").replace("\"","")
    id = str(id).replace("'","").replace("\"","")
    attr = str(attr).replace("'","").replace("\"","")
    cypher = f'''MATCH (n:{type}{{id:'{id}'}}) RETURN n.{attr} AS attr'''
    res = connector.getCursorData(driver, cypher)
    if res.empty:
        return "The node dosen't exist in the knowledge graph."
    else:
        answer = res['attr'][0]
        if answer is not None:
            return f"The {attr} of the node: {answer}."
        else:
            # maybe the input attr has a spelling mistake
            # we consider random sample 3 nodes of the same type can tell us what attributes should be contained in the node of that type
            get_attr = f'''MATCH (n:{type}) RETURN properties(n) AS properties LIMIT 3'''
            result = connector.getCursorData(driver, get_attr)
            valid_attributes = set(key for dic in result["properties"] for key in dic)
            if attr in valid_attributes:
                return f"The {attr} of the node: {answer}."
            else:
                return f"The node doesn't have an attribute named {attr}."

@tool
def query_relation_between_nodes(type1, id1, type2, id2):
    """
    Args:
        type1 (str): _description_
        id1 (int or str): _description_
        type2 (str): _description_
        id2 (int or str): _description_

    Returns:
        str: A description about the relationship from node with type1 and id1 to the node with type2 and id2 in the knowledge graph
    """
    type1 = str(type1).replace("'","").replace("\"","")
    id1 = str(id1).replace("'","").replace("\"","")
    type2 = str(type2).replace("'","").replace("\"","")
    id2 = str(id2).replace("'","").replace("\"","")
    cypher = f'''MATCH (n1:{type1}{{id:'{id1}'}})-[r]->(n2:{type2}{{id:'{id2}'}}) 
    RETURN DISTINCT n1.name AS node1, n2.name AS node2, type(r) AS relation'''
    res = connector.getCursorData(driver, cypher)
    if res.empty:
        # case 1: one of the query node doesn't exist
        node1_existence = query_node_existence_(type1, id1)
        if "doesn't exist" in node1_existence:
            return node1_existence
        node2_existence = query_node_existence_(type2, id2)
        if "doesn't exist" in node2_existence:
            return node2_existence
        # case 2: no relation between node1 and node2
        return f"No relation is found between the node (type: '{type1}', id: '{id1}') and the node (type: '{type2}', id: '{id2}') in the knowledge graph."
    else:
        res = res.drop_duplicates()
        relation_triple = []
        for i, row in res.iterrows():
            node1 = row["node1"]
            node2 = row["node2"]
            relation = row["relation"]
            triple = (node1, relation, node2) 
            relation_triple.append(triple) 
                
        if len(relation_triple) == 1:
            return f"In the KG, the {type1} node {node1} (id: {id1}) has a relationship {relation} to the {type2} node {node2} (id:{id2})."
        else:
            return f"The relationship between two nodes in the KG can be represented in the form of triplets: {', '.join([str(tup) for tup in relation_triple])}."
