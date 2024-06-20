import json
import re
import argparse

def get_tool(task_type, relationship=None):
    match task_type:
        case 'node attribute':
            kg_tool = 'query_node_attribute'
            val_tool = 'get_uniprot_protein_info'
        case 'existence':
            kg_tool = 'query_node_existence'
            val_tool = 'get_uniprot_protein_info'
        case 'one-hop':
            kg_tool = 'query_relation_between_nodes'
            if relationship == 'CURATED_INTERACTS_WITH':
                val_tool = 'pub_rag'
            else:
                val_tool = 'check_interaction_string'
        case 'existing one-hop':
            kg_tool = 'query_relation_between_nodes'
            val_tool = 'pub_rag'
    return kg_tool, val_tool
    

def evaluator(his_path, golden_ans_path):
    with open(golden_ans_path, 'r', encoding='utf-8') as f:
        golden_ans = json.load(f)
    with open(his_path, 'r', encoding='utf-8') as file:
        units = file.read().strip().split('\n\n')
    
    # initialize counters
    succ_exe = len(units)
    right_ans = 0
    right_kg_tool = 0
    sleep_kg = 0
    right_val_tool = 0
    sleep_val = 0
    
    for unit, gd_unit in zip(units, golden_ans):
        lines = unit.strip().split('\n')
        task_line = lines[0]
        ins = gd_unit['instruction']
        if ins == task_line:
            # for final result
            res_line = lines[-1]
            label = gd_unit['label']
            if not "'team_leader'" in res_line:
                succ_exe -= 1
            elif label in res_line:
                right_ans += 1
            
            # tool check preparation
            task_type = gd_unit['check_type']
            if task_type == 'one-hop':
                relationship = gd_unit['graph']['relationship']
            else:
                relationship = None
            kg_tool, val_tool = get_tool(task_type, relationship)
            
            # for process evaluation
            kgtool_flag = 0
            valtool_flag = 0
            for line in lines:
                
                if not kgtool_flag:
                    if "INFO:root:{'kg_agent'" in line: # check if kg agent is invoked
                        kg_flag = 1
                        if re.search(kg_tool, line):
                            right_kg_tool += 1 # check if right kg tool is called
                            kgtool_flag = 1
                    else:
                        kg_flag = 0
                
                if not valtool_flag:
                    if "INFO:root:{'validation_agent'" in line: # check if validation agent is invoked
                        val_flag = 1
                        if re.search(val_tool, line):
                            right_val_tool += 1 # check if right val tool is called
                            valtool_flag = 1
                    else:
                        val_flag = 0
                    
                if kgtool_flag and valtool_flag:
                    break

            if not kg_flag: sleep_kg += 1
            if not val_flag: sleep_val += 1

        else:
            print(f"record missing. instruction: {ins}")
            continue
    
    # calculate metrics
    em = right_ans/len(units)
    exe = succ_exe/len(units)
    right_kg_tool_rate = right_kg_tool/len(units)
    invoked_kg_rate = (len(units) - sleep_kg)/len(units)
    right_val_tool_rate = right_val_tool/len(units)
    invoked_val_rate = (len(units) - sleep_val)/len(units)
    
    # print result
    print(f'''final result:\n 
                exact match = {em}, executability = {exe}\n
kg agent performance:\n
                right tool rate = {right_kg_tool_rate}, agent executability = {invoked_kg_rate}\n
validation agent performance:\n
                right tool rate = {right_val_tool_rate}, agent executability = {invoked_val_rate}''')

        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Task KGCheck - evaluation')
    parser.add_argument('--history_file', '-his', type=str, help='The path to the history file')
    parser.add_argument('--golden_answer_file', '-g', type=str, help='The path to the log file')

    args = parser.parse_args()

    evaluator(args.history_file, args.golden_answer_file)