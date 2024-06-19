import argparse
import os
import subprocess
import time
from urllib.parse import urlparse

import requests

from .configs import ConfigLoader


def _start_worker(name, port, controller, definition):
    subprocess.Popen(
        [
            "python",
            "-m",
            "tasks.KGQA.server.task_worker",
            name,
            "--self",
            f"http://localhost:{port}/api",
            "--port",
            str(port),
            "--controller",
            controller,
            "--config",
            os.path.join(os.path.dirname(__file__), "configs/tasks/kg.yaml")
        ],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        help="Config file to load",
        default=os.path.join(os.path.dirname(__file__), "configs/start_task.yaml"),
    )
    parser.add_argument(
        "--start",
        "-s",
        dest="start",
        type=str,
        nargs="*",
        help="name num_worker name num_worker ...",
    )
    parser.add_argument("--controller", "-l", dest="controller_addr", default="")
    parser.add_argument(
        "--auto-controller", "-a", dest="controller", action="store_true"
    )
    parser.add_argument("--base-port", "-p", dest="port", type=int, default=6001)  # 6001 is for debug, 5001 is for formal usage.
  
    args = parser.parse_args()

    config = ConfigLoader().load_from(args.config)

    root = os.path.dirname(os.path.abspath(__file__))

    if args.controller_addr:
        controller_addr = args.controller_addr
    elif "controller" in config:
        
        controller_addr = config["controller"]
    else:
        controller_addr = f"http://localhost:7624/api"
        
    controller_port = controller_addr.split(":")[2].split("/")[0]

    if args.controller:
        subprocess.Popen(
            ["python", "-m", "tasks.KGQA.server.task_controller", "--port", str(controller_port)]
        )
        for i in range(10):
            try:
                requests.get(f"{controller_addr}/list_workers")
                break
            except Exception as e:
                print("Waiting for controller to start...")
                time.sleep(0.5)
        else:
            raise Exception("Controller failed to start")

    base_port = args.port


    if "start" in config.keys() and not args.start:
        for key, val in config.get("start", {}).items():
            for _ in range(val):
                _start_worker(key, base_port, controller_addr, config["definition"])
                base_port += 1

    n = len(args.start) if args.start else 0
    if n % 2 != 0:
        raise ValueError(
            "--start argument should strictly follow the format: name1 num1 name2 num2 ..."
        )
    for i in range(0, n, 2):
        for _ in range(int(args.start[i + 1])):
            _start_worker(args.start[i], base_port, controller_addr, config["definition"])
            base_port += 1

    while True:
        input()

# try: python start_task.py ../configs/server/test.yaml -a
