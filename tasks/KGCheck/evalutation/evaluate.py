import json
import re

his_path=''
golden_ans_path=''
res_path=''

def final_grader(his_path, golden_ans_path, res_path):
    right_ans = 0
    ans = []
    token_induced = 0
    with open(his_path, 'r', encoding='utf-8') as file:
        units = file.read().strip().split('\n\n')
    for unit in units:
        lines = unit.strip().split('\n')
        first_line = lines[0]
        last_line = lines[-1]
        ans.append({'task': first_line, 'ans': last_line})
    print(len(ans))
    with open(golden_ans_path, 'r', encoding='utf-8') as f:
        golden_ans = json.load(f)
    if len(golden_ans) == len(ans):
        succ_exe = len(ans)
        for i in range(0, len(golden_ans)):
            if golden_ans[i]['label'] in ans[i]['ans']:
                right_ans += 1
            elif not "'team_leader'" in ans[i]['ans']:
                succ_exe -= 1
                if "Bad Request" in ans[i]['ans']:
                    token_induced += 1
    else:
        temp = 0
        miss = []
        for i in ans:
            if i['task'] == golden_ans[temp]['instruction']:
                temp+=1
            else:
                miss.append(temp)
                temp+=1
        print("something wrong.") 
        print(temp)
        print(miss)
        return
    em = right_ans/len(ans)
    exe = succ_exe/len(ans)
    tk = token_induced/len(ans)
    with open(res_path, 'w') as ff:
        ff.write(f"EM = {em}, executability = {exe}, token_induced_err = {tk}")
        
def process_kg(his_path, task_tool, res_path):
    right_kg_tool = 0
    sleep_kg = 0
    with open(his_path, 'r', encoding='utf-8') as file:
        units = file.read().strip().split('\n\n')
    for unit in units:
        lines = unit.strip().split('\n')
        kg_flag = 1
        for line in lines:
            if "INFO:root:{'kg_agent'" in line:
                kg_flag = 1
                if re.search(task_tool, line):
                    right_kg_tool += 1
                    break
            else:
                kg_flag = 0
        if not kg_flag: sleep_kg += 1
    right_tool_rate = right_kg_tool/len(units)
    sleep_kg_rate = sleep_kg/len(units)
    with open(res_path, 'w') as f:
        f.write(f"right_tool_rate = {right_tool_rate}, sleep_kg_rate = {sleep_kg_rate}")
    
def procee_val(his_path, task_tool, res_path):
    right_val_tool = 0
    sleep_val = 0
    with open(his_path, 'r', encoding='utf-8') as file:
        units = file.read().strip().split('\n\n')
    for unit in units:
        lines = unit.strip().split('\n')
        val_flag = 1
        for line in lines:
            if "INFO:root:{'validation_agent'" in line:
                val_flag = 1
                if re.search(task_tool, line):
                    right_val_tool += 1
                    break
            else:
                val_flag = 0
        if not val_flag: sleep_val += 1
    right_tool_rate = right_val_tool/len(units)
    sleep_val_rate = sleep_val/len(units)
    with open(res_path, 'w') as f:
        f.write(f"right_tool_rate = {right_tool_rate}, sleep_val_rate = {sleep_val_rate}")
    
        
if __name__ == '__main__':
    final_grader(his_path, golden_ans_path, res_path)
    # process_kg(his_path, 'query_node_attribute', res_path)
    # procee_val(his_path, 'get_uniprot_protein_info', res_path)