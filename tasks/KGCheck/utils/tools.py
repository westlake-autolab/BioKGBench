import requests
import time
import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from requests.exceptions import ConnectionError, Timeout, HTTPError
from typing import List, Dict
from ....utils.kg.graphdb_connector import connector
from ....utils.agent_fucs.fact_check import search_claim_related_docs
from .logger import check_tool

logger = check_tool()

# KG query tools
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
    try:
        res = connector.getCursorData(driver, cypher)
    except Exception as e:
        logger.info(f"query_node_existence - KG connection failure: {e}")
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
    try:
        res = connector.getCursorData(driver, cypher)
    except Exception as e:
        logger.info(f"query_node_attribute - KG connection failure: {e}")
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
    try:
        res = connector.getCursorData(driver, cypher)
    except Exception as e:
        logger.info(f"query_relation_between_nodes - KG connection failure: {e}")
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

# validation tools
@tool
def check_interaction_string(protein1, protein2):
    """This tool checks for the interaction between two proteins using the STRING database API. Given two protein ids, it will return a description on whether there is an interaction between them.

    Args:
        protein1 (str): a protein id
        protein2 (str): a protein id

    Returns:
        str: A description about whether there is an interaction between the two proteins.
    """
    species=9606
    retries=3
    delay=5
    string_api_url = "https://string-db.org/api/json/network"
    params = {
        "identifiers": f"{protein1}%0D{protein2}",
        "species": species
    }

    for attempt in range(retries):
        try:
            response = requests.get(string_api_url, params=params, timeout=10)
            response.raise_for_status() 
            data = response.json()
            if data:
                return f"Interaction exists between {protein1} and {protein2}, as recorded in database STRING."
            else:
                return f"No interaction found between {protein1} and {protein2}, as recorded in database STRING."

        except (ConnectionError, Timeout, HTTPError) as e:
            logger.info(f"check_interaction_string - attempt {attempt + 1}/{retries} STRING request failure: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return "Fail to access the database STRING."
            
@tool
def get_uniprot_protein_info(protein_id):
    """
    Fetch protein information from UniProt by protein ID and return a description about the protein, including id, accession and name.
    :param protein_id: UniProt protein ID
    :return: Formatted string with protein information, including id, accession and name
    """
    url = f"https://www.uniprot.org/uniprot/{protein_id}.txt"
    retries=3
    delay=5
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            if response.status_code == 200:
                # Process the response text to extract relevant information
                lines = response.text.split('\n')
                protein_info = {
                    'Gene Name': '',
                    'accession': '',
                }
                for line in lines:
                    if line.startswith('ID   '):
                        protein_info['accession'] = line.split()[1]
                    elif line.startswith('GN   Name='):
                        gene_name = line.split('=')[1].split(';')[0]
                        # Remove any reference identifiers from the gene name
                        protein_info['Gene Name'] = gene_name.split(' {')[0]

                # Format the information for LLM prompt
                prompt = f"id: {protein_id}"
                if not protein_info['accession']:
                    return f"The protein with ID '{protein_id}' is removed from UniProtKB."
                prompt += f", accession: {protein_info['accession']}"
                if protein_info['Gene Name']:
                    prompt += f", name: {protein_info['Gene Name']}"
                else:
                    prompt += ", name (i.e. gene) is not recorded."
                
                return prompt

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            logger.info(f"get_uniprot_protein_info - attempt {attempt + 1}/{retries} UniProt request failure: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return f"Failed to retrieve information for protein ID: {protein_id} after {retries} attempts."

env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(env_path)
# MEMO: llm info
llm = ChatOpenAI(
    model=os.getenv('MODEL'),
    temperature=0,
    base_url=os.getenv('BASE_URL')
)

def process_doc(claim, doc: List[Dict]):

    _prompt = '''Read this literature and determine whether it supports this claim and give your confidence score.
    REQUIREMENTS:
    1. Please respond in the following format:
        {{"attitude": 'support', 'refute', or 'not enough information', 
        "confidence": a number from 1 to 5, with a higher number indicating greater certainty}}
    2. Please return a valid JSON format.
    CLAIM: {claim}
    LITERATURE: {literature}'''
    prompt_check = '''This document is considered insufficient to determine whether the claim is correct. Please confirm if this is the case. If it is indeed the case, reply with "not enough information." If it supports the claim, reply with "support." If it does not support the claim, reply with "refute." Please only respond with the requested content, without any additional information.
    CLAIM: {claim}
    DOCUMENT: {document}'''
    supp_evidence, refu_evidence = [], []
    support, refute = 0, 0

    for d in doc:
        doc_id = d['document_id']
        doc_content = d['content']
        prompt = _prompt.format(claim=claim, literature=doc_content)

        isparsed = False
        for i in range(3):
            res = llm.invoke([("human", prompt)]).dict()['content']
            try:
                match = re.search(r'\{.*\}', res, re.DOTALL)
                if match:
                    _json_res = match.group(0)
                    json_res = json.loads(_json_res)
                    isparsed = True
                    break
            except:
                pass
        if not isparsed:
            continue

        attitude = json_res['attitude']
        confidence = json_res['confidence']
        if attitude == 'support':
            support += confidence
            supp_evidence.append(doc_id)
        elif attitude == 'refute':
            refute += confidence
            refu_evidence.append(doc_id)
        else:
            if confidence < 3:
                try:
                    check_res = llm.invoke([("human", prompt_check)]).dict()['content']
                    if check_res == 'support':
                        support += 1
                        supp_evidence.append(doc_id)
                    elif check_res == 'refute':
                        refute += 1
                        refu_evidence.append(doc_id)
                except:
                    pass
    
    liter = '\n'.join(f"{key}: {value}" for key, value in doc.items())
    logger.info(f"pub_rag - Results of the related literature processing: \nsupport socre = {support}, refute score = {refute}\nrelated literature:\n{liter}")
    
    if support > refute:
        return f"support, evidence: {', '.join([pid for pid in supp_evidence])}"
    elif support == refute:
        return f"The retrieved literature is insufficient to provide adequate information to determine whether the claim is correct."
    else:
        return f"refute, evidence: {', '.join([pid for pid in refu_evidence])}"

@tool
def pub_rag(query: str):
    '''retrieve evidence from provided documents to help making a verdict of the given claim
        Args:
            query(str): the claim to be verdicted
        Returns:
            no more than 10 documents ralated to the claim with their ids.
            the basic format is 'document_id: document_content'
    '''
    
    documents = [{'document_id': doc['document_id'], 'content': doc['content']} for doc in search_claim_related_docs(query)[:10]]
    result = process_doc(query, documents)

    return result
