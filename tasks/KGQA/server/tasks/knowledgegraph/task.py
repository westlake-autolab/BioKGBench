import ast
import sys
import re
import json
from typing import List, Tuple, Dict, Any

from .api import *
from ...task import Task, Session
from ....typings import TaskSampleExecutionResult, TaskOutput, SampleIndex, AgentOutputStatus, SampleStatus
from ....utils import ColorMessage


def extract_params(data, function_name):
    pattern = re.compile(r'\b' + re.escape(function_name) + r'\((.*?)\)', re.DOTALL)
    match = pattern.search(data)
    if not match:
        return "Function call not found."

    # 从函数名后的第一个左括号开始
    params_str = match.group(1)
    params = []
    depth = 0
    start = 0
    print(params_str)
    for i, char in enumerate(params_str):
        if char == '(':
            if depth == 0:
                start = i + 1
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                # 我们找到了一个顶层参数
                params.append(params_str[start:i])
                start = i + 1
        elif char == ',' and depth == 0:
            # 如果我们在顶层遇到逗号，那么之前的参数已经结束
            if start != i:
                params.append(params_str[start:i])
            start = i + 1

    try:
        # 直接解析params_str，因为它已经是一个列表格式的字符串
        params = ast.literal_eval(params_str)
        if isinstance(params, list):
            params = [params]
        return list(params)
        # return list(params)
    except Exception as e:
        # 如果解析失败，尝试将参数字符串转换为一个完整的列表
        try:
            params = ast.literal_eval(f"[{params_str}]")
            if isinstance(params, list):
                params = [params]
            return list(params)
        except Exception as e:
            return f"Error parsing parameters: {e}"
        


INSTRUCTIONS = """
You are an agent tasked with answering questions based on the knowledge stored in a knowledge graph (KG) related to proteomics. To accomplish this, you are equipped with the following tools to query the KG:

get_relations_by_ids_agent(entity_ids: List[str]) -> tuple
Retrieves the relationships of multiple entities in a knowledge graph, categorized as 'incoming' or 'outgoing'.
Use case: get_relations_by_ids_agent(['P123', 'P456']) to find all relations connected to the entities with IDs 'P123' and 'P456'.

get_neighbor_type_agent(entity_ids: List[str], relation: str, direction: str) -> tuple
Retrieves the types of neighboring nodes for multiple entities in a knowledge graph based on specified relationships and directions.
Use case: get_neighbor_type_agent(['P123', 'P456'], 'ASSOCIATED_WITH', 'outgoing') to get outgoing neighbors' types associated with the entities 'P123' and 'P456'.

get_neighbor_with_type_agent(entity_ids: List[str], relation: str, direction: str, neighbor_type: str) -> tuple
Retrieves the neighbors of multiple entities in a knowledge graph based on a specific relationship, direction, and type.
Use case: get_neighbor_with_type_agent(['P123', 'P456'], 'ASSOCIATED_WITH', 'outgoing', 'Disease') to get attributes and detailed information of outgoing neighbors associated with the entities 'P123' and 'P456', where the type of neighbors is Disease.

get_intersection_agent(*args: List[str]) -> tuple
Calculates the intersection of multiple lists, returning elements common to all lists.
Use case: get_intersection_agent(['P123', 'P456'], ['P456', 'P789']) to find common entities.

get_union_agent(*args: List[str]) -> tuple
Calculates the union of multiple lists, returning all unique elements from all lists.
Use case: get_union_agent(['P123', 'P456'], ['P456', 'P789']) to combine unique entities.

Single Action Rule: Execute only ONE action at a time, that is, only the first action would be executed. After receiving the observation from its execution, you may proceed with another action. 

Action Limit: You can take at most 15 actions to find the answer to the question.

Objective: Use these tools effectively to navigate through the KG and gather the necessary information to answer the queries presented to you. If the query is about the protein sequence, you need to return the specific sequence. If the query is about the protein structure, you can return a link. In other cases, it's usually to return the name.

Notice: 
1. Please remember to format the FINAL answer as a JSON object, such as, {"Answer": ["RND2", "RHOBTB2", "RHOA"]}. The value of "Answer" must be a list. Only output the JSON format when answering the final answer.
2. Please be flexible. Due to the diversity of question formulations, you need to find the most similar relationship in the knowledge graph (KG) to the one asked in the question for querying.
"""



ONE_SHOT = [
    """Question: What biological processes are associated with the protein encoded by the gene GOLT1A?""",
    """Thought: I need to figure out what proteins are encoded by gene GOLT1A and then find out the biological processes. Firstly, I need to find out the relations of the gene node.
Action: get_relations_by_ids_agent(['GOLT1A'])""",
    """Observation: {"GOLT1A": {"Incoming": null, "Outgoing": "TRANSLATED_INTO"}}""",
    """Thought: The outgoing relation 'TRANSLATED_INTO' is what I concern, and next I need to get neighbor type with the relation. 
Action: get_neighbor_type_agent(['GOLT1A'], 'TRANSLATED_INTO', 'outgoing')""",
    """Observation: {"GOLT1A": {"NeighborTypes": ["Protein"]}}""",
    """Thought: Among the neighbor type, 'Protein' is my concern. So next I should look for what are the neighboring nodes with 'Protein' type that point outward along the edge of the relation 'TRANSLATED_INTO'. 
Action: get_neighbor_with_type_agent(['GOLT1A'], 'TRANSLATED_INTO', 'outgoing', 'Protein')""",
    """Observation: {"GOLT1A": {"TRANSLATED_INTO": ["Q6ZVE7"]}}""",
    """Thought: Now I know that the proteins are ["Q6ZVE7"]. Now I will find out the relation to choose for the next step. 
Action: get_relations_by_ids_agent(["Q6ZVE7"])""",
    """Observation: Observation: {"Q6ZVE7": {"Incoming": "TRANSLATED_INTO, HAS_SEQUENCE, ACTS_ON", "Outgoing": "HAS_SEQUENCE, ASSOCIATED_WITH"}}""",
    """Thought: The outgoing relation 'ASSOCIATED_WITH' is exactly what I concern. Then I'll query the neighbor type with the relation.
Action: get_neighbor_type_agent(["Q6ZVE7"], 'ASSOCIATED_WITH', 'outgoing')""",
    """'Observation: {"Q6ZVE7": {"NeighborTypes": ["Tissue", "Molecular_function", "Biological_process", "Cellular_component", "Disease"]}}""",
    """Thought: Among the neighbor types, 'Biological_process' is what I need to query.
Action: get_neighbor_with_type_agent(["Q6ZVE7"], 'ASSOCIATED_WITH', 'outgoing', 'Biological_process')""",
    """Observation: {"Q6ZVE7": {"ASSOCIATED_WITH": ["endoplasmic reticulum to Golgi vesicle-mediated transport", "biological_process", "protein transport", "retrograde transport, endosome to Golgi"]}}""",
    """Thought: I have identified the answers. Final Answer: {"Answer": ["endoplasmic reticulum to Golgi vesicle-mediated transport", "biological_process", "protein transport", "retrograde transport, endosome to Golgi"]}"""
]

# TODO: the format of data_file ref to agentbench
class KnowledgeGraph(Task):
    def __init__(self, data_file, round=15, **config):
        super().__init__(**config)
        self.round = round
        self.data_file = data_file
        self.data: List[Tuple[dict, set]] = []
        self.inputs: List[dict] = []
        self.targets: List[set] = []
        with open(self.data_file, "r") as f:
            data_object = json.load(f)
        for item in data_object:
            answer = item.pop("answer")
            gold_answer = set()
            for a in answer:
                gold_answer.add(a["answer"])  
            self.data.append((item, gold_answer)) # input and target
            self.inputs.append(item)
            self.targets.append(gold_answer)

    def calculate_overall(self, results: List[TaskOutput]) -> Dict[str, Any]:
        '''evaluate the result with 3 metircs: F1, EM (exact match), executability (whether find the answer successfully)'''
        outputs = [None for _ in range(len(self.data))]
        for result in results:
            outputs[result.index] = result.result
        targets = self.targets

        def F1():
            F1_sum = 0
            for i in range(len(outputs)):
                if not isinstance(outputs[i], dict):
                    continue
                predicted_answer = set(outputs[i]['predict'])
                gold_answer = targets[i]
                TP = len(gold_answer.intersection(predicted_answer))
                FP = len(predicted_answer) - TP
                FN = len(gold_answer) - TP
                if TP == 0:
                    continue
                precision = TP / (TP + FP)
                recall = TP / (TP + FN)
                F1 = 2 * precision * recall / (precision + recall)
                F1_sum += F1
            return F1_sum / len(outputs)

        def EM():
            em_sum = 0
            for i in range(len(outputs)):
                if not isinstance(outputs[i], dict):
                    continue
                predicted_answer = set(outputs[i]['predict'])
                gold_answer = targets[i]
                if len(gold_answer.intersection(predicted_answer))==len(gold_answer) and len(gold_answer)==len(predicted_answer):
                    em_sum += 1
            return em_sum / len(outputs)

        def executability():
            executability_sum = 0
            for i in range(len(outputs)):
                if not isinstance(outputs[i], dict):
                    continue
                if outputs[i]['predict'] is not None and len(outputs[i]['predict'])>0:
                    executability_sum += 1
            return executability_sum / len(outputs)

        return{
            "main": F1(),  
            "F1": F1(),
            "EM": EM(),
            "executability": executability(),
        }
    
    def get_indices(self) -> List[SampleIndex]:
        return list(range(len(self.data)))
    

    async def start_sample(self, index: SampleIndex, session: Session) -> TaskSampleExecutionResult:
        '''run the KG task'''
        # TODO: complete this function
        data = self.inputs[index]
        answer = []
        actions = []
        variables_list = []

        question = data["question"]
        # entities = data["entities"]

        session.inject({
            "role": "user",
            "content": INSTRUCTIONS
        })
        session.inject({"role": "agent", "content": "I've understood your instruction, start please."})
        for idx, shot in enumerate(ONE_SHOT):
            if idx % 2 == 0:
                session.inject({"role": "user", "content": shot})
            else:
                session.inject({"role": "agent", "content": shot})
        session.inject({"role": "user", "content": "A new question: " + question})

        finish_reason = SampleStatus.COMPLETED
        for i in range(self.round):
            message = await session.action()
            if message.status == AgentOutputStatus.AGENT_CONTEXT_LIMIT:
                return TaskSampleExecutionResult(status=SampleStatus.AGENT_CONTEXT_LIMIT)
            elif message.status != AgentOutputStatus.NORMAL:
                return TaskSampleExecutionResult(status=SampleStatus.UNKNOWN)
            message = message.content
            message = message.split("Observation:")[0]
            message = message.replace("\\_", "_")  # not clear about this
            session.history[-1].content = message
            final_answer = re.findall(r'\{"Answer":.*?\}', message)

            if final_answer:
                answer = eval(final_answer[0])["Answer"]
                if isinstance(answer, str):
                    answer = [answer]
                print(answer)
                break

            else:
                lines = [' '.join(message.split("\n"))]
                find_action = False
                for line in lines:
                    execution_message = "Function is not executed!"
                    # if re.match(r"Action.*?:", line):
                    find_action = True
                    function_names = re.findall(r'(\w+)\(', line)
                    function_executed = False
                    for function_name in function_names:
                        print(function_name)
                        try:
                            func = getattr(sys.modules[__name__], function_name)
                            arguments = extract_params(line, function_name)
                            ori_arguments = [str(argument) for argument in arguments]
                            # # process the arguments
                            # for i, argument in enumerate(arguments): 
                            #     argument = argument.replace("variable ", "")  # not clear about this
                            #     argument = argument.replace("Variable ", "")

                            #     if argument.startswith("#"):
                            #         # replace the variable with the actual value
                            #         arguments[i] = variables_list[int(argument[1:])]   # not clear about this, where variables_list is given value?
                            #     elif argument in entities:
                            #         arguments[i] = entities[argument]                                       
                            execution, execution_message = func(*arguments)
                            actions.append(f"{function_name}({', '.join(ori_arguments)})")
                            session.inject({"role": "user", "content": execution_message})
                            function_executed = True
                            break # at most one function is executed in one turn
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            try:
                                execution_message = f"{function_name}({', '.join(ori_arguments)}) cannot be executed: {e}"
                                # if function_name != "intersection":
                                #     execution_message = f"{function_name}({', '.join(ori_arguments)}) cannot be executed. You may make a mistake and need to fix it."
                                # else: # not clear about the following execution_message, why "the two variables"?
                                #     execution_message = f"{function_name}({', '.join(ori_arguments)}) cannot be executed. The two variables are not of the same type. You may further explore them by call get_relations"
                            except UnboundLocalError:
                                execution_message = f"I may make a syntax error when calling {function_name} (e.g., unmatched parenthesis). I need to fix it and reuse the tool"
                            continue
                    if not function_executed:
                        session.inject({"role": "user", "content": execution_message})
                    break # should at most be one line starts with Action

                if not find_action:
                    session.inject({"role": "user", "content": "No executable function found! Need to recheck the action."})
        else:
            finish_reason = SampleStatus.TASK_LIMIT_REACHED

        return TaskSampleExecutionResult(status=finish_reason, result={"predict": answer, "actions":actions})
    

if __name__ == "__main__":
    data: List[Tuple[dict, set]] = []
    inputs: List[dict] = []
    targets: List[set] = []
    data_file = "data/knowledgegraph/std.json"
    with open(data_file, "r") as f:
        data_object = json.load(f)
    for item in data_object:
        answer = item.pop("answer")
        gold_answer = set()
        for a in answer:
            gold_answer.add(a["answer_id"])  # compare the id of entity during evaluation
        data.append((item, gold_answer)) # input and target
        inputs.append(item)
        targets.append(gold_answer)
    print("data: ", data)
    print("inputs: ", inputs)
    print("targets: ", targets)
