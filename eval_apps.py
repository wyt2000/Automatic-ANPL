import pathlib
from apps_metric.apps_metric import apps_metric
import argparse
import logging 
import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('main')

def get_codes(target_dir: str, num_codes: int):
    paths = list(pathlib.Path(target_dir).glob("*.py"))
    problem_ids = set()
    for path in paths:
        name = path.stem.split('_')
        problem_ids.add(int(name[1]))
    generations = {problem_id : ['_' for i in range(num_codes)] for problem_id in problem_ids}
    
    for path in paths:
        name = path.stem.split('_')
        problem_id = int(name[1])
        code_id = int(name[2])
        with open(path, 'r') as f:
            if code_id >= num_codes: continue
            generations[problem_id][code_id] = f.read()
    return list(generations.keys()), list(generations.values())

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-t", "--target", help="Path of target code folder", type=str, required=True)
    argparser.add_argument("-n", "--num_codes", help="Number of code for each problem", type=int, required=True)
    args = argparser.parse_args()

    problem_ids, generations = get_codes(args.target, args.num_codes)
    msg = f"Get {len(problem_ids)} problem_ids: "
    for problem_id in problem_ids:
        msg += f"{problem_id} "
    logger.debug(msg)
    results = apps_metric().compute(problem_ids=problem_ids, predictions=generations, k_list=[args.num_codes], debug=True)
    logger.info(results)

