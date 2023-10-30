import os
import shutil
import pathlib
import coloredlogs
import importlib
import logging 
import logging.config
import json
import functools
import operator
import random
import re
from contextlib import contextmanager

def mkdir_override(dir_path):
    '''
    mkdir: override if exists.
    '''
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    pathlib.Path(dir_path).mkdir(parents=True)

def mkdir_no_override(dir_path):
    '''
    mkdir: do nothing if exists.
    '''
    if os.path.exists(dir_path):
        return
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

@contextmanager
def redirect_loggers(log_path: str):
    '''
    Redirect loggers output to file
    '''
    file_handler = logging.FileHandler(log_path)
    root_logger = logging.getLogger('root')
    root_handlers = [root_logger.handlers[0]]
    root_logger.handlers = [file_handler]
    try:
        yield 
    finally:
        file_handler.close()
        root_logger.handlers = root_handlers

class Cache:
    '''
    Save the responses from GPT.
    '''
    def __init__(self, file_path='cache.json', clean=False):
        self.file_path = file_path
        if clean or not os.path.exists(file_path):
            self.data = {}
            return
        with open(file_path, 'r') as f:
            self.data = json.loads(f.read())

    def get_key(self, *args):
        return str(tuple(args))

    def save(self, responses, *args):
        self.data[self.get_key(*args)] = responses

    def load(self, *args):
        return self.data.get(self.get_key(*args))

    def dump(self):
        with open(self.file_path, 'w') as f:
            f.write(json.dumps(self.data))

def product_to_tensor_idx(prod, dims, idx):
    ans = []
    for dim in dims:
        prod //= dim
        ans.append(idx // prod)
        idx %= prod
    return ans

def sample_product(arrs, n, k):
    indices = random.sample(range(n), k)
    dims = [len(arr) for arr in arrs]
    prod = functools.reduce(operator.mul, dims, 1)
    return [
        product_to_tensor_idx(prod, dims, idx)
        for idx in indices
    ]

# Remove all implemented functions including nested functions
func_pattern = re.compile(r"\s*def\s+(.+)\(.*\).*\:")
def remove_implemented_functions(raw_code: str, target: str, implemented_functions: set[str]):
    # When meet the line "def {implemented_functions}", omit lines until the line whose indent count <= its
    has_target = False
    is_omit = False
    omit_indent = -1
    code = []
    for line in raw_code.splitlines():
        indent = len(line) - len(line.lstrip())
        if is_omit: # in scope of implemented functions
            if indent > omit_indent: continue
            is_omit = False
        if m := func_pattern.match(line): # meet func def
            func_name = m.group(1)
            if indent == 0 and func_name == target:
                has_target = True
            if func_name in implemented_functions: 
                is_omit = True
                omit_indent = indent
                continue
        code.append(line)
    return '\n'.join(code) if has_target else ''

# Extract import lines of ANPL or Python codes
def extract_imports(code: str):
    return '\n'.join([line for line in code.splitlines() if line.startswith('import ') or line.startswith('from ')])
code = '''
def f():
    def g():
        pass
    pass
def h():
    pass
def u():
    pass
    def v():
        pass
        def w():
            pass

'''
   
result = remove_implemented_functions(code, 'h', {'v', 'g'})
print(result)

