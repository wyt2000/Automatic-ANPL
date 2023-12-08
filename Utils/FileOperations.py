import os
import shutil
import pathlib

__all__ = ['mkdir_override', 'mkdir_no_override']

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
