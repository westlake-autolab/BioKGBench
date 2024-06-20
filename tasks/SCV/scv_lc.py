import argparse
from langchain_core.vectorstores import VectorStoreRetriever
from loguru import logger as console_logger
from datetime import datetime
import jsonlines
import os
from pathlib import Path
from tqdm import tqdm
from typing import cast
from typing import List, Tuple
import yaml

from .rag import get_chain, get_retriever
from ..utils.constant_ import SUPPORTS_OPTION, UNSURE_OPTION, REFUTES_OPTION
from ..utils.threadpool_concurrency_ import run_functions_tuples_in_parallel


RUNTIMES = 3
ERROR_RETRY_TIMES = 3
    
def th_fn(log_file, retriever: VectorStoreRetriever, querys_local, gts_local, evidences_local, pbar: tqdm):
    right_answer_local, right_quotes_local, error_answer_local, unsure_answer_local = 0, 0, 0, 0
    for index, (query, gt, ev) in enumerate(zip(querys_local, gts_local, evidences_local)):

        error_cnt = 0
        log = {"query":  query, "gt": gt, "evidence": ev}
        while 1:
            try:
                answer = {'answer': "", "error_msg": None}
                for piece in get_chain(query, retriever).stream(query):
                    if piece is not None and "answer_piece" in piece and piece['answer_piece'] is not None:
                        answer['answer'] += piece['answer_piece']
                    if piece is not None and "quotes" in piece:
                        answer['quotes'] = piece['quotes']

                if answer['error_msg']:
                    error_msg = answer['error_msg']
                    raise RuntimeError(f"{query} {error_cnt} {error_msg}")

                if answer['answer'] in UNSURE_OPTION:
                    unsure_answer_local += 1
                elif answer['answer'] == gt.upper() or (answer['answer'] in SUPPORTS_OPTION and gt.upper() == "SUPPORTS") or (answer in REFUTES_OPTION and gt.upper() == "REFUTED"):
                    right_answer_local += 1

                if len([id for id in [doc['semantic_identifier'] for doc in answer['quotes']] if id in ev]) > 0:
                    right_quotes_local += 1

                log.update({"answer": answer['answer'], "quotes": answer['quotes']})
                with open(log_file, "a+", encoding="utf8") as f:
                    jsonlines.Writer(f).write(log)
                break
            except Exception as e:
                error_cnt += 1
                if error_cnt >= ERROR_RETRY_TIMES:
                    log.update({"error_msg": e.__str__()})
                    with open(log_file, "a+", encoding="utf8") as f:
                        jsonlines.Writer(f).write(log)
                    error_answer_local += 1
                    break

        pbar.update(1)
        pbar.set_description(f"right: {right_answer_local}/{index}, right quotes: {right_quotes_local}/{index}, error: {error_answer_local}/{index}, unsure: {unsure_answer_local}/{index}")
    return index + 1, right_answer_local, right_quotes_local, error_answer_local, unsure_answer_local


def runner(log_file: str = None, retriever: VectorStoreRetriever=None, querys: list = None, gts: list = None, evidences: list = None):
    total_list = [0 for i in range(5)]

    with tqdm(total=len(querys) * RUNTIMES, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
        for i in range(RUNTIMES):
            results = run_functions_tuples_in_parallel([(th_fn, (log_file, retriever, querys[i::args.threads], gts[i::args.threads], evidences[i::args.threads], pbar)) for i in range(args.threads)])

            slice_result_list = (sum([r[0] for r in results]), sum([r[1] for r in results]), sum([r[2] for r in results]), sum([r[3] for r in results]), sum([r[4] for r in results]))
            total_list = [total_list[i] + slice_result_list[i] for i in range(5)]

    console_logger.info(f"right: {total_list[1] / RUNTIMES}/{total_list[0] / RUNTIMES}, right quotes: {total_list[2] / RUNTIMES}/{total_list[0] / RUNTIMES}, error: {total_list[3] / RUNTIMES}/{total_list[0] / RUNTIMES}, unsure: {total_list[4] / RUNTIMES}/{total_list[0] / RUNTIMES}")


def get_data_ready(time_stamp: str) -> List[Tuple[str, List[str], List[str], List[str]]]:
    claim = Path(args.data_path).stem
    log_file = os.path.join("results/svc", f"{claim}_{time_stamp}_answer_{llm}.jsonl")
    with open(args.data_path, "r+", encoding="utf8") as f:
        datas = [data for data in jsonlines.Reader(f)]
            
    console_logger.info(f"claim file: {claim}, querys: {len(datas)}")

    return log_file, [data['claim'] for data in datas], [data['verdict'] for data in datas], [data['evidence'] for data in datas]


if __name__ == "__main__":

    os.makedirs("results/svc", exist_ok=True)

    parser = argparse.ArgumentParser(description="Task SCV")
    parser.add_argument("--data_path", "-d", type=str, help="The path to the data file", required=True)
    parser.add_argument("--threads", "-t", type=int, help="The number of threads", default=6)
    parser.add_argument("--rebuild_vectorstore", action="store_true", help="Whether to build the vectorstore", default=False)

    args = parser.parse_args()

    if args.rebuild_vectorstore:
        import shutil
        shutil.rmtree("results/svc/db", ignore_errors=True)

    retriever = get_retriever(args.data_path)

    endpoint, llm, api_key = yaml.load(open("config/llm_config.yml", "r"), Loader=yaml.FullLoader).values()
    model_type = "local"
    
    time_stamp = datetime.now().timestamp()
    console_logger.info(f"llm: {llm}, model_type: {model_type}, endpoint: {endpoint}")
    log_file, querys, gts, evidences = get_data_ready(time_stamp)
    runner(log_file, retriever, querys, gts, evidences)
