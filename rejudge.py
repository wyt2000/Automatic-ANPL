# Rejudge the results by official humaneval evaluation

from human_eval.data import write_jsonl, read_problems

import logging
import logging.config
import pathlib
import os
import sys
import argparse
from utils import mkdir_override

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-i", "--input_dir", help="solution dir", type=str, required=True)
    argparser.add_argument("-o", "--output_path", help="result json path", type=str, required=True)
    args = argparser.parse_args()
    
    problem_dirs = pathlib.Path(args.input_dir).glob("HumanEval_*")
    all_problems = read_problems()

    problems = []
    samples = []
    for problem_path in problem_dirs:
        task_id = int(str(problem_path).split('_')[-1])
        for program_file in pathlib.Path(problem_path).glob("*"):
            if "final_submit" not in str(program_file): continue
            with open(program_file, 'r') as f:
                program = f.read()
            task_id = f"HumanEval/{task_id}"
            samples.append(dict(task_id=task_id, completion=program))
            problems.append(all_problems[task_id])
    write_jsonl(args.output_path, samples)
    problems_path = args.output_path + ".problems"
    write_jsonl(problems_path, problems)

    os.system(f"evaluate_functional_correctness {args.output_path} --problem_file={problems_path}")

