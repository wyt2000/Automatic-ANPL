import pathlib
from apps_metric.apps_metric import apps_metric
import argparse

def get_codes(target_dir: str,
              start_problem_id: int,
              num_problems: int,
              num_codes: int,
              num_completions: int,
              ):
    generations = [['' for j in range(num_codes)] for i in range(num_problems)]
    paths = pathlib.Path(target_dir).glob("*.py")
    for path in paths:
        name = path.stem.split('_')
        problem_id = int(name[1])
        if problem_id - start_problem_id >= num_problems: continue
        code_id = int(name[2])
        with open(path, 'r') as f:
            s = generations[problem_id - start_problem_id][code_id]
            generations[problem_id - start_problem_id][code_id] = f.read()
    return generations

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-t", "--target", help="Path of target code folder", type=str, required=True)
    argparser.add_argument("-s", "--start", help="Start problem id", type=int, required=True)
    argparser.add_argument("-p", "--num_problems", help="Number of problems", type=int, required=True)
    argparser.add_argument("-n", "--num_codes", help="Number of code for each problem", type=int, required=True)
    argparser.add_argument("-k", "--num_completions", help="Number of function implementations for each code", type=int, required=True)
    args = argparser.parse_args()

    generations = get_codes(args.target, args.start, args.num_problems, args.num_codes, args.num_completions)
    generations = [[gen[1]] for gen in generations]
    #print(generations)
    results = apps_metric().compute(predictions=generations, k_list=[args.num_codes], level="introductory")
    print(results)

