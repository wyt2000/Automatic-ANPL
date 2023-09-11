import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from Synthesizer.Synthesizer import AbstractSynthesizer 
from Synthesizer.ParselSynthesizer import ParselSynthesizer
from pathlib import Path
from utils import mkdir_override, mkdir_no_override
import logging 
import logging.config
from contextlib import redirect_stdout
from contextlib import redirect_stderr

import argparse

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

def generate(task_name: str,
             synthesizer: AbstractSynthesizer,
             n: int,
             k: int,
             input_dir: str,
             save_dir: str,
             cache_dir: str,
             log_dir: str,
             suffix_name: str
             ):

    for i in range(n):
        logger.debug(f"Synthesizing {task_name}_{i}...")
        with open(Path(input_dir, f"{task_name}_{i}.{suffix_name}")) as f:
            code = f.read()
        try:
            with open(Path(log_dir, f"{task_name}_{i}.log"), "w") as log_file:
                with redirect_stdout(log_file), redirect_stderr(log_file):
                    synthesizer.synthesize(
                        code,
                        Path(save_dir, f"{task_name}_{i}"),
                        Path(cache_dir, f"{task_name}_{i}"),
                        [k]
                    )
        except Exception as err:
            logger.exception(err)
        logger.debug(f"Synthesizing {task_name}_{i} done!")

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--path", help="Path of input code folder", type=str, required=True)
    argparser.add_argument("-n", "--num_codes", help="Number of code for each problem", type=int, default=1)
    argparser.add_argument("-k", "--num_completions", help="Number of function implementations for each code", type=int, default=4)
    args = argparser.parse_args()

    synthesizer = ParselSynthesizer()

    suffix_name = "ss"
    paths = list(Path(args.path).glob(f"*.{suffix_name}"))
    tasks = {f"apps_{path.stem.split('_')[1]}" for path in paths}
    tasks = sorted(tasks)
    n = args.num_codes
    k = args.num_completions
    input_dir = args.path 
    cache_dir = input_dir.replace("code", "cache")
    log_dir = input_dir.replace("code", "log")
    save_dir = Path(input_dir.replace("code", "result"), f"{n}x{k}")
    mkdir_override(save_dir)
    mkdir_no_override(cache_dir)
    mkdir_override(log_dir)
    logger.debug(f"Synthesizing {len(tasks)} problems : use {n} code, generate {k} python code for each function!")
    logger.debug(tasks)

    for task in tasks:
        generate(task, synthesizer, n, k, input_dir, save_dir, cache_dir, log_dir, suffix_name)

