# Update rejudge results

from human_eval.data import write_jsonl, read_problems
from human_eval.execution import check_correctness

import pathlib
import os
import argparse

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-i", "--input_dir", help="solution dir", type=str, required=True)
    args = argparser.parse_args()
    
    problem_dirs = pathlib.Path(args.input_dir).glob("HumanEval_*")
    all_problems = read_problems()

    problems = []
    samples = []
    for problem_path in problem_dirs:
        task_id = int(str(problem_path).split('_')[-1])
        for program_file in pathlib.Path(problem_path).glob("*"):
            if "final_submit" not in str(program_file): continue
            path = program_file
            if os.path.exists(path):
                anpl_path = pathlib.Path(problem_path, program_file)
                with open(path, 'r') as f:
                    program = f.read()
                os.remove(path)
                try:
                    status = check_correctness(all_problems[f"HumanEval/{task_id}"], program, 3.0)
                    if status['passed']:
                        print(f"{task_id}: accepted!")
                        with open(pathlib.Path(problem_path, f"HumanEval_{task_id}_final_submit_True.py",), 'w') as f:
                            f.write(program)
                    else:
                        raise Exception(f"{task_id}: failed! {status['result']}")
                except Exception as err:
                    print(err)
                    with open(pathlib.Path(problem_path, f"HumanEval_{task_id}_final_submit_False.py",), 'w') as f:
                        f.write(program)
                break

                        
