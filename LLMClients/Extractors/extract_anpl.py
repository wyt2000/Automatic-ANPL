from Utils.ProgramOperations import extract_imports

__all__ = ['extract_anpl']

def extract_anpl(content: str, question: str):
    # Extract anpl code and add imports from question 
    return '\n'.join([extract_imports(question), content])
