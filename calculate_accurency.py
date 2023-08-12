import json
import pathlib

paths = pathlib.Path(".").glob("*.json")
paths = sorted(paths)
for path in paths:
    with open(path, 'r') as f:
        data = json.loads(f.read())
    block_num = int(path.stem.split("_")[-1])
    name = data["compiler_name"]
    ce = len(data["JudgeCompileError"])
    wa = len(data["JudgeWrongAnswer"])
    tle = len(data["JudgeTimeLimitExceeded"])
    re = len(data["JudgeRuntimeError"])
    ac = len(data["JudgeAccepted"])
    print(f"[{name:^10}]\tlength:{block_num}\tac:{ac}\twa:{wa}\tce:{ce}\tre:{re}\ttle:{tle}\tacc:{ac / (ac+wa+ce+re+tle):.4f}")

