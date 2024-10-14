import json
import re
import argparse


def check_answer_format(result_path):
    with open(result_path, 'r') as f:
        res = json.load(f)
    failed = []
    conclusion_pattern = r'["\']conclusion["\']:\s*["\']([^"\']*)["\']'
    reason_pattern = r'["\']reason["\']:\s*["\']([^"\']*)["\']'
    for r in res:
        if not isinstance(r['answer'], dict):
            text = r['answer']
            conclusion_match = re.search(conclusion_pattern, text)
            reason_match = re.search(reason_pattern, text)

            if conclusion_match and reason_match:
                conclusion = conclusion_match.group(1)
                reason = reason_match.group(1)
                if not conclusion in ["support", "refute"]:
                    failed.append(r)
                    print(f"failed to update:\n{r}")
                    continue    
                new_ans = {
                    "conclusion": conclusion,
                    "reason": reason
                }
                print(f"successfully update:\n{r}\nupdate result: {new_ans}")
                r['answer'] = new_ans
            else:
                print(f"failed to update:\n{r}")
                failed.append(r)
    print("--------------------------")
    print("FAILED:")
    print(failed)
    with open(result_path, 'w') as f:
        json.dump(res, f, indent=4)
        
def judge_conclusion(golden_ans_path, result_path):
    with open(result_path, 'r') as f:
        answer = json.load(f)
    with open(golden_ans_path, 'r') as f:
        golden_answer = json.load(f)
    
    '''
    result unit:
    {
        "instruction": "Please check if the 'name' attribute of the node with type Protein and id Q4G0T1 in the knowledge graph is correct. If it's correct, please respond with 'support'; if not, respond with 'refute'.",
        "answer": {
            "conclusion": "support",
            "reason": "The name attribute 'SCART1' of the Protein node with ID Q4G0T1 in the knowledge graph matches the validated name from the UniProt database."
        }
    }
    
    golden answer unit:
    {
        "check_type": "node attribute",
        "graph": {
            "accession": "A0A2R8Y4M2_HUMAN",
            "id": "A0A2R8Y4M2",
            "synonyms": [
                "A0A2R8Y4M2_HUMAN",
                "ENSG00000284934"
            ],
            "taxid": "9606"
        },
        "instruction": "Please check if the 'name' attribute of the node with type Protein and id A0A2R8Y4M2 in the knowledge graph is correct. If it's correct, please respond with 'support'; if not, respond with 'refute'.",
        "evidence": "Missing name: 'LOC128125816'.",
        "label": "refute"
    }
    '''
    total_num = len(answer)
    em_num = 0
    sucess_exe_num = total_num
    for i in range(total_num):
        question = answer[i]['instruction']
        instruction = golden_answer[i]['instruction']
        if question==instruction:
            ans = answer[i]['answer']['conclusion']
            gdans = golden_answer[i]['label']
            if ans == gdans:
                em_num += 1
            else:
                if not ans:
                    sucess_exe_num -= 1
    
    em_rate = em_num / total_num
    exe_rate = sucess_exe_num / total_num
    print(f"EM = {em_rate}, Executability = {exe_rate}")

        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Task KGCheck - evaluation')
    parser.add_argument('--result_file', '-res', type=str, help='The path to the result file')
    parser.add_argument('--golden_answer_file', '-g', type=str, help='The path to the golden answer file')

    args = parser.parse_args()

    check_answer_format(args.result_file)
    judge_conclusion(args.golden_answer_file, args.result_file)