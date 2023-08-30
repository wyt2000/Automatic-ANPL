from Synthesizer.ParselSynthesizer import ParselSynthesizer
from pathlib import Path
from utils import mkdir_override, mkdir_no_override
import logging 
import logging.config
from contextlib import redirect_stdout
from contextlib import redirect_stderr

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

def generate(task_name: str,
             n: int,
             k: int,
             input_dir: str,
             save_dir: str,
             cache_dir: str,
             log_dir: str,
             suffix_name: str
             ):

    parsel = ParselSynthesizer()
    for i in range(n):
        logger.debug(f"Synthesizing {task_name}_{i}...")
        with open(Path(input_dir, f"{task_name}_{i}.{suffix_name}")) as f:
            parsel_code = f.read()
        try:
            with open(Path(log_dir, f"{task_name}_{i}.log"), "w") as log_file:
                with redirect_stdout(log_file), redirect_stderr(log_file):
                    parsel.synthesize(
                        parsel_code = parsel_code,
                        save_path_prefix = Path(save_dir, f"{task_name}_{i}"),
                        cache_path_prefix = Path(cache_dir, f"{task_name}_{i}"),
                        num_completions_list = [k]
                    )
        except Exception as err:
            logger.exception(err)
        logger.debug(f"Synthesizing {task_name}_{i} done!")

if __name__ == '__main__':
    input_dir = "parsel_apps_code_0830141001"
    save_dir = input_dir.replace("code", "result")
    cache_dir = input_dir.replace("code", "cache")
    log_dir = input_dir.replace("code", "log")
    suffix_name = "ss"
    begin = 3000
    end = 3002
    tasks = [f"apps_{i}" for i in range(begin, end)]
    n = 1
    k = 4
    mkdir_override(save_dir)
    mkdir_no_override(cache_dir)
    mkdir_override(log_dir)
    logger.debug(f"Synthesizing code from {begin} to {end}: use {n} parsel code, each code generate {k} python code for each function!")

    for task in tasks:
        generate(task, n, k, input_dir, save_dir, cache_dir, log_dir, suffix_name)

