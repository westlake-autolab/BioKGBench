from glob import glob
import jsonlines
from loguru import logger as logging
import numpy as np
import os
from pathlib import Path

from ...configs.constant import REFUTES_OPTION, SUPPORTS_OPTION, UNSURE_OPTION


claim = "claims"

def analysis_task2(keyname, llm, filter):
    index_slice, right_answer_slice, right_quotes_slice, not_sure_slice, error_answer_slice = 0, 0, 0, 0, 0
    with open(f'answer/answer_{keyname}_{llm}_{filter}_{claim}.jsonl') as f1:
        for data in jsonlines.Reader(f1):
            index_slice += 1

            try:
                gt = data['gt']
                answer = data['answer']
                ev = data['evidence']
                if answer in ["UNSURE", "UNRELATED"]:
                    not_sure_slice += 1
                    continue
                if answer == gt.upper() or (answer in SUPPORTS_OPTION and gt.upper() == "SUPPORTS") or (answer in REFUTES_OPTION and gt.upper() == "REFUTED"):
                    right_answer_slice += 1
                # quotes_id = [int(quote['semantic_identifier'].split('_')[1]) for quote in data['quotes']]
                quotes_id = [quote['semantic_identifier'] for quote in data['quotes']]
                if len([id for id in quotes_id if id in ev]) > 0:
                    right_quotes_slice += 1

            except Exception as e:
                error_answer_slice += 1
                continue

    logging.info(f"keyname: {keyname}, llm: {llm}, filter: {filter}")
    logging.info(f"right: {right_answer_slice / 3}/{index_slice / 3}, right quotes: {right_quotes_slice / 3}/{index_slice / 3}, error: {error_answer_slice / 3}/{index_slice / 3}, not sure: {not_sure_slice / 3}/{index_slice / 3}")


def get_task3_result_simple():
    if not os.path.exists('./answer/task3/task3_simple.jsonl'):
        logging.warning("task3_simple.jsonl not existed, create it")
        with open('./answer/task3/task3_data_check_Meta-Llama-3-70B-Instruct_all.jsonl') as f:
            result_all = {data['claim']: data['answer'] for data in jsonlines.Reader(f) if "error_msg" not in data.keys()}
        with open('./answer/task3/task3_data_check_Meta-Llama-3-70B-Instruct_ckg.jsonl') as f:
            result_ckg = {data['claim']: data['answer'] for data in jsonlines.Reader(f) if "error_msg" not in data.keys()}

        keys = []
        for k in result_all.keys():
            if k not in result_ckg.keys():
                keys.append(k)
        for k in keys:
            del result_all[k]
        keys.clear()
        for k in result_ckg.keys():
            if k not in result_all.keys():
                keys.append(k)
        for k in keys:
            del result_ckg[k]

        def orgnize_result(result: dict):
            for k, v in result.items():
                if v in SUPPORTS_OPTION:
                    result[k] = "SUPPORTS"
                elif v in REFUTES_OPTION:
                    result[k] = "REFUTES"
                elif v in UNSURE_OPTION:
                    result[k] = "UNSURE"
            return result

        result_all = orgnize_result(result_all)
        result_ckg = orgnize_result(result_ckg)

        with open('./answer/task3/task3_simple.jsonl', 'w') as f:
            jsonlines.Writer(f).write_all([{"claim": k, "answer_all": v, "answer_ckg": result_ckg[k]} for k, v in result_all.items()])

    else:
        logging.warning("task3_simple.jsonl existed, read it")
        with open('./answer/task3/task3_simple.jsonl') as f:
            datas = [data for data in jsonlines.Reader(f)]
            result_ckg = [{"claim": data['claim'], "answer": data['answer_ckg']} for data in datas]
            result_all = [{"claim": data['claim'], "answer": data['answer_all']} for data in datas]

    return result_all, result_ckg

def get_task3_result_with_quotes():
    if not os.path.exists('./answer/task3/task3_with_quote.jsonl'):
        logging.warning("task3_with_quote.jsonl not existed, create it")
        with open('./answer/task3/task3_data_check_Meta-Llama-3-70B-Instruct_all.jsonl') as f:
            result_all = [{"claim": data['claim'], "answer": data['answer'], "quotes": [{quote['document_id']: quote['quote']} for quote in data['quotes']]} for data in jsonlines.Reader(f) if "error_msg" not in data.keys()]
        with open('./answer/task3/task3_data_check_Meta-Llama-3-70B-Instruct_ckg.jsonl') as f:
            result_ckg = [{"claim": data['claim'], "answer": data['answer'], "quotes": [{quote['document_id']: quote['quote']} for quote in data['quotes']]} for data in jsonlines.Reader(f) if "error_msg" not in data.keys()]


        keys_all = []
        for idx, k in enumerate(result_all):
            if k["claim"] not in [claim['claim'] for claim in result_ckg]:
                keys_all.append(idx)
        keys_ckg = []
        for idx, k in enumerate(result_ckg):
            if k['claim'] not in [claim['claim'] for claim in result_all]:
                keys_ckg.append(idx)

        [result_all.pop(k) for k in keys_all]
        [result_ckg.pop(k) for k in keys_ckg]
        # print(len(keys))

        def orgnize_result(result):
            for item in result:
                if item["answer"] in SUPPORTS_OPTION:
                    item["answer"] = "SUPPORTS"
                elif item["answer"] in REFUTES_OPTION:
                    item["answer"] = "REFUTES"
                elif item["answer"] in UNSURE_OPTION:
                    item["answer"] = "UNSURE"
            return result

        result_all = orgnize_result(result_all)
        result_ckg = orgnize_result(result_ckg)

        result_all.sort(key=lambda x: x["claim"])
        result_ckg.sort(key=lambda x: x["claim"])

        with open('./answer/task3/task3_with_quote.jsonl', 'w') as f:
            jsonlines.Writer(f).write_all([{"claim": k["claim"], "answer_all": k["answer"], "answer_ckg": result_ckg[idx]["answer"], "quotes_all": k["quotes"], "quotes_ckg": result_ckg[idx]['quotes']} for idx, k in enumerate(result_all)])

    else:
        logging.warning("task3_with_quote.jsonl existed, read it")
        with open('./answer/task3/task3_with_quote.jsonl') as f:
            datas = [data for data in jsonlines.Reader(f)]
            result_all = [{"claim": data['claim'], "answer": data['answer_all'], "quotes": data['quotes_all']} for data in datas]
            result_ckg = [{"claim": data['claim'], "answer": data['answer_ckg'], "quotes": data['quotes_ckg']} for data in datas]

    return result_all, result_ckg


def task3_compare_result(result_all: dict, result_ckg: dict):
    same_sup, same_unsup, same_unsure, diff_sup, diff_unsup, unsure_sup, unsure_diff, error = 0, 0, 0, 0, 0, 0, 0, 0
    for k, v in result_ckg.items():
        try:
            if result_all[k] == "SUPPORTS" and result_ckg[k] == "SUPPORTS":
                same_sup += 1
            elif result_all[k] == "REFUTES" and result_ckg[k] == "REFUTES":
                same_unsup += 1
            elif result_all[k] == "UNSURE" and result_ckg[k] == "UNSURE":
                same_unsure += 1
            elif result_all[k] == "SUPPORTS" and result_ckg[k] == "REFUTES":
                diff_sup += 1
            elif result_all[k] == "REFUTES" and result_ckg[k] == "SUPPORTS":
                diff_unsup += 1
            elif result_all[k] in ["SUPPORTS", "REFUTES"] and result_ckg[k] == "UNSURE":
                unsure_sup += 1
            elif result_all[k] == "UNSURE" and result_ckg[k] in ["SUPPORTS", "REFUTES"]:
                unsure_diff += 1
            else:
                print(k, result_all[k], result_ckg[k])
            # if 
            # result_all[k] != result_ckg[k] == :
            #     different += 1
            #     # print(k, result_all[k], result_ckg[k])
            # else:
            #     same += 1
        except:
            error += 1
        
    logging.info(f"same support: {same_sup}, same refutes: {same_unsup}, same unsure: {same_unsure}, ref-sup: {diff_sup}, sup-ref: {diff_unsup}, unsure-sup/ref: {unsure_sup}, sup/ref-unsure: {unsure_diff}, error: {error}")


def task3_analysis_result(result: dict, file_name: str, k_keyname: str="is associated", v_keyname: str="SUPPORTS"):
    if file_name.endswith("quotes"):
        records = [{record['claim']: record[f'answer'], "quotes": record[f'quotes']} for record in result if k_keyname in record['claim'] and record['answer'] == v_keyname]
    else:
        records = [{record['claim']: record[f'answer']} for record in result if k_keyname in record['claim'] and record['answer'] == v_keyname]
    
    logging.info(f"keyname: {v_keyname}, {k_keyname}: {len(records)}")

    with open(f'./answer/task3/seperate/{file_name}_{v_keyname}_{k_keyname}.jsonl', 'w') as f:
        jsonlines.Writer(f).write_all(records)

    # return records


if __name__ == "__main__":
    # keyname = "pubmedqa2claim"
    # keyname = "scifact"
    # llm = "Qwen1.5-72B-Chat"
    # llm = "Meta-Llama-3-70B-Instruct"
    # filter = "all"
    # filter = "partial"
    # filter = "match"

    for keyname in ["pubmedqa2claim", "scifact"]:
        for filter in ["all", "partial", "match"]:
            for llm in ["Meta-Llama-3-70B-Instruct", "Qwen1.5-72B-Chat"]:
                analysis_task2(keyname, llm, filter)
    # result_all, result_ckg = get_task3_result_simple()
    # # task3_compare_result(result_all, result_ckg)
    # for k_keyname in ["is associated", "not associated", "interacts with", "acts on"]:
    #     for v_keyname in ["SUPPORTS", "REFUTES", "UNSURE"]:
    #         not_associated_all = task3_analysis_result(result_ckg, "all", k_keyname, v_keyname)
    #         not_associated_ckg = task3_analysis_result(result_all, "ckg", k_keyname, v_keyname)
    
    # result_all, result_ckg = get_task3_result_with_quotes()
    # for k_keyname in ["is associated", "not associated", "interacts with", "acts on"]:
    #     for v_keyname in ["SUPPORTS", "REFUTES", "UNSURE"]:
    #         not_associated_all = task3_analysis_result(result_ckg, "all_with_quotes", k_keyname, v_keyname)
    #         not_associated_ckg = task3_analysis_result(result_all, "ckg_with_quotes", k_keyname, v_keyname)
