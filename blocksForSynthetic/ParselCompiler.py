from parsel.parsel import parsel_str, CodeGen

class ParselCompiler:
    name = 'parsel'
    def __init__(self):
        pass

    def compile(self, name, code, save_path):
        codegen = CodeGen('cache.json')
