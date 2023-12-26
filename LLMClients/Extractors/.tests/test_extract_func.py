import ast
from LLMClients.Extractors import extract_func

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
    result = extract_func(code, 'u', {'u', 'g', 'h', 'w'})
    assert result.strip('\n') == ast.unparse(ast.parse('''
def f():
    pass
def u():
    pass
    def v():
        pass
''')).strip('\n')

    result = extract_func(code, 'h', {'h', 'v', 'g'})
    assert result.strip('\n') == ast.unparse(ast.parse('''
def f():
    pass
def h():
    pass
def u():
    pass
''')).strip('\n')