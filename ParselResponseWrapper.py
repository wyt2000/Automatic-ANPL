from ResponseWrapper import AbstractResponseWrapper

class ParselResponseWrapper(AbstractResponseWrapper):

    def wrap(self, response, *args):
        mark = "\"\"\""
        lines = response.split('\n')
        code = []
        ok = False
        for line in lines:
            if mark in line:
                if ok:
                    break
                ok = True
                continue
            if ok:
                code.append(line)
        return '\n'.join(code)

