import json
import pathlib

paths = pathlib.Path(".").glob("anpl*.json")
for path in paths:
    with open(path, 'r') as f:
        data = json.loads(f.read())
    block_num = int(path.stem.split("_")[-1])
    name = data["compiler_name"]
    ce = len(data["compile_errors"])
    wa = len(data["wrong_answers"]) 
    tle = len(data["time_limit_exceededs"])
    ac = len(data["accepteds"])
    print(f"[{name}]\tlength:{block_num}\tac:{ac}\twa:{wa}\tce:{ce}\ttle:{tle}\tacc:{ac / (ac+wa+ce+tle):.4f}")

