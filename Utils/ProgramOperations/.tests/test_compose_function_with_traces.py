from Utils.ProgramOperations import compose_function_with_traces
from Utils.ProgramOperations import trace_code 

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
    func_with_traces = compose_function_with_traces(func_codes['add'], ios['add'])
    assert func_with_traces == '''# Trace: 
# input: {'x': 1, 'i': 0}, output: 1
# input: {'x': 2, 'i': 1}, output: 3
# input: {'x': 3, 'i': 2}, output: 5
def add(x: int, i: int):
    return x + i
'''.strip('\n')


