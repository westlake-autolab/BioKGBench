from .base import agent, leader, ToolExecutor, AgentState
from .prompts import KG_prompts, VAL_prompts, LEADER_prompts
from langgraph.graph import StateGraph, END
import json
from datetime import datetime
import argparse
import re, os
from typing import List
from tqdm import tqdm
from .utils.logger import get_logger


def add_conditional_edges(agent_name, graph, router):
    graph.add_conditional_edges(
        agent_name,
        lambda x: x['receiver'],
        router
    )

def KGCheck(task, index, log):
    # initialize agents
    kg_agent = agent(name='KG Agent', prompt=KG_prompts, memory_limit=15, index=index, log=log)
    validation_agent = agent(name='Validation Agent', prompt=VAL_prompts, memory_limit=15, index=index, log=log)
    leader_agent = leader(name='Leader', prompt=LEADER_prompts, memory_limit=20, index=index, log=log)
    tool_executor = ToolExecutor(log=log)

    # graph
    graph = StateGraph(AgentState)
    agents = {
        'Leader': leader_agent.agent_node,
        'KG Agent': kg_agent.agent_node,
        'Validation Agent': validation_agent.agent_node,
        'Tool Executor': tool_executor.tool_node
    }
    router = {key: key for key in agents.keys()}
    router['End'] = END

    for name, node in agents.items():
        graph.add_node(name, node)
        add_conditional_edges(name, graph, router)

    graph.set_entry_point('Leader')
    compiled_graph = graph.compile()

    # invoke
    events = compiled_graph.stream(
        {
            "messages": [("human", task)]
        },
        {"recursion_limit": 50},
    )
    result = None
    for s in events:
        print(s)
        result = s
        print('---')
    return result

class result(List):
    def __init__(self, *args):
        super().__init__(*args)
    def append(self, item):
        super().append(item)
        with open("results/kgcheck/results.json", 'w') as f:
            json.dump(self, f, indent=4)
    

if __name__ == '__main__':
    os.makedirs('results/kgcheck', exist_ok=True)
    parser = argparse.ArgumentParser(description='Task KGCheck')
    parser.add_argument('--data_file', '-d', type=str, help='The path to the data file', required=True)
    parser.add_argument('--log_file', '-l', type=str, default=f'results/kgcheck', help='The path to the log file')

    args = parser.parse_args()

    # run experiments
    results = result()
    with open(args.data_file, 'r') as f:
        test = json.load(f)
    failure = []
    for index, unit in tqdm(enumerate(test), total=len(test), desc="Running experiments"):
        logger = get_logger(args.log_file, "run experiments", index=index)
        task = unit['instruction']
        try:
            res = KGCheck(task=task, index=index, log=logger)
        except Exception as e:
            logger.error(f"Task {index} Execution Failed: {e}")
            failure.append(index)
            results.append(
                {
                    "instruction": task,
                    "answer": None
                }
            )
            continue
        try:
            raw = res['Leader']['messages'][0].dict()['content']
            final_ans = json.loads(re.search(r'\{.*\}', raw, re.DOTALL).group(0))
            temp = {
                "instruction": task,
                "answer": final_ans
            }
        except Exception as e:
            logger.info(f"fail to load the JSON result for task: {task}")
            logger.debug(f"load result error: {e}")
            temp = {
                "instruction": task,
                "answer": raw
            }
        results.append(temp)

    print(f"failed to execute the following task: {', '.join(failure)}")

    # debug
    # logger = get_logger("test", index=0)
    # KGCheck(task="Please check if the 'name' attribute of the node with type Protein and id A0A6Q8PFC9 in the knowledge graph is correct. If it's correct, please respond with 'support'; if not, respond with 'refute'.", log=logger, index=0)