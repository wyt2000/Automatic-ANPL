
__all__ = ['extract_code']

def extract_code(content: str):
    # Extract vaild Python code or ANPL code
    if not '`' in content:
        return content
    code = []
    is_target = False
    for line in content.splitlines():
        if '`' in line:
            if is_target:
                break
            else:
                is_target = True
                continue
        if is_target:
            code.append(line)
    return '\n'.join(code)
