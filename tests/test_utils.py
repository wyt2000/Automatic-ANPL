from utils import remove_implemented_functions, extract_asserts 

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


