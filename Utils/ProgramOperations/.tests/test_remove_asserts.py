from Utils.ProgramOperations import remove_asserts

def test_remove_asserts_in_top_level():
    code = '''
for i in range(100):
    if i % 10 == 0:
        assert 1 == 1
assert 2 == 2
def main(input_str: str):
    assert 3 == 3
    for i in range(100):
        if i % 10 == 0:
            assert 4 == 4
assert 5 == 5
'''
    assert remove_asserts(code).strip('\n') == '''
for i in range(100):
    if i % 10 == 0:
        pass
pass

def main(input_str: str):
    assert 3 == 3
    for i in range(100):
        if i % 10 == 0:
            assert 4 == 4
pass
'''.strip('\n')


def test_remove_asserts_with_recursive_call():
    code = '''
def main(input_str: str):
    assert 1 == 1
    for i in range(100):
        if i % 10 == 0:
            assert main('1') == '1'
'''
    assert remove_asserts(code).strip('\n') == '''
def main(input_str: str):
    assert 1 == 1
    for i in range(100):
        if i % 10 == 0:
            pass
'''.strip('\n')

   