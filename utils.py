import os
import shutil
import pathlib
import coloredlogs
import importlib

def mkdir_override(dir_path):
    '''
    mkdir: override if exists.
    '''
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    pathlib.Path(dir_path).mkdir(parents=True)

color_ansi = {
    'red'   : '\033[31m',
    'green' : '\033[32m',
    'reset' : '\033[00m'
}
def color_str(s, color):
    '''
    Add color to str. 
    '''
    if color not in color_ansi:
        return s
    return color_ansi[color] + s + color_ansi['reset']

class ColoredFormatter(coloredlogs.ColoredFormatter):
    '''
    Colored log formatter.
    '''
    def __init__(self, fmt=None, datefmt=None, style='%'):
        '''Match coloredlogs.ColoredFormatter arguments with logging.Formatter'''
        coloredlogs.ColoredFormatter.__init__(self, fmt=fmt, datefmt=datefmt)

def make_object(module_name, class_name, **kwargs):
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls(**kwargs)
