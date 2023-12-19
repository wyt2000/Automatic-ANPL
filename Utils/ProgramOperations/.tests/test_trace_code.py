from Utils.ProgramOperations import trace_code 

def test_compile_error():
    code = '''
def main(input_str: str):
    +- 
    inputs = parse_input(input_str)
    return add_list(inputs)
    '''
    _, _, ios, exc = trace_code(code, ["1 2 3 4 5"])
    assert ios is None
    assert exc.args[0] == "invalid syntax (<unknown>, line 3): +-"


def test_io_trace():
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
    func_names_sorted, func_codes, ios, exc = trace_code(code, ["1 2 3 4 5"])
    assert func_names_sorted == ['add', 'add_list', 'parse_input', 'main']
    assert func_codes == {'add': 'def add(x: int, i: int):\n    return x + i', 'add_list': 'def add_list(inputs: list[int]):\n    for i in range(len(inputs)):\n        inputs[i] = add(inputs[i], i)\n    return inputs', 'parse_input': 'def parse_input(input_str: str):\n    input_list = list(map(int, input_str.split()))\n    return input_list', 'main': 'def main(input_str: str):\n    inputs = parse_input(input_str)\n    return add_list(inputs)'}
    assert repr(ios) == "IOCollector({'parse_input': [input: {'input_str': '1 2 3 4 5'}, output: [1, 2, 3, 4, 5]], 'add': [input: {'x': 1, 'i': 0}, output: 1, input: {'x': 2, 'i': 1}, output: 3, input: {'x': 3, 'i': 2}, output: 5], 'add_list': [input: {'inputs': [1, 2, 3, 4, 5]}, output: [1, 3, 5, 7, 9]], 'main': [input: {'input_str': '1 2 3 4 5'}, output: [1, 3, 5, 7, 9]]})"
    assert exc is None

def test_runtime_error():
    code = '''
def g(inputs: str):
    return inputs[100]
def f(inputs: str):
    return g(inputs) 
def parse_input(input_str: str):
    return input_str
def main(input_str: str):
    inputs = parse_input(input_str)
    return f(inputs)
    '''
    _, _, ios, exc = trace_code(code, ["123"])
    assert repr(ios) == "IOCollector({'parse_input': [input: {'input_str': '123'}, output: '123'], 'g': [input: {'inputs': '123'}, exception: IndexError('string index out of range') at line 3 in function 'g': return inputs[100]], 'f': [input: {'inputs': '123'}, exception: IndexError('string index out of range') at line 5 in function 'f': return g(inputs)], 'main': [input: {'input_str': '123'}, exception: IndexError('string index out of range') at line 10 in function 'main': return f(inputs)]})"
    assert "IndexError" in repr(exc.args[0])

def test_time_limit_exceeded():
    code = '''
from time import sleep
def g(inputs: str):
    sleep(5)
    return -1
def f(inputs: str):
    return g(inputs) 
def parse_input(input_str: str):
    return input_str
def main(input_str: str):
    inputs = parse_input(input_str)
    return f(inputs)
    '''
    _, _, ios, exc = trace_code(code, ["123"])
    assert repr(ios) == "IOCollector({'parse_input': [input: {'input_str': '123'}, output: '123'], 'g': [input: {'inputs': '123'}, exception: TimeoutError() at line 4 in function 'g': sleep(5)], 'f': [input: {'inputs': '123'}, exception: TimeoutError() at line 7 in function 'f': return g(inputs)], 'main': [input: {'input_str': '123'}, exception: TimeoutError() at line 12 in function 'main': return f(inputs)]})"
    assert "TimeoutError" in repr(exc.args[0])

def test_memory_limit_exceeded():
    code = '''
def g(inputs: str):
    a = [0] * 1000000000
    return -1
def f(inputs: str):
    return g(inputs) 
def parse_input(input_str: str):
    return input_str
def main(input_str: str):
    inputs = parse_input(input_str)
    return f(inputs)
    '''
    _, _, ios, exc = trace_code(code, ["123"])
    assert repr(ios) == "IOCollector({'parse_input': [input: {'input_str': '123'}, output: '123'], 'g': [input: {'inputs': '123'}, exception: MemoryError() at line 3 in function 'g': a = [0] * 1000000000], 'f': [input: {'inputs': '123'}, exception: MemoryError() at line 6 in function 'f': return g(inputs)], 'main': [input: {'input_str': '123'}, exception: MemoryError() at line 11 in function 'main': return f(inputs)]})"
    assert "MemoryError" in repr(exc.args[0])

def test_assert_str():
    code = '''
from typing import List
def f(arr: List[int]):
    return sum(arr)
def main(arr: List[int]):
    return f(arr) 
    '''
    _, _, ios, exc = trace_code(code, "assert main([1,2,3,4]) == 10, \"Wrong!\" ")
    assert repr(ios) == "IOCollector({'f': [input: {'arr': [1, 2, 3, 4]}, output: 10], 'main': [input: {'arr': [1, 2, 3, 4]}, output: 10]})"
    assert exc is None
    _, _, ios, exc = trace_code(code, "assert main([1,2,3,4]) == 15")
    assert repr(ios) == "IOCollector({'f': [input: {'arr': [1, 2, 3, 4]}, output: 10], 'main': [input: {'arr': [1, 2, 3, 4]}, output: 10]})"
    assert "assert main([1,2,3,4]) == 15" in repr(exc.args[0])

def test_args_error():
    code = '''
from typing import List
def f(x: int):
    return sum(arr)
def main(arr: List[int]):
    return f(1, 2) + 2
    '''
    _, _, ios, exc = trace_code(code, "assert main([1,2,3,4]) == 0, \"Wrong!\" ")
    assert repr(ios) == "IOCollector({'f': [input: {'x': 1}, exception: TypeError('f() takes 1 positional argument but 2 were given') at line 3 in function 'f': def f(x: int):], 'main': [input: {'arr': [1, 2, 3, 4]}, exception: TypeError('f() takes 1 positional argument but 2 were given') at line 6 in function 'main': return f(1, 2) + 2]})"
    assert "f() takes 1 positional argument but 2 were given" in repr(exc.args[0])


