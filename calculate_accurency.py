import json
import pathlib

paths = pathlib.Path(".").glob("*.json")
paths = sorted(paths)
for path in paths:
    with open(path, 'r') as f:
        data = json.loads(f.read())
    block_num = int(path.stem.split("_")[-1])
    name = data["synthesizer_name"]
    data = data["judge_status"]
    ce = len(data.get("JudgeCompileError", []))
    wa = len(data.get("JudgeWrongAnswer", []))
    tle = len(data.get("JudgeTimeLimitExceeded", []))
    re = len(data.get("JudgeRuntimeError", []))
    ac = len(data.get("JudgeAccepted", []))
    print(f"[{name:^10}]\tlength:{block_num}\tac:{ac}\twa:{wa}\tce:{ce}\tre:{re}\ttle:{tle}\tacc:{ac / (ac+wa+ce+re+tle):.4f}")

