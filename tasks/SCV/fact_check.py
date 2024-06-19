import argparse
# import logging
from loguru import logger as console_logger
import glob
import jsonlines
import openai
import os
from pathlib import Path
from tqdm import tqdm
from typing import cast
from typing import List, Tuple

from constant import USERNAME, PASSWORD
from constant import DOCUMENT_SET_NAME
from danswerAPI import getToken, fact_check, get_model_name
from threadpool_concurrency import run_functions_tuples_in_parallel


def th_fn(token, api_key, api_type, llm_name, log_file, querys_local, gts_local, evidences_local, pbar: tqdm):
    right_answer_local, right_quotes_local, error_answer_local, unsure_answer_local = 0, 0, 0, 0
    keyname, llm, claim = log_file.split('.jsonl')[0].split("_")[1:4]
    for index, (query, gt, ev) in enumerate(zip(querys_local, gts_local, evidences_local)):

        error_cnt = 0
        log = {"query":  query, "gt": gt, "evidence": ev}
        while 1:
            try:
                answer = fact_check(token, api_key, api_type, llm_name, query, ENDPOINT, [DOCUMENT_SET_NAME], num_hits=5, source_type=["plain_text"])
                if answer['error_msg']:
                    error_msg = answer['error_msg']
                    # console_logger.error(f"{query} {error_cnt} {error_msg}")
                    raise RuntimeError(f"{query} {error_cnt} {error_msg}")

                # if answer['answer'] not in ["SUPPORTED", "SUPPORTS", "REFUTES"]:
                #     error_msg = f"answer is not SUPPORTS or REFUTES, {answer['answer']}"
                #     raise Exception("answer is not SUPPORTS or REFUTES")
                if answer['answer'] in ["UNSURE", "UNRELATED"]:
                    unsure_answer_local += 1
                elif answer['answer'] == gt.upper() or (answer['answer'] in ["SUPPORTED", "SUPPORTS"] and gt.upper() == "SUPPORTS") or (answer in ["UNSUPPORT", "UNSUPPORTED", "UNSUPPORTS", "UNSUPPORTE", "REFUTED", "REFUTES"] and gt.upper() == "REFUTED"):
                    right_answer_local += 1

                if len([id for id in [int(doc['semantic_identifier'].split('_')[-1]) for doc in answer['quotes']] if id in ev]) > 0:
                    right_quotes_local += 1

                log.update({"answer": answer['answer'], "quotes": answer['quotes']})
                if IFLOG:
                    with open(f"answer/{log_file}", "a+", encoding="utf8") as f:
                        jsonlines.Writer(f).write(log)
                break
            except KeyboardInterrupt:
                console_logger.warning(f"right: {right_answer_local}/{index}, right quotes: {right_quotes_local}/{index}, error: {error_answer_local}/{index}, unsure: {unsure_answer_local}/{index}")
                console_logger.warning("KeyboardInterrupt")
                raise SystemExit
            except Exception as e:
                error_cnt += 1
                if error_cnt >= ERROR_RETRY_TIMES:
                    if IFLOG:
                        log.update({"error_msg": e.__str__()})
                        with open(f"answer/{log_file}", "a+", encoding="utf8") as f:
                            jsonlines.Writer(f).write(log)
                    error_answer_local += 1
                    break

        pbar.update(1)
        pbar.set_description(f"right: {right_answer_local}/{index}, right quotes: {right_quotes_local}/{index}, error: {error_answer_local}/{index}, unsure: {unsure_answer_local}/{index}")
    return index, right_answer_local, right_quotes_local, error_answer_local, unsure_answer_local


def runner(api_key, api_type, llm_name, keyname: str, log_file: str = None, querys: list = None, gts: list = None, evidences: list = None):
    console_logger.info(f"llm: {llm}, dataset: {keyname}")

    token = getToken(USERNAME, PASSWORD)

    # debug
    # querys = querys[:5]
    # gts = gts[:5]
    # evidences = evidences[:5]

    total_list = [0 for i in range(5)]

    with tqdm(total=len(querys) * RUNTIMES, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
        for i in range(RUNTIMES):
            results = run_functions_tuples_in_parallel([(th_fn, (token, api_key, api_type, llm_name, log_file, querys[i::THREAD_NUM], gts[i::THREAD_NUM], evidences[i::THREAD_NUM], pbar)) for i in range(THREAD_NUM)])
            # th_fn(querys, gts, evidences, pbar)

            slice_result_list = (sum([r[0] for r in results]), sum([r[1] for r in results]), sum([r[2] for r in results]), sum([r[3] for r in results]), sum([r[4] for r in results]))
            total_list = [total_list[i] + slice_result_list[i] for i in range(5)]

            console_logger.info(f"dataset: {keyname}, right: {slice_result_list[1]}/{slice_result_list[0]}, right quotes: {slice_result_list[2]}/{slice_result_list[0]}, error: {slice_result_list[3]}/{slice_result_list[0]}, unsure: {slice_result_list[4]}/{slice_result_list[0]}")

    console_logger.info(f"dataset: {keyname}, right: {total_list[1] / RUNTIMES}/{total_list[0] / RUNTIMES}, right quotes: {total_list[2] / RUNTIMES}/{total_list[0] / RUNTIMES}, error: {total_list[3] / RUNTIMES}/{total_list[0] / RUNTIMES}, unsure: {total_list[4] / RUNTIMES}/{total_list[0] / RUNTIMES}")


def get_data_ready(keyname: str) -> List[Tuple[str, List[str], List[str], List[str]]]:
    input_datas = []
    for file_path in glob.glob(f"benchmarkdata/{keyname}/claims*.jsonl"):
        claim = Path(file_path).stem
        log_file = f"answer_{keyname}_{llm}_{claim}.jsonl"
        with open(file_path, "r+", encoding="utf8") as f:
            datas = [data for data in jsonlines.Reader(f)]
            input_datas.append((log_file, [data['claim'] for data in datas], [data['verdict'] for data in datas], [data['evidence'] for data in datas]))
                
        console_logger.info(f"claim file: {claim}, querys: {len(datas)}")

    return input_datas


if __name__ == "__main__":
    THREAD_NUM = 6
    RUNTIMES = 3
    ERROR_RETRY_TIMES = 3
    SERVERS = ["http://10.0.1.194:7010", "http://172.16.55.223:7010", "http://172.16.55.82:7011", "http://172.16.55.82:7012"]
    MODEL_DICT = {
        "local": ["local"],
        "openai": ["gpt-3.5-turbo", "gpt-4-turbo"],
        "qwen":["qwen-turbo", "qwen-plus", "qwen-max"],
        "zhipu":["glm-3", "glm-4"],
    }
    KEYNAMES = ["scifact", "pubmedqa2claim"]
    # KEYNAMES = ["scifact"]
    # KEYNAMES = ["pubmedqa2claim"]
    # KEYNAMES = ["ckg_ppi"]

    possible_models = []
    [possible_models.extend(v) for v in MODEL_DICT.values()]
        

    parser = argparse.ArgumentParser()
    parser.add_argument("--server", "-s", type=int, default=0, help="Server index to run the demo on.", choices=list(range(len(SERVERS))))
    parser.add_argument("--log", action="store_true", help="Log the answer.")
    parser.add_argument("--key", "-k", type=str, default="sk-cariri", help="API key to use.")
    parser.add_argument("--model", "-m", type=str, default="local", help="Model name to use.", choices=possible_models)

    args = parser.parse_args()

    IFLOG = args.log
    API_KEY = args.key
    
    # web_types = {
    #         "google": False,
    #         "pubmed": False,
    #         "arxiv": False
    #     }
    # source_type = [k for k, v in web_types.items() if v is True]
    # if quote_from_file is True or len(source_type) == 0:
    #     source_type.append('file')
    # source_type.append('plain_text')


    os.makedirs("answer", exist_ok=True)
    if args.model == "local":
        ENDPOINT = SERVERS[args.server]
        llm = get_model_name(ENDPOINT)
        api_type = "local"
    else:
        ENDPOINT = f"https://api.openai.com/v1"
        llm = args.model
        api_type = [k for k, v in MODEL_DICT.items() if args.model in v][0]

    # print(f"llm: {llm}, model_type: {model_type}, endpoint: {ENDPOINT}")
    for keyname in KEYNAMES:
        inputs = get_data_ready(keyname)
        for input_data in inputs:
            log_file, querys, gts, evidences = input_data
            runner(API_KEY, api_type, llm, keyname, log_file, querys, gts, evidences)
