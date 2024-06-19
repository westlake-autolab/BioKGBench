import json
from src.kg.graphdb_connector import connector




from typing import List, Tuple, Dict, Optional, Union

def get_relations_by_ids_agent(entity_ids: List[str]) -> Tuple[Dict[str, Dict[str, List[str]]], str]:
    """
    Retrieves the relationships of multiple entities in a knowledge graph, categorized as 'incoming' or 'outgoing'.

    Args:
    entity_ids (List[str]): The IDs of the entities whose relationships are to be retrieved.

    Returns:
    Tuple[Dict[str, Dict[str, List[str]]], str]: A tuple where the first element is a dictionary with each entity ID as 
                                                keys and another dictionary as values categorizing the relationships 
                                                as 'incoming' and 'outgoing'. The second element is a string with a JSON 
                                                representation of the natural language description of the relationships.
    """
    try:
        driver = connector.getGraphDatabaseConnectionConfiguration()
        with driver.session() as session:
            relations_summary = {}
            for entity_id in entity_ids:
                entity_id_clean = entity_id.strip('\'')
                query = f'''
                MATCH (n {{id: '{entity_id_clean}'}})-[r]-(m)
                RETURN DISTINCT type(r) as relation,
                       case when exists((n)-[r]->(m)) then 'outgoing' else 'incoming' end as direction
                '''
                result = session.run(query)
                relations = {'incoming': [], 'outgoing': []}
                for record in result:
                    relations[record['direction']].append(record['relation'])

                relations_summary[entity_id_clean] = relations

            observations = {eid: {"Incoming": ", ".join(set(rels['incoming'])) or None,
                                  "Outgoing": ", ".join(set(rels['outgoing'])) or None}
                            for eid, rels in relations_summary.items()}
            json_observations = json.dumps(observations)  # Convert observations to a JSON string
            return relations_summary, f"Observation: {json_observations}"
    except Exception as e:
        error_message = json.dumps({"Error": f"An error occurred while fetching relations: {str(e)}"})
        return {}, f"Observation: {error_message}"

def get_neighbor_type_agent(entity_ids: List[str], relation: str, direction: str) -> Tuple[Optional[Dict[str, List[str]]], str]:
    """
    Retrieves the types of neighboring nodes for multiple entities in a knowledge graph based on specified relationships and directions.

    Args:
    entity_ids (List[str]): The IDs of the entities whose neighbor types are to be found.
    relation (str): The type of the relationships to consider.
    direction (str): The direction of the relationships ('incoming' or 'outgoing').

    Returns:
    Tuple[Optional[Dict[str, List[str]]], str]: A tuple where the first element is a dictionary with entity IDs as keys
                                                and lists of neighbor types as values. The second element is a string
                                                with a JSON representation of the observations.
    """
    try:
        driver = connector.getGraphDatabaseConnectionConfiguration()
        with driver.session() as session:
            all_neighbors_type = {}
            for entity_id in entity_ids:
                entity_id_clean = entity_id.strip('\'')
                relation_clean = relation.strip('\'')
                direction_clean = direction.strip('\'').lower()
                query_direction = f"-[r:{relation_clean}]->" if direction_clean == 'outgoing' else f"<-[r:{relation_clean}]-"
                query = f"""
                MATCH (n {{id: '{entity_id_clean}'}}){query_direction}(m)
                RETURN DISTINCT labels(m) as neighbor_type
                """
                result = session.run(query)
                neighbors_type = list(set([record['neighbor_type'][0] for record in result if record['neighbor_type']]))

                all_neighbors_type[entity_id_clean] = neighbors_type if neighbors_type else None

            observations = {eid: {"NeighborTypes": neighbors_type or []} for eid, neighbors_type in all_neighbors_type.items()}
            json_description = json.dumps(observations)  # Convert observations to a JSON string
            return all_neighbors_type, f"Observation: {json_description}"
    except Exception as e:
        return None, f"Observation: An error occurred while fetching neighbor types: {str(e)}"
    
def get_neighbor_with_type_agent(entity_ids: List[str], relation: str, direction: str, neighbor_type: str) -> Tuple[Optional[Dict[str, Dict[str, List[str]]]], str]:
    """
    Retrieves the neighbors of multiple entities in a knowledge graph based on a specific relationship and direction.

    Args:
    entity_ids (List[str]): The IDs of the entities whose neighbors are to be found.
    relation (str): The type of the relationship to consider.
    direction (str): The direction of the relationship ('incoming' or 'outgoing').
    neighbor_type (str): The type of the neighboring node to query.

    Returns:
    Tuple[Optional[Dict[str, Dict[str, List[str]]]], str]: A tuple where the first element is a dictionary with each entity ID as keys
                                                           and another dictionary as values categorizing the neighbors based on the 
                                                           relationship. The second element is a string with a JSON representation 
                                                           of the neighbor relationships.
    """
    try:
        driver = connector.getGraphDatabaseConnectionConfiguration()
        with driver.session() as session:
            all_neighbors_summary = {}
            for entity_id in entity_ids:
                entity_id_clean = entity_id.strip('\'')
                relation_clean = relation.strip('\'')
                direction_clean = direction.strip('\'').lower()
                neighbor_type_clean = neighbor_type.strip('\'').capitalize()
                query_direction = f"-[r:{relation_clean}]->" if direction_clean == 'outgoing' else f"<-[r:{relation_clean}]-"
                query = f"""
                MATCH (n {{id: '{entity_id_clean}'}}){query_direction}(m:{neighbor_type_clean})
                RETURN DISTINCT m as neighbor
                """

                result = session.run(query)
                neighbors = [record['neighbor'] for record in result if record['neighbor'] is not None]

                attribute = ""
                if neighbor_type_clean == 'Protein':
                    attribute = 'id'
                elif neighbor_type_clean == 'Disease':
                    attribute = 'name'
                elif neighbor_type_clean == 'Protein_structure':
                    attribute = 'id'
                elif neighbor_type_clean == 'Amino_acid_sequence':
                    attribute = 'sequence'
                elif neighbor_type_clean == 'Cellular_component':
                    attribute = 'name'
                elif neighbor_type_clean == 'Molecular_function':
                    attribute = 'name'
                elif neighbor_type_clean == 'Biological_process':
                    attribute = 'name'
                elif neighbor_type_clean == 'Pathway':
                    attribute = 'name'
                elif neighbor_type_clean == 'Modified_protein':
                    attribute = 'id'
                elif neighbor_type_clean == 'Modification':
                    attribute = 'id'
                else:
                    attribute = 'id'
                
                neighbors_attr = [str(n[attribute]) for n in neighbors]
                all_neighbors_summary[entity_id_clean] = {relation_clean: neighbors_attr}

            json_summary = json.dumps(all_neighbors_summary)  # Convert to JSON string for the summary
            return all_neighbors_summary, f"Observation: {json_summary}"
    except Exception as e:
        error_message = json.dumps({"Error": f"An error occurred while fetching neighbors: {str(e)}"})
        return None, f"Observation: {error_message}"

def get_intersection_agent(*args: List[str]) -> Tuple[List[str], str]:
    """
    Calculates the intersection of multiple lists, returning elements common to all lists.

    Args:
    *args (List[str]): An arbitrary number of lists.

    Returns:
    Tuple[List[str], str]: A tuple where the first element is a list representing the intersection of all input lists. 
                            The second element is a string with a JSON representation of the result.
    """
    if not args:
        return [], "Observation: No lists provided"

    intersected_elements = set(args[0])
    for lst in args[1:]:
        intersected_elements &= set(lst)
    
    intersected_elements = list(intersected_elements)
    result = {"Intersection": intersected_elements}
    json_result = json.dumps(result)
    return intersected_elements, f"Observation: {json_result}"

def get_union_agent(*args: List[str]) -> Tuple[List[str], str]:
    """
    Calculates the union of multiple lists, returning all unique elements from all lists.

    Args:
    *args (List[str]): An arbitrary number of lists.

    Returns:
    Tuple[List[str], str]: A tuple where the first element is a list representing the union of all input lists. 
                            The second element is a string with a JSON representation of the result.
    """
    if not args:
        return [], "Observation: No lists provided"

    unioned_elements = set()
    for lst in args:
        unioned_elements |= set(lst)
    
    unioned_elements = list(unioned_elements)
    result = {"Union": unioned_elements}
    json_result = json.dumps(result)
    return unioned_elements, f"Observation: {json_result}"

if __name__ == "__main__":
    # pass
    # e_list =["Q3KR16", "Q9Y6J0", "wrong", "O15225"]
    # e_list = ["wrong"]
    # type = "Protein"
    # print(get_entity_types_by_ids_agent(e_list))
    
    # print(get_neighbor_with_type_agent(["Q6ZVE7"], 'ASSOCIATED_WITH', 'outgoing', 'Biological_process'))
    
    # print(get_intersection_agent(["as",'wq'],['as','er']))
    print(get_neighbor_with_type_agent(['GOLT1A'], 'TRANSLATED_INTO', 'outgoing', 'Protein'))
    # print(get_neighbor_with_type_agent(['Q8TEV9'], 'ACTS_ON', 'outgoing', 'Protein')[1])
    # print(get_neighbor_type_agent(e_list, 'ACTS_ON', 'Outgoing'))
    # print(get_neighbor_with_type_agent(e_list, 'ACTS_ON', 'Outgoing', 'Protein'))
    # print(get_entity_types_by_ids_agent(e_list))
    # entity_name = "Q3KR16"
    # # print(get_relations_by_id(entity_name))
    # match = get_neighbor(entity_name, "TRANSLATED_INTO", "incoming")
    # print(match)

    # relation=dict({'type1': 'Functional_region', 'relation': 'FOUND_IN_PROTEIN', 'type2': 'Protein'})
    # matched_entities = get_neighbor("Protein", entity_name,relation)
    # print(matched_entities)
    # attributes = get_all_attributes(entity_name)
    # for attr in attributes:
    #     print(attr)


