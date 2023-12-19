
__all__ = ['verify_python']

def verify_python(string):
    # Verify python syntax, faster than `ast.parse`.
    if not string: return False
    try:
        compile(string, '<string>', 'exec')
        return True
    except SyntaxError:
        return False
