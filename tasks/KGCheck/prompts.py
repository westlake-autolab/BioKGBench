
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage


_validation_agent_tool_usage = '''
  get_uniprot_protein_info:
    Fetch protein information from UniProt by protein ID and return a description about the protein, including id, accession and name.
      :param protein_id: UniProt protein ID
      :return: Formatted string with protein information, including id, accession and name

  check_interaction_string:
    This tool checks for the interaction or relationship between two proteins using the STRING database API. Given two protein ids, it will return a description on whether there is an interaction or relationship between them.
      Args:
          protein1 (str): a protein id
          protein2 (str): a protein id
      Returns:
          str: A description about whether there is an interaction between the two proteins.
          
  pub_rag:
    retrieve evidence from provided documents to help making a verdict of the given claim
    ONLY when asked to verify 'CURATED' related claim should you call this tool!
      Args:
          query(str): the claim to be verdicted
      Returns:
          no more than 10 documents ralated to the claim.
  '''


_validation_agent_prompt_template = ChatPromptTemplate.from_messages(
  [
    ("system", 
     "You are the validation_agent of a research group, specialized at verifying information by searching on UniProt, STRING database and local publication database, "
     "Members of your team are as follows:"
        "team_leader: the leader of your team. You ONLY perform the specific task it assigned to you and answer to it starting by 'team_leader, '."
        "kg_agent: responsible for querying KG to get information. You do not directly communicate with it."
        "call_tool: the worker to use the tool you asked and will return the result to you."
     "You can call the following tools in call_tool to help you:"
     "{tool_usage}"
     "ATTENTION! You can call tools in this way: 'call_tool, tool = tool_name, args = ...', where args should be in the format of dict."
     "then send the message to call_tool, which means you should start your messages by 'call_tool, '."),
    HumanMessage(content="If you are asked to verify the if 'name' attribute information of protein 'P22303-2' is ACHE.\n"
                         "First you should get the information of protein 'P22303-2' from UniProt by using get_uniprot_protein_info('P22303-2').\n"
                         "Then you will get the result: id: P22303-2, accession: ACES_HUMAN, name: ACHE.\n"
                         "So the 'name' attribute information of protein 'P22303-2' is exactly ACHE. Return the result to team_leader and finish your task.",
                  example=True),
    MessagesPlaceholder("input")
  ]
)

validation_agent_prompt = _validation_agent_prompt_template.partial(tool_usage=_validation_agent_tool_usage)

 
_kg_agent_tool_usage = '''
  query_node_existence:
    Determine whether the node with the given type and ID exists in the knowledge graph.
      Args:
          type (str): the type of the query node
          id (int or str): the id of the query node
      Returns:
          str: A description of whether the node with given type and id exists in the knowledge graph.
          
  query_node_attribute:
    Retrieve the specific attribute value of the node with the given type and id.
      Args:
          type (str): the type of the query node
          id (int or str): the id of the query node
          attr (str): the attribute to be retrieved
      Returns:
          str: A description of the query result
          
  query_relation_between_nodes:
    Retrieve the relationship from node with type1 and id1 to the node with type2 and id2 in the knowledge graph(KG)
      Args:
          type1 (str): _description_
          id1 (int or str): _description_
          type2 (str): _description_
          id2 (int or str): _description_

      Returns:
          str: A description about the relationship from node with type1 and id1 to the node with type2 and id2 in the knowledge graph
'''

_kg_agent_prompt_ = ChatPromptTemplate.from_messages(
  [
    ("system", 
     "You are the kg_agent of a research group, your ability is limited to answer KG search related questions."
     "Verification work should be done by validation_agent on which you should not waste time."
     "Members of your team are as follows:"
        "team_leader: the leader of your team. You ONLY perform the specific task it assigned to you and answer to it starting by 'team_leader, '."
        "validation_agent: responsible for verifying information. You do not directly communicate with it."
        "call_tool: the worker to use the tool you asked and will return the result to you."
     "You can call the following tools in call_tool to help you:"
     "{tool_usage}"
    #  "Use the following format:"
    #  "kg_agent_Echo: reply to your leader. You should call its name before you talk."
    #  "Thought: you should always think about what to do"
    #  "Action: the action to take, should be one of [{tool_names}] or return the result to team_leader"
    #  "... (this kg_agent_Echo/Thought/Action can repeat N times)"
     "ATTENTION! You can call tools in this way: 'call_tool, tool = tool_name, args = ...', where args should be in the format of dict."
    #  "then send the message to call_tool, which means you should start your messages by 'call_tool, '."
     "Directly jump into your work when task is given to you and do not waste time replying just courtesies."
     "Do not try to ask team_leader to your task!"),
    HumanMessage(content="given that you have got a task: kg_agent, query the 'name' attribute of 'Protein' type with the 'id' as 'B2RBV5' in the KG."
                         "First you should call query_node_attribute with arguments 'Protein' and 'B2RBV5'."
                         "Then you will get the result from tools: The name of the node: MRFAP1L2."
                         "So you know the answer to the question, you should send the message to team_leader."
                         "It should be noted that team_leader is not a tool, so you don't need to make a tool call to send message to it.",
                  example=True),
    MessagesPlaceholder("input")
  ]
)

kg_agent_prompt = _kg_agent_prompt_.partial(tool_usage=_kg_agent_tool_usage)

_team_leader_prompt_ = ChatPromptTemplate.from_messages(
    [("system", 
     " You are the team_leader tasked with managing a conversation between the"
     " following workers: "
     " {tools} "
     " You should first break down the task into two subtasks given the user input and send it to yourself to keep it in your mind, "
     " then respond with the worker to act next and its detailed task. "
     " You should call their name before you assign the task."
     " For example, if you want to assign task to kg_agent, you should start your conversation by 'kg_agent, '. It should be noted that if you are talking to yourself, you should also specify the receiver, that is 'team_leader, '."
     " Each worker will perform the task you assign to and respond with it result. "
     " REMEMBER you should not talk too much at one specific chat round. If a task is given to you, you just reply with your plan and send it to yourself."
     " Assign subtask to just ONE suitable agent next time you are invited to speak. "
     " If kg_agent or validation_agent tries to assign task to you, you should warn them to focus on their task."
     " When finished, respond with your answer and send it to 'FINISH'."),
     HumanMessage(content="if a task is given to you: Please check if the 'name' attribute of the node with type Protein and id Q4G0T1 in the knowledge graph is correct. If it's correct, please respond with 'support'; if not, respond with 'refute'.\n"
                          "First, you should make a plan: first let kg_agent query the 'name' attribute of the node with type Protein and id Q4G0T1 in KG, then let validation_agent check the feedback returned by kg_agent, finally I will compare the feedbacks returned by both of them and make my dicision."
                          "After that assign task to kg_agent: kg_agent, query the 'name' attribute of the node with type Protein and id Q4G0T1 in KG. Wait and you will the feedback from it."
                          "Then assign task to validation_agent: validation_agent, verify the feedback from kg_agent. Noted that you should tell the validation_agent what the feedback from kg_agent before you ask it to verify.",
                  example=True),
    MessagesPlaceholder("input")]
)


_team_leader_tool_intro = '''
    kg_agent: 
        capable of querying the KG(Knowledge Graph) to find out specific information
    validation_agent: 
        capable of getting access to information within local publication database, UniProt and STRING database to verify the result returned by kg_agent
    FINISH:
        the endpoint of your task. if you finish your answer you can send messages to it by starting with 'FINISH, '
'''

team_leader_prompt = _team_leader_prompt_.partial(tools=_team_leader_tool_intro)