from utils import remove_implemented_functions

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
    assert result.strip('\n') == '''
def f():
    pass
def u():
    pass
    def v():
        pass
'''.strip('\n')

    result = remove_implemented_functions(code, 'h', {'v', 'g'})
    assert result.strip('\n') == '''
def f():
    pass
def h():
    pass
def u():
    pass
'''.strip('\n')


