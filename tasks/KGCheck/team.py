import argparse
from datetime import datetime
import json
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
import logging
import operator
import os
import re
from tqdm import tqdm
from typing import Annotated, Sequence, TypedDict, List, Union, Tuple, Dict

from .agents import leader_chain
from .agents import kg_chain
from .agents import validation_chain
from .tool_box import tool_node


# helper utilities
def tool_calling_parser(res: str) -> str | bool:
    '''find out whether if the agent made a tool call.
        validate the tool name and arguments.'''
    receiver_match = re.match(r"([^,]+),", res)
    if receiver_match:
        tool_flag = receiver_match.group(1) == 'call_tool'
    else:
        return "You should specify the receiver before you assign task. Please regenerate your message and it should start by 'sender, ' where sender is the one you assign task to. Tool calling message should start by 'call_tool, '"
    tool_match = re.search(r"tool\s*=\s*([a-zA-Z_]+)", res)
    if tool_match:
        args_match = re.search(r"args\s*=\s*(\{.*\})", res)
        if not args_match:
            return "failed to generate the necessary arguments for tool calling, please try again. "
        else:
            return True
    elif not tool_flag:
        if receiver_match.group(1) != 'team_leader':
            return "Please tell me what tool to use. You can format your reply like tool = tool_name, args = ... so I can better understand."
        else:
            return False
        
    
def get_receiver(content: str) -> Union[bool, str]:
    '''get the receiver of the next round
       the leader will regenerate the result if receiver is not provided'''
    temp = re.match(r"([^,]+),", content)
    # if not temp: temp = re.match(r"([^:]+):", content)
    if not temp:
        return False, "You should specify the receiver before you assign task. Please regenerate your message and it should start by 'sender, ' where sender is the one you assign task to ."
    else:
        temp_ = temp.group(1).strip()
        if temp_ not in ['team_leader', 'kg_agent', 'validation_agent', 'FINISH']:
            return False, "You should specify the receiver before you assign task. Please regenerate your message and it should start by 'sender, ' where sender is the one you assign task to ."
        return True, temp_
    
def parse_content(raw: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    res = []
    for k in raw:
        res.append({'role':k[0], 'content':k[1]})
    return res

def read_write(data, path):
    with open(path, 'a+', encoding='utf-8') as ff:
        json.dump(data, ff)

def save_answer(m_le, m_kg, m_va):
    
    mm_le = parse_content(m_le)
    mm_kg = parse_content(m_kg)
    mm_va = parse_content(m_va)

    print(mm_le, mm_kg, mm_va)
    raise SystemExit
    
    # read_write(mm_le, fp_leader)
    # read_write(mm_kg, fp_kg)
    # read_write(mm_va, fp_validation)

class assist_agent:
    '''
        agents can only get the access to conversations related to them.
        a simple method is applied to build their memories.
    '''
    def __init__(self, name, llm_chain) -> None:
        self.memory: List[Sequence[BaseMessage]] = []
        self.name = name
        self.agent = llm_chain
    
    def agent_node(self, state):
        inputs_ = state['messages'][-1]
        self.memory.append(inputs_)
        if len(self.memory) == 20:
            return {
                "messages": [('ai','I have run out of my budget, so we cannot finish the task. You should terminate it.')],
                "sender": self.name,
                "receiver": 'team_leader'
            }
        res = self.agent.invoke({"input": self.memory}).dict()['content']
        self.memory.append(('ai', res))
        tool_check = tool_calling_parser(res)
        if isinstance(tool_check, str):
            return {
                "messages": [('human', tool_check)],
                "sender": self.name,
                "receiver": self.name
            }
        if tool_check:
            rec = 'call_tool'
        else:
            rec = 'team_leader'
        return {
            "messages": [('ai', res)],
            "sender": self.name,
            "receiver": rec
        }
        
        
class leader_agent(assist_agent):
    def agent_node(self, state):
        inputs_ = state['messages'][-1]
        self.memory.append(inputs_)
        if 'break down' in inputs_[1]:
            self.memory.append(('ai', 'I have made my plan, time to assign the task to specific worker.'))
        if len(self.memory) == 20:
            return {
                "messages": [('ai','I have run out of my budget so I have to terminate the task.')],
                "sender": self.name,
                "receiver": 'FINISH'
            }
        res = self.agent.invoke({"input": self.memory}).dict()['content']
        flag, temp = get_receiver(res)
        if flag :
            if temp != 'team_leader':
                self.memory.append(('ai', res))
            return {
            "messages": [('ai', res)],
            "sender": self.name,
            "receiver": temp
        }
        else:
            self.memory.append(('ai', res))
            return {
            "messages": [('human', temp)],
            "sender": self.name,
            "receiver": self.name
        }


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add] # sender, receiver, message_content
    sender: str
    receiver: str


leader_router = {"team_leader": "team_leader", "kg_agent": "kg_agent", "validation_agent": "validation_agent", "FINISH": END}
kg_assistant_router = {"call_tool": "call_tool", "team_leader": "team_leader", "kg_agent": "kg_agent"}
validation_assistant_router = {"call_tool": "call_tool", "team_leader": "team_leader", "validation_agent": "validation_agent"}
tool_router = {"kg_agent": "kg_agent", "validation_agent": "validation_agent"}


def main(task: str):
    # task = sys.argv[1]
    # task = input("task: ")
    # print(task)

    # define agents
    team_leader = leader_agent('team_leader', leader_chain)
    kg_agent = assist_agent('kg_agent', kg_chain)
    validation_agent = assist_agent('validation_agent', validation_chain)

    # define the graph
    workflow = StateGraph(AgentState)

    workflow.add_node('team_leader', team_leader.agent_node)
    workflow.add_node('kg_agent', kg_agent.agent_node)
    workflow.add_node('validation_agent', validation_agent.agent_node)
    workflow.add_node('call_tool', tool_node)

    workflow.add_conditional_edges(
        'team_leader',
        lambda x: x['receiver'],
        leader_router
    )
    workflow.add_conditional_edges(
        'kg_agent',
        lambda x: x['receiver'],
        kg_assistant_router
    )
    workflow.add_conditional_edges(
        'validation_agent',
        lambda x: x['receiver'],
        validation_assistant_router
    )
    workflow.add_conditional_edges(
        'call_tool',
        lambda x: x['receiver'],
        tool_router
    )
    workflow.set_entry_point('team_leader')

    graph = workflow.compile()

    # invoke the graph
    events = graph.stream(
        {
            "messages": [("human", task)]
        },
        # Maximum number of steps to take in the graph
        {"recursion_limit": 150},
    )
    for s in events:
        print(s)
        print('---')
        logging.info(s)
        if 'team_leader' in s.keys():
            if s['team_leader']['receiver'] == 'FINISH':
                save_answer(team_leader.memory,
                            kg_agent.memory,
                            validation_agent.memory)

if __name__ == '__main__':

    os.makedirs('results/kgcheck', exist_ok=True)
    
    fp_leader = ''
    fp_kg = ''
    fp_validation = ''

    parser = argparse.ArgumentParser(description='Task KGCheck')
    parser.add_argument('--data_file', '-d', type=str, help='The path to the data file', required=True)
    parser.add_argument('--log_file', '-l', type=str, default=f'results/kgcheck/log_{datetime.now().timestamp()}.txt', help='The path to the log file')

    args = parser.parse_args()

    logging.basicConfig(filename=args.log_file, level=logging.INFO, filemode='a')

    with open(args.data_file, 'r') as file:
        data = json.load(file)

    for element in tqdm(data):
        instruction = element['instruction']
        main(instruction)
        with open(args.log_file, 'a') as f:
            f.write('\n')

