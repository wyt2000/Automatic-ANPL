import json
import pathlib

paths = pathlib.Path(".").glob("parsel*.json")
paths = sorted(paths)
for path in paths:
    with open(path, 'r') as f:
        data = json.loads(f.read())
    block_num = int(path.stem.split("_")[-1])
    name = data["compiler_name"]
    ce = len(data["compile_errors"])
    wa = len(data["wrong_answers"])
    tle = len(data["time_limit_exceededs"])
    re = len(data["runtime_errors"])
    ac = len(data["accepteds"])
    print(f"[{name:^10}]\tlength:{block_num}\tac:{ac}\twa:{wa}\tce:{ce}\tre:{20-ac-wa-ce-tle}\ttle:{tle}\tacc:{ac / (20):.4f}")

