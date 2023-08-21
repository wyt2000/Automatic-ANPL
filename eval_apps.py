import pathlib
import json
from apps_metric.apps_metric import apps_metric

def get_codes(target_dir, prefix, num_problems):
    generations = [None] * num_problems
    for i in range(num_problems):
        path = pathlib.Path(target_dir, f'{prefix}_{i}.json')
        with open(path, 'r') as f:
            generations[i] = json.loads(f.read())[:20]
    return generations

if __name__ == '__main__':
    generations = get_codes('gpt_apps_code', 'gpt', 5)
    results = apps_metric().compute(predictions=generations, k_list=[20], level="all")
    print(results)

