from ResponseWrapper import AbstractResponseWrapper
import re

class ANPLResponseWrapper(AbstractResponseWrapper):

    def wrap(self, response, *args):
        func_head = re.compile("def .+\(.+\).*\:")
        func_return = 'return'
        lines = response.split('\n')
        code = []
        ok = False
        for line in lines:
            if func_head.match(line):
                ok = True
            if ok:
                code.append(line)
            if ok and func_return in line:
                break
        return '\n'.join(code)

