from LLMClients.Extractors import extract_code

def test_extract_code_with_backticks():
    content = '''
This is a description...
```python
def f():
    return 0
def main():
    return f()
```
This is another description...
'''
    assert extract_code(content) == '''
def f():
    return 0
def main():
    return f()
'''.strip('\n')

def test_extract_code_without_backticks():
    content = '''
def f():
    return 0
def main():
    return f()
'''
    assert extract_code(content) == content