import os
import shutil
import pathlib
from typing import Any, List

__all__ = [
    'mkdir_override',
    'mkdir_no_override',
    'save_one',
    'save_all',
]

def mkdir_override(dir_path):
    # mkdir: override if exists.
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    pathlib.Path(dir_path).mkdir(parents=True)

def mkdir_no_override(dir_path):
    # mkdir: do nothing if exists.
    if os.path.exists(dir_path):
        return
    pathlib.Path(dir_path).mkdir(parents=True)

def save_one(result: Any, save_dir: str, filename: str):
    # Save response to file
    with open(pathlib.Path(save_dir, filename), 'w') as f:
        f.write(str(result))

def save_all(results: List[Any], save_dir: str, filename: str):
    # Save responses to files named as 0 to n - 1
    for i, response in enumerate(results):
        with open(pathlib.Path(save_dir, filename.format(i=i)), 'w') as f:
            f.write(str(response))
