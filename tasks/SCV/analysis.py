from glob import glob
import jsonlines
from loguru import logger as logging
import numpy as np
import os
from pathlib import Path
import argparse

from ..utils.constant_ import REFUTES_OPTION, SUPPORTS_OPTION, UNSURE_OPTION


def analysis_task2(result_file):
    tag = Path(result_file).stem.split('_')
    dataset, timestamp, llm = tag[0], tag[1], tag[-1]
    index_slice, right_answer_slice, right_quotes_slice, not_sure_slice, error_answer_slice = 0, 0, 0, 0, 0
    with open(result_file) as f1:
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
    
    logging.info(f"dataset: {dataset}, timestamp: {timestamp}, llm: {llm}")
    logging.info(f"right: {right_answer_slice / 3}/{index_slice / 3}, right quotes: {right_quotes_slice / 3}/{index_slice / 3}, error: {error_answer_slice / 3}/{index_slice / 3}, not sure: {not_sure_slice / 3}/{index_slice / 3}")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Task SCV")
    parser.add_argument("--result", "-r", type=str, help="The path to the result file", required=True)
    args = parser.parse_args()

    analysis_task2(args.result)
