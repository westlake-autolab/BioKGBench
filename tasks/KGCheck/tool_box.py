import re
import ast

from .kg_toolbox.kg_tools import query_node_existence, query_node_attribute, query_relation_between_nodes
from .retrieve_toolbox.web_api import get_uniprot_protein_info, check_interaction_string
from .retrieve_toolbox.corpus_based_retrieve import pub_rag


tool_list = [query_node_existence, query_node_attribute, query_relation_between_nodes,
            get_uniprot_protein_info, pub_rag, check_interaction_string]

tool_map = {'query_node_existence': query_node_existence, 'query_node_attribute': query_node_attribute, 
            'query_relation_between_nodes': query_relation_between_nodes, 'get_uniprot_protein_info': get_uniprot_protein_info,
            'pub_rag': pub_rag, 'check_interaction_string': check_interaction_string}

def content_parser(res: str):
    '''get the tool name and arguments'''
    tool_match = re.search(r"tool\s*=\s*([a-zA-Z_]+)", res)
    args_match = re.search(r"args\s*=\s*(\{.*\})", res)
    tool_content = tool_match.group(1)
    args_content = args_match.group(1)
    args = ast.literal_eval(args_content)
    return tool_content, args
  

def tool_node(state):
    input_ = state['messages'][-1][1]
    tool_name, args = content_parser(input_)
    res = tool_map[tool_name].invoke(args)
    return {'messages': [('human', res)],
            'sender': 'call_tool',
            'receiver': state['sender']}
