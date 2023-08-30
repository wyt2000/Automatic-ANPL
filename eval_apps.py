import pathlib
from apps_metric.apps_metric import apps_metric

def get_codes(target_dir, num_problems, num_completions):
    generations = [[] for _ in range(num_problems)]
    paths = pathlib.Path(target_dir).glob("*.py")
    for path in paths:
        name = path.stem.split('_')
        problem_id = int(name[1])
        with open(path, 'r') as f:
            generations[problem_id - 3000].append(f.read())
    return generations

if __name__ == '__main__':
    generations = get_codes('parsel_apps_result_0830141001', 2, 4)
    results = apps_metric().compute(predictions=generations, k_list=[1], level="competition")
    print(results)

