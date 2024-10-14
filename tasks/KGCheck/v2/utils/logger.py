import logging
import sys
import os
from pathlib import Path

MEMO_PATH = Path('results/kgcheck/agent_memory')
os.makedirs(MEMO_PATH, exist_ok=True)

def agent_memory(name, index) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    file_path = MEMO_PATH / str(index)
    os.makedirs(file_path, exist_ok=True)
    file_handler = logging.FileHandler(file_path / f"{name}.log")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def check_tool() -> logging.Logger:
    '''The usage of all tools will be recorded together.'''
    logger = logging.getLogger("tool usage record")
    logger.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(MEMO_PATH / "tool_usage_record.log")
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(dir_path, name, index) -> logging.Logger:
    
    logger = logging.getLogger(f"{name} - {index}")
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(dir_path+f"/{name} - {index}.log")
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger