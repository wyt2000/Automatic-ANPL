import os
import shutil
import pathlib

def mkdir_override(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    pathlib.Path(dir_path).mkdir(parents=True)

