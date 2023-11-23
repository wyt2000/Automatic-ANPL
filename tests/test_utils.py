from utils import remove_implemented_functions, extract_asserts, compose_function_with_traces
from Tracer import trace_code
import ast

def test_compose_function_with_traces():
    code = '''
def add(x: int, i: int):
    return x + i
def add_list(inputs: list[int]):
    for i in range(len(inputs)):
        inputs[i] = add(inputs[i], i)
    return inputs
def parse_input(input_str: str):
    input_list = list(map(int, input_str.split()))
    return input_list
def main(input_str: str):
    inputs = parse_input(input_str)
    return add_list(inputs)
    '''
    func_code = '''def add(x: int, i: int):
    return x + i'''
    _, _, ios, _ = trace_code(code, "assert main('1 2 3 4 5') == [1, 3, 5, 7, 9]")
    func = compose_function_with_traces(func_code, ios['add'])
    ans = '''# Trace: 
# input: {'x': 1, 'i': 0}, output: 1
# input: {'x': 2, 'i': 1}, output: 3
# input: {'x': 3, 'i': 2}, output: 5
def add(x: int, i: int):
    return x + i'''
    assert func == ans

def test_extract_asserts():
    code = '''
def f():
    while True:
        assert f(1) == 1, 'xxx' #yyy
    '''
    assert extract_asserts(code) == "assert f(1) == 1, 'xxx'"
    code = '''
assert f(1) == 1, 'xxx' #yyy
assert f(2) == 2 # Hello! 
assert f(3) == 1 + 2
    '''
    assert set(extract_asserts(code).split('\n')) == set('''
assert f(1) == 1, 'xxx'
assert f(2) == 2
assert f(3) == 1 + 2
'''.strip('\n').split('\n'))
    code = '''
    +-
    assert 1 == 2
    '''
    assert extract_asserts(code) == ''
    
def test_remove_implemented_functions():
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
    result = remove_implemented_functions(code, 'u', {'g', 'h', 'w'})
    assert result.strip('\n') == ast.unparse(ast.parse('''
def f():
    pass
def u():
    pass
    def v():
        pass
''')).strip('\n')

    result = remove_implemented_functions(code, 'h', {'v', 'g'})
    assert result.strip('\n') == ast.unparse(ast.parse('''
def f():
    pass
def h():
    pass
def u():
    pass
''')).strip('\n')

