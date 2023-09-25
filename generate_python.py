from Synthesizer.Synthesizer import AbstractSynthesizer 
from Synthesizer.ANPLSynthesizer import ANPLSynthesizer 
from ProblemSampler.APPSProblemSampler import APPSProblemSampler

from pathlib import Path
from utils import mkdir_override, mkdir_no_override
import logging 
import logging.config
from contextlib import redirect_stdout
from contextlib import redirect_stderr
import json
import argparse

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

def generate(problem_id: int,
             synthesizer: AbstractSynthesizer,
             sampler: APPSProblemSampler,
             n: int,
             k: int,
             input_dir: str,
             save_dir: str,
             cache_dir: str,
             log_dir: str,
             suffix_name: str
             ):

    task_name = f"apps_{problem_id}"
    question = sampler.apps[problem_id]["question"]
    input_output = sampler.apps[problem_id]["input_output"]
    input_output = json.loads(input_output)
    inputs = input_output["inputs"]
    outputs = input_output["outputs"]

    for i in range(n):
        logger.debug(f"Synthesizing {task_name}_{i}...")
        try:
            with open(Path(input_dir, f"{task_name}_{i}.{suffix_name}")) as f:
                code = f.read()
            log_path = Path(log_dir, f"{task_name}_{i}.log")
            with open(log_path, "w") as log_file:
                with redirect_stdout(log_file), redirect_stderr(log_file):
                    file_handler = logging.FileHandler(log_path)
                    root_logger = logging.getLogger('root')
                    root_handlers = [root_logger.handlers[0]]
                    root_logger.handlers = [file_handler]
                    synthesizer.synthesize(
                        f"{task_name}_{i}",
                        code,
                        Path(save_dir, f"{task_name}_{i}"),
                        Path(cache_dir, f"{task_name}_{i}"),
                        question,
                        inputs,
                        outputs,
                        [k]
                    )
                    file_handler.close()
                    root_logger.handlers = root_handlers
        except Exception as err:
            logger.exception(err)
        logger.debug(f"Synthesizing {task_name}_{i} done!")

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--path", help="Path of input code folder", type=str, required=True)
    argparser.add_argument("-n", "--num_codes", help="Number of code for each problem", type=int, default=1)
    argparser.add_argument("-k", "--num_completions", help="Number of function implementations for each code", type=int, default=4)
    args = argparser.parse_args()

    synthesizer = ANPLSynthesizer()
    sampler = APPSProblemSampler(difficulties=['all'])

    suffix_name = 'anpl'
    paths = list(Path(args.path).glob(f"*.{suffix_name}"))
    problem_ids = {int(path.stem.split('_')[1]) for path in paths}
    problem_ids = sorted(problem_ids)

    n = args.num_codes
    k = args.num_completions
    input_dir = args.path 
    cache_dir = input_dir.replace("code", "cache")
    log_dir = Path(input_dir.replace("code", "log"), f"{n}x{k}")
    save_dir = Path(input_dir.replace("code", "result"), f"{n}x{k}")
    mkdir_override(save_dir)
    mkdir_no_override(cache_dir)
    mkdir_override(log_dir)
    logger.debug(f"Synthesizing {len(problem_ids)} problems : use {n} code, generate {k} python code for each function!")
    logger.debug(problem_ids)

    for problem_id in problem_ids:
        generate(problem_id, synthesizer, sampler, n, k, input_dir, save_dir, cache_dir, log_dir, suffix_name)

