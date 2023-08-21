import pathlib
import json
from evaluate import load

def get_codes(target_dir, prefix, num_problems):
    generations = [None] * num_problems
    for i in range(num_problems):
        path = pathlib.Path(target_dir, f'{prefix}_{i}.json')
        with open(path, 'r') as f:
            generations[i] = json.loads(f.read())

if __name__ == '__main__':
    generations = get_codes('gpt_apps_code', 'gpt', 5)
    apps_metric = load('codeparrot/apps_metric')
    results = apps_metric.compute(predictions=generations, level="all")
    print(results)

