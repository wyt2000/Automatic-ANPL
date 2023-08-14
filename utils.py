import os
import shutil
import pathlib
import coloredlogs

def mkdir_override(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    pathlib.Path(dir_path).mkdir(parents=True)

class ColoredFormatter(coloredlogs.ColoredFormatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        '''Match coloredlogs.ColoredFormatter arguments with logging.Formatter'''
        coloredlogs.ColoredFormatter.__init__(self, fmt=fmt, datefmt=datefmt)
