from langchain_openai import ChatOpenAI
from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from .prompts import MAKE_PLAN, ASSISTANT_CHAT_TEMPLATE, LEADER_CHAT_TEMPLATE
from .utils.tools import query_node_existence, query_node_attribute, query_relation_between_nodes, check_interaction_string, get_uniprot_protein_info, pub_rag
from .retrieve_toolbox.corpus_based_retrieve import pub_rag
from .utils.logger import agent_memory
import operator
import json
import re
import os
import yaml

config = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "../../config/llm_config.yml")))
llm = ChatOpenAI(
    model=config['model'], 
    temperature=0, 
    api_key=config['api_key'], 
    base_url=config['base_url']
)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sender: str
    receiver: str
    
    
class memory(List):
    def __init__(self, name, index):
        self.logger = agent_memory(name, index)
    def append(self, item):
        if isinstance(item, tuple):
            content = item[1]
        else:
            content = item.dict()['content']
        self.logger.info(content)
        super().append(item)


class agent:

    def __init__(self, name, prompt, memory_limit, index, log) -> None:
        '''
        parameters:
            - name: the name of the agent, which should be consistent with its node name
            - prompt: a dictionary of related prompts
            - memory_limit: max chat rounds
        '''
        self.memory = memory(name, index)
        self.name = name
        self.llm = llm
        self.prompts = prompt
        self.memory_limit = memory_limit
        self.first_call = True
        self.logger = log
    
    @staticmethod
    def llm_formatter(content):
        llm_formatter = ChatOpenAI(
            model='gpt-4o-mini', 
            temperature=0, 
            api_key=config['api_key'], 
            base_url=config['base_url']
        )
        prompt = f'''Please check if the text conforms to JSON format. If it does not, output the correct JSON format result or extract the part in JSON format; if it does, return the original text.
        Please return a valid JSON result, without any extra explanations or symbols.
        TEXT: {content}'''
        checked_res = llm_formatter.invoke([('human', prompt)]).dict()['content']
        return checked_res

    def load(self, res):
        # assume the format is correct.
        try:
            json_res = json.loads(res)
            return json_res
        except:
            pass
        # try to extract using pattern matching methods.
        try:
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                _json_res = match.group(0)
                json_res = json.loads(_json_res)
                return json_res
        except:
            pass
        # try to use LLM to correct the format.
        try:
            _json_res = self.llm_formatter(res)
            json_res = json.loads(_json_res)
            return json_res
        except:
            # failed to parse the result
            raise

    def load_json_res(self, res):
        try:
            json_res = self.load(res=res)

            receiver = json_res['receiver']
            chat_content = f"{self.name}: {json_res['content']}"
            self.memory.append(('ai', chat_content))
            return receiver, chat_content
        except:
            pass
    
    def agent_node(self, state):
        '''call the llm to generate answer, also serving as a node in the graph'''
        # receive the message
        inputs_ = state['messages'][-1]
        self.memory.append(inputs_)
        # check if run out of budget
        isfull = self.manage_memory()
        if isfull:
            return {
                "messages": [AIMessage(content="I'm sorry, but I have exceeded my budget, so I can no longer provide services.")],
                "sender": self.name,
                "receiver": state['sender']
            }
        else:
            # If it is the first time receiving the task, then plan the task.
            if self.first_call:
                self.analyse_task(inputs_)
                self.first_call = False
            # bind the prompt template
            prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        content=ASSISTANT_CHAT_TEMPLATE.format(role=self.prompts['role description'], tools=self.prompts['tool description'])
                    ),
                    MessagesPlaceholder("history")
                ]
            )
            chain = prompt | self.llm
            
            isparsed = False
            for i in range(3):
                res = chain.invoke({"history": self.memory}).dict()['content']
                try:
                    receiver, chat_content = self.load_json_res(res)
                    isparsed = True
                    break
                except Exception as e:
                    self.logger.info(f"{self.name} - reply generation failure: Trail {i+1}/3 - failed to parse the result due to {e}")
            if not isparsed:
                chat_content = f"{self.name}: I'm sorry, I'm facing some difficulties and cannot respond to you at the moment. You can come back to ask me later."
                self.memory.append(('ai', chat_content))
                receiver = state['sender']

            return {
                "messages": [AIMessage(content=chat_content)],
                "sender": self.name,
                "receiver": receiver
            }
    
    def manage_memory(self):
        '''if the number of chat round exceeds the limit, the agent will stop the task immediately and froze itself.'''
        if len(self.memory) >= self.memory_limit:
            self.logger.info(f"{self.name} has run out of its total chat round budget: {self.memory_limit}.")
            return True
        else:
            return False
        
    def analyse_task(self, assignment):
        '''
        decide the type of the task to perform, then corresponding one-shot prompt will be provided.
        make a plan based on the type of task.
        '''
        if isinstance(assignment, AIMessage):
            task = assignment.dict()['content']
        elif isinstance(assignment, tuple):
            task = assignment[1]
        else:
            self.logger.info(f"{self.name} failed to make a plan for its upcoming work.")
            return
        
        role_des = self.prompts['role description']
        task_des = self.prompts['task description']
        tool_des = self.prompts['tool description']
        plan_template = PromptTemplate(template=MAKE_PLAN, input_variables=['role_description', 'task_description', 'tool_description', 'user_input'])
        
        prompt = plan_template.partial(role_description=role_des,
                                      task_description=task_des,
                                      tool_description=tool_des)
        chain = (
            prompt
            | self.llm
        )
        _plan = chain.invoke(
            {"user_input": task}
        )
        plan = AIMessage(content=f"{self.name}: {_plan.dict()['content']}")
        self.memory.append(plan)
        
        
class leader(agent):
    '''team leader'''
    
    def agent_node(self, state):
        inputs_ = state['messages'][-1]
        self.memory.append(inputs_)
        isfull = self.manage_memory()
        if isfull:
            return {
                "messages": [
                    AIMessage(
                        content='{"conclusion": None, "reason": "run out of budegt"}'
                    )
                ],
                "sender": self.name,
                "receiver": 'End'
            }
        else:
            if self.first_call:
                self.analyse_task(inputs_)
                self.first_call = False
            prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(content=LEADER_CHAT_TEMPLATE),
                    MessagesPlaceholder("history")
                ]
            )
            chain = prompt | self.llm
            
            isparsed = False
            for i in range(3):
                res = chain.invoke({"history": self.memory}).dict()['content']
                try:
                    receiver, chat_content = self.load_json_res(res)
                    isparsed = True
                    break
                except Exception as e:
                    self.logger.info(f"{self.name} - reply generation failure: Trail {i+1}/3 - failed to parse the result due to {e}")
            if not isparsed:
                chat_content = f"{self.name}: I'm sorry, I'm facing some difficulties and cannot respond to you at the moment. You can come back to ask me later."
                self.memory.append(('ai', chat_content))
                receiver = state['sender']

            return {
                "messages": [AIMessage(content=chat_content)],
                "sender": self.name,
                "receiver": receiver
            }


class ToolExecutor:
    '''An agent specifically responsible for executing tools.'''
    def __init__(self, log) -> None:
        self.tool_map = {
            'query_node_existence': query_node_existence, 
            'query_node_attribute': query_node_attribute, 
            'query_relation_between_nodes': query_relation_between_nodes, 'get_uniprot_protein_info': get_uniprot_protein_info,
            'pub_rag': pub_rag, 
            'check_interaction_string': check_interaction_string
        }
        self.log = log
        
    def parse_content(self, raw):

        try:
            args_dict = json.loads(raw)
            tool, args = args_dict.values()
            return tool, args
        except Exception as e:
            self.log.info(f"Tool Executor - instruction parsing failure: {e}")
            
    @staticmethod
    def llm_formatter(content):
        llm_formatter = ChatOpenAI(
            model='gpt-4o-mini', 
            temperature=0,
            api_key=config['api_key'], 
            base_url=config['base_url']
        )
        prompt = f'''Please check if the text conforms to JSON format. If it does not, output the correct JSON format result; if it does, return the original text.
        Please return a valid JSON result, without any extra explanations or symbols.
        TEXT: {content}'''
        checked_res = llm_formatter.invoke([('human', prompt)]).dict()['content']
        return checked_res

    def load_args(self, content):
        # try to extract using pattern matching methods
        try:
            match = re.search(r'(\{.*\})', content, re.DOTALL)
            if match:
                return self.parse_content(match.group(0))
        except:
            pass
        # try to use LLM to correct the format
        try:
            checked_content = self.llm_formatter(content)
            return self.parse_content(checked_content)
        except:
            raise

    def execute(self, content):
        try:
            tool, args = self.load_args(content=content)
        except Exception as e:
            self.log.info(f"Tool Executor - tool arguments loading failure: {e}")
        try:
            tool_res = self.tool_map[tool].invoke(args)
            return tool_res
        except:
            pass

    def tool_node(self, state):
        content = state['messages'][-1].dict()['content']
        tool_res = self.execute(content)
        if tool_res:
            return {
                'messages': [AIMessage(content=f"Tool Executor: {tool_res}")],
                'sender': 'Tool Executor',
                'receiver': state['sender']
            }
        else:
            return {
                'messages': [AIMessage(content="Tool Executor: Invalid tool information. Please provide the correct tool information.")],
                'sender': 'Tool Executor',
                'receiver': state['sender']
            }

if __name__ == '__main__':
    temp_tool = ToolExecutor()
    res = temp_tool.llm_formatter('{"tool name": "query_node_attribute", "args": {"type": "Protein", "id": "Q4G0T1", "attr": "name"}')
    print(res)