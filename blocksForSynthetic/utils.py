import pickle
import json
import time
import os

def read_io(path):
    with open(path, "r") as f:
        test = json.load(f)
    return test

def read_anpl(path):
    with open(path, "rb") as f:
        anpl = pickle.load(f)
    return anpl

def clean_anpl(prev_anpl, new_anpl):
    new_fun_names = set(new_anpl.funs.keys() - prev_anpl.funs.keys())
    subfuns = set()
    for name in new_fun_names:
        if name in new_anpl.funs:
            for n in new_anpl.funs[name].dependencies:
                subfuns.add(n)
    entries = new_fun_names - subfuns
    if len(entries) == 1:
        new_anpl.clean(entries.pop())
        return True
    else:
        return False

def save(anpl, save_path):
    code = anpl.to_python()
    with open(save_path, "w") as f:
        f.write(code)
