import requests
import subprocess
from multiprocessing import Pool
from torch import cuda
import argparse


def _start_worker(port, device):
    obj = subprocess.Popen(
        [
            "python",
            "-m",
            "embedding_api",
            "--device",
            str(device),
            "--port",
            str(port)
        ],
    )
    print(f"Worker {device} started on port {port}, device {device}")
    obj.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Embedding server")
    parser.add_argument("--worker", "-w", type=int, default=1)
    parser.add_argument("--port", "-p", type=int, default=15888)
    
    args = parser.parse_args()

    pool = Pool(args.worker)

    for i in range(args.worker):
        pool.apply_async(_start_worker, (args.port + i, i % cuda.device_count()))
    pool.close()
    pool.join()
    print("All workers started")
