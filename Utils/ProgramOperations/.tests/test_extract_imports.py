from Utils.ProgramOperations import extract_imports

def test_imports_1():
    code = '''
from math import sqrt
def g():
    "This is function g."
def f():
    "This is function f."
    import math
from utils import dummy
'''
    assert extract_imports(code) == "from math import sqrt\nfrom utils import dummy"

def test_imports_2():
    code = '''
def g():
    "This is function g."
    import math
    return 0
'''
    assert extract_imports(code) == ""
